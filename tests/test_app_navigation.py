"""Testes da navegação principal e do posicionamento do produto."""

from __future__ import annotations

import pandas as pd

import app as app_module
import components.header as header_module


def test_main_navigation_contains_only_primary_financial_flows():
    assert app_module.MAIN_TAB_LABELS == (
        "Visão geral",
        "Transações",
        "Metas",
    )


def test_load_data_passes_received_user_context(
    monkeypatch,
) -> None:
    calls: dict[str, object] = {}

    monkeypatch.setattr(
        app_module,
        "load_user_profile",
        lambda *, user_id: (
            calls.update(
                profile_user_id=user_id
            )
            or {
                "user_id": user_id,
            }
        ),
    )

    monkeypatch.setattr(
        app_module,
        "load_transactions",
        lambda *, user_id, data_mode: (
            calls.update(
                transaction_user_id=user_id,
                data_mode=data_mode,
            )
            or pd.DataFrame()
        ),
    )

    monkeypatch.setattr(
        app_module,
        "load_rejections",
        pd.DataFrame,
    )

    profile, transactions, rejections = (
        app_module.load_data.__wrapped__(
            "user-1",
            "demo",
        )
    )

    assert calls == {
        "profile_user_id": "user-1",
        "transaction_user_id": "user-1",
        "data_mode": "demo",
    }

    assert profile == {
        "user_id": "user-1",
    }

    assert transactions.empty
    assert rejections.empty


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
