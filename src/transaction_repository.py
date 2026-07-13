"""Persistência SQLite das transações do FinanTec."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
)
from src.transaction_validation import (
    REQUIRED_TRANSACTION_COLUMNS,
)
from src.user_context import (
    LOCAL_USER_ID,
)


USER_ID_COLUMN = "user_id"
DATA_MODE_COLUMN = "data_mode"

TRANSACTION_SOURCE_COLUMN = (
    "arquivo_origem"
)

TRANSACTION_PERIOD_COLUMN = (
    "ano_mes"
)

VALID_TRANSACTION_DATA_MODES = {
    "user",
    "demo",
}

PERSISTED_TRANSACTION_COLUMNS = [
    TRANSACTION_ID_COLUMN,
    *REQUIRED_TRANSACTION_COLUMNS,
    TRANSACTION_SOURCE_COLUMN,
    TRANSACTION_PERIOD_COLUMN,
]

MUTABLE_TRANSACTION_COLUMNS = {
    *REQUIRED_TRANSACTION_COLUMNS,
    TRANSACTION_SOURCE_COLUMN,
    TRANSACTION_PERIOD_COLUMN,
}

_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)


class TransactionNotFoundError(
    LookupError
):
    """Indica que uma transação não existe no contexto informado."""


class DuplicateTransactionIdError(
    ValueError
):
    """Indica uma tentativa de persistir IDs duplicados."""


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


def _normalize_transaction_id(
    transaction_id: object,
) -> str:
    """Valida o identificador de uma transação."""
    normalized_transaction_id = str(
        transaction_id
        if transaction_id is not None
        else ""
    ).strip()

    if not normalized_transaction_id:
        raise ValueError(
            "O identificador da transação "
            "não pode ser vazio."
        )

    return normalized_transaction_id


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


def _validate_columns_for_insert(
    transactions: pd.DataFrame,
) -> None:
    """Valida o contrato necessário para inserção direta."""
    missing_columns = [
        column
        for column
        in PERSISTED_TRANSACTION_COLUMNS
        if column not in transactions.columns
    ]

    if missing_columns:
        raise ValueError(
            "Não foi possível inserir as transações. "
            "Colunas obrigatórias ausentes: "
            + ", ".join(
                missing_columns
            )
        )


def _validate_transaction_ids(
    transactions: pd.DataFrame,
) -> list[str]:
    """Valida os IDs presentes em um lote."""
    transaction_ids = [
        _normalize_transaction_id(
            value
        )
        for value in transactions[
            TRANSACTION_ID_COLUMN
        ].tolist()
    ]

    if (
        len(transaction_ids)
        != len(set(transaction_ids))
    ):
        raise DuplicateTransactionIdError(
            "O lote possui transaction_id duplicado."
        )

    return transaction_ids


def _ensure_table_accepts_columns(
    connection: sqlite3.Connection,
    table_name: str,
    columns: list[str],
) -> None:
    """Verifica se a tabela aceita as colunas informadas."""
    existing_columns = (
        _get_table_columns(
            connection,
            table_name,
        )
    )

    missing_columns = [
        column
        for column in columns
        if column not in existing_columns
    ]

    if missing_columns:
        raise RuntimeError(
            "A tabela de transações possui "
            "uma estrutura incompatível. "
            "Colunas ausentes: "
            + ", ".join(
                missing_columns
            )
        )


def _find_existing_transaction_ids(
    connection: sqlite3.Connection,
    table_name: str,
    user_id: str,
    data_mode: str,
    transaction_ids: list[str],
) -> set[str]:
    """Localiza IDs já usados no mesmo contexto."""
    if not transaction_ids:
        return set()

    existing_ids: set[str] = set()

    chunk_size = 500

    for start in range(
        0,
        len(transaction_ids),
        chunk_size,
    ):
        current_ids = (
            transaction_ids[
                start:
                start + chunk_size
            ]
        )

        placeholders = ", ".join(
            "?"
            for _ in current_ids
        )

        rows = connection.execute(
            f"""
            SELECT {TRANSACTION_ID_COLUMN}
            FROM {table_name}
            WHERE
                {USER_ID_COLUMN} = ?
                AND {DATA_MODE_COLUMN} = ?
                AND {TRANSACTION_ID_COLUMN}
                    IN ({placeholders})
            """,
            (
                user_id,
                data_mode,
                *current_ids,
            ),
        ).fetchall()

        existing_ids.update(
            str(
                row[TRANSACTION_ID_COLUMN]
            )
            for row in rows
        )

    return existing_ids


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
            if not _table_exists(
                connection,
                normalized_table_name,
            ):
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

            _ensure_table_accepts_columns(
                connection=connection,
                table_name=normalized_table_name,
                columns=(
                    prepared_transactions
                    .columns
                    .tolist()
                ),
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


def insert_transactions(
    transactions: pd.DataFrame,
    database_path: Path,
    table_name: str,
    user_id: str = LOCAL_USER_ID,
    data_mode: str = "user",
) -> int:
    """Insere novas transações sem substituir o contexto."""
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

    if transactions.empty:
        return 0

    _validate_columns_for_insert(
        transactions
    )

    transaction_ids = (
        _validate_transaction_ids(
            transactions
        )
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
            if not _table_exists(
                connection,
                normalized_table_name,
            ):
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

                return int(
                    len(
                        prepared_transactions
                    )
                )

            _ensure_transaction_context_columns(
                connection,
                normalized_table_name,
            )

            _ensure_table_accepts_columns(
                connection=connection,
                table_name=normalized_table_name,
                columns=(
                    prepared_transactions
                    .columns
                    .tolist()
                ),
            )

            existing_ids = (
                _find_existing_transaction_ids(
                    connection=connection,
                    table_name=normalized_table_name,
                    user_id=normalized_user_id,
                    data_mode=normalized_data_mode,
                    transaction_ids=transaction_ids,
                )
            )

            if existing_ids:
                duplicate_id = sorted(
                    existing_ids
                )[0]

                raise DuplicateTransactionIdError(
                    "Já existe uma transação "
                    "com o transaction_id "
                    f"{duplicate_id} neste contexto."
                )

            prepared_transactions.to_sql(
                normalized_table_name,
                connection,
                if_exists="append",
                index=False,
            )

    except DuplicateTransactionIdError:
        raise

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível inserir "
            "as transações no SQLite."
        ) from error

    return int(
        len(
            prepared_transactions
        )
    )


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


def load_transaction(
    database_path: Path,
    table_name: str,
    transaction_id: str,
    user_id: str = LOCAL_USER_ID,
    data_mode: str = "user",
) -> dict[str, Any] | None:
    """Carrega uma transação específica do contexto."""
    normalized_table_name = (
        _normalize_identifier(
            table_name,
            "O nome da tabela",
        )
    )

    normalized_transaction_id = (
        _normalize_transaction_id(
            transaction_id
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
        return None

    try:
        with _connect(
            database_path
        ) as connection:
            if not _table_exists(
                connection,
                normalized_table_name,
            ):
                return None

            _ensure_transaction_context_columns(
                connection,
                normalized_table_name,
            )

            columns = _get_table_columns(
                connection,
                normalized_table_name,
            )

            if (
                TRANSACTION_ID_COLUMN
                not in columns
            ):
                return None

            row = connection.execute(
                f"""
                SELECT *
                FROM {normalized_table_name}
                WHERE
                    {USER_ID_COLUMN} = ?
                    AND {DATA_MODE_COLUMN} = ?
                    AND {TRANSACTION_ID_COLUMN} = ?
                LIMIT 1
                """,
                (
                    normalized_user_id,
                    normalized_data_mode,
                    normalized_transaction_id,
                ),
            ).fetchone()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "a transação do SQLite."
        ) from error

    if row is None:
        return None

    return {
        key: row[key]
        for key in row.keys()
    }


def update_transaction(
    database_path: Path,
    table_name: str,
    transaction_id: str,
    updates: Mapping[str, object],
    user_id: str = LOCAL_USER_ID,
    data_mode: str = "user",
) -> dict[str, Any]:
    """Atualiza uma transação sem alterar seu contexto ou ID."""
    normalized_table_name = (
        _normalize_identifier(
            table_name,
            "O nome da tabela",
        )
    )

    normalized_transaction_id = (
        _normalize_transaction_id(
            transaction_id
        )
    )

    (
        normalized_user_id,
        normalized_data_mode,
    ) = _normalize_transaction_context(
        user_id=user_id,
        data_mode=data_mode,
    )

    if not updates:
        raise ValueError(
            "Nenhum campo foi informado "
            "para atualização."
        )

    invalid_columns = sorted(
        set(
            updates
        )
        - MUTABLE_TRANSACTION_COLUMNS
    )

    if invalid_columns:
        raise ValueError(
            "Campos não permitidos na atualização: "
            + ", ".join(
                invalid_columns
            )
        )

    update_columns = list(
        updates.keys()
    )

    assignments = ", ".join(
        f"{column} = ?"
        for column in update_columns
    )

    values = [
        updates[column]
        for column in update_columns
    ]

    try:
        with _connect(
            database_path
        ) as connection:
            if not _table_exists(
                connection,
                normalized_table_name,
            ):
                raise TransactionNotFoundError(
                    "A transação informada "
                    "não foi encontrada."
                )

            _ensure_transaction_context_columns(
                connection,
                normalized_table_name,
            )

            _ensure_table_accepts_columns(
                connection=connection,
                table_name=normalized_table_name,
                columns=[
                    TRANSACTION_ID_COLUMN,
                    *update_columns,
                ],
            )

            cursor = connection.execute(
                f"""
                UPDATE {normalized_table_name}
                SET {assignments}
                WHERE
                    {USER_ID_COLUMN} = ?
                    AND {DATA_MODE_COLUMN} = ?
                    AND {TRANSACTION_ID_COLUMN} = ?
                """,
                (
                    *values,
                    normalized_user_id,
                    normalized_data_mode,
                    normalized_transaction_id,
                ),
            )

            if cursor.rowcount == 0:
                raise TransactionNotFoundError(
                    "A transação informada "
                    "não foi encontrada."
                )

    except TransactionNotFoundError:
        raise

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível atualizar "
            "a transação no SQLite."
        ) from error

    updated_transaction = (
        load_transaction(
            database_path=database_path,
            table_name=normalized_table_name,
            transaction_id=normalized_transaction_id,
            user_id=normalized_user_id,
            data_mode=normalized_data_mode,
        )
    )

    if updated_transaction is None:
        raise RuntimeError(
            "A transação foi atualizada, "
            "mas não pôde ser carregada novamente."
        )

    return updated_transaction


def delete_transaction(
    database_path: Path,
    table_name: str,
    transaction_id: str,
    user_id: str = LOCAL_USER_ID,
    data_mode: str = "user",
) -> bool:
    """Exclui uma transação específica do contexto."""
    normalized_table_name = (
        _normalize_identifier(
            table_name,
            "O nome da tabela",
        )
    )

    normalized_transaction_id = (
        _normalize_transaction_id(
            transaction_id
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
        return False

    try:
        with _connect(
            database_path
        ) as connection:
            if not _table_exists(
                connection,
                normalized_table_name,
            ):
                return False

            _ensure_transaction_context_columns(
                connection,
                normalized_table_name,
            )

            columns = _get_table_columns(
                connection,
                normalized_table_name,
            )

            if (
                TRANSACTION_ID_COLUMN
                not in columns
            ):
                return False

            cursor = connection.execute(
                f"""
                DELETE FROM {normalized_table_name}
                WHERE
                    {USER_ID_COLUMN} = ?
                    AND {DATA_MODE_COLUMN} = ?
                    AND {TRANSACTION_ID_COLUMN} = ?
                """,
                (
                    normalized_user_id,
                    normalized_data_mode,
                    normalized_transaction_id,
                ),
            )

            return (
                cursor.rowcount > 0
            )

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível excluir "
            "a transação do SQLite."
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