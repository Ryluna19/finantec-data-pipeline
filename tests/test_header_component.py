"""Testes dos cabeçalhos visuais do FinanTec."""

from __future__ import annotations

import pytest

from components.header import (
    build_page_header_html,
    build_section_header_html,
)


def test_build_page_header_html_normalizes_and_escapes_content():
    html = build_page_header_html(
        title="  Visão   <geral>  ",
        description=(
            "  Resumo financeiro  & período  "
        ),
    )

    assert (
        '<section class="finantec-page-header">'
        in html
    )

    assert "Visão &lt;geral&gt;" in html
    assert "Resumo financeiro &amp; período" in html
    assert "  " not in html


def test_build_section_header_html_supports_compact_variant():
    html = build_section_header_html(
        title="Período analisado",
        compact=True,
    )

    assert (
        'class="finantec-section-header compact"'
        in html
    )

    assert "<h3>Período analisado</h3>" in html


def test_page_header_rejects_empty_title():
    with pytest.raises(
        ValueError,
        match="não pode ficar vazio",
    ):
        build_page_header_html(
            title="   ",
            description="Descrição",
        )