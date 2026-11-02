from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.prediction import FEATURES, PredictorFuga


@pytest.fixture(scope="module")
def clients() -> pd.DataFrame:
    return pd.read_csv("data/processed/clientes_limpios.csv").head(12)


@pytest.fixture(scope="module")
def predictor() -> PredictorFuga:
    return PredictorFuga()


def test_artifacts_are_compatible(predictor: PredictorFuga) -> None:
    assert predictor.artifact_id == "3a2890fbab71e9c8"
    assert len(predictor.transformed_features) == 11
    assert predictor.modelo.input_shape[-1] == 11
    assert predictor.modelo.output_shape[-1] == 1


def test_batch_predictions_are_finite_probabilities(
    predictor: PredictorFuga, clients: pd.DataFrame
) -> None:
    probabilities = predictor.predecir_lote(clients)
    assert probabilities.shape == (len(clients),)
    assert np.isfinite(probabilities).all()
    assert ((probabilities >= 0) & (probabilities <= 1)).all()


def test_individual_and_batch_predictions_are_equivalent(
    predictor: PredictorFuga, clients: pd.DataFrame
) -> None:
    batch = predictor.predecir_lote(clients)
    individual = np.array(
        [predictor.predecir(clients.iloc[[position]]) for position in range(len(clients))]
    )
    np.testing.assert_allclose(individual, batch, rtol=1e-6, atol=1e-7)


def test_extra_columns_are_not_used_for_inference(
    predictor: PredictorFuga, clients: pd.DataFrame
) -> None:
    with_target = clients.copy()
    with_target["Exited"] = 1
    expected = predictor.predecir_lote(clients[FEATURES])
    obtained = predictor.predecir_lote(with_target)
    np.testing.assert_allclose(obtained, expected, rtol=0, atol=0)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("Age", np.nan, "valores faltantes"),
        ("Balance", np.inf, "deben ser finitas"),
        ("HasCrCard", 2, "solo admite"),
        ("Geography", "Atlantis", "categorías desconocidas"),
        ("NumOfProducts", 0, "enteros mayores"),
    ],
)
def test_invalid_client_values_are_rejected(
    predictor: PredictorFuga,
    clients: pd.DataFrame,
    column: str,
    value: object,
    message: str,
) -> None:
    invalid = clients.iloc[[0]].copy()
    invalid[column] = invalid[column].astype(object)
    invalid.loc[:, column] = value
    with pytest.raises(ValueError, match=message):
        predictor.predecir(invalid)


def test_missing_predictor_column_is_rejected(
    predictor: PredictorFuga, clients: pd.DataFrame
) -> None:
    invalid = clients.iloc[[0]].drop(columns="Age")
    with pytest.raises(ValueError, match="Faltan columnas predictoras"):
        predictor.predecir(invalid)


def test_single_prediction_requires_exactly_one_row(
    predictor: PredictorFuga, clients: pd.DataFrame
) -> None:
    with pytest.raises(ValueError, match="exactamente un cliente"):
        predictor.predecir(clients.iloc[:2])
