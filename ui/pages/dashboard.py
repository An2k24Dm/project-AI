"""Página ejecutiva de cartera y oportunidades."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import calcular_indicadores, filtrar_cartera
from ui.components import mostrar_aviso_academico, mostrar_kpis
from ui.styles import BLUE, GRAY, GREEN


def _mostrar_filtros(cartera: pd.DataFrame) -> pd.DataFrame:
    with st.expander("Filtros", expanded=True):
        columns = st.columns(5)
        countries = columns[0].multiselect(
            "País",
            sorted(cartera["Geography"].dropna().unique()),
        )
        profitability = columns[1].multiselect(
            "Rentabilidad",
            sorted(cartera["rentabilidad"].unique()),
        )
        decisions = columns[2].multiselect(
            "Decisión",
            sorted(cartera["decision"].unique()),
        )
        incentives = columns[3].multiselect(
            "Incentivo",
            sorted(cartera["incentivo_mostrado"].unique()),
        )
        probability_range = columns[4].slider(
            "Probabilidad",
            0.0,
            1.0,
            (0.0, 1.0),
            step=0.01,
        )
    return filtrar_cartera(
        cartera,
        paises=countries,
        rentabilidades=profitability,
        decisiones=decisions,
        incentivos=incentives,
        rango_probabilidad=probability_range,
    )


def _mostrar_graficos_riesgo(cartera: pd.DataFrame) -> None:
    left, right = st.columns(2)
    histogram = px.histogram(
        cartera,
        x="probabilidad_fuga",
        nbins=30,
        color_discrete_sequence=[BLUE],
        title="Distribución de probabilidades ajustadas",
        labels={"probabilidad_fuga": "Probabilidad de abandono"},
    )
    left.plotly_chart(histogram, width="stretch")
    profitability = px.pie(
        cartera,
        names="rentabilidad",
        title="Clientes rentables y deficitarios",
        color="rentabilidad",
        color_discrete_map={"Rentable": GREEN, "Deficitario": GRAY},
    )
    right.plotly_chart(profitability, width="stretch")


def _mostrar_graficos_decisiones(cartera: pd.DataFrame) -> None:
    left, right = st.columns(2)
    decision_counts = cartera["decision"].value_counts().reset_index()
    decisions = px.bar(
        decision_counts,
        x="decision",
        y="count",
        color="decision",
        title="Distribución de decisiones",
        labels={"decision": "Decisión", "count": "Clientes"},
    )
    left.plotly_chart(decisions, width="stretch")

    incentive_counts = (
        cartera.loc[cartera["decision"].eq("Retener"), "incentivo"]
        .value_counts()
        .reset_index()
    )
    incentives = px.bar(
        incentive_counts,
        x="incentivo",
        y="count",
        color="incentivo",
        title="Clientes por incentivo recomendado",
        labels={"incentivo": "Incentivo", "count": "Clientes"},
    )
    right.plotly_chart(incentives, width="stretch")

    scatter = px.scatter(
        cartera,
        x="probabilidad_fuga",
        y="margen_anual_usd",
        color="decision",
        hover_data=["CustomerId", "incentivo_mostrado"],
        render_mode="webgl",
        title="Probabilidad de abandono frente a margen neto",
        labels={
            "probabilidad_fuga": "Probabilidad de abandono",
            "margen_anual_usd": "Margen neto anual (USD)",
        },
    )
    st.plotly_chart(scatter, width="stretch")


def _mostrar_graficos_economia(cartera: pd.DataFrame) -> None:
    retained = cartera.loc[cartera["decision"].eq("Retener")]
    grouped = retained.groupby("incentivo", as_index=False).agg(
        inversion_usd=("costo", "sum"),
        gne_usd=("gne", "sum"),
    )
    left, right = st.columns(2)
    investment = px.bar(
        grouped,
        x="incentivo",
        y="inversion_usd",
        color="incentivo",
        title="Inversión proyectada por incentivo",
    )
    left.plotly_chart(investment, width="stretch")
    gne = px.bar(
        grouped,
        x="incentivo",
        y="gne_usd",
        color="incentivo",
        title="GNE agregada por incentivo",
    )
    right.plotly_chart(gne, width="stretch")
    margin = px.box(
        cartera,
        x="decision",
        y="margen_anual_usd",
        color="decision",
        title="Rentabilidad según decisión comercial",
    )
    st.plotly_chart(margin, width="stretch")


def _mostrar_tabla_oportunidades(cartera: pd.DataFrame) -> None:
    st.subheader("Clientes y oportunidades")
    table = cartera.sort_values("gne", ascending=False)[
        [
            "CustomerId",
            "Geography",
            "probabilidad_fuga",
            "margen_anual_usd",
            "decision",
            "incentivo_mostrado",
            "costo",
            "gne",
        ]
    ]
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "probabilidad_fuga": st.column_config.ProgressColumn(
                "Probabilidad",
                min_value=0.0,
                max_value=1.0,
                format="%.2f",
            ),
            "margen_anual_usd": st.column_config.NumberColumn(
                "Margen anual USD",
                format="%.2f",
            ),
            "decision": "Decisión",
            "incentivo_mostrado": "Incentivo",
            "costo": st.column_config.NumberColumn("Costo USD", format="%.2f"),
            "gne": st.column_config.NumberColumn("GNE USD", format="%.2f"),
        },
    )


def render_dashboard(cartera: pd.DataFrame) -> None:
    """Renderiza KPI, filtros y gráficos sin recalcular decisiones."""

    st.header("Panel ejecutivo de cartera")
    st.write(
        "Los filtros modifican la visualización y los KPI del subconjunto, pero "
        "no recalculan percentiles ni decisiones."
    )
    filtered = _mostrar_filtros(cartera)
    mostrar_kpis(calcular_indicadores(filtered))
    if filtered.empty:
        st.info("No hay clientes que cumplan los filtros seleccionados.")
        return

    tab_risk, tab_decisions, tab_economy = st.tabs(
        ["Riesgo", "Decisiones", "Economía"]
    )
    with tab_risk:
        _mostrar_graficos_riesgo(filtered)
    with tab_decisions:
        _mostrar_graficos_decisiones(filtered)
    with tab_economy:
        _mostrar_graficos_economia(filtered)
    _mostrar_tabla_oportunidades(filtered)
    mostrar_aviso_academico()
