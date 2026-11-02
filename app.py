"""Aplicación ejecutiva de Deep Retention."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import (
    calcular_indicadores,
    comparar_escenarios,
    enriquecer_resultados,
    filtrar_cartera,
)
from src.data_processing import (
    CATALOG_PATH,
    CLIENTS_PATH,
    ClienteNoEncontradoError,
    buscar_cliente,
    cargar_catalogo,
    cargar_clientes,
    crear_catalogo_escenario,
)
from src.financial import (
    calcular_umbrales_comerciales,
    evaluar_cartera,
)
from src.prediction import PredictorFuga


st.set_page_config(
    page_title="Deep Retention",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#102A43"
BLUE = "#1F5A94"
GREEN = "#16856B"
GRAY = "#627D98"

st.markdown(
    f"""
    <style>
      .stApp {{ background: #F5F7FA; }}
      [data-testid="stSidebar"] {{ background: {NAVY}; }}
      [data-testid="stSidebar"] * {{ color: white; }}
      [data-testid="stMain"] {{ color: #243B53; }}
      [data-testid="stMain"] h1,
      [data-testid="stMain"] h2,
      [data-testid="stMain"] h3,
      [data-testid="stMain"] p,
      [data-testid="stMain"] label,
      [data-testid="stMain"] [data-testid="stMetricValue"] {{
        color: #243B53 !important;
      }}
      div[data-testid="stMetric"] {{
        background: white; border: 1px solid #D9E2EC; border-radius: 12px;
        padding: 14px 16px; box-shadow: 0 2px 8px rgba(16,42,67,.06);
      }}
      .decision-card {{
        border-radius: 12px; padding: 18px; margin: 8px 0 16px 0;
        border-left: 6px solid {GREEN}; background: white;
      }}
      .risk-badge {{
        display: inline-block; padding: 6px 12px; border-radius: 999px;
        font-weight: 700; margin-bottom: 8px;
      }}
      .academic-note {{
        color: {GRAY}; font-size: .88rem; background: #E9F2FA;
        border-radius: 8px; padding: 10px 12px;
      }}
      [data-testid="stBaseButton-primary"],
      [data-testid="stBaseButton-primaryFormSubmit"] {{
        background: {GREEN}; border-color: {GREEN}; color: white !important;
      }}
      [data-testid="stBaseButton-primary"] p,
      [data-testid="stBaseButton-primaryFormSubmit"] p {{
        color: white !important;
      }}
      [data-testid="stBaseButton-primary"]:hover,
      [data-testid="stBaseButton-primaryFormSubmit"]:hover {{
        background: #0F6D58; border-color: #0F6D58; color: white !important;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _file_version(*paths: Path) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


@st.cache_data(show_spinner=False)
def cargar_datos_aplicacion(version: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    del version
    return cargar_clientes(), cargar_catalogo()


@st.cache_resource(show_spinner=False)
def cargar_predictor() -> PredictorFuga:
    return PredictorFuga()


@st.cache_data(show_spinner=False)
def generar_probabilidades(version: str) -> np.ndarray:
    clientes, _ = cargar_datos_aplicacion(version)
    return cargar_predictor().predecir_lote(clientes)


@st.cache_data(show_spinner=False)
def construir_escenario_base(version: str):
    clientes, catalogo = cargar_datos_aplicacion(version)
    probabilidades = generar_probabilidades(version)
    umbrales = calcular_umbrales_comerciales(clientes, catalogo)
    decisiones = evaluar_cartera(clientes, probabilidades, catalogo, umbrales)
    cartera = enriquecer_resultados(clientes, decisiones)
    indicadores = calcular_indicadores(cartera)
    return probabilidades, umbrales, cartera, indicadores


@st.cache_data(show_spinner=False)
def construir_escenario_simulado(
    version: str,
    parametros: tuple[tuple[int, float, float], ...],
):
    clientes, catalogo = cargar_datos_aplicacion(version)
    probabilidades, umbrales, _, _ = construir_escenario_base(version)
    cambios = {
        incentive_id: {
            "costo_anual_usd": cost,
            "efectividad": effectiveness,
        }
        for incentive_id, cost, effectiveness in parametros
    }
    catalogo_simulado = crear_catalogo_escenario(catalogo, cambios)
    decisiones = evaluar_cartera(
        clientes,
        probabilidades,
        catalogo_simulado,
        umbrales,
    )
    cartera = enriquecer_resultados(clientes, decisiones)
    return catalogo_simulado, cartera, calcular_indicadores(cartera)


def formato_usd(value: float | None) -> str:
    return "No aplicable" if value is None else f"USD {value:,.2f}"


def formato_numero(value: float | int | None, decimals: int = 2) -> str:
    return "No aplicable" if value is None else f"{value:,.{decimals}f}"


def nivel_riesgo(probability: float) -> tuple[str, str, str]:
    if probability < 0.20:
        return "Bajo", "#D1FAE5", "#065F46"
    if probability < 0.40:
        return "Moderado", "#FEF3C7", "#92400E"
    if probability < 0.70:
        return "Alto", "#FED7AA", "#9A3412"
    return "Muy alto", "#FEE2E2", "#991B1B"


def mostrar_aviso_academico() -> None:
    st.markdown(
        "<div class='academic-note'>Los datos financieros, costos, "
        "efectividades y resultados son simulados. Las cifras son proyecciones "
        "académicas, no beneficios realizados ni recomendaciones bancarias reales.</div>",
        unsafe_allow_html=True,
    )


def mostrar_kpis(indicadores: dict[str, float | int | None]) -> None:
    first = st.columns(5)
    first[0].metric("Clientes", f"{indicadores['clientes_analizados']:,}")
    first[1].metric("Retener", f"{indicadores['clientes_retener']:,}")
    first[2].metric(
        "No intervención", f"{indicadores['clientes_no_intervencion']:,}"
    )
    first[3].metric(
        "Salida permitida", f"{indicadores['clientes_salida_permitida']:,}"
    )
    first[4].metric("Inversión", formato_usd(indicadores["inversion_total_usd"]))

    second = st.columns(5)
    second[0].metric("GNE total", formato_usd(indicadores["gne_total_usd"]))
    second[1].metric(
        "Valor esperado a rescatar",
        formato_usd(indicadores["valor_rescatable_estimado_usd"]),
    )
    roi = indicadores["roi_proyectado_pct"]
    second[2].metric("ROI proyectado", "N/A" if roi is None else f"{roi:.2f} %")
    second[3].metric(
        "Saldo expuesto¹",
        formato_numero(indicadores["saldo_expuesto_unidades_originales"]),
    )
    avoided = indicadores["abandonos_esperados_evitados"]
    weighted = indicadores["efectividad_ponderada_riesgo"]
    weighted_text = "N/A" if weighted is None else f"{weighted:.1%} ponderada"
    second[4].metric(
        "Abandonos esperados evitados",
        formato_numero(avoided),
        weighted_text,
    )
    st.caption(
        "¹ Σ(probabilidad × Balance), expresado en las unidades originales no "
        "declaradas de Balance. No equivale a margen ni a dinero recuperado."
    )


def render_buscador(clientes: pd.DataFrame, cartera: pd.DataFrame) -> None:
    st.header("Buscador individual de clientes")
    st.write(
        "Consulte el perfil bancario, la probabilidad ajustada y la decisión "
        "económica trazable de un cliente."
    )

    default_id = str(int(clientes["CustomerId"].iloc[0]))
    customer_id = st.text_input("CustomerId", value=default_id)
    try:
        client = buscar_cliente(clientes, customer_id)
    except ClienteNoEncontradoError as error:
        st.warning(str(error))
        return

    result = cartera.loc[cartera["CustomerId"].eq(client["CustomerId"])]
    if len(result) != 1:
        st.error("No fue posible asociar la decisión financiera al cliente.")
        return
    decision = result.iloc[0]

    surname = "No disponible" if pd.isna(client["Surname"]) else str(client["Surname"])
    profile_names = [
        option["perfil_requerido"]
        for option in decision["alternativas"]
        if option["elegible_comercial"]
    ]
    commercial_profile = ", ".join(profile_names) or "Sin perfil elegible"

    st.subheader("Información general")
    general = st.columns(4)
    general[0].metric("Cliente", int(client["CustomerId"]))
    general[1].metric("Apellido", surname)
    general[2].metric("Edad", f"{int(client['Age'])} años")
    general[3].metric("País", client["Geography"])

    info = pd.DataFrame(
        {
            "Dato": [
                "Antigüedad",
                "Saldo",
                "Productos",
                "Actividad bancaria",
                "Transacciones mensuales",
                "Volumen mensual",
                "Comisiones anuales",
                "Margen neto anual",
                "Rentabilidad",
                "Perfiles comerciales elegibles",
            ],
            "Valor": [
                f"{int(client['Tenure'])} años",
                f"{client['Balance']:,.2f} (unidad original)",
                int(client["NumOfProducts"]),
                "Activo" if int(client["IsActiveMember"]) == 1 else "Inactivo",
                int(client["MonthlyTransactions_Sim"]),
                formato_usd(float(client["MonthlyTransactionVolume_USD_Sim"])),
                formato_usd(float(client["AnnualCommissionIncome_USD_Sim"])),
                formato_usd(float(client["AnnualNetMargin_USD_Sim"])),
                decision["rentabilidad"],
                commercial_profile,
            ],
        }
    )
    info["Valor"] = info["Valor"].astype(str)
    st.dataframe(info, hide_index=True, width="stretch")

    st.subheader("Predicción de abandono")
    probability = float(decision["probabilidad_fuga"])
    risk, background, foreground = nivel_riesgo(probability)
    left, right = st.columns([1, 3])
    left.metric("Probabilidad ajustada", f"{probability:.2%}")
    right.markdown(
        f"<span class='risk-badge' style='background:{background};color:{foreground}'>"
        f"Riesgo descriptivo: {risk}</span>",
        unsafe_allow_html=True,
    )
    right.write(
        "La probabilidad estima riesgo de abandono. El nivel visual no autoriza "
        "incentivos: la decisión depende de elegibilidad, margen y GNE."
    )

    st.subheader("Decisión comercial")
    decision_color = {
        "Retener": GREEN,
        "No intervención": BLUE,
        "Salida permitida": GRAY,
    }[decision["decision"]]
    if decision["decision"] == "Retener":
        explanation = (
            f"Se recomienda **{decision['incentivo']}** porque el cliente cumple "
            f"los criterios comerciales y genera una GNE positiva de "
            f"{formato_usd(float(decision['gne']))}."
        )
    else:
        explanation = str(decision["motivo"])
    st.markdown(
        f"<div class='decision-card' style='border-left-color:{decision_color}'>"
        f"<h3 style='margin:0'>{decision['decision']}</h3></div>",
        unsafe_allow_html=True,
    )
    st.markdown(explanation)

    financial = st.columns(4)
    financial[0].metric("Margen anual", formato_usd(decision["margen_anual_usd"]))
    financial[1].metric("Incentivo", decision["incentivo"] or "Ninguno")
    financial[2].metric("Costo anual", formato_usd(decision["costo"]))
    financial[3].metric("GNE seleccionada", formato_usd(decision["gne"]))

    with st.expander("Auditar todas las alternativas evaluadas"):
        alternatives = pd.DataFrame(decision["alternativas"])
        if alternatives.empty:
            st.info("No se evalúan gastos para clientes con margen no positivo.")
        else:
            alternatives = alternatives.rename(
                columns={
                    "incentivo": "Incentivo",
                    "perfil_requerido": "Perfil",
                    "efectividad": "Efectividad",
                    "costo_anual_usd": "Costo anual USD",
                    "gne": "GNE USD",
                    "elegible_comercial": "Elegible comercial",
                    "elegible": "Elegible total",
                    "gne_positiva": "GNE positiva",
                    "motivo": "Motivo",
                }
            )
            visible = [
                "Incentivo",
                "Perfil",
                "Efectividad",
                "Costo anual USD",
                "GNE USD",
                "Elegible comercial",
                "Elegible total",
                "GNE positiva",
                "Motivo",
            ]
            st.dataframe(alternatives[visible], hide_index=True, width="stretch")
    mostrar_aviso_academico()


def render_dashboard(cartera: pd.DataFrame) -> None:
    st.header("Panel ejecutivo de cartera")
    st.write(
        "Los filtros modifican la visualización y los KPI del subconjunto, pero "
        "no recalculan percentiles ni decisiones."
    )

    with st.expander("Filtros", expanded=True):
        columns = st.columns(5)
        countries = columns[0].multiselect(
            "País", sorted(cartera["Geography"].dropna().unique())
        )
        profitability = columns[1].multiselect(
            "Rentabilidad", sorted(cartera["rentabilidad"].unique())
        )
        decisions = columns[2].multiselect(
            "Decisión", sorted(cartera["decision"].unique())
        )
        incentives = columns[3].multiselect(
            "Incentivo", sorted(cartera["incentivo_mostrado"].unique())
        )
        probability_range = columns[4].slider(
            "Probabilidad", 0.0, 1.0, (0.0, 1.0), step=0.01
        )

    filtered = filtrar_cartera(
        cartera,
        paises=countries,
        rentabilidades=profitability,
        decisiones=decisions,
        incentivos=incentives,
        rango_probabilidad=probability_range,
    )
    indicators = calcular_indicadores(filtered)
    mostrar_kpis(indicators)

    if filtered.empty:
        st.info("No hay clientes que cumplan los filtros seleccionados.")
        return

    tab_risk, tab_decisions, tab_economy = st.tabs(
        ["Riesgo", "Decisiones", "Economía"]
    )
    with tab_risk:
        left, right = st.columns(2)
        histogram = px.histogram(
            filtered,
            x="probabilidad_fuga",
            nbins=30,
            color_discrete_sequence=[BLUE],
            title="Distribución de probabilidades ajustadas",
            labels={"probabilidad_fuga": "Probabilidad de abandono"},
        )
        left.plotly_chart(histogram, width="stretch")
        profitability_chart = px.pie(
            filtered,
            names="rentabilidad",
            title="Clientes rentables y deficitarios",
            color="rentabilidad",
            color_discrete_map={"Rentable": GREEN, "Deficitario": GRAY},
        )
        right.plotly_chart(profitability_chart, width="stretch")

    with tab_decisions:
        left, right = st.columns(2)
        decision_counts = filtered["decision"].value_counts().reset_index()
        decision_chart = px.bar(
            decision_counts,
            x="decision",
            y="count",
            color="decision",
            title="Distribución de decisiones",
            labels={"decision": "Decisión", "count": "Clientes"},
        )
        left.plotly_chart(decision_chart, width="stretch")
        incentive_counts = (
            filtered.loc[filtered["decision"].eq("Retener"), "incentivo"]
            .value_counts()
            .reset_index()
        )
        incentive_chart = px.bar(
            incentive_counts,
            x="incentivo",
            y="count",
            color="incentivo",
            title="Clientes por incentivo recomendado",
            labels={"incentivo": "Incentivo", "count": "Clientes"},
        )
        right.plotly_chart(incentive_chart, width="stretch")

        scatter = px.scatter(
            filtered,
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

    with tab_economy:
        retained = filtered.loc[filtered["decision"].eq("Retener")].copy()
        grouped = (
            retained.groupby("incentivo", as_index=False)
            .agg(inversion_usd=("costo", "sum"), gne_usd=("gne", "sum"))
        )
        left, right = st.columns(2)
        investment_chart = px.bar(
            grouped,
            x="incentivo",
            y="inversion_usd",
            color="incentivo",
            title="Inversión proyectada por incentivo",
        )
        left.plotly_chart(investment_chart, width="stretch")
        gne_chart = px.bar(
            grouped,
            x="incentivo",
            y="gne_usd",
            color="incentivo",
            title="GNE agregada por incentivo",
        )
        right.plotly_chart(gne_chart, width="stretch")
        margin_chart = px.box(
            filtered,
            x="decision",
            y="margen_anual_usd",
            color="decision",
            title="Rentabilidad según decisión comercial",
        )
        st.plotly_chart(margin_chart, width="stretch")

    st.subheader("Clientes y oportunidades")
    table = filtered.sort_values("gne", ascending=False)[
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
                "Probabilidad", min_value=0.0, max_value=1.0, format="%.2f"
            ),
            "margen_anual_usd": st.column_config.NumberColumn(
                "Margen anual USD", format="%.2f"
            ),
            "decision": "Decisión",
            "incentivo_mostrado": "Incentivo",
            "costo": st.column_config.NumberColumn("Costo USD", format="%.2f"),
            "gne": st.column_config.NumberColumn("GNE USD", format="%.2f"),
        },
    )
    mostrar_aviso_academico()


def _initialize_simulator(catalog: pd.DataFrame) -> None:
    for _, incentive in catalog.iterrows():
        incentive_id = int(incentive["incentivo_id"])
        st.session_state.setdefault(
            f"sim_cost_{incentive_id}", float(incentive["costo_anual_usd"])
        )
        st.session_state.setdefault(
            f"sim_effect_{incentive_id}", float(incentive["efectividad"])
        )


def _reset_simulator(catalog: pd.DataFrame) -> None:
    for _, incentive in catalog.iterrows():
        incentive_id = int(incentive["incentivo_id"])
        st.session_state[f"sim_cost_{incentive_id}"] = float(
            incentive["costo_anual_usd"]
        )
        st.session_state[f"sim_effect_{incentive_id}"] = float(
            incentive["efectividad"]
        )


def render_simulador(
    version: str,
    catalog: pd.DataFrame,
    base_portfolio: pd.DataFrame,
    base_indicators: dict[str, float | int | None],
) -> None:
    st.header("Simulador de campañas")
    st.write(
        "Modifique costos y efectividades para crear un escenario temporal. "
        "Las probabilidades del MLP y los percentiles de referencia se conservan."
    )
    _initialize_simulator(catalog)

    if st.button("Restablecer valores originales", type="secondary"):
        _reset_simulator(catalog)
        st.rerun()

    with st.form("simulator_parameters"):
        parameters: list[tuple[int, float, float]] = []
        for _, incentive in catalog.iterrows():
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

    parameter_tuple = tuple(parameters)
    original_tuple = tuple(
        (
            int(row["incentivo_id"]),
            float(row["costo_anual_usd"]),
            float(row["efectividad"]),
        )
        for _, row in catalog.iterrows()
    )
    if parameter_tuple == original_tuple:
        simulated_catalog = catalog
        simulated_portfolio = base_portfolio
        simulated_indicators = base_indicators
    else:
        with st.spinner("Recalculando elegibilidad y GNE sin ejecutar nuevamente el MLP..."):
            simulated_catalog, simulated_portfolio, simulated_indicators = (
                construir_escenario_simulado(version, parameter_tuple)
            )

    st.subheader("Comparación de escenarios")
    comparison = comparar_escenarios(base_indicators, simulated_indicators)
    st.dataframe(comparison, hide_index=True, width="stretch")

    base_distribution = (
        base_portfolio.loc[base_portfolio["decision"].eq("Retener"), "incentivo"]
        .value_counts()
        .rename("Clientes")
        .reset_index()
        .assign(Escenario="Base")
    )
    simulated_distribution = (
        simulated_portfolio.loc[
            simulated_portfolio["decision"].eq("Retener"), "incentivo"
        ]
        .value_counts()
        .rename("Clientes")
        .reset_index()
        .assign(Escenario="Simulado")
    )
    distribution = pd.concat(
        [base_distribution, simulated_distribution], ignore_index=True
    )
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

    st.subheader("Indicadores del escenario simulado")
    mostrar_kpis(simulated_indicators)
    with st.expander("Catálogo temporal utilizado"):
        st.dataframe(simulated_catalog, hide_index=True, width="stretch")
    mostrar_aviso_academico()


def main() -> None:
    st.title("Deep Retention")
    st.caption("Sistema académico de retención selectiva de clientes")

    try:
        version = _file_version(CLIENTS_PATH, CATALOG_PATH)
        with st.spinner("Cargando cartera, modelo y decisiones base..."):
            clients, catalog = cargar_datos_aplicacion(version)
            _, _, portfolio, indicators = construir_escenario_base(version)
    except Exception as error:  # límite de interfaz: mensaje seguro y detención
        st.error(
            "No fue posible iniciar Deep Retention. Verifique datos, catálogo y "
            f"artefactos. Detalle: {error}"
        )
        st.stop()

    st.sidebar.title("Deep Retention")
    st.sidebar.caption("Inteligencia de retención")
    section = st.sidebar.radio(
        "Navegación",
        ["Buscador de clientes", "Panel de cartera", "Simulador"],
    )
    st.sidebar.divider()
    st.sidebar.success("Modelo y artefactos cargados")
    st.sidebar.caption(f"Clientes: {len(clients):,}")
    st.sidebar.caption("Escenario base: reglas académicas")

    if section == "Buscador de clientes":
        render_buscador(clients, portfolio)
    elif section == "Panel de cartera":
        render_dashboard(portfolio)
    else:
        render_simulador(version, catalog, portfolio, indicators)


if __name__ == "__main__":
    main()
