"""Persistência SQLite das transações do FinanTec."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

from src.user_context import (
    LOCAL_USER_ID,
)


USER_ID_COLUMN = "user_id"
DATA_MODE_COLUMN = "data_mode"

VALID_TRANSACTION_DATA_MODES = {
    "user",
    "demo",
}

_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)


def _normalize_identifier(
    value: str,
    field_label: str,
) -> str:
    """Valida nomes internos usados em comandos SQL."""
    normalized_value = str(
        value
    ).strip()

    if not _IDENTIFIER_PATTERN.fullmatch(
        normalized_value
    ):
        raise ValueError(
            f"{field_label} possui um formato inválido."
        )

    return normalized_value


def _normalize_transaction_context(
    user_id: str,
    data_mode: str,
) -> tuple[str, str]:
    """Valida o usuário e o modo associados às transações."""
    normalized_user_id = str(
        user_id
    ).strip()

    normalized_data_mode = (
        str(
            data_mode
        )
        .strip()
        .lower()
    )

    if not normalized_user_id:
        raise ValueError(
            "O identificador do usuário "
            "não pode ser vazio."
        )

    if (
        normalized_data_mode
        not in VALID_TRANSACTION_DATA_MODES
    ):
        raise ValueError(
            "O modo das transações deve ser "
            "'user' ou 'demo'."
        )

    return (
        normalized_user_id,
        normalized_data_mode,
    )


def _connect(
    database_path: Path,
) -> sqlite3.Connection:
    """Abre uma conexão SQLite."""
    database_path = Path(
        database_path
    )

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        database_path,
        timeout=5.0,
    )

    connection.row_factory = (
        sqlite3.Row
    )

    return connection


def _table_exists(
    connection: sqlite3.Connection,
    table_name: str,
) -> bool:
    """Verifica se uma tabela existe."""
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE
            type = 'table'
            AND name = ?
        LIMIT 1
        """,
        (
            table_name,
        ),
    ).fetchone()

    return row is not None


def _get_table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    """Retorna as colunas existentes na tabela."""
    rows = connection.execute(
        f"""
        PRAGMA table_info(
            {table_name}
        )
        """
    ).fetchall()

    return {
        str(
            row["name"]
        )
        for row in rows
    }


def _ensure_transaction_context_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> None:
    """Migra tabelas antigas para o contexto multiusuário."""
    if not _table_exists(
        connection,
        table_name,
    ):
        return

    columns = _get_table_columns(
        connection,
        table_name,
    )

    if USER_ID_COLUMN not in columns:
        connection.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {USER_ID_COLUMN} TEXT
            """
        )

    if DATA_MODE_COLUMN not in columns:
        connection.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {DATA_MODE_COLUMN} TEXT
            """
        )

    # Dados antigos são tratados como dados reais do usuário local.
    # A demonstração pode ser gerada novamente quando necessário.
    connection.execute(
        f"""
        UPDATE {table_name}
        SET {USER_ID_COLUMN} = ?
        WHERE
            {USER_ID_COLUMN} IS NULL
            OR TRIM({USER_ID_COLUMN}) = ''
        """,
        (
            LOCAL_USER_ID,
        ),
    )

    connection.execute(
        f"""
        UPDATE {table_name}
        SET {DATA_MODE_COLUMN} = 'user'
        WHERE
            {DATA_MODE_COLUMN} IS NULL
            OR TRIM({DATA_MODE_COLUMN}) = ''
        """
    )

    connection.execute(
        f"""
        CREATE INDEX IF NOT EXISTS
            idx_{table_name}_context
        ON {table_name} (
            {USER_ID_COLUMN},
            {DATA_MODE_COLUMN}
        )
        """
    )


def _prepare_transactions_for_context(
    transactions: pd.DataFrame,
    user_id: str,
    data_mode: str,
) -> pd.DataFrame:
    """Associa todas as linhas ao contexto informado."""
    prepared_transactions = (
        transactions.copy()
    )

    prepared_transactions[
        USER_ID_COLUMN
    ] = user_id

    prepared_transactions[
        DATA_MODE_COLUMN
    ] = data_mode

    return prepared_transactions


