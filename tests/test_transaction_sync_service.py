"""Testes da sincronização entre fontes e SQLite."""

from __future__ import annotations

from uuid import uuid4

import pandas as pd
import pytest

from src.transaction_repository import (
    insert_transactions,
    load_transaction,
)
from src.transaction_sync_service import (
    delete_persisted_transaction,
    prepare_persisted_transaction_updates,
    update_persisted_transaction,
)


TABLE_NAME = "transacoes_processadas"


def create_transaction_fixture(
    tmp_path,
) -> tuple:
    """Cria a mesma transação no arquivo e no SQLite."""
    project_root = tmp_path

    source_dir = (
        project_root
        / "data"
        / "raw"
    )

    source_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_file = (
        source_dir
        / "transacoes_2026_07.csv"
    )

    database_path = (
        project_root
        / "database"
        / "finantec.db"
    )

    transaction_id = str(
        uuid4()
    )

    source_transactions = pd.DataFrame(
        [
            {
                "transaction_id": transaction_id,
                "data": "2026-07-10",
                "tipo": "despesa",
                "descricao": "Mercado",
                "categoria": "Alimentação",
                "valor": 100.0,
            }
        ]
    )

    source_transactions.to_csv(
        source_file,
        index=False,
        encoding="utf-8-sig",
    )

    persisted_transactions = (
        source_transactions.copy()
    )

    persisted_transactions[
        "arquivo_origem"
    ] = source_file.name

    persisted_transactions[
        "ano_mes"
    ] = "2026-07"

    insert_transactions(
        transactions=(
            persisted_transactions
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    return (
        project_root,
        source_dir,
        source_file,
        database_path,
        transaction_id,
    )


def test_prepare_updates_normalizes_values():
    result = (
        prepare_persisted_transaction_updates(
            {
                "data": "2026-08-15",
                "tipo": " DESPESA ",
                "descricao": " Mercado ",
                "categoria": " Alimentação ",
                "valor": "250.50",
            }
        )
    )

    assert result == {
        "data": "2026-08-15",
        "tipo": "despesa",
        "descricao": "Mercado",
        "categoria": "Alimentação",
        "valor": 250.50,
        "ano_mes": "2026-08",
    }


def test_update_persisted_transaction_updates_both_sources(
    tmp_path,
):
    (
        project_root,
        source_dir,
        source_file,
        database_path,
        transaction_id,
    ) = create_transaction_fixture(
        tmp_path
    )

    update_persisted_transaction(
        transaction_id=transaction_id,
        updates={
            "data": "2026-08-01",
            "tipo": "despesa",
            "descricao": "Supermercado",
            "categoria": "Alimentação",
            "valor": 250.50,
        },
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
        source_dir=source_dir,
        project_root=project_root,
    )

    source_result = pd.read_csv(
        source_file,
        encoding="utf-8-sig",
    )

    database_result = load_transaction(
        database_path=database_path,
        table_name=TABLE_NAME,
        transaction_id=transaction_id,
        user_id="user-1",
        data_mode="user",
    )

    assert (
        source_result.loc[
            0,
            "descricao",
        ]
        == "Supermercado"
    )

    assert (
        source_result.loc[
            0,
            "valor",
        ]
        == 250.50
    )

    assert database_result is not None

    assert (
        database_result[
            "descricao"
        ]
        == "Supermercado"
    )

    assert (
        database_result[
            "ano_mes"
        ]
        == "2026-08"
    )


def test_delete_persisted_transaction_removes_both_sources(
    tmp_path,
):
    (
        project_root,
        source_dir,
        source_file,
        database_path,
        transaction_id,
    ) = create_transaction_fixture(
        tmp_path
    )

    delete_persisted_transaction(
        transaction_id=transaction_id,
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
        source_dir=source_dir,
        project_root=project_root,
    )

    source_result = pd.read_csv(
        source_file,
        encoding="utf-8-sig",
    )

    database_result = load_transaction(
        database_path=database_path,
        table_name=TABLE_NAME,
        transaction_id=transaction_id,
        user_id="user-1",
        data_mode="user",
    )

    assert source_result.empty
    assert database_result is None


def test_invalid_update_does_not_change_sources(
    tmp_path,
):
    (
        project_root,
        source_dir,
        source_file,
        database_path,
        transaction_id,
    ) = create_transaction_fixture(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="valor menor ou igual a zero",
    ):
        update_persisted_transaction(
            transaction_id=transaction_id,
            updates={
                "data": "2026-08-01",
                "tipo": "despesa",
                "descricao": "Inválida",
                "categoria": "Alimentação",
                "valor": -10.0,
            },
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="user",
            source_dir=source_dir,
            project_root=project_root,
        )

    source_result = pd.read_csv(
        source_file,
        encoding="utf-8-sig",
    )

    database_result = load_transaction(
        database_path=database_path,
        table_name=TABLE_NAME,
        transaction_id=transaction_id,
        user_id="user-1",
        data_mode="user",
    )

    assert (
        source_result.loc[
            0,
            "descricao",
        ]
        == "Mercado"
    )

    assert database_result is not None

    assert (
        database_result[
            "descricao"
        ]
        == "Mercado"
    )