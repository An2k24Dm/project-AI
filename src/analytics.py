"""Agregados, filtros y comparaciones para la interfaz ejecutiva."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from src.financial import resumir_cartera


CLIENT_CONTEXT_COLUMNS = [
    "CustomerId",
    "Surname",
    "Age",
    "Geography",
    "Tenure",
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
]


def enriquecer_resultados(
    clientes: pd.DataFrame,
    resultados: pd.DataFrame,
) -> pd.DataFrame:
    """Añade atributos descriptivos sin recalcular ninguna decisión."""

    missing = [column for column in CLIENT_CONTEXT_COLUMNS if column not in clientes]
    if missing:
        raise ValueError(f"Faltan columnas descriptivas: {missing}")
    if "CustomerId" not in resultados:
        raise ValueError("Los resultados no contienen CustomerId.")

    context_columns = [
        column for column in CLIENT_CONTEXT_COLUMNS if column not in resultados.columns
    ]
    context = clientes[["CustomerId", *[c for c in context_columns if c != "CustomerId"]]]
    enriched = resultados.merge(
        context,
        on="CustomerId",
        how="left",
        validate="one_to_one",
    )
    if len(enriched) != len(resultados):
        raise ValueError("La unión de resultados alteró la cantidad de clientes.")
    enriched["rentabilidad"] = np.where(
        enriched["margen_anual_usd"].gt(0), "Rentable", "Deficitario"
    )
    enriched["incentivo_mostrado"] = enriched["incentivo"].fillna("Sin incentivo")
    enriched["beneficio_bruto_esperado_usd"] = np.where(
        enriched["decision"].eq("Retener"),
        enriched["gne"] + enriched["costo"],
        0.0,
    )
    return enriched


def calcular_indicadores(cartera: pd.DataFrame) -> dict[str, float | int | None]:
    """Calcula KPI financieros y operativos para una cartera o subconjunto."""

    if cartera.empty:
        return {
            "clientes_analizados": 0,
            "clientes_rentables": 0,
            "clientes_deficitarios": 0,
            "clientes_retener": 0,
            "clientes_no_intervencion": 0,
            "clientes_salida_permitida": 0,
            "inversion_total_usd": 0.0,
            "valor_rescatable_estimado_usd": 0.0,
            "beneficio_bruto_esperado_usd": 0.0,
            "gne_total_usd": 0.0,
            "roi_proyectado_pct": None,
            "saldo_expuesto_usd": 0.0,
            "abandonos_esperados_evitados": 0.0,
            "efectividad_ponderada_riesgo": None,
        }

    required = {
        "probabilidad_fuga",
        "Balance",
        "efectividad",
        "decision",
        "margen_anual_usd",
        "costo",
        "gne",
    }
    missing = sorted(required - set(cartera.columns))
    if missing:
        raise ValueError(f"Faltan columnas para los indicadores: {missing}")

    indicators = resumir_cartera(cartera)
    probability = cartera["probabilidad_fuga"].to_numpy(dtype=float)
    balance = cartera["Balance"].to_numpy(dtype=float)
    if not np.isfinite(probability).all() or not np.isfinite(balance).all():
        raise ValueError("Probabilidad y Balance deben ser finitos.")

    retained = cartera["decision"].eq("Retener")
    retained_risk = cartera.loc[retained, "probabilidad_fuga"].to_numpy(dtype=float)
    retained_effectiveness = cartera.loc[retained, "efectividad"].to_numpy(dtype=float)
    avoided = float(np.sum(retained_risk * retained_effectiveness))
    risk_sum = float(np.sum(retained_risk))
    profitable = cartera["margen_anual_usd"].gt(0)
    gross_benefit = float(
        (cartera.loc[retained, "gne"] + cartera.loc[retained, "costo"]).sum()
    )

    return {
        **indicators,
        "clientes_rentables": int(profitable.sum()),
        "clientes_deficitarios": int((~profitable).sum()),
        "beneficio_bruto_esperado_usd": gross_benefit,
        "saldo_expuesto_usd": float(np.sum(probability * balance)),
        "abandonos_esperados_evitados": avoided,
        "efectividad_ponderada_riesgo": avoided / risk_sum if risk_sum > 0 else None,
    }


def filtrar_cartera(
    cartera: pd.DataFrame,
    paises: Sequence[str] | None = None,
    rentabilidades: Sequence[str] | None = None,
    decisiones: Sequence[str] | None = None,
    incentivos: Sequence[str] | None = None,
    rango_probabilidad: tuple[float, float] = (0.0, 1.0),
) -> pd.DataFrame:
    """Filtra resultados existentes; nunca recalcula percentiles ni decisiones."""

    lower, upper = rango_probabilidad
    if not 0 <= lower <= upper <= 1:
        raise ValueError("El rango de probabilidad debe estar dentro de [0, 1].")

    mask = cartera["probabilidad_fuga"].between(lower, upper, inclusive="both")
    for column, selected in (
        ("Geography", paises),
        ("rentabilidad", rentabilidades),
        ("decision", decisiones),
        ("incentivo_mostrado", incentivos),
    ):
        if selected:
            mask &= cartera[column].isin(selected)
    return cartera.loc[mask].copy()


def comparar_escenarios(
    base: dict[str, float | int | None],
    simulado: dict[str, float | int | None],
) -> pd.DataFrame:
    """Compara KPI comunes mediante diferencias absolutas y porcentuales."""

    keys = [
        "clientes_retener",
        "inversion_total_usd",
        "beneficio_bruto_esperado_usd",
        "gne_total_usd",
        "roi_proyectado_pct",
        "abandonos_esperados_evitados",
    ]
    rows = []
    for key in keys:
        base_value = base.get(key)
        scenario_value = simulado.get(key)
        if base_value is None or scenario_value is None:
            absolute = None
            percentage = None
        else:
            absolute = float(scenario_value) - float(base_value)
            percentage = (
                absolute / float(base_value) * 100
                if float(base_value) != 0
                else None
            )
        rows.append(
            {
                "indicador": key,
                "escenario_base": base_value,
                "escenario_simulado": scenario_value,
                "diferencia_absoluta": absolute,
                "diferencia_porcentual": percentage,
            }
        )
    return pd.DataFrame(rows)
