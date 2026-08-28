"""Camada comum de acesso ao banco de dados."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Iterator, NoReturn


DATABASE_BACKEND_ENV = "FINANTEC_DATABASE_BACKEND"
TURSO_DATABASE_URL_ENV = "TURSO_DATABASE_URL"
TURSO_AUTH_TOKEN_ENV = "TURSO_AUTH_TOKEN"

SQLITE_BACKEND = "sqlite"
TURSO_BACKEND = "turso"


class DatabaseError(RuntimeError):
    """Indica uma falha genérica de persistência."""


class DatabaseIntegrityError(DatabaseError):
    """Indica violação de integridade no banco."""


def _is_integrity_error(
    error: Exception,
) -> bool:
    """Identifica erros de constraint nos drivers suportados."""
    if isinstance(
        error,
        sqlite3.IntegrityError,
    ):
        return True

    return (
        'code: "SQLITE_CONSTRAINT"'
        in str(
            error
        )
    )


def _raise_database_error(
    error: Exception,
    *,
    message: str,
    integrity_message: str | None = None,
) -> NoReturn:
    """Traduz erros dos drivers para exceções da aplicação."""
    if _is_integrity_error(
        error
    ):
        raise DatabaseIntegrityError(
            integrity_message
            or (
                "A operação violou uma "
                "restrição de integridade."
            )
        ) from error

    raise DatabaseError(
        message
    ) from error


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
        cursor: Any,
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
        row: Any,
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

        except Exception as error:
            _raise_database_error(
                error,
                message=(
                    "Não foi possível ler "
                    "o resultado da consulta."
                ),
            )

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

        except Exception as error:
            _raise_database_error(
                error,
                message=(
                    "Não foi possível ler "
                    "os resultados da consulta."
                ),
            )

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

        except Exception as error:
            _raise_database_error(
                error,
                message=(
                    "Não foi possível percorrer "
                    "os resultados da consulta."
                ),
            )


class DatabaseConnection:
    """Adapta uma conexão para a interface comum da aplicação."""

    def __init__(
        self,
        connection: Any,
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

        except Exception as error:
            _raise_database_error(
                error,
                message=(
                    "Não foi possível executar "
                    "a operação no banco."
                ),
            )

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

        except Exception as error:
            _raise_database_error(
                error,
                message=(
                    "Não foi possível executar "
                    "as operações no banco."
                ),
            )

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

        except Exception as error:
            _raise_database_error(
                error,
                message=(
                    "Não foi possível executar "
                    "o script no banco."
                ),
            )

        return DatabaseCursor(
            cursor
        )

    def commit(
        self,
    ) -> None:
        try:
            self._connection.commit()

        except Exception as error:
            _raise_database_error(
                error,
                message=(
                    "Não foi possível confirmar "
                    "a transação no banco."
                ),
            )

    def rollback(
        self,
    ) -> None:
        try:
            self._connection.rollback()

        except Exception as error:
            _raise_database_error(
                error,
                message=(
                    "Não foi possível desfazer "
                    "a transação no banco."
                ),
            )

    def close(
        self,
    ) -> None:
        try:
            self._connection.close()

        except Exception as error:
            _raise_database_error(
                error,
                message=(
                    "Não foi possível fechar "
                    "a conexão com o banco."
                ),
            )

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


def _get_database_backend() -> str:
    """Obtém o backend de persistência configurado."""
    backend = os.environ.get(
        DATABASE_BACKEND_ENV,
        SQLITE_BACKEND,
    ).strip().lower()

    if backend not in {
        SQLITE_BACKEND,
        TURSO_BACKEND,
    }:
        raise DatabaseError(
            "Backend de banco de dados "
            "não suportado."
        )

    return backend


def _connect_sqlite(
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

    except Exception as error:
        _raise_database_error(
            error,
            message=(
                "Não foi possível conectar "
                "ao banco de dados local."
            ),
        )

    return DatabaseConnection(
        connection
    )


def _connect_turso() -> DatabaseConnection:
    """Abre uma conexão com o banco remoto Turso."""
    database_url = os.environ.get(
        TURSO_DATABASE_URL_ENV,
        "",
    ).strip()

    auth_token = os.environ.get(
        TURSO_AUTH_TOKEN_ENV,
        "",
    ).strip()

    if not database_url:
        raise DatabaseError(
            "A URL do banco Turso "
            "não está configurada."
        )

    if not auth_token:
        raise DatabaseError(
            "O token de autenticação do Turso "
            "não está configurado."
        )

    try:
        import libsql

    except ImportError as error:
        raise DatabaseError(
            "O driver libsql não está instalado."
        ) from error

    try:
        connection = libsql.connect(
            database=database_url,
            auth_token=auth_token,
        )

    except Exception as error:
        raise DatabaseError(
            "Não foi possível conectar "
            "ao banco Turso."
        ) from error

    return DatabaseConnection(
        connection
    )


def connect_database(
    database_path: Path,
) -> DatabaseConnection:
    """Abre a conexão usando o backend configurado."""
    backend = (
        _get_database_backend()
    )

    if backend == TURSO_BACKEND:
        return _connect_turso()

    return _connect_sqlite(
        database_path
    )