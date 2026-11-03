"""Carga y consulta de datos para la aplicación Streamlit."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd

from src.constants import CATALOG_PATH, CLIENTS_PATH, FEATURES
from src.financial import validar_catalogo

APP_REQUIRED_COLUMNS = {
    "CustomerId",
    "Surname",
    "Age",
    "Geography",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "IsActiveMember",
    "MonthlyTransactions_Sim",
    "MonthlyTransactionVolume_USD_Sim",
    "AvgTransactionFee_USD_Sim",
    "AnnualCommissionIncome_USD_Sim",
    "AnnualFinancialMargin_USD_Sim",
    "AnnualOperatingCosts_USD_Sim",
    "AnnualNetMargin_USD_Sim",
    "ProfitabilitySegment_Sim",
    *FEATURES,
}


class ClienteNoEncontradoError(LookupError):
    """Indica que el identificador solicitado no existe en la cartera."""


def cargar_clientes(path: str | Path = CLIENTS_PATH) -> pd.DataFrame:
    """Carga y valida la cartera con sus variables financieras simuladas."""

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"No se encontró el dataset de clientes: {source}")
    clients = pd.read_csv(source)
    missing = sorted(APP_REQUIRED_COLUMNS - set(clients.columns))
    if missing:
        raise ValueError(f"El dataset está incompleto: {missing}")
    if clients.empty:
        raise ValueError("El dataset de clientes está vacío.")
    if clients["CustomerId"].isna().any() or not clients["CustomerId"].is_unique:
        raise ValueError("CustomerId debe ser completo y único.")

    numeric_columns = [
        *FEATURES,
        "MonthlyTransactions_Sim",
        "MonthlyTransactionVolume_USD_Sim",
        "AvgTransactionFee_USD_Sim",
        "AnnualCommissionIncome_USD_Sim",
        "AnnualFinancialMargin_USD_Sim",
        "AnnualOperatingCosts_USD_Sim",
        "AnnualNetMargin_USD_Sim",
    ]
    numeric_columns.remove("Geography")
    for column in numeric_columns:
        clients[column] = pd.to_numeric(clients[column], errors="raise")
    numeric_values = clients[numeric_columns].to_numpy(dtype=float)
    if not np.isfinite(numeric_values).all():
        raise ValueError("Las variables numéricas deben ser finitas.")

    nonnegative_columns = [
        "Balance",
        "MonthlyTransactions_Sim",
        "MonthlyTransactionVolume_USD_Sim",
        "AvgTransactionFee_USD_Sim",
        "AnnualCommissionIncome_USD_Sim",
        "AnnualFinancialMargin_USD_Sim",
        "AnnualOperatingCosts_USD_Sim",
    ]
    if clients[nonnegative_columns].lt(0).any().any():
        raise ValueError(
            "Las variables de actividad, ingresos y costos no pueden ser negativas."
        )
    if not clients["ProfitabilitySegment_Sim"].isin(
        ["Rentable", "Deficitario"]
    ).all():
        raise ValueError("ProfitabilitySegment_Sim contiene valores desconocidos.")
    expected_profitability = clients["AnnualNetMargin_USD_Sim"].gt(0).map(
        {True: "Rentable", False: "Deficitario"}
    )
    if not clients["ProfitabilitySegment_Sim"].equals(expected_profitability):
        raise ValueError("La rentabilidad no coincide con el margen neto simulado.")
    return clients


def cargar_catalogo(path: str | Path = CATALOG_PATH) -> pd.DataFrame:
    """Carga una copia validada del catálogo académico."""

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"No se encontró el catálogo: {source}")
    return validar_catalogo(pd.read_csv(source))


def buscar_cliente(clientes: pd.DataFrame, customer_id: object) -> pd.Series:
    """Devuelve un cliente único o lanza un error comprensible."""

    try:
        identifier = int(str(customer_id).strip())
    except (TypeError, ValueError) as error:
        raise ClienteNoEncontradoError(
            "El identificador debe ser un número entero."
        ) from error

    matches = clientes.loc[clientes["CustomerId"].eq(identifier)]
    if matches.empty:
        raise ClienteNoEncontradoError(
            f"No existe un cliente con CustomerId {identifier}."
        )
    if len(matches) != 1:
        raise ValueError(f"CustomerId {identifier} no identifica una fila única.")
    return matches.iloc[0].copy()


def crear_catalogo_escenario(
    catalogo_original: pd.DataFrame,
    cambios: Mapping[int, Mapping[str, float]],
) -> pd.DataFrame:
    """Aplica cambios temporales sin mutar el catálogo original."""

    scenario = validar_catalogo(catalogo_original).copy(deep=True)
    known_ids = set(scenario["incentivo_id"].astype(int))
    unknown_ids = set(cambios) - known_ids
    if unknown_ids:
        raise ValueError(f"Incentivos desconocidos en el escenario: {sorted(unknown_ids)}")

    allowed = {"costo_anual_usd", "efectividad"}
    for incentive_id, parameters in cambios.items():
        unexpected = set(parameters) - allowed
        if unexpected:
            raise ValueError(
                f"Parámetros no editables para {incentive_id}: {sorted(unexpected)}"
            )
        mask = scenario["incentivo_id"].eq(int(incentive_id))
        for parameter, value in parameters.items():
            scenario.loc[mask, parameter] = value

    return validar_catalogo(scenario)
