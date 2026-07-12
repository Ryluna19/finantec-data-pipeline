"""Testes da persistência dos IDs nas fontes de transação."""

from __future__ import annotations

from uuid import UUID

import pandas as pd

import src.transaction_editor as transaction_editor
from src.transaction_files import (
    create_transactions_fingerprint,
    save_imported_transactions,
)
from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
    create_transaction_id,
)


def build_transactions() -> pd.DataFrame:
    """Cria uma base pequena de transações válidas."""
    return pd.DataFrame(
        [
            {
                "data": "2026-07-12",
                "tipo": "receita",
                "descricao": "Mesada",
                "categoria": "Trabalho",
                "valor": 900.0,
            },
            {
                "data": "2026-07-12",
                "tipo": "despesa",
                "descricao": "Conta de luz",
                "categoria": "Serviços",
                "valor": 120.0,
            },
        ]
    )


def assert_valid_uuid(
    value: str,
) -> None:
    """Confirma que o valor está no formato UUID."""
    assert str(
        UUID(value)
    ) == value


def test_manual_save_persists_transaction_ids(
    tmp_path,
    monkeypatch,
) -> None:
    source_file = (
        tmp_path
        / "transacoes_manuais.csv"
    )

    monkeypatch.setattr(
        transaction_editor,
        "RAW_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        transaction_editor,
        "ARQUIVO_TRANSACOES_MANUAIS",
        source_file,
    )

    transactions = (
        build_transactions()
    )

    transaction_editor.salvar_transacoes_manuais(
        transactions
    )

    saved_transactions = pd.read_csv(
        source_file,
        encoding="utf-8-sig",
    )

    assert (
        TRANSACTION_ID_COLUMN
        in saved_transactions.columns
    )

    assert saved_transactions[
        TRANSACTION_ID_COLUMN
    ].nunique() == len(
        saved_transactions
    )

    for transaction_id in saved_transactions[
        TRANSACTION_ID_COLUMN
    ]:
        assert_valid_uuid(
            transaction_id
        )


def test_manual_save_preserves_existing_id(
    tmp_path,
    monkeypatch,
) -> None:
    source_file = (
        tmp_path
        / "transacoes_manuais.csv"
    )

    monkeypatch.setattr(
        transaction_editor,
        "RAW_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        transaction_editor,
        "ARQUIVO_TRANSACOES_MANUAIS",
        source_file,
    )

    existing_id = (
        create_transaction_id()
    )

    transactions = (
        build_transactions()
    )

    transactions[
        TRANSACTION_ID_COLUMN
    ] = [
        existing_id,
        "",
    ]

    transaction_editor.salvar_transacoes_manuais(
        transactions
    )

    saved_transactions = pd.read_csv(
        source_file,
        encoding="utf-8-sig",
    )

    assert saved_transactions.loc[
        0,
        TRANSACTION_ID_COLUMN,
    ] == existing_id


def test_imported_batch_persists_transaction_ids(
    tmp_path,
) -> None:
    saved_path = (
        save_imported_transactions(
            build_transactions(),
            import_dir=tmp_path,
        )
    )

    saved_transactions = pd.read_csv(
        saved_path,
        encoding="utf-8-sig",
    )

    assert list(
        saved_transactions.columns
    ) == [
        TRANSACTION_ID_COLUMN,
        "data",
        "tipo",
        "descricao",
        "categoria",
        "valor",
    ]

    assert saved_transactions[
        TRANSACTION_ID_COLUMN
    ].nunique() == len(
        saved_transactions
    )


def test_fingerprint_ignores_transaction_ids() -> None:
    first_transactions = (
        build_transactions()
    )

    second_transactions = (
        build_transactions()
    )

    first_transactions[
        TRANSACTION_ID_COLUMN
    ] = [
        create_transaction_id(),
        create_transaction_id(),
    ]

    second_transactions[
        TRANSACTION_ID_COLUMN
    ] = [
        create_transaction_id(),
        create_transaction_id(),
    ]

    assert (
        create_transactions_fingerprint(
            first_transactions
        )
        == create_transactions_fingerprint(
            second_transactions
        )
    )