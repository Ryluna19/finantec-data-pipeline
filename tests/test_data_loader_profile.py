"""Testes da integração do perfil com o carregamento de dados."""

from __future__ import annotations

import sqlite3

from data_loader import (
    merge_profile_with_legacy_goals,
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


def test_merge_profile_with_legacy_goals():
    profile = {
        "user_id": "local-user",
        "nome": "Ryan",
    }

    seed_profile = {
        "nome": "Marina",
        "objetivos_financeiros": [
            {
                "nome": "Notebook",
                "valor_meta": 2800.0,
            }
        ],
    }

    result = (
        merge_profile_with_legacy_goals(
            profile=profile,
            seed_profile=seed_profile,
        )
    )

    assert result[
        "nome"
    ] == "Ryan"

    assert result[
        "objetivos_financeiros"
    ] == [
        {
            "nome": "Notebook",
            "valor_meta": 2800.0,
        }
    ]

    assert (
        "objetivos_financeiros"
        not in profile
    )