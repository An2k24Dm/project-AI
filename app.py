"""Punto de entrada de la aplicación Deep Retention."""

from __future__ import annotations

import logging

import streamlit as st

from ui.pages.buscador import render_buscador
from ui.pages.dashboard import render_dashboard
from ui.pages.simulador import render_simulador
from ui.services import (
    cargar_datos_aplicacion,
    construir_escenario_base,
    obtener_version_recursos,
)
from ui.styles import aplicar_estilos


st.set_page_config(
    page_title="Deep Retention",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

SECTIONS = ("Buscador de clientes", "Panel de cartera", "Simulador")
LOGGER = logging.getLogger(__name__)


def _configurar_navegacion(client_count: int) -> str:
    st.sidebar.title("Deep Retention")
    st.sidebar.caption("Inteligencia de retención")
    section = st.sidebar.radio("Navegación", SECTIONS)
    st.sidebar.divider()
    st.sidebar.success("Datos y catálogo validados")
    st.sidebar.caption(f"Clientes: {client_count:,}")
    st.sidebar.caption("Escenario base: reglas académicas")
    return section


def main() -> None:
    """Inicializa recursos mínimos y delega la página seleccionada."""

    aplicar_estilos()
    st.title("Deep Retention")
    st.caption("Sistema académico de retención selectiva de clientes")

    try:
        version = obtener_version_recursos()
        datos = cargar_datos_aplicacion(version)
    except Exception:  # límite de interfaz: mensaje seguro y detención
        LOGGER.exception("No fue posible inicializar Deep Retention.")
        st.error(
            "No fue posible iniciar Deep Retention. Verifique que los datos, "
            "el catálogo y los artefactos requeridos estén disponibles."
        )
        st.stop()

    section = _configurar_navegacion(len(datos.clientes))
    try:
        if section == "Buscador de clientes":
            render_buscador(datos.clientes, version)
            return

        with st.spinner("Cargando modelo y escenario de cartera..."):
            base = construir_escenario_base(version)
        st.sidebar.success("Modelo y escenario listos")
        if section == "Panel de cartera":
            render_dashboard(base.cartera)
        else:
            render_simulador(version, datos.catalogo, base)
    except Exception:  # límite de presentación
        LOGGER.exception("No fue posible preparar la vista seleccionada.")
        st.error(
            "No fue posible preparar la vista seleccionada. Intente nuevamente "
            "o solicite una revisión de los recursos de la aplicación."
        )


if __name__ == "__main__":
    main()
