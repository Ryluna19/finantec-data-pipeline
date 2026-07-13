"""Testes do isolamento das transações no SQLite."""

from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from src.transaction_repository import (
    DATA_MODE_COLUMN,
    USER_ID_COLUMN,
    delete_transactions,
    load_transactions,
    replace_transactions,
)
from src.user_context import (
    LOCAL_USER_ID,
)


TABLE_NAME = "transacoes_processadas"


def build_transactions(
    description: str,
    value: float,
) -> pd.DataFrame:
    """Cria uma pequena base de transações."""
    return pd.DataFrame(
        [
            {
                "transaction_id": (
                    f"id-{description}"
                ),
                "data": "2026-07-10",
                "tipo": "despesa",
                "descricao": description,
                "categoria": "Teste",
                "valor": value,
                "arquivo_origem": "teste.csv",
                "ano_mes": "2026-07",
            }
        ]
    )


def test_default_context_remains_compatible(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    replace_transactions(
        transactions=build_transactions(
            "Mercado",
            100.0,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
    )

    loaded = load_transactions(
        database_path=database_path,
        table_name=TABLE_NAME,
    )

    assert len(
        loaded
    ) == 1

    assert (
        loaded.iloc[0][
            USER_ID_COLUMN
        ]
        == LOCAL_USER_ID
    )

    assert (
        loaded.iloc[0][
            DATA_MODE_COLUMN
        ]
        == "user"
    )


def test_transactions_are_isolated_by_user(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    replace_transactions(
        transactions=build_transactions(
            "Usuário 1",
            100.0,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    replace_transactions(
        transactions=build_transactions(
            "Usuário 2",
            200.0,
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


def test_transactions_are_isolated_by_data_mode(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    replace_transactions(
        transactions=build_transactions(
            "Dados reais",
            100.0,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    replace_transactions(
        transactions=build_transactions(
            "Demonstração",
            999.0,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="demo",
    )

    user_transactions = (
        load_transactions(
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="user",
        )
    )

    demo_transactions = (
        load_transactions(
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="demo",
        )
    )

    assert (
        user_transactions.iloc[0][
            "descricao"
        ]
        == "Dados reais"
    )

    assert (
        demo_transactions.iloc[0][
            "descricao"
        ]
        == "Demonstração"
    )


def test_replacing_partition_preserves_other_contexts(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    replace_transactions(
        transactions=build_transactions(
            "Versão antiga",
            100.0,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    replace_transactions(
        transactions=build_transactions(
            "Outro usuário",
            300.0,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-2",
        data_mode="user",
    )

    replace_transactions(
        transactions=build_transactions(
            "Versão nova",
            200.0,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
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

    assert len(
        first_user
    ) == 1

    assert (
        first_user.iloc[0]["descricao"]
        == "Versão nova"
    )

    assert (
        second_user.iloc[0]["descricao"]
        == "Outro usuário"
    )


def test_empty_replacement_clears_only_partition(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    replace_transactions(
        transactions=build_transactions(
            "Real",
            100.0,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    replace_transactions(
        transactions=build_transactions(
            "Demo",
            200.0,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="demo",
    )

    empty_transactions = (
        build_transactions(
            "Vazia",
            0.0,
        )
        .iloc[0:0]
        .copy()
    )

    replace_transactions(
        transactions=empty_transactions,
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    assert (
        load_transactions(
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="user",
        )
        .empty
    )

    assert len(
        load_transactions(
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="demo",
        )
    ) == 1


def test_delete_transactions_preserves_other_user(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    replace_transactions(
        transactions=build_transactions(
            "Usuário 1",
            100.0,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-1",
        data_mode="user",
    )

    replace_transactions(
        transactions=build_transactions(
            "Usuário 2",
            200.0,
        ),
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id="user-2",
        data_mode="user",
    )

    deleted_count = (
        delete_transactions(
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="user",
        )
    )

    assert deleted_count == 1

    assert (
        load_transactions(
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="user",
        )
        .empty
    )

    assert len(
        load_transactions(
            database_path=database_path,
            table_name=TABLE_NAME,
            user_id="user-2",
            data_mode="user",
        )
    ) == 1


def test_legacy_table_is_migrated_to_local_user(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    legacy_transactions = (
        build_transactions(
            "Transação antiga",
            100.0,
        )
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        legacy_transactions.to_sql(
            TABLE_NAME,
            connection,
            if_exists="replace",
            index=False,
        )

    loaded = load_transactions(
        database_path=database_path,
        table_name=TABLE_NAME,
        user_id=LOCAL_USER_ID,
        data_mode="user",
    )

    assert len(
        loaded
    ) == 1

    assert (
        loaded.iloc[0]["descricao"]
        == "Transação antiga"
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                f"""
                PRAGMA table_info(
                    {TABLE_NAME}
                )
                """
            ).fetchall()
        }

    assert USER_ID_COLUMN in columns
    assert DATA_MODE_COLUMN in columns


def test_rejects_invalid_data_mode(
    tmp_path,
):
    with pytest.raises(
        ValueError,
        match="user.*demo",
    ):
        load_transactions(
            database_path=(
                tmp_path
                / "finantec.db"
            ),
            table_name=TABLE_NAME,
            user_id="user-1",
            data_mode="invalid",
        )