"""Testes do fluxo de importação direta do componente."""

from __future__ import annotations

import pandas as pd

from components import (
    file_transfer,
)


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
    """Simula somente os recursos usados na confirmação."""

    def __init__(
        self,
        *,
        button_result: bool,
    ) -> None:
        self.button_result = (
            button_result
        )

        self.session_state: dict = {}

        self.info_messages: list[str] = []

    def columns(
        self,
        *args,
        **kwargs,
    ):
        return (
            DummyContext(),
            DummyContext(),
        )

    def container(
        self,
        *args,
        **kwargs,
    ):
        return DummyContext()

    def metric(
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

    def info(
        self,
        message,
        *args,
        **kwargs,
    ) -> None:
        self.info_messages.append(
            str(
                message
            )
        )

    def button(
        self,
        *args,
        **kwargs,
    ) -> bool:
        return self.button_result


def build_imported_transactions() -> pd.DataFrame:
    """Cria duas transações válidas para importação."""
    return pd.DataFrame(
        [
            {
                "data": pd.Timestamp(
                    "2026-08-01"
                ),
                "tipo": "receita",
                "descricao": "Bolsa-estágio",
                "categoria": "Trabalho",
                "valor": 1600.00,
            },
            {
                "data": pd.Timestamp(
                    "2026-08-02"
                ),
                "tipo": "despesa",
                "descricao": "Compra no mercado",
                "categoria": "Alimentação",
                "valor": 200.50,
            },
        ]
    )


def configure_component(
    monkeypatch,
    *,
    button_result: bool,
):
    """Configura uma versão mínima do Streamlit."""
    fake_streamlit = FakeStreamlit(
        button_result=button_result
    )

    monkeypatch.setattr(
        file_transfer,
        "st",
        fake_streamlit,
    )

    monkeypatch.setattr(
        file_transfer,
        "get_current_user_id",
        lambda: "user-1",
    )

    return fake_streamlit


def test_import_confirmation_saves_all_new_transactions(
    monkeypatch,
):
    fake_streamlit = (
        configure_component(
            monkeypatch,
            button_result=True,
        )
    )

    valid_transactions = (
        build_imported_transactions()
    )

    captured: dict = {}

    def fake_save(
        transactions,
        database_path,
        table_name,
        user_id,
    ):
        captured[
            "transactions"
        ] = transactions.copy()

        captured[
            "user_id"
        ] = user_id

        return len(
            transactions
        )

    monkeypatch.setattr(
        file_transfer,
        "save_imported_transactions_to_database",
        fake_save,
    )

    result = (
        file_transfer
        .render_import_confirmation(
            valid_transactions=(
                valid_transactions
            ),
            existing_transactions=(
                pd.DataFrame()
            ),
        )
    )

    assert result is True

    assert len(
        captured["transactions"]
    ) == 2

    assert (
        captured["user_id"]
        == "user-1"
    )

    assert (
        fake_streamlit.session_state[
            file_transfer.DATA_MODE_KEY
        ]
        == "user"
    )
    assert (
        fake_streamlit.session_state[
            file_transfer.IMPORT_WIDGET_VERSION_KEY
        ]
        == 1
    )

    assert (
        fake_streamlit.session_state[
            "file_import_result"
        ]
        == {
            "success": True,
            "message": (
                "Transações importadas diretamente "
                "para o banco local."
            ),
            "imported_transactions": 2,
        }
    )


def test_import_confirmation_does_nothing_before_click(
    monkeypatch,
):
    configure_component(
        monkeypatch,
        button_result=False,
    )

    save_called = False

    def fake_save(
        transactions,
        database_path,
        table_name,
        user_id,
    ):
        nonlocal save_called

        save_called = True

        return len(
            transactions
        )

    monkeypatch.setattr(
        file_transfer,
        "save_imported_transactions_to_database",
        fake_save,
    )

    result = (
        file_transfer
        .render_import_confirmation(
            valid_transactions=(
                build_imported_transactions()
            ),
            existing_transactions=(
                pd.DataFrame()
            ),
        )
    )

    assert result is False
    assert save_called is False


def test_skip_matches_imports_only_new_rows(
    monkeypatch,
):
    configure_component(
        monkeypatch,
        button_result=True,
    )

    valid_transactions = (
        build_imported_transactions()
    )

    existing_transactions = (
        valid_transactions
        .head(
            1
        )
        .copy()
    )

    captured: dict = {}

    monkeypatch.setattr(
        file_transfer,
        "render_matching_transactions",
        lambda matching: (
            file_transfer.SKIP_MATCHES
        ),
    )

    def fake_save(
        transactions,
        database_path,
        table_name,
        user_id,
    ):
        captured[
            "transactions"
        ] = transactions.copy()

        return len(
            transactions
        )

    monkeypatch.setattr(
        file_transfer,
        "save_imported_transactions_to_database",
        fake_save,
    )

    result = (
        file_transfer
        .render_import_confirmation(
            valid_transactions=(
                valid_transactions
            ),
            existing_transactions=(
                existing_transactions
            ),
        )
    )

    assert result is True

    imported = captured[
        "transactions"
    ]

    assert len(
        imported
    ) == 1

    assert (
        imported.iloc[
            0
        ]["descricao"]
        == "Compra no mercado"
    )


def test_include_matches_imports_complete_batch(
    monkeypatch,
):
    configure_component(
        monkeypatch,
        button_result=True,
    )

    valid_transactions = (
        build_imported_transactions()
    )

    existing_transactions = (
        valid_transactions
        .head(
            1
        )
        .copy()
    )

    captured: dict = {}

    monkeypatch.setattr(
        file_transfer,
        "render_matching_transactions",
        lambda matching: (
            file_transfer.INCLUDE_MATCHES
        ),
    )

    def fake_save(
        transactions,
        database_path,
        table_name,
        user_id,
    ):
        captured[
            "transactions"
        ] = transactions.copy()

        return len(
            transactions
        )

    monkeypatch.setattr(
        file_transfer,
        "save_imported_transactions_to_database",
        fake_save,
    )

    result = (
        file_transfer
        .render_import_confirmation(
            valid_transactions=(
                valid_transactions
            ),
            existing_transactions=(
                existing_transactions
            ),
        )
    )

    assert result is True

    assert len(
        captured["transactions"]
    ) == 2


def test_all_matching_rows_prevent_empty_import(
    monkeypatch,
):
    fake_streamlit = (
        configure_component(
            monkeypatch,
            button_result=True,
        )
    )

    valid_transactions = (
        build_imported_transactions()
    )

    monkeypatch.setattr(
        file_transfer,
        "render_matching_transactions",
        lambda matching: (
            file_transfer.SKIP_MATCHES
        ),
    )

    def unexpected_save(
        transactions,
        database_path,
        table_name,
        user_id,
    ):
        raise AssertionError(
            "O serviço não deveria ser chamado."
        )

    monkeypatch.setattr(
        file_transfer,
        "save_imported_transactions_to_database",
        unexpected_save,
    )

    result = (
        file_transfer
        .render_import_confirmation(
            valid_transactions=(
                valid_transactions
            ),
            existing_transactions=(
                valid_transactions.copy()
            ),
        )
    )

    assert result is False

    assert any(
        "nenhuma linha"
        in message.lower()
        for message
        in fake_streamlit.info_messages
    )

def test_matching_rows_require_explicit_strategy(
    monkeypatch,
):
    """Não importa duplicatas antes da escolha do usuário."""
    fake_streamlit = (
        configure_component(
            monkeypatch,
            button_result=True,
        )
    )

    valid_transactions = (
        build_imported_transactions()
    )

    existing_transactions = (
        valid_transactions
        .head(
            1
        )
        .copy()
    )

    save_called = False

    monkeypatch.setattr(
        file_transfer,
        "render_matching_transactions",
        lambda matching: None,
    )

    def fake_save(
        transactions,
        database_path,
        table_name,
        user_id,
    ):
        nonlocal save_called

        save_called = True

        return len(
            transactions
        )

    monkeypatch.setattr(
        file_transfer,
        "save_imported_transactions_to_database",
        fake_save,
    )

    result = (
        file_transfer
        .render_import_confirmation(
            valid_transactions=(
                valid_transactions
            ),
            existing_transactions=(
                existing_transactions
            ),
        )
    )

    assert result is False
    assert save_called is False

    assert any(
        "Escolha como tratar"
        in message
        for message
        in fake_streamlit.info_messages
    )