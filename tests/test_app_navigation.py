"""Testes da navegação principal e do posicionamento do produto."""

from __future__ import annotations

import app as app_module
import components.header as header_module


def test_main_navigation_contains_only_primary_financial_flows():
    assert app_module.MAIN_TAB_LABELS == (
        "Visão geral",
        "Transações",
        "Metas",
    )


def test_header_presents_finantec_as_local_application(
    monkeypatch,
) -> None:
    rendered_html: list[str] = []
    rendered_alerts: list[tuple[str, str]] = []

    monkeypatch.setattr(
        header_module,
        "render_html",
        rendered_html.append,
    )

    monkeypatch.setattr(
        header_module,
        "render_alert",
        lambda *, text, variant: rendered_alerts.append(
            (
                text,
                variant,
            )
        ),
    )

    header_module.render_header(
        period="Julho/2026",
    )

    assert "Aplicativo local de organização financeira" in rendered_html[0]
    assert "Assistente de organização financeira" not in rendered_html[0]

    assert rendered_alerts == [
        (
            "Projeto educativo de uso local. "
            "O FinanTec não oferece recomendação personalizada "
            "de investimento.",
            "warning",
        ),
        (
            "Período analisado: Julho/2026",
            "info",
        ),
    ]
