"""Inferencia reproducible del modelo de abandono de Deep Retention."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"

FEATURES = [
    "CreditScore",
    "Geography",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
    "EstimatedSalary",
]

NUMERIC_FEATURES = [
    "CreditScore",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
    "EstimatedSalary",
]


class PredictorFuga:
    """Carga los artefactos aprobados y estima probabilidades ajustadas.

    La corrección por pesos de clase revierte aproximadamente el cambio de
    prior inducido durante el entrenamiento. No sustituye una calibración
    probabilística aprendida con un conjunto independiente.
    """

    def __init__(self, models_dir: str | Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        preprocessor_path = self.models_dir / "preprocesador.joblib"
        model_path = self.models_dir / "modelo_churn.keras"
        correction_path = self.models_dir / "correccion_probabilidades.json"

        missing_artifacts = [
            path.name
            for path in (preprocessor_path, model_path, correction_path)
            if not path.is_file()
        ]
        if missing_artifacts:
            raise FileNotFoundError(
                "Faltan artefactos de inferencia: "
                + ", ".join(missing_artifacts)
            )

        # Joblib solo debe cargar artefactos confiables incluidos en el proyecto.
        self.preprocesador = joblib.load(preprocessor_path)
        self.modelo = tf.keras.models.load_model(model_path, compile=False)

        with correction_path.open(encoding="utf-8") as file:
            configuration = json.load(file)

        required_configuration = {
            "method",
            "class_weight_0",
            "class_weight_1",
            "artifact_id",
            "features",
        }
        missing_configuration = required_configuration - configuration.keys()
        if missing_configuration:
            raise ValueError(
                "Configuración de corrección incompleta: "
                f"{sorted(missing_configuration)}"
            )
        if configuration["method"] != "class_weight_prior_correction":
            raise ValueError("Método de corrección de probabilidades no soportado.")

        weight_0 = float(configuration["class_weight_0"])
        weight_1 = float(configuration["class_weight_1"])
        if not np.isfinite([weight_0, weight_1]).all() or weight_0 <= 0 or weight_1 <= 0:
            raise ValueError("Pesos de clase inválidos.")

        self.factor = weight_1 / weight_0
        self.artifact_id = str(configuration["artifact_id"])
        self.transformed_features = list(self.preprocesador.get_feature_names_out())

        if self.transformed_features != list(configuration["features"]):
            raise ValueError(
                "Las características del preprocesador no coinciden con la corrección."
            )

        preprocessor_artifact_id = getattr(
            self.preprocesador, "artifact_id_", None
        )
        if preprocessor_artifact_id != self.artifact_id:
            raise ValueError(
                "El preprocesador y la corrección pertenecen a versiones distintas."
            )

        input_shape = self.modelo.input_shape
        output_shape = self.modelo.output_shape
        if isinstance(input_shape, list) or input_shape[-1] != len(self.transformed_features):
            raise ValueError("La entrada del modelo no coincide con el preprocesador.")
        if isinstance(output_shape, list) or output_shape[-1] != 1:
            raise ValueError("El modelo no produce una única probabilidad por cliente.")

        geography_encoder = self.preprocesador.named_transformers_["geography"]
        self.allowed_geographies = set(geography_encoder.categories_[0].tolist())

    def _validate_clients(self, clients: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(clients, pd.DataFrame):
            raise TypeError("Los clientes deben proporcionarse en un DataFrame.")
        if clients.empty:
            raise ValueError("El DataFrame de clientes está vacío.")
        if clients.columns.duplicated().any():
            duplicates = clients.columns[clients.columns.duplicated()].tolist()
            raise ValueError(f"Existen columnas duplicadas: {duplicates}")

        missing_columns = [column for column in FEATURES if column not in clients]
        if missing_columns:
            raise ValueError(f"Faltan columnas predictoras: {missing_columns}")

        validated = clients.loc[:, FEATURES].copy()
        if validated.isna().any().any():
            missing = validated.columns[validated.isna().any()].tolist()
            raise ValueError(f"Existen valores faltantes en: {missing}")

        for column in NUMERIC_FEATURES:
            try:
                validated[column] = pd.to_numeric(validated[column], errors="raise")
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"La columna {column} contiene valores no numéricos."
                ) from error

        numeric_values = validated[NUMERIC_FEATURES].to_numpy(dtype=float)
        if not np.isfinite(numeric_values).all():
            raise ValueError("Las variables numéricas deben ser finitas.")

        validated["Geography"] = validated["Geography"].astype("string").str.strip()
        if validated["Geography"].eq("").any():
            raise ValueError("Geography no puede estar vacía.")
        unknown_geographies = set(validated["Geography"]) - self.allowed_geographies
        if unknown_geographies:
            raise ValueError(
                "Geography contiene categorías desconocidas: "
                f"{sorted(unknown_geographies)}"
            )

        for binary_column in ("HasCrCard", "IsActiveMember"):
            if not validated[binary_column].isin([0, 1]).all():
                raise ValueError(f"{binary_column} solo admite los valores 0 y 1.")

        integer_rules = {
            "Age": 18,
            "Tenure": 0,
            "NumOfProducts": 1,
        }
        for column, minimum in integer_rules.items():
            values = validated[column].to_numpy(dtype=float)
            if (values < minimum).any() or not np.equal(values, np.floor(values)).all():
                raise ValueError(
                    f"{column} debe contener enteros mayores o iguales a {minimum}."
                )

        if (validated["CreditScore"] <= 0).any():
            raise ValueError("CreditScore debe ser positivo.")
        for nonnegative_column in ("Balance", "EstimatedSalary"):
            if (validated[nonnegative_column] < 0).any():
                raise ValueError(f"{nonnegative_column} no puede ser negativo.")

        return validated

    def _adjust_probabilities(self, probabilities: np.ndarray) -> np.ndarray:
        denominator = probabilities + self.factor * (1.0 - probabilities)
        adjusted = probabilities / denominator
        if not np.isfinite(adjusted).all() or not (
            (adjusted >= 0) & (adjusted <= 1)
        ).all():
            raise ValueError("La corrección produjo probabilidades inválidas.")
        return adjusted.astype(float, copy=False)

    def predecir_lote(
        self, clients: pd.DataFrame, batch_size: int = 256
    ) -> np.ndarray:
        """Devuelve probabilidades ajustadas para los clientes, en el mismo orden."""

        if not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError("batch_size debe ser un entero positivo.")

        validated = self._validate_clients(clients)
        transformed = self.preprocesador.transform(validated).astype(np.float32)
        if transformed.shape != (len(validated), len(self.transformed_features)):
            raise ValueError("El preprocesador produjo dimensiones incompatibles.")
        if not np.isfinite(transformed).all():
            raise ValueError("El preprocesador produjo características no finitas.")

        probabilities = np.asarray(
            self.modelo.predict(
                transformed,
                batch_size=batch_size,
                verbose=0,
            )
        ).reshape(-1)
        if len(probabilities) != len(validated):
            raise ValueError("El modelo no devolvió una probabilidad por cliente.")
        if not np.isfinite(probabilities).all() or not (
            (probabilities >= 0) & (probabilities <= 1)
        ).all():
            raise ValueError("El modelo produjo probabilidades inválidas.")

        return self._adjust_probabilities(probabilities)

    def predecir(self, client: pd.DataFrame) -> float:
        """Devuelve la probabilidad ajustada para un único cliente."""

        if not isinstance(client, pd.DataFrame) or len(client) != 1:
            raise ValueError("Se requiere exactamente un cliente en un DataFrame.")
        return float(self.predecir_lote(client, batch_size=1)[0])
