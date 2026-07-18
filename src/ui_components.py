"""Utilitários visuais compartilhados do FinanTec."""

from __future__ import annotations

from html import escape
from pathlib import Path
from textwrap import dedent

import streamlit as st

from components.appearance import (
    build_visual_marker_classes,
    get_visual_preferences,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STYLES_DIR = (
    PROJECT_ROOT
    / "assets"
    / "styles"
)

STYLE_FILES = (
    STYLES_DIR / "tokens.css",
    STYLES_DIR / "base.css",
    STYLES_DIR / "components.css",
    STYLES_DIR / "responsive.css",
    STYLES_DIR / "transaction-drafts.css",
    STYLES_DIR / "auth.css",
    STYLES_DIR / "themes.css",
)

INCOME_COLOR = "#22c55e"
EXPENSE_COLOR = "#ef4444"

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


def load_visual_styles() -> str:
    """Carrega os estilos na ordem definida pela aplicação."""
    missing_files = [
        style_file
        for style_file in STYLE_FILES
        if not style_file.exists()
    ]

    if missing_files:
        missing_names = ", ".join(
            str(
                file_path.relative_to(
                    PROJECT_ROOT
                )
            )
            for file_path in missing_files
        )

        raise FileNotFoundError(
            "Arquivos de estilo não encontrados: "
            f"{missing_names}"
        )

    style_parts = [
        style_file.read_text(
            encoding="utf-8"
        ).rstrip()
        for style_file in STYLE_FILES
    ]

    return "\n\n".join(
        style_parts
    )


def apply_visual_styles() -> None:
    """Carrega o CSS e aplica as preferências visuais."""
    try:
        styles = load_visual_styles()

    except (
        FileNotFoundError,
        OSError,
    ) as error:
        st.warning(
            str(error)
        )
        return

    appearance, accent_palette = (
        get_visual_preferences()
    )

    marker_classes = (
        build_visual_marker_classes(
            appearance,
            accent_palette,
        )
    )

    st.markdown(
        f"<style>{styles}</style>",
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            f'<div class="{marker_classes}" '
            'aria-hidden="true"></div>'
        ),
        unsafe_allow_html=True,
    )


def render_html(
    content: str,
) -> None:
    """Renderiza HTML sem o Markdown alterar sua estrutura."""
    compact_html = " ".join(
        line.strip()
        for line in dedent(
            content
        ).splitlines()
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
    """Exibe uma mensagem usando o estilo do FinanTec."""
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