"""Reglas financieras y comerciales de Deep Retention."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd


CATALOG_PERCENTILE_RULES = {
    "percentil_transacciones_minimo": "MonthlyTransactions_Sim",
    "percentil_comision_minimo": "AnnualCommissionIncome_USD_Sim",
    "percentil_balance_minimo": "Balance",
    "percentil_volumen_minimo": "MonthlyTransactionVolume_USD_Sim",
}

CATALOG_REQUIRED_COLUMNS = {
    "incentivo_id",
    "nombre",
    "costo_anual_usd",
    "efectividad",
    "margen_minimo_usd",
    "perfil_requerido",
    *CATALOG_PERCENTILE_RULES,
}

COMMERCIAL_PROFILE_COLUMNS = list(CATALOG_PERCENTILE_RULES.values())

ALLOWED_PROFILES = {
    "Transaccional",
    "Generador de comisiones",
    "Preferencial",
    "Patrimonial",
}


def _finite_float(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} debe ser numérico.") from error
    if not math.isfinite(number):
        raise ValueError(f"{name} debe ser finito.")
    return number


def calcular_gne(
    probabilidad: float,
    efectividad: float,
    margen: float,
    costo: float,
) -> float:
    """Calcula GNE en USD con margen y costo comparables en horizonte anual."""

    probability = _finite_float(probabilidad, "La probabilidad")
    effectiveness = _finite_float(efectividad, "La efectividad")
    annual_margin = _finite_float(margen, "El margen anual")
    annual_cost = _finite_float(costo, "El costo anual")

    if not 0 <= probability <= 1:
        raise ValueError("La probabilidad debe estar entre 0 y 1.")
    if not 0 <= effectiveness <= 1:
        raise ValueError("La efectividad debe estar entre 0 y 1.")
    if annual_cost < 0:
        raise ValueError("El costo no puede ser negativo.")

    return probability * effectiveness * annual_margin - annual_cost


def validar_catalogo(catalogo: pd.DataFrame) -> pd.DataFrame:
    """Valida y normaliza una copia del catálogo académico de incentivos."""

    if not isinstance(catalogo, pd.DataFrame):
        raise TypeError("El catálogo debe ser un DataFrame.")
    if catalogo.empty:
        raise ValueError("El catálogo no puede estar vacío.")

    missing_columns = sorted(CATALOG_REQUIRED_COLUMNS - set(catalogo.columns))
    if missing_columns:
        raise ValueError(f"El catálogo está incompleto: {missing_columns}")

    validated = catalogo.loc[:, sorted(CATALOG_REQUIRED_COLUMNS)].copy()
    if validated.isna().any().any():
        columns = validated.columns[validated.isna().any()].tolist()
        raise ValueError(f"El catálogo contiene valores faltantes en: {columns}")

    validated["nombre"] = validated["nombre"].astype(str).str.strip()
    validated["perfil_requerido"] = (
        validated["perfil_requerido"].astype(str).str.strip()
    )
    if validated["nombre"].eq("").any():
        raise ValueError("Los nombres de incentivos no pueden estar vacíos.")
    if not validated["incentivo_id"].is_unique:
        raise ValueError("Los identificadores de incentivos deben ser únicos.")
    if not validated["nombre"].is_unique:
        raise ValueError("Los nombres de incentivos deben ser únicos.")

    numeric_columns = [
        "incentivo_id",
        "costo_anual_usd",
        "efectividad",
        "margen_minimo_usd",
        *CATALOG_PERCENTILE_RULES,
    ]
    for column in numeric_columns:
        try:
            validated[column] = pd.to_numeric(validated[column], errors="raise")
        except (TypeError, ValueError) as error:
            raise ValueError(f"{column} debe ser numérica.") from error
        if not np.isfinite(validated[column].to_numpy(dtype=float)).all():
            raise ValueError(f"{column} debe contener valores finitos.")

    ids = validated["incentivo_id"].to_numpy(dtype=float)
    if (ids <= 0).any() or not np.equal(ids, np.floor(ids)).all():
        raise ValueError("incentivo_id debe contener enteros positivos.")
    validated["incentivo_id"] = validated["incentivo_id"].astype(int)

    if (validated["costo_anual_usd"] < 0).any():
        raise ValueError("Los costos anuales no pueden ser negativos.")
    if not validated["efectividad"].between(0, 1).all():
        raise ValueError("Las efectividades deben estar entre 0 y 1.")
    if (validated["margen_minimo_usd"] < 0).any():
        raise ValueError("Los márgenes mínimos no pueden ser negativos.")
    for column in CATALOG_PERCENTILE_RULES:
        if not validated[column].between(0, 1).all():
            raise ValueError(f"{column} debe estar entre 0 y 1.")

    unknown_profiles = set(validated["perfil_requerido"]) - ALLOWED_PROFILES
    if unknown_profiles:
        raise ValueError(
            f"Perfiles comerciales desconocidos: {sorted(unknown_profiles)}"
        )

    return validated.sort_values("incentivo_id", kind="stable").reset_index(drop=True)


def calcular_umbrales_comerciales(
    cartera: pd.DataFrame,
    catalogo: pd.DataFrame,
) -> dict[str, dict[float, float]]:
    """Calcula cortes relativos de elegibilidad sobre la cartera analizada."""

    validated_catalog = validar_catalogo(catalogo)
    if not isinstance(cartera, pd.DataFrame) or cartera.empty:
        raise ValueError("La cartera debe ser un DataFrame no vacío.")

    missing = [
        column for column in COMMERCIAL_PROFILE_COLUMNS if column not in cartera
    ]
    if missing:
        raise ValueError(f"Faltan variables del perfil comercial: {missing}")

    thresholds: dict[str, dict[float, float]] = {}
    for rule_column, data_column in CATALOG_PERCENTILE_RULES.items():
        try:
            values = pd.to_numeric(cartera[data_column], errors="raise")
        except (TypeError, ValueError) as error:
            raise ValueError(f"{data_column} debe ser numérica.") from error
        if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"{data_column} debe contener valores finitos.")
        if (values < 0).any():
            raise ValueError(f"{data_column} no puede ser negativa.")

        quantiles = sorted(
            {
                float(value)
                for value in validated_catalog[rule_column]
                if float(value) > 0
            }
        )
        thresholds[rule_column] = {
            quantile: float(values.quantile(quantile))
            for quantile in quantiles
        }

    return thresholds


def _validate_commercial_profile(
    cliente: pd.Series | Mapping[str, object] | None,
) -> dict[str, float]:
    if cliente is None:
        raise ValueError(
            "Se requiere el perfil comercial para evaluar incentivos."
        )
    if isinstance(cliente, pd.Series):
        source: Mapping[str, object] = cliente.to_dict()
    elif isinstance(cliente, Mapping):
        source = cliente
    else:
        raise TypeError("El perfil comercial debe ser una Series o un mapping.")

    missing = [column for column in COMMERCIAL_PROFILE_COLUMNS if column not in source]
    if missing:
        raise ValueError(f"Faltan variables del perfil comercial: {missing}")

    profile = {
        column: _finite_float(source[column], column)
        for column in COMMERCIAL_PROFILE_COLUMNS
    }
    negative = [column for column, value in profile.items() if value < 0]
    if negative:
        raise ValueError(f"Variables comerciales negativas: {negative}")
    return profile


def _commercial_eligibility(
    profile: Mapping[str, float],
    incentive: pd.Series,
    thresholds: Mapping[str, Mapping[float, float]],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for rule_column, data_column in CATALOG_PERCENTILE_RULES.items():
        quantile = float(incentive[rule_column])
        if quantile <= 0:
            continue
        if rule_column not in thresholds or quantile not in thresholds[rule_column]:
            raise ValueError(
                f"Falta el umbral p{quantile * 100:g} para {data_column}."
            )
        threshold = _finite_float(
            thresholds[rule_column][quantile],
            f"Umbral de {data_column}",
        )
        if profile[data_column] < threshold:
            reasons.append(
                f"{data_column} inferior al percentil {quantile:.0%} "
                f"de la cartera ({threshold:.2f})"
            )
    return not reasons, reasons


def _base_result(
    probability: float,
    annual_margin: float,
    decision: str,
    reason: str,
    alternatives: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "probabilidad_fuga": probability,
        "margen_anual_usd": annual_margin,
        "decision": decision,
        "motivo": reason,
        "incentivo_id": None,
        "incentivo": None,
        "perfil_requerido": None,
        "efectividad": 0.0,
        "costo": 0.0,
        "gne": 0.0,
        "elegible": False,
        "alternativas": alternatives,
    }


def seleccionar_incentivo(
    probabilidad: float,
    margen: float,
    catalogo: pd.DataFrame,
    cliente: pd.Series | Mapping[str, object] | None = None,
    umbrales: Mapping[str, Mapping[float, float]] | None = None,
) -> dict[str, object]:
    """Selecciona la alternativa elegible con mayor GNE estrictamente positiva.

    Los empates de GNE se resuelven por menor costo anual y luego por menor
    ``incentivo_id``. La selección nunca utiliza un umbral fijo de probabilidad.
    """

    probability = _finite_float(probabilidad, "La probabilidad de fuga")
    annual_margin = _finite_float(margen, "El margen neto anual")
    if not 0 <= probability <= 1:
        raise ValueError("La probabilidad de fuga debe estar entre 0 y 1.")

    validated_catalog = validar_catalogo(catalogo)
    if annual_margin <= 0:
        return _base_result(
            probability,
            annual_margin,
            "Salida permitida",
            "Cliente con margen neto anual no positivo; se bloquea todo gasto.",
            [],
        )

    profile = _validate_commercial_profile(cliente)
    if umbrales is None:
        raise ValueError("Se requieren umbrales comerciales de la cartera.")

    alternatives: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    for _, incentive in validated_catalog.iterrows():
        cost = float(incentive["costo_anual_usd"])
        effectiveness = float(incentive["efectividad"])
        minimum_margin = float(incentive["margen_minimo_usd"])
        gne = float(calcular_gne(probability, effectiveness, annual_margin, cost))

        commercial_eligible, commercial_reasons = _commercial_eligibility(
            profile, incentive, umbrales
        )
        margin_eligible = annual_margin >= minimum_margin
        eligible = commercial_eligible and margin_eligible

        reasons = list(commercial_reasons)
        if not margin_eligible:
            reasons.append(
                f"Margen anual inferior al mínimo académico de ${minimum_margin:.2f}"
            )
        if eligible and gne <= 0:
            reasons.append("La GNE no es estrictamente positiva")

        alternative = {
            "incentivo_id": int(incentive["incentivo_id"]),
            "incentivo": str(incentive["nombre"]),
            "perfil_requerido": str(incentive["perfil_requerido"]),
            "efectividad": effectiveness,
            "costo_anual_usd": cost,
            "margen_minimo_usd": minimum_margin,
            "gne": gne,
            "elegible_comercial": commercial_eligible,
            "elegible": eligible,
            "gne_positiva": gne > 0,
            "motivo": "; ".join(reasons) if reasons else "Alternativa elegible",
        }
        alternatives.append(alternative)
        if eligible and gne > 0:
            candidates.append(alternative)

    if not candidates:
        return _base_result(
            probability,
            annual_margin,
            "No intervención",
            "Cliente rentable sin incentivos elegibles con GNE positiva.",
            alternatives,
        )

    selected = sorted(
        candidates,
        key=lambda item: (
            -float(item["gne"]),
            float(item["costo_anual_usd"]),
            int(item["incentivo_id"]),
        ),
    )[0]
    return {
        "probabilidad_fuga": probability,
        "margen_anual_usd": annual_margin,
        "decision": "Retener",
        "motivo": "Incentivo elegible con la mayor GNE positiva.",
        "incentivo_id": selected["incentivo_id"],
        "incentivo": selected["incentivo"],
        "perfil_requerido": selected["perfil_requerido"],
        "efectividad": selected["efectividad"],
        "costo": selected["costo_anual_usd"],
        "gne": selected["gne"],
        "elegible": True,
        "alternativas": alternatives,
    }


def evaluar_cartera(
    clientes: pd.DataFrame,
    probabilidades: Sequence[float] | np.ndarray,
    catalogo: pd.DataFrame,
    umbrales: Mapping[str, Mapping[float, float]] | None = None,
) -> pd.DataFrame:
    """Cruza probabilidades con perfiles financieros sin usar ``Exited``."""

    required = [
        "CustomerId",
        "AnnualNetMargin_USD_Sim",
        *COMMERCIAL_PROFILE_COLUMNS,
    ]
    if not isinstance(clientes, pd.DataFrame) or clientes.empty:
        raise ValueError("Los clientes deben proporcionarse en un DataFrame no vacío.")
    missing = [column for column in required if column not in clientes]
    if missing:
        raise ValueError(f"Faltan columnas para evaluar la cartera: {missing}")

    probabilities = np.asarray(probabilidades, dtype=float).reshape(-1)
    if len(probabilities) != len(clientes):
        raise ValueError("Debe existir una probabilidad por cliente.")
    if not np.isfinite(probabilities).all() or not (
        (probabilities >= 0) & (probabilities <= 1)
    ).all():
        raise ValueError("Las probabilidades de la cartera son inválidas.")

    validated_catalog = validar_catalogo(catalogo)
    if umbrales is None:
        umbrales = calcular_umbrales_comerciales(clientes, validated_catalog)

    records: list[dict[str, object]] = []
    for position, (_, client) in enumerate(clientes.iterrows()):
        result = seleccionar_incentivo(
            probabilities[position],
            client["AnnualNetMargin_USD_Sim"],
            validated_catalog,
            cliente=client,
            umbrales=umbrales,
        )
        records.append(
            {
                "CustomerId": client["CustomerId"],
                **{column: client[column] for column in COMMERCIAL_PROFILE_COLUMNS},
                **result,
            }
        )

    return pd.DataFrame(records)


def resumir_cartera(resultados: pd.DataFrame) -> dict[str, float | int | None]:
    """Calcula agregados coherentes a partir de decisiones trazables."""

    required = {
        "decision",
        "margen_anual_usd",
        "costo",
        "gne",
        "elegible",
    }
    if not isinstance(resultados, pd.DataFrame) or resultados.empty:
        raise ValueError("Los resultados deben ser un DataFrame no vacío.")
    missing = sorted(required - set(resultados.columns))
    if missing:
        raise ValueError(f"Faltan columnas de resultados: {missing}")

    allowed_decisions = {"Retener", "No intervención", "Salida permitida"}
    if not set(resultados["decision"]).issubset(allowed_decisions):
        raise ValueError("Existen decisiones financieras desconocidas.")

    retained = resultados["decision"].eq("Retener")
    no_intervention = resultados["decision"].eq("No intervención")
    allowed_exit = resultados["decision"].eq("Salida permitida")

    if (resultados.loc[allowed_exit, "margen_anual_usd"] > 0).any():
        raise ValueError("Salida permitida solo corresponde a margen no positivo.")
    if (resultados.loc[retained, "margen_anual_usd"] <= 0).any():
        raise ValueError("Un cliente deficitario no puede recibir incentivos.")
    if not (resultados.loc[retained, "gne"] > 0).all():
        raise ValueError("Toda retención debe tener GNE positiva.")
    if not resultados.loc[retained, "elegible"].all():
        raise ValueError("Toda retención debe ser comercialmente elegible.")
    if not (resultados.loc[~retained, ["costo", "gne"]].fillna(0) == 0).all().all():
        raise ValueError("Las no intervenciones no deben generar costo ni GNE.")

    investment = float(resultados.loc[retained, "costo"].sum())
    total_gne = float(resultados.loc[retained, "gne"].sum())
    recoverable_value = investment + total_gne
    roi = total_gne / investment * 100 if investment > 0 else None

    return {
        "clientes_analizados": int(len(resultados)),
        "clientes_retener": int(retained.sum()),
        "clientes_no_intervencion": int(no_intervention.sum()),
        "clientes_salida_permitida": int(allowed_exit.sum()),
        "inversion_total_usd": investment,
        "valor_rescatable_estimado_usd": recoverable_value,
        "gne_total_usd": total_gne,
        "roi_proyectado_pct": roi,
    }
