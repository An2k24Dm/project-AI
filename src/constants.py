"""Rutas y características compartidas por inferencia y aplicación."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
CLIENTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clientes_financieros_simulados.csv"
)
CATALOG_PATH = PROJECT_ROOT / "data" / "incentivos.csv"

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
