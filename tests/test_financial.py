from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src.constants import CLIENTS_PATH
from src.financial import (
    CATALOG_PERCENTILE_RULES,
    calcular_gne,
    calcular_umbrales_comerciales,
    evaluar_cartera,
    resumir_cartera,
    seleccionar_incentivo,
    validar_catalogo,
)


@pytest.fixture(scope="module")
def portfolio() -> pd.DataFrame:
    return pd.read_csv(CLIENTS_PATH)


@pytest.fixture(scope="module")
def catalog() -> pd.DataFrame:
    return pd.read_csv("data/incentivos.csv")


@pytest.fixture(scope="module")
def thresholds(
    portfolio: pd.DataFrame, catalog: pd.DataFrame
) -> dict[str, dict[float, float]]:
    return calcular_umbrales_comerciales(portfolio, catalog)


@pytest.fixture()
def high_profile() -> dict[str, float]:
    return {
        "Balance": 300_000.0,
        "AnnualCommissionIncome_USD_Sim": 400.0,
        "MonthlyTransactions_Sim": 50.0,
        "MonthlyTransactionVolume_USD_Sim": 25_000.0,
    }


@pytest.mark.parametrize(
    ("probability", "effectiveness", "margin", "cost", "expected"),
    [
        (0.0, 0.2, 100.0, 20.0, -20.0),
        (1.0, 0.2, 100.0, 20.0, 0.0),
        (1.0, 0.2, 200.0, 20.0, 20.0),
    ],
)
def test_gne_negative_zero_and_positive(
    probability: float,
    effectiveness: float,
    margin: float,
    cost: float,
    expected: float,
) -> None:
    assert math.isclose(
        calcular_gne(probability, effectiveness, margin, cost), expected
    )


@pytest.mark.parametrize("probability", [-0.01, 1.01, np.nan, np.inf, -np.inf])
def test_invalid_probabilities_are_rejected(probability: float) -> None:
    with pytest.raises(ValueError):
        calcular_gne(probability, 0.5, 500.0, 50.0)


@pytest.mark.parametrize("margin", [-100.0, 0.0])
def test_nonpositive_margin_always_blocks_retention(
    margin: float, catalog: pd.DataFrame
) -> None:
    result = seleccionar_incentivo(1.0, margin, catalog)
    assert result["decision"] == "Salida permitida"
    assert result["incentivo"] is None
    assert result["costo"] == 0
    assert result["gne"] == 0
    assert result["elegible"] is False


@pytest.mark.parametrize(
    ("probability", "margin", "expected_decision"),
    [
        (0.0, 100.0, "No intervención"),  # GNE = -20
        (1.0, 100.0, "No intervención"),  # GNE = 0
        (1.0, 200.0, "Retener"),          # GNE = 20
    ],
)
def test_selection_rejects_nonpositive_gne_and_accepts_positive(
    probability: float,
    margin: float,
    expected_decision: str,
    high_profile: dict[str, float],
) -> None:
    rules = {column: 0.0 for column in CATALOG_PERCENTILE_RULES}
    one_incentive = pd.DataFrame([
        {
            "incentivo_id": 1,
            "nombre": "Incentivo de prueba",
            "costo_anual_usd": 20.0,
            "efectividad": 0.20,
            "margen_minimo_usd": 0.0,
            "perfil_requerido": "Transaccional",
            **rules,
        }
    ])
    empty_thresholds = {column: {} for column in CATALOG_PERCENTILE_RULES}
    result = seleccionar_incentivo(
        probability,
        margin,
        one_incentive,
        cliente=high_profile,
        umbrales=empty_thresholds,
    )
    assert result["decision"] == expected_decision
    if expected_decision == "Retener":
        assert result["gne"] > 0
    else:
        assert result["costo"] == 0
        assert result["gne"] == 0


