"""Componentes visuales reutilizables de Deep Retention."""

from __future__ import annotations

from collections.abc import Mapping

import streamlit as st


def formato_usd(value: float | int | None) -> str:
    """Formatea un importe simulado o informa que no aplica."""

    return "No aplicable" if value is None else f"USD {value:,.2f}"


def formato_numero(
    value: float | int | None,
    decimals: int = 2,
) -> str:
    """Formatea una magnitud sin asignarle una unidad monetaria."""

    return "No aplicable" if value is None else f"{value:,.{decimals}f}"


def nivel_riesgo(probability: float) -> tuple[str, str, str]:
    """Devuelve etiqueta y colores del nivel visual de riesgo."""

    if probability < 0.20:
        return "Bajo", "#D1FAE5", "#065F46"
    if probability < 0.40:
        return "Moderado", "#FEF3C7", "#92400E"
    if probability < 0.70:
        return "Alto", "#FED7AA", "#9A3412"
    return "Muy alto", "#FEE2E2", "#991B1B"


def mostrar_aviso_academico() -> None:
    """Aclara el carácter simulado de los resultados financieros."""

    st.markdown(
        "<div class='academic-note'>Los datos financieros, costos, "
        "efectividades y resultados son simulados. Las cifras son proyecciones "
        "académicas, no beneficios realizados ni recomendaciones bancarias "
        "reales.</div>",
        unsafe_allow_html=True,
    )


def mostrar_kpis(indicadores: Mapping[str, float | int | None]) -> None:
    """Presenta los indicadores comunes del panel y del simulador."""

    first = st.columns(3)
    first[0].metric("Clientes", f"{indicadores['clientes_analizados']:,}")
    first[1].metric("Rentables", f"{indicadores['clientes_rentables']:,}")
    first[2].metric("Deficitarios", f"{indicadores['clientes_deficitarios']:,}")

    second = st.columns(3)
    second[0].metric("Retener", f"{indicadores['clientes_retener']:,}")
    second[1].metric(
        "No intervención",
        f"{indicadores['clientes_no_intervencion']:,}",
    )
    second[2].metric(
        "Salida permitida",
        f"{indicadores['clientes_salida_permitida']:,}",
    )

    third = st.columns(2)
    third[0].metric(
        "Inversión",
        formato_usd(indicadores["inversion_total_usd"]),
    )
    third[1].metric(
        "Beneficio bruto esperado",
        formato_usd(indicadores["beneficio_bruto_esperado_usd"]),
    )

    fourth = st.columns(2)
    fourth[0].metric("GNE total", formato_usd(indicadores["gne_total_usd"]))
    roi = indicadores["roi_proyectado_pct"]
    fourth[1].metric("ROI proyectado", "N/A" if roi is None else f"{roi:.2f} %")

    fifth = st.columns(2)
    fifth[0].metric(
        "Saldo expuesto¹",
        formato_numero(indicadores["saldo_expuesto_unidades_originales"]),
    )
    weighted = indicadores["efectividad_ponderada_riesgo"]
    weighted_text = "N/A" if weighted is None else f"{weighted:.1%} ponderada"
    fifth[1].metric(
        "Abandonos esperados evitados²",
        formato_numero(indicadores["abandonos_esperados_evitados"]),
        weighted_text,
    )
    st.caption(
        "¹ Σ(probabilidad × Balance), en las unidades originales no declaradas "
        "de Balance; no equivale a dinero perdido. ² Proyección basada en "
        "efectividades académicas, no en campañas observadas."
    )