def replace_transactions(
    transactions: pd.DataFrame,
    database_path: Path,
    table_name: str,
    user_id: str = LOCAL_USER_ID,
    data_mode: str = "user",
) -> None:
    """Substitui somente as transações do contexto informado."""
    normalized_table_name = (
        _normalize_identifier(
            table_name,
            "O nome da tabela",
        )
    )

    (
        normalized_user_id,
        normalized_data_mode,
    ) = _normalize_transaction_context(
        user_id=user_id,
        data_mode=data_mode,
    )

    prepared_transactions = (
        _prepare_transactions_for_context(
            transactions=transactions,
            user_id=normalized_user_id,
            data_mode=normalized_data_mode,
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            table_already_exists = (
                _table_exists(
                    connection,
                    normalized_table_name,
                )
            )

            if not table_already_exists:
                prepared_transactions.to_sql(
                    normalized_table_name,
                    connection,
                    if_exists="replace",
                    index=False,
                )

                _ensure_transaction_context_columns(
                    connection,
                    normalized_table_name,
                )

                return

            _ensure_transaction_context_columns(
                connection,
                normalized_table_name,
            )

            existing_columns = (
                _get_table_columns(
                    connection,
                    normalized_table_name,
                )
            )

            missing_columns = [
                column
                for column
                in prepared_transactions.columns
                if column not in existing_columns
            ]

            if missing_columns:
                raise RuntimeError(
                    "A tabela de transações possui "
                    "uma estrutura antiga incompatível. "
                    "Colunas ausentes: "
                    + ", ".join(
                        missing_columns
                    )
                )

            connection.execute(
                f"""
                DELETE FROM {normalized_table_name}
                WHERE
                    {USER_ID_COLUMN} = ?
                    AND {DATA_MODE_COLUMN} = ?
                """,
                (
                    normalized_user_id,
                    normalized_data_mode,
                ),
            )

            if prepared_transactions.empty:
                return

            prepared_transactions.to_sql(
                normalized_table_name,
                connection,
                if_exists="append",
                index=False,
            )

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível salvar "
            "as transações no SQLite."
        ) from error


def load_transactions(
    database_path: Path,
    table_name: str,
    user_id: str = LOCAL_USER_ID,
    data_mode: str = "user",
) -> pd.DataFrame:
    """Carrega somente as transações do contexto informado."""
    normalized_table_name = (
        _normalize_identifier(
            table_name,
            "O nome da tabela",
        )
    )

    (
        normalized_user_id,
        normalized_data_mode,
    ) = _normalize_transaction_context(
        user_id=user_id,
        data_mode=data_mode,
    )

    database_path = Path(
        database_path
    )

    if not database_path.exists():
        return pd.DataFrame()

    try:
        with _connect(
            database_path
        ) as connection:
            if not _table_exists(
                connection,
                normalized_table_name,
            ):
                return pd.DataFrame()

            _ensure_transaction_context_columns(
                connection,
                normalized_table_name,
            )

            query = f"""
                SELECT *
                FROM {normalized_table_name}
                WHERE
                    {USER_ID_COLUMN} = ?
                    AND {DATA_MODE_COLUMN} = ?
            """

            return pd.read_sql_query(
                query,
                connection,
                params=(
                    normalized_user_id,
                    normalized_data_mode,
                ),
            )

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "as transações do SQLite."
        ) from error


def delete_transactions(
    database_path: Path,
    table_name: str,
    user_id: str,
    data_mode: str | None = None,
) -> int:
    """Remove as transações de um usuário sem apagar outras tabelas."""
    normalized_table_name = (
        _normalize_identifier(
            table_name,
            "O nome da tabela",
        )
    )

    normalized_user_id = str(
        user_id
    ).strip()

    if not normalized_user_id:
        raise ValueError(
            "O identificador do usuário "
            "não pode ser vazio."
        )

    normalized_data_mode: str | None = None

    if data_mode is not None:
        (
            _,
            normalized_data_mode,
        ) = _normalize_transaction_context(
            user_id=normalized_user_id,
            data_mode=data_mode,
        )

    database_path = Path(
        database_path
    )

    if not database_path.exists():
        return 0

    try:
        with _connect(
            database_path
        ) as connection:
            if not _table_exists(
                connection,
                normalized_table_name,
            ):
                return 0

            _ensure_transaction_context_columns(
                connection,
                normalized_table_name,
            )

            if normalized_data_mode is None:
                cursor = connection.execute(
                    f"""
                    DELETE FROM {normalized_table_name}
                    WHERE {USER_ID_COLUMN} = ?
                    """,
                    (
                        normalized_user_id,
                    ),
                )

            else:
                cursor = connection.execute(
                    f"""
                    DELETE FROM {normalized_table_name}
                    WHERE
                        {USER_ID_COLUMN} = ?
                        AND {DATA_MODE_COLUMN} = ?
                    """,
                    (
                        normalized_user_id,
                        normalized_data_mode,
                    ),
                )

            return int(
                cursor.rowcount
            )

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível remover "
            "as transações do usuário."
        ) from error