def test_client_without_commercial_eligibility_is_not_intervened(
    catalog: pd.DataFrame,
    thresholds: dict[str, dict[float, float]],
) -> None:
    low_profile = {
        "Balance": 0.0,
        "AnnualCommissionIncome_USD_Sim": 0.0,
        "MonthlyTransactions_Sim": 0.0,
        "MonthlyTransactionVolume_USD_Sim": 0.0,
    }
    result = seleccionar_incentivo(
        1.0,
        1_000.0,
        catalog,
        cliente=low_profile,
        umbrales=thresholds,
    )
    assert result["decision"] == "No intervención"
    assert result["costo"] == 0
    assert not any(option["elegible"] for option in result["alternativas"])


def test_selects_eligible_incentive_with_highest_positive_gne(
    catalog: pd.DataFrame,
    thresholds: dict[str, dict[float, float]],
    high_profile: dict[str, float],
) -> None:
    result = seleccionar_incentivo(
        0.7,
        1_000.0,
        catalog,
        cliente=high_profile,
        umbrales=thresholds,
    )
    eligible_positive = [
        option
        for option in result["alternativas"]
        if option["elegible"] and option["gne"] > 0
    ]
    assert result["decision"] == "Retener"
    assert result["gne"] == max(option["gne"] for option in eligible_positive)


def test_gne_tie_prefers_lower_cost_then_identifier(
    high_profile: dict[str, float],
) -> None:
    base_rules = {column: 0.0 for column in CATALOG_PERCENTILE_RULES}
    tied_catalog = pd.DataFrame(
        [
            {
                "incentivo_id": 2,
                "nombre": "Alternativa costosa",
                "costo_anual_usd": 100.0,
                "efectividad": 0.20,
                "margen_minimo_usd": 0.0,
                "perfil_requerido": "Transaccional",
                **base_rules,
            },
            {
                "incentivo_id": 1,
                "nombre": "Alternativa económica",
                "costo_anual_usd": 50.0,
                "efectividad": 0.15,
                "margen_minimo_usd": 0.0,
                "perfil_requerido": "Transaccional",
                **base_rules,
            },
        ]
    )
    empty_thresholds = {column: {} for column in CATALOG_PERCENTILE_RULES}
    result = seleccionar_incentivo(
        1.0,
        1_000.0,
        tied_catalog,
        cliente=high_profile,
        umbrales=empty_thresholds,
    )
    assert result["gne"] == 100.0
    assert result["incentivo_id"] == 1


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data.drop(columns="efectividad"),
        lambda data: data.assign(incentivo_id=1),
        lambda data: data.assign(costo_anual_usd=-1),
        lambda data: data.assign(efectividad=1.5),
        lambda data: data.assign(percentil_balance_minimo=1.5),
    ],
)
def test_invalid_catalogs_are_rejected(
    catalog: pd.DataFrame, mutation
) -> None:
    with pytest.raises(ValueError):
        validar_catalogo(mutation(catalog.copy()))


def test_portfolio_evaluation_and_aggregates_are_consistent(
    portfolio: pd.DataFrame,
    catalog: pd.DataFrame,
    thresholds: dict[str, dict[float, float]],
) -> None:
    sample = portfolio.iloc[:20].copy()
    probabilities = np.linspace(0, 1, len(sample))
    results = evaluar_cartera(sample, probabilities, catalog, thresholds)
    summary = resumir_cartera(results)

    retained = results["decision"].eq("Retener")
    deficit = results["margen_anual_usd"].le(0)
    assert not (retained & deficit).any()
    assert (results.loc[~retained, "costo"] == 0).all()
    assert summary["clientes_analizados"] == len(sample)
    assert (
        summary["clientes_retener"]
        + summary["clientes_no_intervencion"]
        + summary["clientes_salida_permitida"]
        == len(sample)
    )
    assert math.isclose(
        summary["gne_total_usd"], results.loc[retained, "gne"].sum()
    )
    assert math.isclose(
        summary["inversion_total_usd"], results.loc[retained, "costo"].sum()
    )
