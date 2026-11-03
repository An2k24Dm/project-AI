"""Coordinación y caché de datos, inferencia y escenarios financieros."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

import numpy as np
import pandas as pd
import streamlit as st

from src.analytics import calcular_indicadores, enriquecer_resultados
from src.constants import CATALOG_PATH, CLIENTS_PATH, MODELS_DIR
from src.data_processing import (
    buscar_cliente,
    cargar_catalogo,
    cargar_clientes,
    crear_catalogo_escenario,
)
from src.financial import calcular_umbrales_comerciales, evaluar_cartera

if TYPE_CHECKING:
    from src.prediction import PredictorFuga


Indicadores: TypeAlias = dict[str, float | int | None]
ParametrosEscenario: TypeAlias = tuple[tuple[int, float, float], ...]

RESOURCE_PATHS = (
    CLIENTS_PATH,
    CATALOG_PATH,
    MODELS_DIR / "modelo_churn.keras",
    MODELS_DIR / "preprocesador.joblib",
    MODELS_DIR / "correccion_probabilidades.json",
)


@dataclass(frozen=True)
class DatosAplicacion:
    """Datos validados requeridos por las páginas."""

    clientes: pd.DataFrame
    catalogo: pd.DataFrame


@dataclass(frozen=True)
class EscenarioCartera:
    """Resultados completos de un escenario financiero."""

    probabilidades: np.ndarray
    umbrales: dict[str, dict[float, float]]
    cartera: pd.DataFrame
    indicadores: Indicadores


@dataclass(frozen=True)
class EscenarioSimulado:
    """Catálogo temporal y resultados derivados de una simulación."""

    catalogo: pd.DataFrame
    cartera: pd.DataFrame
    indicadores: Indicadores


def obtener_version_recursos(paths: tuple[Path, ...] = RESOURCE_PATHS) -> str:
    """Crea una firma ligera a partir de tamaño y fecha de cada recurso.

    La firma evita releer el modelo completo en cada interacción y cambia ante
    cualquier escritura o reemplazo normal de datos, catálogo o artefactos.
    """

    metadata = []
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"No se encontró el recurso requerido: {path}")
        stat = path.stat()
        metadata.append((path.name, stat.st_size, stat.st_mtime_ns))
    payload = json.dumps(metadata, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


@st.cache_data(show_spinner=False)
def cargar_datos_aplicacion(version: str) -> DatosAplicacion:
    """Carga clientes y catálogo; ``version`` controla la invalidación."""

    del version
    return DatosAplicacion(cargar_clientes(), cargar_catalogo())


@st.cache_resource(show_spinner=False)
def cargar_predictor(version: str) -> "PredictorFuga":
    """Mantiene una instancia del predictor por versión de artefactos."""

    del version
    from src.prediction import PredictorFuga

    return PredictorFuga()


@st.cache_data(show_spinner=False)
def obtener_umbrales_comerciales(
    version: str,
) -> dict[str, dict[float, float]]:
    """Calcula una vez los percentiles sobre la cartera completa."""

    datos = cargar_datos_aplicacion(version)
    return calcular_umbrales_comerciales(datos.clientes, datos.catalogo)


@st.cache_data(show_spinner=False)
def generar_probabilidades(version: str) -> np.ndarray:
    """Ejecuta y almacena la inferencia por lotes de la cartera completa."""

    datos = cargar_datos_aplicacion(version)
    return cargar_predictor(version).predecir_lote(datos.clientes)


@st.cache_data(show_spinner=False)
def construir_escenario_base(version: str) -> EscenarioCartera:
    """Construye las decisiones de referencia sin repetir inferencia."""

    datos = cargar_datos_aplicacion(version)
    probabilidades = generar_probabilidades(version)
    umbrales = obtener_umbrales_comerciales(version)
    decisiones = evaluar_cartera(
        datos.clientes,
        probabilidades,
        datos.catalogo,
        umbrales,
    )
    cartera = enriquecer_resultados(datos.clientes, decisiones)
    return EscenarioCartera(
        probabilidades=probabilidades,
        umbrales=umbrales,
        cartera=cartera,
        indicadores=calcular_indicadores(cartera),
    )


@st.cache_data(show_spinner=False)
def obtener_resultado_cliente(version: str, customer_id: object) -> pd.Series:
    """Evalúa un cliente sin construir previamente toda la cartera."""

    datos = cargar_datos_aplicacion(version)
    cliente = buscar_cliente(datos.clientes, customer_id)
    cliente_df = datos.clientes.loc[
        datos.clientes["CustomerId"].eq(cliente["CustomerId"])
    ]
    probabilidad = cargar_predictor(version).predecir(cliente_df)
    decision = evaluar_cartera(
        cliente_df,
        np.array([probabilidad]),
        datos.catalogo,
        obtener_umbrales_comerciales(version),
    )
    return enriquecer_resultados(cliente_df, decision).iloc[0].copy()


@st.cache_data(show_spinner=False)
def construir_escenario_simulado(
    version: str,
    parametros: ParametrosEscenario,
) -> EscenarioSimulado:
    """Recalcula finanzas sin volver a ejecutar el MLP."""

    datos = cargar_datos_aplicacion(version)
    base = construir_escenario_base(version)
    cambios = {
        incentive_id: {
            "costo_anual_usd": cost,
            "efectividad": effectiveness,
        }
        for incentive_id, cost, effectiveness in parametros
    }
    catalogo_simulado = crear_catalogo_escenario(datos.catalogo, cambios)
    decisiones = evaluar_cartera(
        datos.clientes,
        base.probabilidades,
        catalogo_simulado,
        base.umbrales,
    )
    cartera = enriquecer_resultados(datos.clientes, decisiones)
    return EscenarioSimulado(
        catalogo=catalogo_simulado,
        cartera=cartera,
        indicadores=calcular_indicadores(cartera),
    )
