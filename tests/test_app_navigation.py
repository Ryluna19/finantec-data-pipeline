"""Testes da navegação principal e do posicionamento do produto."""

from __future__ import annotations

import pandas as pd

import app as app_module
import components.header as header_module


class TabContext:
    """Simula uma aba do Streamlit."""

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exception_type,
        exception_value,
        traceback,
    ) -> bool:
        return False


class MainStreamlit:
    """Oferece o estado mínimo usado pela composição principal."""

    def __init__(
        self,
    ) -> None:
        self.session_state: dict = {}

    def tabs(
        self,
        labels,
    ):
        return tuple(
            TabContext()
            for _ in labels
        )


def test_main_navigation_contains_only_primary_financial_flows():
    assert app_module.MAIN_TAB_LABELS == (
        "Visão geral",
        "Transações",
        "Orçamento",
        "Metas",
    )


def test_load_data_passes_received_user_context(
    monkeypatch,
) -> None:
    calls: dict[str, object] = {}
    profile_calls: list[
        tuple[str, str]
    ] = []

    monkeypatch.setattr(
        app_module,
        "load_user_profile",
        lambda *, user_id, data_mode: (
            profile_calls.append(
                (
                    user_id,
                    data_mode,
                )
            )
            or {
                "user_id": user_id,
                "data_mode": data_mode,
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

    (
        personal_profile,
        active_profile,
        transactions,
        rejections,
    ) = (
        app_module.load_data.__wrapped__(
            "user-1",
            "demo",
        )
    )

    assert calls == {
        "transaction_user_id": "user-1",
        "data_mode": "demo",
    }

    assert profile_calls == [
        (
            "user-1",
            "demo",
        ),
        (
            "user-1",
            "user",
        ),
    ]

    assert personal_profile == {
        "user_id": "user-1",
        "data_mode": "user",
    }

    assert active_profile == {
        "user_id": "user-1",
        "data_mode": "demo",
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


def test_main_flows_render_without_configured_profile(
    monkeypatch,
) -> None:
    fake_streamlit = MainStreamlit()
    events: list[str] = []
    empty_transactions = pd.DataFrame()

    monkeypatch.setattr(
        app_module,
        "st",
        fake_streamlit,
    )
    monkeypatch.setattr(
        app_module,
        "apply_visual_styles",
        lambda: None,
    )
    monkeypatch.setattr(
    app_module,
    "render_authentication_gate",
    lambda: {
        "user_id": "user-1",
        "username": "Ryan",
    },
    )

    monkeypatch.setattr(
        app_module,
        "render_account_sidebar",
        lambda account: None,
    )
    monkeypatch.setattr(
        app_module,
        "get_current_user_id",
        lambda: "user-1",
    )
    monkeypatch.setattr(
        app_module,
        "load_data",
        lambda user_id, data_mode: (
            {
                "user_id": user_id,
                "objetivos_financeiros": [],
            },
            {
                "user_id": user_id,
                "objetivos_financeiros": [],
            },
            empty_transactions,
            pd.DataFrame(),
        ),
    )
    monkeypatch.setattr(
        app_module,
        "render_user_navigation",
        lambda profile, data_mode: "main",
    )
    monkeypatch.setattr(
        app_module,
        "render_monthly_budget",
        lambda **kwargs: events.append(
            "budget"
        ),
    )
    monkeypatch.setattr(
        app_module,
        "select_period",
        lambda transactions: (
            0,
            "Sem dados",
            transactions,
        ),
    )
    monkeypatch.setattr(
        app_module,
        "render_header",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        app_module,
        "render_empty_dashboard",
        lambda: events.append(
            "dashboard"
        ),
    )
    monkeypatch.setattr(
        app_module,
        "render_transactions_tab",
        lambda **kwargs: events.append(
            "transactions"
        ),
    )
    monkeypatch.setattr(
        app_module,
        "render_goal_simulator",
        lambda **kwargs: events.append(
            "goals"
        ),
    )

    app_module.main()

    assert events == [
        "dashboard",
        "transactions",
        "budget",
        "goals",
    ]
    
def test_main_stops_when_user_is_not_authenticated(
    monkeypatch,
) -> None:
    fake_streamlit = (
        MainStreamlit()
    )

    monkeypatch.setattr(
        app_module,
        "st",
        fake_streamlit,
    )

    monkeypatch.setattr(
        app_module,
        "apply_visual_styles",
        lambda: None,
    )

    monkeypatch.setattr(
        app_module,
        "render_authentication_gate",
        lambda: None,
    )

    def fail_if_data_is_loaded(
        *args,
        **kwargs,
    ):
        raise AssertionError(
            "Os dados não devem ser carregados "
            "sem autenticação."
        )

    monkeypatch.setattr(
        app_module,
        "load_data",
        fail_if_data_is_loaded,
    )

    app_module.main()