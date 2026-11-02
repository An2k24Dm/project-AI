"""Página de simulación temporal de campañas."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import comparar_escenarios
from ui.components import mostrar_aviso_academico, mostrar_kpis
from ui.services import (
    EscenarioCartera,
    ParametrosEscenario,
    construir_escenario_simulado,
)
from ui.styles import GRAY, GREEN


def inicializar_simulador(catalogo: pd.DataFrame) -> None:
    """Inicializa los controles sin sobrescribir el estado de la sesión."""

    for _, incentive in catalogo.iterrows():
        incentive_id = int(incentive["incentivo_id"])
        st.session_state.setdefault(
            f"sim_cost_{incentive_id}",
            float(incentive["costo_anual_usd"]),
        )
        st.session_state.setdefault(
            f"sim_effect_{incentive_id}",
            float(incentive["efectividad"]),
        )


def restablecer_simulador(catalogo: pd.DataFrame) -> None:
    """Restaura costos y efectividades a los valores del catálogo base."""

    for _, incentive in catalogo.iterrows():
        incentive_id = int(incentive["incentivo_id"])
        st.session_state[f"sim_cost_{incentive_id}"] = float(
            incentive["costo_anual_usd"]
        )
        st.session_state[f"sim_effect_{incentive_id}"] = float(
            incentive["efectividad"]
        )


def _capturar_parametros(catalogo: pd.DataFrame) -> ParametrosEscenario:
    parameters: list[tuple[int, float, float]] = []
    with st.form("simulator_parameters"):
        for _, incentive in catalogo.iterrows():
            incentive_id = int(incentive["incentivo_id"])
            st.markdown(f"**{incentive['nombre']}**")
            left, right = st.columns(2)
            cost = left.number_input(
                "Costo anual USD",
                min_value=0.0,
                step=5.0,
                key=f"sim_cost_{incentive_id}",
            )
            effectiveness = right.number_input(
                "Efectividad estimada",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                format="%.2f",
                key=f"sim_effect_{incentive_id}",
            )
            parameters.append((incentive_id, float(cost), float(effectiveness)))
        st.form_submit_button("Recalcular escenario", type="primary")
    return tuple(parameters)


def _parametros_originales(catalogo: pd.DataFrame) -> ParametrosEscenario:
    return tuple(
        (
            int(row["incentivo_id"]),
            float(row["costo_anual_usd"]),
            float(row["efectividad"]),
        )
        for _, row in catalogo.iterrows()
    )


def _mostrar_distribucion(
    base_portfolio: pd.DataFrame,
    simulated_portfolio: pd.DataFrame,
) -> None:
    base = (
        base_portfolio.loc[base_portfolio["decision"].eq("Retener"), "incentivo"]
        .value_counts()
        .rename("Clientes")
        .reset_index()
        .assign(Escenario="Base")
    )
    simulated = (
        simulated_portfolio.loc[
            simulated_portfolio["decision"].eq("Retener"),
            "incentivo",
        ]
        .value_counts()
        .rename("Clientes")
        .reset_index()
        .assign(Escenario="Simulado")
    )
    distribution = pd.concat([base, simulated], ignore_index=True)
    chart = px.bar(
        distribution,
        x="incentivo",
        y="Clientes",
        color="Escenario",
        barmode="group",
        title="Distribución de incentivos: base y simulación",
        color_discrete_map={"Base": GRAY, "Simulado": GREEN},
    )
    st.plotly_chart(chart, width="stretch")


def render_simulador(
    version: str,
    catalogo: pd.DataFrame,
    base: EscenarioCartera,
) -> None:
    """Renderiza controles, comparación e indicadores del escenario."""

    st.header("Simulador de campañas")
    st.write(
        "Modifique costos y efectividades para crear un escenario temporal. "
        "Las probabilidades del MLP y los percentiles de referencia se conservan."
    )
    inicializar_simulador(catalogo)
    if st.button("Restablecer valores originales", type="secondary"):
        restablecer_simulador(catalogo)
        st.rerun()

    parameters = _capturar_parametros(catalogo)
    if parameters == _parametros_originales(catalogo):
        simulated_catalog = catalogo
        simulated_portfolio = base.cartera
        simulated_indicators = base.indicadores
    else:
        with st.spinner(
            "Recalculando elegibilidad y GNE sin ejecutar nuevamente el MLP..."
        ):
            scenario = construir_escenario_simulado(version, parameters)
        simulated_catalog = scenario.catalogo
        simulated_portfolio = scenario.cartera
        simulated_indicators = scenario.indicadores

    st.subheader("Comparación de escenarios")
    comparison = comparar_escenarios(base.indicadores, simulated_indicators)
    st.dataframe(comparison, hide_index=True, width="stretch")
    _mostrar_distribucion(base.cartera, simulated_portfolio)

    st.subheader("Indicadores del escenario simulado")
    mostrar_kpis(simulated_indicators)
    with st.expander("Catálogo temporal utilizado"):
        st.dataframe(simulated_catalog, hide_index=True, width="stretch")
    mostrar_aviso_academico()
