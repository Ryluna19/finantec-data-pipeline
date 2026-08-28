"""Testes da camada comum de conexão com o banco."""

from __future__ import annotations

import pytest

from src.database_connection import (
    DatabaseError,
    DatabaseIntegrityError,
    connect_database,
)


def test_database_row_supports_name_and_index(
    tmp_path,
):
    database_path = (
        tmp_path
        / "database.db"
    )

    with connect_database(
        database_path
    ) as connection:
        connection.execute(
            """
            CREATE TABLE test_rows (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            INSERT INTO test_rows (
                name
            )
            VALUES (?)
            """,
            (
                "FinanTec",
            ),
        )

        row = connection.execute(
            """
            SELECT id, name
            FROM test_rows
            """
        ).fetchone()

    assert row is not None
    assert row[0] == 1
    assert row["name"] == "FinanTec"
    assert row.keys() == [
        "id",
        "name",
    ]


def test_cursor_supports_iteration(
    tmp_path,
):
    database_path = (
        tmp_path
        / "database.db"
    )

    with connect_database(
        database_path
    ) as connection:
        connection.execute(
            """
            CREATE TABLE test_iteration (
                value TEXT NOT NULL
            )
            """
        )

        connection.executemany(
            """
            INSERT INTO test_iteration (
                value
            )
            VALUES (?)
            """,
            [
                ("a",),
                ("b",),
            ],
        )

        cursor = connection.execute(
            """
            SELECT value
            FROM test_iteration
            ORDER BY value
            """
        )

        values = [
            row["value"]
            for row in cursor
        ]

    assert values == [
        "a",
        "b",
    ]


def test_cursor_exposes_rowcount(
    tmp_path,
):
    database_path = (
        tmp_path
        / "database.db"
    )

    with connect_database(
        database_path
    ) as connection:
        connection.execute(
            """
            CREATE TABLE test_rowcount (
                id INTEGER PRIMARY KEY
            )
            """
        )

        cursor = connection.execute(
            """
            INSERT INTO test_rowcount
            DEFAULT VALUES
            """
        )

    assert cursor.rowcount == 1


def test_executescript_and_executemany(
    tmp_path,
):
    database_path = (
        tmp_path
        / "database.db"
    )

    with connect_database(
        database_path
    ) as connection:
        connection.executescript(
            """
            CREATE TABLE test_batch (
                value TEXT NOT NULL
            );

            INSERT INTO test_batch (
                value
            )
            VALUES ('first');
            """
        )

        cursor = connection.executemany(
            """
            INSERT INTO test_batch (
                value
            )
            VALUES (?)
            """,
            [
                ("second",),
                ("third",),
            ],
        )

        rows = connection.execute(
            """
            SELECT value
            FROM test_batch
            ORDER BY rowid
            """
        ).fetchall()

    assert cursor.rowcount == 2

    assert [
        row["value"]
        for row in rows
    ] == [
        "first",
        "second",
        "third",
    ]


def test_context_manager_rolls_back_on_error(
    tmp_path,
):
    database_path = (
        tmp_path
        / "database.db"
    )

    with connect_database(
        database_path
    ) as connection:
        connection.execute(
            """
            CREATE TABLE test_rollback (
                value TEXT NOT NULL
            )
            """
        )

    with pytest.raises(
        RuntimeError
    ):
        with connect_database(
            database_path
        ) as connection:
            connection.execute(
                """
                INSERT INTO test_rollback (
                    value
                )
                VALUES (?)
                """,
                (
                    "should-rollback",
                ),
            )

            raise RuntimeError(
                "falha simulada"
            )

    with connect_database(
        database_path
    ) as connection:
        row = connection.execute(
            """
            SELECT COUNT(*)
            FROM test_rollback
            """
        ).fetchone()

    assert row is not None
    assert row[0] == 0


def test_integrity_error_is_translated(
    tmp_path,
):
    database_path = (
        tmp_path
        / "database.db"
    )

    with connect_database(
        database_path
    ) as connection:
        connection.execute(
            """
            CREATE TABLE test_unique (
                name TEXT NOT NULL UNIQUE
            )
            """
        )

        connection.execute(
            """
            INSERT INTO test_unique (
                name
            )
            VALUES (?)
            """,
            (
                "duplicate",
            ),
        )

        with pytest.raises(
            DatabaseIntegrityError
        ):
            connection.execute(
                """
                INSERT INTO test_unique (
                    name
                )
                VALUES (?)
                """,
                (
                    "duplicate",
                ),
            )


def test_generic_database_error_is_translated(
    tmp_path,
):
    database_path = (
        tmp_path
        / "database.db"
    )

    with connect_database(
        database_path
    ) as connection:
        with pytest.raises(
            DatabaseError
        ):
            connection.execute(
                """
                SELECT *
                FROM table_that_does_not_exist
                """
            )