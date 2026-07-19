"""Testes da composição da aba de transações."""

from __future__ import annotations

import pandas as pd
import pytest

import app as app_module


class DummyContext:
    """Simula containers e colunas do Streamlit."""

    def __enter__(self):
        return self

    def __exit__(
        self,
        exception_type,
        exception_value,
        traceback,
    ) -> bool:
        return False


class FakeStreamlit:
    """Simula somente os controles da composição testada."""

    def __init__(
        self,
        *,
        clicked_label: str | None = None,
    ) -> None:
        self.clicked_label = clicked_label
        self.session_state: dict = {}
        self.button_labels: list[str] = []
        self.rerun_requested = False

    def subheader(
        self,
        *args,
        **kwargs,
    ) -> None:
        return None

    def caption(
        self,
        *args,
        **kwargs,
    ) -> None:
        return None

    def markdown(
        self,
        *args,
        **kwargs,
    ) -> None:
        return None

    def columns(
        self,
        count,
        *args,
        **kwargs,
    ):
        return tuple(
            DummyContext()
            for _ in range(
                int(
                    count
                )
            )
        )

    def button(
        self,
        label,
        *args,
        on_click=None,
        **kwargs,
    ) -> bool:
        self.button_labels.append(
            str(
                label
            )
        )

        clicked = (
            label == self.clicked_label
        )

        if clicked and on_click:
            on_click(
                *kwargs.get(
                    "args",
                    (),
                )
            )

        return clicked

    def container(
        self,
        *args,
        **kwargs,
    ) -> DummyContext:
        return DummyContext()

    def rerun(self) -> None:
        self.rerun_requested = True


def build_transactions() -> pd.DataFrame:
    """Cria dados suficientes para distinguir período e base completa."""
    return pd.DataFrame(
        [
            {
                "transaction_id": "transaction-1",
                "data": pd.Timestamp(
                    "2026-07-01"
                ),
                "tipo": "despesa",
                "descricao": "Mercado",
                "categoria": "Alimentação",
                "valor": 100.00,
            },
            {
                "transaction_id": "transaction-2",
                "data": pd.Timestamp(
                    "2026-06-01"
                ),
                "tipo": "receita",
                "descricao": "Bolsa",
                "categoria": "Trabalho",
                "valor": 1200.00,
            },
        ]
    )


def configure_composition(
    monkeypatch,
    *,
    import_result: bool = False,
) -> tuple[
    FakeStreamlit,
    list[str],
    pd.DataFrame,
]:
    """Substitui os renderizadores por registros de chamadas."""
    fake_streamlit = FakeStreamlit()
    events: list[str] = []

    period_transactions = (
        build_transactions()
        .head(
            1
        )
        .copy()
    )

    visible_transactions = (
        period_transactions.copy()
    )

    monkeypatch.setattr(
        app_module,
        "st",
        fake_streamlit,
    )

    monkeypatch.setattr(
        app_module,
        "render_period_selector",
        lambda transactions, *, key_prefix: (
            events.append(
                "period"
            )
            or (
                7,
                "Julho/2026",
                period_transactions,
            )
        ),
    )

    monkeypatch.setattr(
        app_module,
        "render_manual_transaction_editor",
        lambda: events.append(
            "new"
        ),
    )

    monkeypatch.setattr(
        app_module,
        "render_transaction_import",
        lambda transactions: (
            events.append(
                "import"
            )
            or import_result
        ),
    )

    monkeypatch.setattr(
        app_module,
        "render_transaction_downloads",
        lambda transactions: events.append(
            "export"
        ),
    )

    monkeypatch.setattr(
        app_module,
        "render_period_transactions",
        lambda transactions: (
            events.append(
                "query"
            )
            or visible_transactions
        ),
    )

    monkeypatch.setattr(
        app_module,
        "render_persisted_transaction_management",
        lambda transactions: events.append(
            "management"
        ),
    )

    monkeypatch.setattr(
        app_module,
        "render_data_validation",
        lambda valid_count, rejections: (
            events.append(
                "validation"
            )
        ),
    )

    return (
        fake_streamlit,
        events,
        period_transactions,
    )


def test_transaction_action_toggle_is_exclusive_and_closes(
    monkeypatch,
) -> None:
    fake_streamlit = FakeStreamlit()

    monkeypatch.setattr(
        app_module,
        "st",
        fake_streamlit,
    )

    app_module._toggle_transaction_action(
        app_module.TRANSACTION_ACTION_NEW
    )

    assert fake_streamlit.session_state[
        app_module.TRANSACTION_ACTION_KEY
    ] == app_module.TRANSACTION_ACTION_NEW

    app_module._toggle_transaction_action(
        app_module.TRANSACTION_ACTION_IMPORT
    )

    assert fake_streamlit.session_state[
        app_module.TRANSACTION_ACTION_KEY
    ] == app_module.TRANSACTION_ACTION_IMPORT

    app_module._toggle_transaction_action(
        app_module.TRANSACTION_ACTION_IMPORT
    )

    assert fake_streamlit.session_state[
        app_module.TRANSACTION_ACTION_KEY
    ] is None


