"""Componentes responsáveis pelos cabeçalhos do FinanTec."""

from __future__ import annotations

from html import escape

import streamlit as st

from components.appearance import (
    render_appearance_controls,
)
from ui_components import render_html


def _normalize_heading_text(
    value: object,
) -> str:
    """Normaliza textos usados nos cabeçalhos visuais."""
    return " ".join(
        str(
            value
            if value is not None
            else ""
        )
        .strip()
        .split()
    )


def build_page_header_html(
    *,
    title: str,
    description: str,
) -> str:
    """Monta o cabeçalho padronizado de uma página interna."""
    normalized_title = _normalize_heading_text(
        title
    )

    normalized_description = (
        _normalize_heading_text(
            description
        )
    )

    if not normalized_title:
        raise ValueError(
            "O título da página não pode ficar vazio."
        )

    description_html = (
        (
            '<p class="finantec-page-header-description">'
            f"{escape(normalized_description)}"
            "</p>"
        )
        if normalized_description
        else ""
    )

    return (
        '<section class="finantec-page-header">'
        '<div class="finantec-page-header-copy">'
        f"<h2>{escape(normalized_title)}</h2>"
        f"{description_html}"
        "</div>"
        "</section>"
    )


def build_section_header_html(
    *,
    title: str,
    description: str | None = None,
    compact: bool = False,
) -> str:
    """Monta um título local sem âncora automática do Markdown."""
    normalized_title = _normalize_heading_text(
        title
    )

    normalized_description = (
        _normalize_heading_text(
            description
        )
    )

    if not normalized_title:
        raise ValueError(
            "O título da seção não pode ficar vazio."
        )

    class_name = (
        "finantec-section-header compact"
        if compact
        else "finantec-section-header"
    )

    description_html = (
        (
            '<p class="finantec-section-header-description">'
            f"{escape(normalized_description)}"
            "</p>"
        )
        if normalized_description
        else ""
    )

    return (
        f'<div class="{class_name}">'
        f"<h3>{escape(normalized_title)}</h3>"
        f"{description_html}"
        "</div>"
    )


def build_brand_header_html() -> str:
    """Monta a identidade exibida no cabeçalho global."""
    return """
        <header class="finantec-brand-header">
            <div class="finantec-brand-title-row">
                <span
                    class="finantec-brand-icon"
                    aria-hidden="true"
                >
                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        <path
                            d="M4 7.5H18C19.1 7.5 20 8.4 20 9.5V17.5C20 18.6 19.1 19.5 18 19.5H5C3.9 19.5 3 18.6 3 17.5V6.5C3 5.4 3.9 4.5 5 4.5H16"
                        />

                        <path
                            d="M3 8H18"
                        />

                        <path
                            d="M15.5 12H20V16H15.5C14.4 16 13.5 15.1 13.5 14C13.5 12.9 14.4 12 15.5 12Z"
                        />

                        <circle
                            cx="16.5"
                            cy="14"
                            r="0.5"
                            fill="currentColor"
                            stroke="none"
                        />
                    </svg>
                </span>

                <div class="finantec-brand-copy">
                    <div class="finantec-brand-eyebrow">
                        Organização financeira
                    </div>

                    <h1>
                        FinanTec
                    </h1>
                </div>
            </div>

            <p class="finantec-brand-description">
                Aplicativo local de organização financeira para estudantes
                e pessoas em início de carreira.
            </p>
        </header>
    """


def render_header(
    _period: str | None = None,
) -> None:
    """Exibe identidade e aparência na mesma superfície global."""
    with st.container(
        border=False,
        key="finantec-global-header-shell",
    ):
        brand_column, appearance_column = st.columns(
            [4.5, 1],
            gap="small",
        )

        with brand_column:
            render_html(
                build_brand_header_html()
            )

        with appearance_column:
            with st.container(
                key="finantec-global-header-actions",
            ):
                render_appearance_controls(
                    compact=True
                )