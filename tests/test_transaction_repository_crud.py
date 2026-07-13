"""Testes do CRUD direto de transações no SQLite."""

from __future__ import annotations

from uuid import uuid4

import pandas as pd
import pytest

from src.transaction_repository import (
    DuplicateTransactionIdError,
    TransactionNotFoundError,
    delete_transaction,
    insert_transactions,
    load_transaction,
    load_transactions,
    update_transaction,
)


TABLE_NAME = "transacoes_processadas"


def build_transaction(
    description: str = "Mercado",
    *,
    transaction_id: str | None = None,
    value: float = 100.0,
) -> pd.DataFrame:
    """Cria uma transação processada válida."""
    return pd.DataFrame(
        [
            {
                "transaction_id": (
                    transaction_id
                    or str(
                        uuid4()
                    )
                ),
                "data": "2026-07-10",
                "tipo": "despesa",
                "descricao": description,
                "categoria": "Alimentação",
                "valor": value,
                "arquivo_origem": "manual",
                "ano_mes": "2026-07",
            }
        ]
    )


def test_insert_transactions_creates_and_loads_rows(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    transaction = build_transaction(
        "Compra no mercado"
    )

    inserted_count = (
        insert_transactions(
            transactions=transaction,
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="user",
        )
    )

    loaded = load_transactions(
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    assert inserted_count == 1
    assert len(loaded) == 1

    assert (
        loaded.iloc[0]["descricao"]
        == "Compra no mercado"
    )

    assert (
        loaded.iloc[0]["user_id"]
        == "user-1"
    )

    assert (
        loaded.iloc[0]["data_mode"]
        == "user"
    )


def test_insert_transactions_does_not_replace_existing_rows(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    insert_transactions(
        transactions=build_transaction(
            "Primeira transação"
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    insert_transactions(
        transactions=build_transaction(
            "Segunda transação"
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    loaded = load_transactions(
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    assert len(loaded) == 2

    assert set(
        loaded["descricao"]
    ) == {
        "Primeira transação",
        "Segunda transação",
    }


def test_insert_rejects_duplicate_id_inside_batch(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    repeated_id = str(
        uuid4()
    )

    batch = pd.concat(
        [
            build_transaction(
                "Primeira",
                transaction_id=repeated_id,
            ),
            build_transaction(
                "Segunda",
                transaction_id=repeated_id,
            ),
        ],
        ignore_index=True,
    )

    with pytest.raises(
        DuplicateTransactionIdError,
        match="duplicado",
    ):
        insert_transactions(
            transactions=batch,
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="user",
        )


def test_insert_rejects_id_already_used_in_context(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    transaction_id = str(
        uuid4()
    )

    insert_transactions(
        transactions=build_transaction(
            "Original",
            transaction_id=transaction_id,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    with pytest.raises(
        DuplicateTransactionIdError,
        match="Já existe",
    ):
        insert_transactions(
            transactions=build_transaction(
                "Duplicada",
                transaction_id=transaction_id,
            ),
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="user",
        )

    loaded = load_transactions(
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    assert len(loaded) == 1

    assert (
        loaded.iloc[0]["descricao"]
        == "Original"
    )


def test_same_transaction_id_can_exist_in_other_user(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    transaction_id = str(
        uuid4()
    )

    insert_transactions(
        transactions=build_transaction(
            "Usuário 1",
            transaction_id=transaction_id,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    insert_transactions(
        transactions=build_transaction(
            "Usuário 2",
            transaction_id=transaction_id,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-2",
        data_mode="user",
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

    assert (
        first_user.iloc[0]["descricao"]
        == "Usuário 1"
    )

    assert (
        second_user.iloc[0]["descricao"]
        == "Usuário 2"
    )


def test_load_transaction_returns_only_selected_context(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    transaction_id = str(
        uuid4()
    )

    insert_transactions(
        transactions=build_transaction(
            transaction_id=transaction_id,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    found = load_transaction(
        database_path=database_path,
        table_name=TABLE_NAME,
        transaction_id=transaction_id,
        user_id="user-1",
        data_mode="user",
    )

    missing = load_transaction(
        database_path=database_path,
        table_name=TABLE_NAME,
        transaction_id=transaction_id,
        user_id="user-2",
        data_mode="user",
    )

    assert found is not None

    assert (
        found["descricao"]
        == "Mercado"
    )

    assert missing is None


def test_update_transaction_preserves_id_and_context(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    transaction_id = str(
        uuid4()
    )

    insert_transactions(
        transactions=build_transaction(
            "Mercado",
            transaction_id=transaction_id,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    updated = update_transaction(
        database_path=database_path,
        table_name=TABLE_NAME,
        transaction_id=transaction_id,
        user_id="user-1",
        data_mode="user",
        updates={
            "data": "2026-08-01",
            "descricao": "Supermercado",
            "valor": 250.50,
            "ano_mes": "2026-08",
        },
    )

    assert (
        updated["transaction_id"]
        == transaction_id
    )

    assert (
        updated["user_id"]
        == "user-1"
    )

    assert (
        updated["data_mode"]
        == "user"
    )

    assert (
        updated["descricao"]
        == "Supermercado"
    )

    assert (
        updated["valor"]
        == 250.50
    )

    assert (
        updated["ano_mes"]
        == "2026-08"
    )


def test_update_missing_transaction_raises_error(
    tmp_path,
):
    with pytest.raises(
        TransactionNotFoundError,
        match="não foi encontrada",
    ):
        update_transaction(
            database_path=(
                tmp_path
                / "finantec.db"
            ),
            table_name=TABLE_NAME,
            transaction_id=str(
                uuid4()
            ),
            user_id="user-1",
            data_mode="user",
            updates={
                "descricao": "Inexistente",
            },
        )


def test_update_rejects_context_and_id_columns(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    transaction_id = str(
        uuid4()
    )

    insert_transactions(
        transactions=build_transaction(
            transaction_id=transaction_id,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    with pytest.raises(
        ValueError,
        match="não permitidos",
    ):
        update_transaction(
            database_path=database_path,
            table_name=TABLE_NAME,
            transaction_id=transaction_id,
            user_id="user-1",
            data_mode="user",
            updates={
                "user_id": "user-2",
                "transaction_id": str(
                    uuid4()
                ),
            },
        )


def test_delete_transaction_removes_only_selected_context(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    transaction_id = str(
        uuid4()
    )

    insert_transactions(
        transactions=build_transaction(
            "Usuário 1",
            transaction_id=transaction_id,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    insert_transactions(
        transactions=build_transaction(
            "Usuário 2",
            transaction_id=transaction_id,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-2",
        data_mode="user",
    )

    deleted = delete_transaction(
        database_path=database_path,
        table_name=TABLE_NAME,
        transaction_id=transaction_id,
        user_id="user-1",
        data_mode="user",
    )

    assert deleted is True

    assert (
        load_transaction(
            database_path=database_path,
            table_name=TABLE_NAME,
            transaction_id=transaction_id,
            user_id="user-1",
            data_mode="user",
        )
        is None
    )

    assert (
        load_transaction(
            database_path=database_path,
            table_name=TABLE_NAME,
            transaction_id=transaction_id,
            user_id="user-2",
            data_mode="user",
        )
        is not None
    )


def test_insert_rejects_incomplete_processed_contract(
    tmp_path,
):
    incomplete = pd.DataFrame(
        [
            {
                "transaction_id": str(
                    uuid4()
                ),
                "data": "2026-07-10",
                "tipo": "despesa",
                "descricao": "Mercado",
                "categoria": "Alimentação",
                "valor": 100.0,
            }
        ]
    )

    with pytest.raises(
        ValueError,
        match="arquivo_origem.*ano_mes",
    ):
        insert_transactions(
            transactions=incomplete,
            database_path=(
                tmp_path
                / "finantec.db"
            ),
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="user",
        )