def test_transactions_tab_starts_closed_and_queries_first(
    monkeypatch,
) -> None:
    (
        fake_streamlit,
        events,
        _,
    ) = configure_composition(
        monkeypatch
    )

    app_module.render_transactions_tab(
        all_transactions=build_transactions(),
        rejections=pd.DataFrame(),
    )

    assert fake_streamlit.button_labels == [
        "Nova transação",
        "Importar",
        "Exportar",
    ]

    assert events == [
        "period",
        "query",
        "management",
        "validation",
    ]


@pytest.mark.parametrize(
    ("active_action", "expected_event"),
    [
        (
            app_module.TRANSACTION_ACTION_NEW,
            "new",
        ),
        (
            app_module.TRANSACTION_ACTION_IMPORT,
            "import",
        ),
        (
            app_module.TRANSACTION_ACTION_EXPORT,
            "export",
        ),
    ],
)
def test_transactions_tab_renders_only_active_action(
    monkeypatch,
    active_action,
    expected_event,
) -> None:
    (
        fake_streamlit,
        events,
        _,
    ) = configure_composition(
        monkeypatch
    )

    fake_streamlit.session_state[
        app_module.TRANSACTION_ACTION_KEY
    ] = active_action

    app_module.render_transactions_tab(
        all_transactions=build_transactions(),
        rejections=pd.DataFrame(),
    )

    action_events = [
        event
        for event in events
        if event in {
            "new",
            "import",
            "export",
        }
    ]

    assert action_events == [
        expected_event
    ]

    assert events[0] == "period"

    assert events[-3:] == [
        "query",
        "management",
        "validation",
    ]


def test_pending_feedback_restores_matching_action(
    monkeypatch,
) -> None:
    fake_streamlit = FakeStreamlit()

    monkeypatch.setattr(
        app_module,
        "st",
        fake_streamlit,
    )

    fake_streamlit.session_state[
        "resultado_etl"
    ] = {
        "sucesso": True,
    }

    assert (
        app_module
        ._get_active_transaction_action()
        == app_module.TRANSACTION_ACTION_NEW
    )

    fake_streamlit.session_state.pop(
        "resultado_etl"
    )

    fake_streamlit.session_state[
        "file_import_result"
    ] = {
        "success": True,
    }

    assert (
        app_module
        ._get_active_transaction_action()
        == app_module.TRANSACTION_ACTION_IMPORT
    )


def test_action_panels_receive_correct_transaction_scopes(
    monkeypatch,
) -> None:
    fake_streamlit = FakeStreamlit()
    captured: dict[str, pd.DataFrame] = {}

    monkeypatch.setattr(
        app_module,
        "st",
        fake_streamlit,
    )

    monkeypatch.setattr(
        app_module,
        "render_transaction_import",
        lambda transactions: (
            captured.update(
                import_data=(
                    transactions.copy()
                )
            )
            or False
        ),
    )

    monkeypatch.setattr(
        app_module,
        "render_transaction_downloads",
        lambda transactions: (
            captured.update(
                download_data=(
                    transactions.copy()
                )
            )
        ),
    )

    all_transactions = build_transactions()
    period_transactions = (
        all_transactions
        .head(
            1
        )
        .copy()
    )

    app_module._render_transaction_action_panel(
        active_action=(
            app_module.TRANSACTION_ACTION_IMPORT
        ),
        period_transactions=period_transactions,
        all_transactions=all_transactions,
    )

    app_module._render_transaction_action_panel(
        active_action=(
            app_module.TRANSACTION_ACTION_EXPORT
        ),
        period_transactions=period_transactions,
        all_transactions=all_transactions,
    )

    assert captured[
        "import_data"
    ].equals(
        all_transactions
    )

    assert captured[
        "download_data"
    ].equals(
        period_transactions
    )


def test_completed_import_refreshes_data_before_query(
    monkeypatch,
) -> None:
    (
        fake_streamlit,
        events,
        _,
    ) = configure_composition(
        monkeypatch,
        import_result=True,
    )

    fake_streamlit.session_state[
        app_module.TRANSACTION_ACTION_KEY
    ] = app_module.TRANSACTION_ACTION_IMPORT

    cache_events: list[str] = []

    monkeypatch.setattr(
        app_module.load_data,
        "clear",
        lambda: cache_events.append(
            "clear"
        ),
    )

    app_module.render_transactions_tab(
        all_transactions=build_transactions(),
        rejections=pd.DataFrame(),
    )

    assert events == [
        "period",
        "import",
    ]

    assert cache_events == [
        "clear"
    ]

    assert fake_streamlit.rerun_requested is True