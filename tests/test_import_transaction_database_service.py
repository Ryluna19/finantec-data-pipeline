"""Testes da persistência direta de importações no SQLite."""

from __future__ import annotations

from uuid import UUID

import pandas as pd
import pytest

from src.import_transaction_database_service import (
    IMPORT_DATABASE_SOURCE,
    prepare_imported_transactions_for_database,
    save_imported_transactions_to_database,
)
from src.transaction_repository import (
    load_transactions,
)


TABLE_NAME = (
    "transacoes_processadas"
)


def build_imported_transactions() -> pd.DataFrame:
    """Cria um lote importado válido."""
    return pd.DataFrame(
        [
            {
                "data": "2026-08-01",
                "tipo": " RECEITA ",
                "descricao": " Bolsa-estágio ",
                "categoria": " Trabalho ",
                "valor": "1600.00",
            },
            {
                "data": "2026-08-02",
                "tipo": " DESPESA ",
                "descricao": " Compra no mercado ",
                "categoria": " Alimentação ",
                "valor": "200.50",
            },
        ]
    )


def is_valid_uuid(value: object) -> bool:
    """Verifica se um valor representa um UUID válido."""
    try:
        parsed_value = UUID(
            str(
                value
            )
        )

    except (
        TypeError,
        ValueError,
        AttributeError,
    ):
        return False

    return str(
        parsed_value
    ) == str(
        value
    )


def test_prepare_imported_transactions_creates_database_contract():
    result = (
        prepare_imported_transactions_for_database(
            build_imported_transactions()
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

    assert len(
        result
    ) == 2

    assert result[
        "transaction_id"
    ].map(
        is_valid_uuid
    ).all()

    assert result[
        "transaction_id"
    ].is_unique

    assert result[
        "data"
    ].tolist() == [
        "2026-08-01",
        "2026-08-02",
    ]

    assert result[
        "tipo"
    ].tolist() == [
        "receita",
        "despesa",
    ]

    assert result[
        "descricao"
    ].tolist() == [
        "Bolsa-estágio",
        "Compra no mercado",
    ]

    assert result[
        "categoria"
    ].tolist() == [
        "Trabalho",
        "Alimentação",
    ]

    assert result[
        "valor"
    ].tolist() == [
        1600.00,
        200.50,
    ]

    assert result[
        "arquivo_origem"
    ].unique().tolist() == [
        IMPORT_DATABASE_SOURCE,
    ]

    assert result[
        "ano_mes"
    ].tolist() == [
        "2026-08",
        "2026-08",
    ]


def test_identical_imported_rows_receive_different_ids():
    transaction = (
        build_imported_transactions()
        .head(
            1
        )
    )

    duplicated_batch = pd.concat(
        [
            transaction,
            transaction,
        ],
        ignore_index=True,
    )

    result = (
        prepare_imported_transactions_for_database(
            duplicated_batch
        )
    )

    assert len(
        result
    ) == 2

    assert result[
        "transaction_id"
    ].is_unique


def test_save_imported_transactions_inserts_directly(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    inserted_count = (
        save_imported_transactions_to_database(
            transactions=(
                build_imported_transactions()
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

    assert inserted_count == 2
    assert len(
        loaded
    ) == 2

    assert set(
        loaded["descricao"]
    ) == {
        "Bolsa-estágio",
        "Compra no mercado",
    }

    assert set(
        loaded["arquivo_origem"]
    ) == {
        IMPORT_DATABASE_SOURCE,
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


def test_imported_transactions_are_isolated_by_user(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    transactions = (
        build_imported_transactions()
    )

    save_imported_transactions_to_database(
        transactions=transactions,
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
    )

    save_imported_transactions_to_database(
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


def test_empty_import_does_not_create_database(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    inserted_count = (
        save_imported_transactions_to_database(
            transactions=pd.DataFrame(),
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
        )
    )

    assert inserted_count == 0
    assert not database_path.exists()


def test_invalid_import_is_not_saved(
    tmp_path,
):
    transactions = (
        build_imported_transactions()
    )

    transactions.loc[
        0,
        "valor",
    ] = "-10.0"

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
        save_imported_transactions_to_database(
            transactions=transactions,
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
        )

    assert not database_path.exists()