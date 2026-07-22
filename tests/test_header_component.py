"""Testes dos cabeçalhos visuais do FinanTec."""

from __future__ import annotations

from contextlib import nullcontext

import pytest

import components.header as header_module
from components.header import (
    build_brand_header_html,
    build_page_header_html,
    build_section_header_html,
)


class FakeStreamlit:
    """Simula apenas a estrutura usada pelo cabeçalho global."""

    def __init__(self) -> None:
        self.container_calls: list[dict[str, object]] = []
        self.columns_calls: list[tuple[list[float], str]] = []

    def container(
        self,
        *,
        border: bool | None = None,
        key: str | None = None,
    ):
        self.container_calls.append(
            {
                "border": border,
                "key": key,
            }
        )

        return nullcontext()

    def columns(
        self,
        spec: list[float],
        *,
        gap: str,
    ):
        self.columns_calls.append(
            (
                spec,
                gap,
            )
        )

        return (
            nullcontext(),
            nullcontext(),
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


def test_build_brand_header_html_contains_product_identity():
    html = build_brand_header_html()

    assert (
        'class="finantec-brand-header"'
        in html
    )
    assert "Organização financeira" in html
    assert "FinanTec" in html
    assert "finantec-brand-description" in html


def test_render_header_groups_brand_and_appearance(
    monkeypatch,
) -> None:
    fake_streamlit = FakeStreamlit()
    rendered_html: list[str] = []
    appearance_calls: list[bool] = []

    monkeypatch.setattr(
        header_module,
        "st",
        fake_streamlit,
    )
    monkeypatch.setattr(
        header_module,
        "render_html",
        rendered_html.append,
    )
    monkeypatch.setattr(
        header_module,
        "render_appearance_controls",
        lambda *, compact: (
            appearance_calls.append(compact)
        ),
    )

    header_module.render_header()

    assert fake_streamlit.container_calls == [
        {
            "border": False,
            "key": "finantec-global-header-shell",
        },
        {
            "border": None,
            "key": "finantec-global-header-actions",
        },
    ]
    assert fake_streamlit.columns_calls == [
        (
            [4.5, 1],
            "small",
        )
    ]
    assert len(rendered_html) == 1
    assert appearance_calls == [True]


def test_page_header_rejects_empty_title():
    with pytest.raises(
        ValueError,
        match="não pode ficar vazio",
    ):
        build_page_header_html(
            title="   ",
            description="Descrição",
        )