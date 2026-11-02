"""Paleta y estilos visuales compartidos por la aplicación."""

from __future__ import annotations

import streamlit as st


NAVY = "#102A43"
BLUE = "#1F5A94"
GREEN = "#16856B"
GRAY = "#627D98"


def aplicar_estilos() -> None:
    """Aplica únicamente los estilos no cubiertos por el tema de Streamlit."""

    st.markdown(
        f"""
        <style>
          [data-testid="stSidebar"] {{ background: {NAVY}; }}
          [data-testid="stSidebar"] * {{ color: white; }}
          [data-testid="stMetric"] {{
            background: white;
            border: 1px solid #D9E2EC;
            border-radius: 12px;
            padding: 14px 16px;
            box-shadow: 0 2px 8px rgba(16, 42, 67, .06);
          }}
          .decision-card {{
            border-radius: 12px;
            padding: 18px;
            margin: 8px 0 16px 0;
            border-left: 6px solid {GREEN};
            background: white;
          }}
          .risk-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            font-weight: 700;
            margin-bottom: 8px;
          }}
          .academic-note {{
            color: {GRAY};
            font-size: .88rem;
            background: #E9F2FA;
            border-radius: 8px;
            padding: 10px 12px;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )
