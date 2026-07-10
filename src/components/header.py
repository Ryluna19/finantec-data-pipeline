"""Componente responsável pelo cabeçalho principal do FinanTec."""

from __future__ import annotations

import streamlit as st

from ui_components import render_alert


def render_header(period: str) -> None:
    """Exibe o título, a descrição e os avisos do período analisado."""
    st.title("💰 FinanTec")

    st.caption(
        "Assistente de organização financeira para estudantes "
        "e pessoas em início de carreira."
    )

    render_alert(
        text=(
            "Projeto educativo com dados simulados. "
            "O FinanTec não oferece recomendação personalizada "
            "de investimento."
        ),
        variant="warning",
    )

    render_alert(
        text=f"Período analisado: {period}",
        variant="info",
    )