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
from src.constants import CLIENTS_PATH
from src.data_processing import (
    ClienteNoEncontradoError,
    buscar_cliente,
    cargar_clientes,
    crear_catalogo_escenario,
)
from src.financial import calcular_umbrales_comerciales, evaluar_cartera
from ui.services import (
    RESOURCE_PATHS,
    cargar_datos_aplicacion,
    construir_escenario_base,
    construir_escenario_simulado,
    obtener_resultado_cliente,
    obtener_version_recursos,
)


@pytest.fixture(scope="module")
def app_state():
    version = obtener_version_recursos()
    data = cargar_datos_aplicacion(version)
    base = construir_escenario_base(version)
    return (
        data.clientes,
        data.catalogo,
        base.probabilidades,
        base.umbrales,
        base.cartera,
        base.indicadores,
        version,
    )


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
    assert indicators["clientes_rentables"] == 7_880
    assert indicators["clientes_deficitarios"] == 2_120
    assert indicators["clientes_retener"] == 793
    assert indicators["clientes_no_intervencion"] == 7_087
    assert indicators["clientes_salida_permitida"] == 2_120
    assert math.isclose(indicators["inversion_total_usd"], 35_600.0)
    assert math.isclose(indicators["gne_total_usd"], 42_180.78140083612)
    assert math.isclose(
        indicators["beneficio_bruto_esperado_usd"],
        indicators["inversion_total_usd"] + indicators["gne_total_usd"],
    )
    assert indicators["saldo_expuesto_unidades_originales"] > 0
    assert indicators["abandonos_esperados_evitados"] > 0
    assert 0 <= indicators["efectividad_ponderada_riesgo"] <= 1


def test_search_decision_equals_portfolio_decision(app_state) -> None:
    clients, catalog, probabilities, thresholds, portfolio, _, _ = app_state
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


@pytest.mark.parametrize(
    ("filters", "column", "expected"),
    [
        ({"paises": ["France"]}, "Geography", "France"),
        ({"rentabilidades": ["Rentable"]}, "rentabilidad", "Rentable"),
        ({"decisiones": ["Retener"]}, "decision", "Retener"),
        (
            {
                "paises": ["Germany"],
                "rentabilidades": ["Rentable"],
                "decisiones": ["Retener"],
            },
            "decision",
            "Retener",
        ),
    ],
)
def test_dashboard_filters(app_state, filters, column, expected) -> None:
    filtered = filtrar_cartera(app_state[4], **filters)
    assert not filtered.empty
    assert filtered[column].eq(expected).all()
    assert calcular_indicadores(filtered)["clientes_analizados"] == len(filtered)


def test_dashboard_empty_subset(app_state) -> None:
    filtered = filtrar_cartera(app_state[4], paises=["País inexistente"])
    indicators = calcular_indicadores(filtered)
    assert filtered.empty
    assert indicators["clientes_analizados"] == 0
    assert indicators["inversion_total_usd"] == 0
    assert indicators["roi_proyectado_pct"] is None


@pytest.mark.parametrize(
    "decision",
    ["Retener", "No intervención", "Salida permitida"],
)
def test_lazy_client_search_matches_reference_portfolio(app_state, decision) -> None:
    portfolio = app_state[4]
    reference = portfolio.loc[portfolio["decision"].eq(decision)].iloc[0]
    result = obtener_resultado_cliente(
        app_state[6],
        int(reference["CustomerId"]),
    )
    assert result["decision"] == reference["decision"]
    assert (result["incentivo"] or "") == (reference["incentivo"] or "")
    assert result["costo"] == reference["costo"]
    assert math.isclose(
        result["probabilidad_fuga"],
        reference["probabilidad_fuga"],
        rel_tol=0,
        abs_tol=2e-6,
    )
    assert math.isclose(result["gne"], reference["gne"], abs_tol=1e-3)


def test_simulation_updates_results_without_mutating_catalog(app_state) -> None:
    clients, catalog, probabilities, thresholds, _, _, _ = app_state
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
    ("parameter", "value"),
    [("costo_anual_usd", 30.0), ("efectividad", 0.0)],
)
def test_cached_simulation_changes_scenario_only(
    app_state,
    parameter,
    value,
) -> None:
    catalog = app_state[1]
    original = catalog.copy(deep=True)
    parameters = []
    for _, row in catalog.iterrows():
        cost = float(row["costo_anual_usd"])
        effectiveness = float(row["efectividad"])
        if int(row["incentivo_id"]) == int(catalog.iloc[0]["incentivo_id"]):
            if parameter == "costo_anual_usd":
                cost = value
            else:
                effectiveness = value
        parameters.append((int(row["incentivo_id"]), cost, effectiveness))

    scenario = construir_escenario_simulado(app_state[6], tuple(parameters))
    pd.testing.assert_frame_equal(catalog, original)
    assert scenario.indicadores != app_state[5]
    assert len(scenario.cartera) == len(app_state[0])


def test_resource_version_tracks_all_required_artifacts(tmp_path) -> None:
    assert {path.name for path in RESOURCE_PATHS} == {
        "clientes_financieros_simulados.csv",
        "incentivos.csv",
        "modelo_churn.keras",
        "preprocesador.joblib",
        "correccion_probabilidades.json",
    }
    resources = (tmp_path / "one", tmp_path / "two")
    for resource in resources:
        resource.write_text("v1", encoding="utf-8")
    first = obtener_version_recursos(resources)
    resources[0].write_text("version-two", encoding="utf-8")
    assert obtener_version_recursos(resources) != first


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


def test_application_uses_complete_financial_source(app_state) -> None:
    assert CLIENTS_PATH.name == "clientes_financieros_simulados.csv"
    required = {
        "MonthlyTransactions_Sim",
        "MonthlyTransactionVolume_USD_Sim",
        "AvgTransactionFee_USD_Sim",
        "AnnualCommissionIncome_USD_Sim",
        "AnnualFinancialMargin_USD_Sim",
        "AnnualOperatingCosts_USD_Sim",
        "AnnualNetMargin_USD_Sim",
        "ProfitabilitySegment_Sim",
    }
    assert required <= set(app_state[0].columns)
    assert app_state[0]["CustomerId"].is_unique


def test_streamlit_application_interactions() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=120).run(timeout=120)
    assert not app.exception
    assert app.title[0].value == "Deep Retention"
    assert app.sidebar.radio[0].value == "Buscador de clientes"

    app.button[0].click()
    app.run(timeout=120)
    assert not app.exception
    assert {item.value for item in app.subheader} >= {
        "A. Identificación y perfil bancario",
        "B. Predicción del modelo neuronal",
        "C. Información financiera simulada",
        "D. Decisión comercial recomendada",
    }
    metric_labels = {metric.label for metric in app.metric}
    assert {
        "Puntaje MLP (probabilidad)",
        "Costo anual",
        "Beneficio bruto esperado",
        "GNE seleccionada",
    } <= metric_labels

    app.text_input[0].set_value("identificador-inválido")
    app.run(timeout=120)
    app.button[0].click()
    app.run(timeout=120)
    assert not app.exception
    assert "número entero" in app.warning[0].value

    app.sidebar.radio[0].set_value("Panel de cartera")
    app.run(timeout=120)
    assert not app.exception
    assert app.metric[0].value == "10,000"
    app.multiselect[0].set_value(["France"])
    app.run(timeout=120)
    assert not app.exception
    assert int(app.metric[0].value.replace(",", "")) < 10_000

    app.sidebar.radio[0].set_value("Simulador")
    app.run(timeout=120)
    assert not app.exception
    base_investment = app.metric[6].value
    app.number_input[0].set_value(30.0)
    app.get("form_submit_button")[0].click()
    app.run(timeout=120)
    assert not app.exception
    assert app.number_input[0].value == 30.0
    assert app.metric[6].value != base_investment

    app.button[0].click()
    app.run(timeout=120)
    assert not app.exception
    assert app.number_input[0].value == 20.0
    assert app.metric[3].value == "793"
    assert app.metric[6].value == base_investment
