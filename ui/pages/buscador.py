"""Página de consulta individual de clientes."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data_processing import ClienteNoEncontradoError
from ui.components import formato_usd, mostrar_aviso_academico, nivel_riesgo
from ui.services import obtener_resultado_cliente
from ui.styles import BLUE, GRAY, GREEN


def _limpiar_resultado_anterior() -> None:
    st.session_state.pop("buscador_resultado_id", None)


def _mostrar_identificacion(cliente: pd.Series) -> None:
    surname = (
        "No disponible" if pd.isna(cliente["Surname"]) else str(cliente["Surname"])
    )
    st.subheader("A. Identificación y perfil bancario")
    general = st.columns(4)
    general[0].metric("Cliente", int(cliente["CustomerId"]))
    general[1].metric("Apellido", surname)
    general[2].metric("Edad", f"{int(cliente['Age'])} años")
    general[3].metric("País", cliente["Geography"])

    info = pd.DataFrame(
        {
            "Dato": [
                "Antigüedad",
                "Saldo",
                "Productos",
                "Actividad bancaria",
            ],
            "Valor": [
                f"{int(cliente['Tenure'])} años",
                f"{cliente['Balance']:,.2f} (unidad original)",
                str(int(cliente["NumOfProducts"])),
                "Activo" if int(cliente["IsActiveMember"]) == 1 else "Inactivo",
            ],
        }
    )
    st.dataframe(info, hide_index=True, width="stretch")


def _mostrar_prediccion(cliente: pd.Series) -> None:
    st.subheader("B. Predicción del modelo neuronal")
    probability = float(cliente["probabilidad_fuga"])
    risk, background, foreground = nivel_riesgo(probability)
    left, right = st.columns([1, 3])
    left.metric("Puntaje MLP (probabilidad)", f"{probability:.2%}")
    right.markdown(
        f"<span class='risk-badge' style='background:{background};"
        f"color:{foreground}'>Riesgo descriptivo: {risk}</span>",
        unsafe_allow_html=True,
    )
    right.write(
        "Es una estimación del MLP, no una certeza de abandono ni el CreditScore. "
        "El nivel visual no autoriza incentivos: la decisión depende de "
        "elegibilidad, margen y GNE."
    )
    st.progress(probability, text=f"Riesgo estimado: {probability:.2%}")


def _mostrar_informacion_financiera(cliente: pd.Series) -> None:
    st.subheader("C. Información financiera simulada")
    summary = st.columns(3)
    summary[0].metric(
        "Ingresos por comisiones",
        formato_usd(cliente["AnnualCommissionIncome_USD_Sim"]),
    )
    summary[1].metric(
        "Costos operativos",
        formato_usd(cliente["AnnualOperatingCosts_USD_Sim"]),
    )
    summary[2].metric(
        "Margen neto anual",
        formato_usd(cliente["margen_anual_usd"]),
    )

    information = pd.DataFrame(
        {
            "Indicador": [
                "Transacciones mensuales",
                "Volumen mensual simulado",
                "Comisión promedio por transacción",
                "Contribución financiera anual",
                "Costos operativos anuales",
                "Margen neto anual",
                "Rentabilidad",
            ],
            "Valor": [
                str(int(cliente["MonthlyTransactions_Sim"])),
                formato_usd(cliente["MonthlyTransactionVolume_USD_Sim"]),
                formato_usd(cliente["AvgTransactionFee_USD_Sim"]),
                formato_usd(cliente["AnnualFinancialMargin_USD_Sim"]),
                formato_usd(cliente["AnnualOperatingCosts_USD_Sim"]),
                formato_usd(cliente["margen_anual_usd"]),
                str(cliente["rentabilidad"]),
            ],
        }
    )
    st.dataframe(information, hide_index=True, width="stretch")


def _mostrar_decision(cliente: pd.Series) -> None:
    st.subheader("D. Decisión comercial recomendada")
    color = {
        "Retener": GREEN,
        "No intervención": BLUE,
        "Salida permitida": GRAY,
    }[cliente["decision"]]
    if cliente["decision"] == "Retener":
        explanation = (
            f"Se recomienda **{cliente['incentivo']}** porque el cliente cumple "
            "los criterios comerciales y genera una GNE positiva de "
            f"{formato_usd(float(cliente['gne']))}."
        )
    else:
        explanation = str(cliente["motivo"])

    st.markdown(
        f"<div class='decision-card' style='border-left-color:{color}'>"
        f"<h3 style='margin:0'>{cliente['decision']}</h3></div>",
        unsafe_allow_html=True,
    )
    st.markdown(explanation)

    financial = st.columns(3)
    financial[0].metric(
        "Margen anual",
        formato_usd(cliente["margen_anual_usd"]),
    )
    financial[1].metric("Incentivo", cliente["incentivo"] or "Ninguno")
    financial[2].metric("Costo anual", formato_usd(cliente["costo"]))
    projected = st.columns(3)
    projected[0].metric(
        "Efectividad supuesta",
        f"{float(cliente['efectividad']):.0%}",
    )
    projected[1].metric(
        "Beneficio bruto esperado",
        formato_usd(cliente["beneficio_bruto_esperado_usd"]),
    )
    projected[2].metric("GNE seleccionada", formato_usd(cliente["gne"]))

    if cliente["decision"] == "Retener":
        st.code(
            "GNE = ({:.4f} × {:.2f} × {:.2f}) − {:.2f} = {:.2f} USD".format(
                float(cliente["probabilidad_fuga"]),
                float(cliente["efectividad"]),
                float(cliente["margen_anual_usd"]),
                float(cliente["costo"]),
                float(cliente["gne"]),
            ),
            language=None,
        )
    elif cliente["decision"] == "No intervención":
        st.info(
            "El cliente genera margen, pero no se ejecutará una campaña: "
            "el beneficio bruto, el costo y la GNE seleccionada son cero."
        )
    else:
        st.warning(
            "El margen neto no es positivo; se bloquea cualquier gasto de retención."
        )

    with st.expander("Auditar todas las alternativas evaluadas"):
        alternatives = pd.DataFrame(cliente["alternativas"])
        if alternatives.empty:
            st.info("No se evalúan gastos para clientes con margen no positivo.")
            return
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
        alternatives["Beneficio bruto USD"] = (
            alternatives["GNE USD"] + alternatives["Costo anual USD"]
        )
        visible = [
            "Incentivo",
            "Perfil",
            "Efectividad",
            "Costo anual USD",
            "Beneficio bruto USD",
            "GNE USD",
            "Elegible comercial",
            "Elegible total",
            "GNE positiva",
            "Motivo",
        ]
        st.dataframe(alternatives[visible], hide_index=True, width="stretch")


def render_buscador(clientes: pd.DataFrame, version: str) -> None:
    """Renderiza la búsqueda diferida y la decisión individual."""

    st.header("Buscador individual de clientes")
    st.write(
        "Consulte el perfil bancario, la probabilidad ajustada y la decisión "
        "económica trazable de un cliente. El modelo se carga al buscar."
    )

    default_id = str(int(clientes["CustomerId"].iloc[0]))
    customer_id = st.text_input(
        "CustomerId",
        value=default_id,
        key="buscador_input",
        on_change=_limpiar_resultado_anterior,
    )
    if st.button("Buscar cliente", type="primary"):
        st.session_state["buscador_resultado_id"] = customer_id

    selected_id = st.session_state.get("buscador_resultado_id")
    if selected_id is None:
        st.info("Ingrese un identificador y pulse «Buscar cliente».")
        return

    try:
        with st.spinner("Calculando probabilidad y decisión..."):
            resultado = obtener_resultado_cliente(version, selected_id)
    except ClienteNoEncontradoError as error:
        st.warning(str(error))
        return

    _mostrar_identificacion(resultado)
    _mostrar_prediccion(resultado)
    _mostrar_informacion_financiera(resultado)
    _mostrar_decision(resultado)
    mostrar_aviso_academico()
