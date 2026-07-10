"""Utilitários visuais compartilhados do FinanTec."""

from __future__ import annotations

from html import escape
from pathlib import Path
from textwrap import dedent

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STYLES_FILE = PROJECT_ROOT / "assets" / "styles.css"

INCOME_COLOR = "#22c55e"
EXPENSE_COLOR = "#ff7a00"

MONTH_NAMES_PT_BR = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

TRANSACTION_TYPE_LABELS = {
    "receita": "Receita",
    "despesa": "Despesa",
}

ALERT_VARIANTS = {
    "info",
    "warning",
    "success",
    "error",
}


def apply_visual_styles() -> None:
    """Carrega o arquivo CSS principal da aplicação."""
    if not STYLES_FILE.exists():
        st.warning(
            f"Arquivo de estilos não encontrado: {STYLES_FILE}"
        )
        return

    styles = STYLES_FILE.read_text(encoding="utf-8")

    st.markdown(
        f"<style>{styles}</style>",
        unsafe_allow_html=True,
    )


def render_html(content: str) -> None:
    """Renderiza HTML sem permitir que o Markdown altere sua estrutura."""
    compact_html = " ".join(
        line.strip()
        for line in dedent(content).splitlines()
        if line.strip()
    )

    st.markdown(
        compact_html,
        unsafe_allow_html=True,
    )


def render_alert(
    text: str,
    variant: str = "info",
) -> None:
    """Exibe uma mensagem usando o estilo visual do FinanTec."""
    safe_variant = (
        variant
        if variant in ALERT_VARIANTS
        else "info"
    )

    render_html(
        f"""
        <div class="finantec-alert {escape(safe_variant)}">
            {escape(text)}
        </div>
        """
    )