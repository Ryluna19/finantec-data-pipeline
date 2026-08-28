"""Camada comum de acesso ao banco de dados."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterator


class DatabaseError(RuntimeError):
    """Indica uma falha genérica de persistência."""


class DatabaseIntegrityError(DatabaseError):
    """Indica violação de integridade no banco."""


class DatabaseRow:
    """Representa uma linha acessível por índice ou coluna."""

    def __init__(
        self,
        columns: list[str],
        values: tuple[Any, ...],
    ) -> None:
        self._columns = tuple(
            columns
        )
        self._values = tuple(
            values
        )
        self._index_by_name = {
            column: index
            for index, column in enumerate(
                self._columns
            )
        }

    def __getitem__(
        self,
        key: int | str,
    ) -> Any:
        if isinstance(
            key,
            str,
        ):
            try:
                index = self._index_by_name[
                    key
                ]

            except KeyError as error:
                raise IndexError(
                    f"Coluna não encontrada: {key}"
                ) from error

            return self._values[
                index
            ]

        return self._values[
            key
        ]

    def __iter__(
        self,
    ) -> Iterator[Any]:
        return iter(
            self._values
        )

    def __len__(
        self,
    ) -> int:
        return len(
            self._values
        )

    def keys(
        self,
    ) -> list[str]:
        return list(
            self._columns
        )


class DatabaseCursor:
    """Adapta um cursor para a interface comum do projeto."""

    def __init__(
        self,
        cursor: sqlite3.Cursor,
    ) -> None:
        self._cursor = cursor

    @property
    def rowcount(
        self,
    ) -> int:
        return int(
            self._cursor.rowcount
        )

    @property
    def description(
        self,
    ) -> Any:
        return self._cursor.description

    def _get_columns(
        self,
    ) -> list[str]:
        description = (
            self._cursor.description
            or ()
        )

        return [
            str(
                column[0]
            )
            for column in description
        ]

    def _convert_row(
        self,
        row: tuple[Any, ...] | None,
    ) -> DatabaseRow | None:
        if row is None:
            return None

        return DatabaseRow(
            self._get_columns(),
            tuple(
                row
            ),
        )

    def fetchone(
        self,
    ) -> DatabaseRow | None:
        try:
            return self._convert_row(
                self._cursor.fetchone()
            )

        except sqlite3.Error as error:
            raise DatabaseError(
                "Não foi possível ler "
                "o resultado da consulta."
            ) from error

    def fetchall(
        self,
    ) -> list[DatabaseRow]:
        try:
            columns = (
                self._get_columns()
            )

            return [
                DatabaseRow(
                    columns,
                    tuple(
                        row
                    ),
                )
                for row in (
                    self._cursor.fetchall()
                )
            ]

        except sqlite3.Error as error:
            raise DatabaseError(
                "Não foi possível ler "
                "os resultados da consulta."
            ) from error

    def __iter__(
        self,
    ) -> Iterator[DatabaseRow]:
        columns = (
            self._get_columns()
        )

        try:
            for row in self._cursor:
                yield DatabaseRow(
                    columns,
                    tuple(
                        row
                    ),
                )

        except sqlite3.Error as error:
            raise DatabaseError(
                "Não foi possível percorrer "
                "os resultados da consulta."
            ) from error


class DatabaseConnection:
    """Adapta uma conexão SQLite para a aplicação."""

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self._connection = connection

    def execute(
        self,
        sql: str,
        parameters: Any = (),
    ) -> DatabaseCursor:
        try:
            cursor = (
                self._connection.execute(
                    sql,
                    parameters,
                )
            )

        except sqlite3.IntegrityError as error:
            raise DatabaseIntegrityError(
                "A operação violou uma "
                "restrição de integridade."
            ) from error

        except sqlite3.Error as error:
            raise DatabaseError(
                "Não foi possível executar "
                "a operação no banco."
            ) from error

        return DatabaseCursor(
            cursor
        )

    def executemany(
        self,
        sql: str,
        parameters: Any,
    ) -> DatabaseCursor:
        try:
            cursor = (
                self._connection.executemany(
                    sql,
                    parameters,
                )
            )

        except sqlite3.IntegrityError as error:
            raise DatabaseIntegrityError(
                "A operação violou uma "
                "restrição de integridade."
            ) from error

        except sqlite3.Error as error:
            raise DatabaseError(
                "Não foi possível executar "
                "as operações no banco."
            ) from error

        return DatabaseCursor(
            cursor
        )

    def executescript(
        self,
        sql_script: str,
    ) -> DatabaseCursor:
        try:
            cursor = (
                self._connection.executescript(
                    sql_script
                )
            )

        except sqlite3.IntegrityError as error:
            raise DatabaseIntegrityError(
                "O script violou uma "
                "restrição de integridade."
            ) from error

        except sqlite3.Error as error:
            raise DatabaseError(
                "Não foi possível executar "
                "o script no banco."
            ) from error

        return DatabaseCursor(
            cursor
        )

    def commit(
        self,
    ) -> None:
        try:
            self._connection.commit()

        except sqlite3.Error as error:
            raise DatabaseError(
                "Não foi possível confirmar "
                "a transação no banco."
            ) from error

    def rollback(
        self,
    ) -> None:
        try:
            self._connection.rollback()

        except sqlite3.Error as error:
            raise DatabaseError(
                "Não foi possível desfazer "
                "a transação no banco."
            ) from error

    def close(
        self,
    ) -> None:
        try:
            self._connection.close()

        except sqlite3.Error as error:
            raise DatabaseError(
                "Não foi possível fechar "
                "a conexão com o banco."
            ) from error

    def __enter__(
        self,
    ) -> DatabaseConnection:
        return self

    def __exit__(
        self,
        exception_type: object,
        exception: object,
        traceback: object,
    ) -> None:
        if exception_type is None:
            self.commit()

        else:
            self.rollback()


def connect_database(
    database_path: Path,
) -> DatabaseConnection:
    """Abre uma conexão com o SQLite local."""
    normalized_path = Path(
        database_path
    )

    normalized_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        connection = sqlite3.connect(
            normalized_path,
            timeout=5.0,
        )

    except sqlite3.Error as error:
        raise DatabaseError(
            "Não foi possível conectar "
            "ao banco de dados."
        ) from error

    return DatabaseConnection(
        connection
    )