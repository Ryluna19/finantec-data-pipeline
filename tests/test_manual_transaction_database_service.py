"""Testes da persistência direta de transações manuais."""

from __future__ import annotations

import pandas as pd
import pytest

from src.manual_transaction_database_service import (
    MANUAL_DATABASE_SOURCE,
    prepare_manual_transactions_for_database,
    save_manual_transactions_to_database,
)
from src.transaction_repository import (
    load_transactions,
)


TABLE_NAME = (
    "transacoes_processadas"
)

MANUAL_TRANSACTION_ID_1 = (
    "11111111-1111-4111-8111-111111111111"
)

MANUAL_TRANSACTION_ID_2 = (
    "22222222-2222-4222-8222-222222222222"
)


def build_manual_transactions(
    *,
    include_ids: bool = True,
) -> pd.DataFrame:
    """Cria um rascunho manual válido."""
    transactions = pd.DataFrame(
        [
            {
                "data": "2026-07-10",
                "tipo": "despesa",
                "descricao": "Mercado",
                "categoria": "Alimentação",
                "valor": 100.0,
            },
            {
                "data": "2026-07-15",
                "tipo": "receita",
                "descricao": "Freelance",
                "categoria": "Trabalho",
                "valor": 500.0,
            },
        ]
    )

    if include_ids:
        transactions.insert(
            0,
            "transaction_id",
            [
            MANUAL_TRANSACTION_ID_1,
            MANUAL_TRANSACTION_ID_2,
        ],
        )

    return transactions


def test_prepare_manual_transactions_creates_database_contract():
    result = (
        prepare_manual_transactions_for_database(
            build_manual_transactions()
        )
    )

    assert result.columns.tolist() == [
        "transaction_id",
        "data",
        "tipo",
        "descricao",
        "categoria",
        "valor",
        "arquivo_origem",
        "ano_mes",
    ]

    assert result[
        "transaction_id"
    ].tolist() == [
        MANUAL_TRANSACTION_ID_1,
        MANUAL_TRANSACTION_ID_2,
    ]

    assert result[
        "arquivo_origem"
    ].unique().tolist() == [
        MANUAL_DATABASE_SOURCE,
    ]

    assert result[
        "ano_mes"
    ].tolist() == [
        "2026-07",
        "2026-07",
    ]

    assert result[
        "data"
    ].tolist() == [
        "2026-07-10",
        "2026-07-15",
    ]


def test_prepare_manual_transactions_generates_missing_ids():
    result = (
        prepare_manual_transactions_for_database(
            build_manual_transactions(
                include_ids=False,
            )
        )
    )

    transaction_ids = (
        result[
            "transaction_id"
        ]
        .astype(str)
        .str.strip()
    )

    assert transaction_ids.ne(
        ""
    ).all()

    assert transaction_ids.is_unique


def test_save_manual_transactions_inserts_directly(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    result = (
        save_manual_transactions_to_database(
            transactions=(
                build_manual_transactions()
            ),
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
        )
    )

    loaded = load_transactions(
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    assert result == {
        "inserted": 2,
        "updated": 0,
        "total": 2,
    }

    assert len(
        loaded
    ) == 2

    assert set(
        loaded["descricao"]
    ) == {
        "Mercado",
        "Freelance",
    }

    assert set(
        loaded["arquivo_origem"]
    ) == {
        MANUAL_DATABASE_SOURCE,
    }

    assert set(
        loaded["user_id"]
    ) == {
        "user-1",
    }

    assert set(
        loaded["data_mode"]
    ) == {
        "user",
    }


def test_save_manual_transactions_updates_existing_ids(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    transactions = (
        build_manual_transactions()
    )

    save_manual_transactions_to_database(
        transactions=transactions,
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
    )

    transactions.loc[
        transactions[
            "transaction_id"
        ]
        == MANUAL_TRANSACTION_ID_1,
        "descricao",
    ] = "Supermercado"

    transactions.loc[
        transactions[
            "transaction_id"
        ]
        == MANUAL_TRANSACTION_ID_1,
        "valor",
    ] = 250.0

    result = (
        save_manual_transactions_to_database(
            transactions=transactions,
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
        )
    )

    loaded = load_transactions(
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    mercado = (
        loaded.loc[
            loaded[
                "transaction_id"
            ]
            == MANUAL_TRANSACTION_ID_1
        ]
        .iloc[0]
    )

    assert result == {
        "inserted": 0,
        "updated": 2,
        "total": 2,
    }

    assert len(
        loaded
    ) == 2

    assert (
        mercado["descricao"]
        == "Supermercado"
    )

    assert (
        mercado["valor"]
        == 250.0
    )


def test_manual_transactions_are_isolated_by_user(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    transactions = (
        build_manual_transactions()
    )

    save_manual_transactions_to_database(
        transactions=transactions,
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
    )

    save_manual_transactions_to_database(
        transactions=transactions,
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-2",
    )

    first_user = load_transactions(
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    second_user = load_transactions(
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-2",
        data_mode="user",
    )

    assert len(
        first_user
    ) == 2

    assert len(
        second_user
    ) == 2

    assert set(
        first_user["user_id"]
    ) == {
        "user-1",
    }

    assert set(
        second_user["user_id"]
    ) == {
        "user-2",
    }


def test_invalid_manual_transaction_is_not_saved(
    tmp_path,
):
    transactions = (
        build_manual_transactions()
    )

    transactions.loc[
        0,
        "valor",
    ] = -10.0

    database_path = (
        tmp_path
        / "finantec.db"
    )

    with pytest.raises(
        ValueError,
        match=(
            "valor menor ou igual a zero"
        ),
    ):
        save_manual_transactions_to_database(
            transactions=transactions,
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
        )

    assert not database_path.exists()