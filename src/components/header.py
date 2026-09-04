"""Componentes responsáveis pelos cabeçalhos do FinanTec."""

from __future__ import annotations

from base64 import b64encode
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st

from components.appearance import (
    render_appearance_controls,
)
from ui_components import render_html


BRAND_MARK_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "assets"
    / "branding"
    / "finantec-header-mark.svg"
)


@lru_cache(maxsize=1)
def load_brand_mark_data_uri() -> str:
    """Carrega a marca vetorial como uma data URI."""
    try:
        encoded_mark = b64encode(
            BRAND_MARK_PATH.read_bytes()
        ).decode(
            "ascii"
        )
    except OSError as error:
        raise RuntimeError(
            "Não foi possível carregar a marca "
            f"do FinanTec em {BRAND_MARK_PATH}."
        ) from error

    return (
        "data:image/svg+xml;base64,"
        f"{encoded_mark}"
    )

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
    brand_mark_src = escape(
        load_brand_mark_data_uri(),
        quote=True,
    )

    return f"""
        <header class="finantec-brand-header">
            <div class="finantec-brand-title-row">
                <span
                    class="finantec-brand-icon"
                    aria-hidden="true"
                >
                    <img
                        class="finantec-brand-mark"
                        src="{brand_mark_src}"
                        alt=""
                    />
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
                Aplicativo de organização financeira pessoal para estudantes
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