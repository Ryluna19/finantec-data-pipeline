"""Testes da integração do perfil com o carregamento de dados."""

from __future__ import annotations

import sqlite3

from data_loader import (
    sqlite_table_exists,
)


def test_sqlite_table_exists(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            """
            CREATE TABLE user_profiles (
                user_id TEXT PRIMARY KEY
            )
            """
        )

    assert sqlite_table_exists(
        database_path=database_path,
        table_name="user_profiles",
    )

    assert not sqlite_table_exists(
        database_path=database_path,
        table_name="transacoes_processadas",
    )
