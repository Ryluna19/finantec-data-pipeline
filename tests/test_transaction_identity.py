"""Testes da identidade estável das transações."""

from __future__ import annotations

from uuid import UUID

import pandas as pd

from scripts.etl_transacoes import (
    read_raw_transactions,
)
from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
    create_transaction_id,
    ensure_transaction_ids,
)
from src.transaction_validation import (
    REQUIRED_TRANSACTION_COLUMNS,
)


def build_transactions() -> pd.DataFrame:
    """Cria transações válidas para os testes."""
    return pd.DataFrame(
        [
            {
                "data": "2026-07-12",
                "tipo": "receita",
                "descricao": "Mesada",
                "categoria": "Serviços",
                "valor": 900.0,
            },
            {
                "data": "2026-07-12",
                "tipo": "despesa",
                "descricao": "Conta de luz",
                "categoria": "Reserva",
                "valor": 120.0,
            },
        ]
    )


def assert_valid_uuid(
    value: str,
) -> None:
    """Confirma que um valor possui formato UUID."""
    assert str(
        UUID(value)
    ) == value


def test_create_transaction_id_returns_uuid() -> None:
    transaction_id = (
        create_transaction_id()
    )

    assert_valid_uuid(
        transaction_id
    )


def test_ensure_transaction_ids_adds_missing_ids() -> None:
    transactions = (
        build_transactions()
    )

    identified = ensure_transaction_ids(
        transactions=transactions,
        source_key="data/raw/transacoes_manuais.csv",
        identity_columns=(
            REQUIRED_TRANSACTION_COLUMNS
        ),
    )

    assert (
        TRANSACTION_ID_COLUMN
        in identified.columns
    )

    assert identified[
        TRANSACTION_ID_COLUMN
    ].nunique() == len(
        identified
    )

    for transaction_id in identified[
        TRANSACTION_ID_COLUMN
    ]:
        assert_valid_uuid(
            transaction_id
        )


def test_ensure_transaction_ids_is_stable() -> None:
    transactions = (
        build_transactions()
    )

    first_result = ensure_transaction_ids(
        transactions=transactions,
        source_key="data/raw/transacoes_manuais.csv",
        identity_columns=(
            REQUIRED_TRANSACTION_COLUMNS
        ),
    )

    second_result = ensure_transaction_ids(
        transactions=transactions,
        source_key="data/raw/transacoes_manuais.csv",
        identity_columns=(
            REQUIRED_TRANSACTION_COLUMNS
        ),
    )

    assert first_result[
        TRANSACTION_ID_COLUMN
    ].tolist() == second_result[
        TRANSACTION_ID_COLUMN
    ].tolist()


def test_identical_rows_receive_different_ids() -> None:
    transaction = (
        build_transactions()
        .iloc[[0]]
    )

    duplicated_transactions = pd.concat(
        [
            transaction,
            transaction,
        ],
        ignore_index=True,
    )

    identified = ensure_transaction_ids(
        transactions=duplicated_transactions,
        source_key="data/raw/transacoes_duplicadas.csv",
        identity_columns=(
            REQUIRED_TRANSACTION_COLUMNS
        ),
    )

    assert identified[
        TRANSACTION_ID_COLUMN
    ].nunique() == 2


def test_existing_transaction_id_is_preserved() -> None:
    transactions = (
        build_transactions()
    )

    existing_id = (
        create_transaction_id()
    )

    transactions[
        TRANSACTION_ID_COLUMN
    ] = [
        existing_id,
        "",
    ]

    identified = ensure_transaction_ids(
        transactions=transactions,
        source_key="data/raw/transacoes_manuais.csv",
        identity_columns=(
            REQUIRED_TRANSACTION_COLUMNS
        ),
    )

    assert identified.loc[
        0,
        TRANSACTION_ID_COLUMN,
    ] == existing_id

    assert_valid_uuid(
        identified.loc[
            1,
            TRANSACTION_ID_COLUMN,
        ]
    )


def test_read_raw_transactions_adds_stable_ids(
    tmp_path,
) -> None:
    source_file = (
        tmp_path
        / "transacoes_teste.csv"
    )

    build_transactions().to_csv(
        source_file,
        index=False,
        encoding="utf-8-sig",
    )

    first_read = read_raw_transactions(
        source_file
    )

    second_read = read_raw_transactions(
        source_file
    )

    assert first_read[
        TRANSACTION_ID_COLUMN
    ].tolist() == second_read[
        TRANSACTION_ID_COLUMN
    ].tolist()

    assert first_read[
        "arquivo_origem"
    ].eq(
        source_file.name
    ).all()