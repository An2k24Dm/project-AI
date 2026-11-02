from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.analytics import (
    calcular_indicadores,
    enriquecer_resultados,
    filtrar_cartera,
)
from src.data_processing import (
    ClienteNoEncontradoError,
    buscar_cliente,
    cargar_catalogo,
    cargar_clientes,
    crear_catalogo_escenario,
)
from src.financial import calcular_umbrales_comerciales, evaluar_cartera
from src.prediction import PredictorFuga


@pytest.fixture(scope="module")
def app_state():
    clients = cargar_clientes()
    catalog = cargar_catalogo()
    predictor = PredictorFuga()
    probabilities = predictor.predecir_lote(clients)
    thresholds = calcular_umbrales_comerciales(clients, catalog)
    decisions = evaluar_cartera(clients, probabilities, catalog, thresholds)
    portfolio = enriquecer_resultados(clients, decisions)
    indicators = calcular_indicadores(portfolio)
    return clients, catalog, probabilities, thresholds, portfolio, indicators


def test_existing_and_missing_client_queries(app_state) -> None:
    clients = app_state[0]
    existing_id = int(clients["CustomerId"].iloc[0])
    assert int(buscar_cliente(clients, existing_id)["CustomerId"]) == existing_id
    with pytest.raises(ClienteNoEncontradoError, match="No existe"):
        buscar_cliente(clients, -1)
    with pytest.raises(ClienteNoEncontradoError, match="número entero"):
        buscar_cliente(clients, "cliente-inválido")


def test_base_dashboard_matches_verified_financial_results(app_state) -> None:
    indicators = app_state[5]
    assert indicators["clientes_analizados"] == 10_000
    assert indicators["clientes_retener"] == 1_214
    assert indicators["clientes_no_intervencion"] == 5_184
    assert indicators["clientes_salida_permitida"] == 3_602
    assert math.isclose(indicators["inversion_total_usd"], 66_640.0)
    assert math.isclose(indicators["gne_total_usd"], 90_099.68581665923)
    assert indicators["saldo_expuesto_unidades_originales"] > 0
    assert indicators["abandonos_esperados_evitados"] > 0
    assert 0 <= indicators["efectividad_ponderada_riesgo"] <= 1


def test_search_decision_equals_portfolio_decision(app_state) -> None:
    clients, catalog, probabilities, thresholds, portfolio, _ = app_state
    position = 25
    client = clients.iloc[position]
    single = evaluar_cartera(
        clients.iloc[[position]],
        np.array([probabilities[position]]),
        catalog,
        thresholds,
    ).iloc[0]
    batch = portfolio.loc[portfolio["CustomerId"].eq(client["CustomerId"])].iloc[0]
    assert single["decision"] == batch["decision"]
    assert single["incentivo"] == batch["incentivo"]
    assert math.isclose(single["gne"], batch["gne"])


def test_visual_filters_do_not_change_client_decisions(app_state) -> None:
    portfolio = app_state[4]
    filtered = filtrar_cartera(
        portfolio,
        paises=["France"],
        decisiones=["Retener"],
        rango_probabilidad=(0.2, 0.8),
    )
    assert not filtered.empty
    joined = filtered[["CustomerId", "decision", "incentivo", "gne"]].merge(
        portfolio[["CustomerId", "decision", "incentivo", "gne"]],
        on="CustomerId",
        suffixes=("_filtered", "_base"),
        validate="one_to_one",
    )
    assert joined["decision_filtered"].equals(joined["decision_base"])
    assert joined["incentivo_filtered"].equals(joined["incentivo_base"])
    np.testing.assert_allclose(joined["gne_filtered"], joined["gne_base"])


def test_simulation_updates_results_without_mutating_catalog(app_state) -> None:
    clients, catalog, probabilities, thresholds, _, _ = app_state
    original = catalog.copy(deep=True)
    changes = {
        int(row["incentivo_id"]): {
            "costo_anual_usd": 0.0,
            "efectividad": 0.0,
        }
        for _, row in catalog.iterrows()
    }
    scenario_catalog = crear_catalogo_escenario(catalog, changes)
    pd.testing.assert_frame_equal(catalog, original)

    scenario = evaluar_cartera(
        clients,
        probabilities,
        scenario_catalog,
        thresholds,
    )
    indicators = calcular_indicadores(enriquecer_resultados(clients, scenario))
    assert indicators["clientes_retener"] == 0
    assert indicators["inversion_total_usd"] == 0
    assert indicators["gne_total_usd"] == 0
    assert indicators["roi_proyectado_pct"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {1: {"costo_anual_usd": -1.0}},
        {1: {"efectividad": 1.01}},
        {999: {"costo_anual_usd": 10.0}},
        {1: {"margen_minimo_usd": 10.0}},
    ],
)
def test_invalid_simulator_parameters_are_rejected(app_state, changes) -> None:
    with pytest.raises(ValueError):
        crear_catalogo_escenario(app_state[1], changes)


def test_missing_application_data_is_rejected(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        cargar_clientes(tmp_path / "missing.csv")


def test_streamlit_application_starts_without_exceptions() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=120).run(timeout=120)
    assert not app.exception
    assert app.title[0].value == "Deep Retention"
    assert app.sidebar.radio[0].value == "Buscador de clientes"
