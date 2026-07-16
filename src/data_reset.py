"""Consulta e limpeza segura dos dados locais do usuário."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from src.transaction_repository import (
    delete_transactions,
    load_transactions,
)
from src.user_context import (
    LOCAL_USER_ID,
)

from src.budget_repository import BUDGET_TABLE_NAME
from src.chat_repository import CHAT_TABLE_NAME
from src.goal_repository import (
    GOAL_SEED_TABLE_NAME,
    GOAL_TABLE_NAME,
)
from src.profile_repository import PROFILE_TABLE_NAME
from src.transaction_repository import (
    DATA_MODE_COLUMN,
    USER_ID_COLUMN,
    delete_transactions,
    load_transactions,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
)

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "finantec.db"
)

LOG_PATH = (
    PROJECT_ROOT
    / "logs"
    / "etl_transacoes.log"
)

TRANSACTION_TABLE_NAME = (
    "transacoes_processadas"
)

USER_DATA_MODE = "user"


def _remove_file(
    file_path: Path,
) -> bool:
    """Remove um arquivo e informa se ele existia."""
    file_path = Path(
        file_path
    )

    if not file_path.exists():
        return False

    file_path.unlink()

    return True


def _normalize_user_id(
    user_id: str,
) -> str:
    """Valida o identificador do usuário."""
    normalized_user_id = str(
        user_id
    ).strip()

    if not normalized_user_id:
        raise ValueError(
            "O identificador do usuário "
            "não pode ser vazio."
        )

    return normalized_user_id

def _table_exists(
    connection: sqlite3.Connection,
    table_name: str,
) -> bool:
    """Verifica se uma tabela existe no banco."""
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def _get_table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    """Retorna as colunas de uma tabela existente."""
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return {
        str(row[1])
        for row in rows
    }


def _delete_user_rows(
    connection: sqlite3.Connection,
    table_name: str,
    user_id: str,
    *,
    data_mode: str | None = None,
) -> int:
    """Remove linhas pertencentes a um usuário."""
    if not _table_exists(
        connection,
        table_name,
    ):
        return 0

    columns = _get_table_columns(
        connection,
        table_name,
    )

    if USER_ID_COLUMN not in columns:
        raise RuntimeError(
            f"A tabela {table_name} não possui contexto de usuário."
        )

    where_clause = f"{USER_ID_COLUMN} = ?"
    parameters: list[str] = [user_id]

    if data_mode is not None:
        if DATA_MODE_COLUMN not in columns:
            raise RuntimeError(
                f"A tabela {table_name} não possui modo de dados."
            )

        where_clause += f" AND {DATA_MODE_COLUMN} = ?"
        parameters.append(data_mode)

    cursor = connection.execute(
        f"""
        DELETE FROM {table_name}
        WHERE {where_clause}
        """,
        tuple(parameters),
    )

    return int(cursor.rowcount)

def find_user_source_files(
    raw_dir: Path = RAW_DIR,
) -> list[Path]:
    """Localiza as fontes reais de transações do usuário."""
    raw_dir = Path(
        raw_dir
    )

    if not raw_dir.exists():
        return []

    return sorted(
        raw_dir.rglob(
            "transacoes_*.csv"
        )
    )


def count_user_transaction_rows(
    database_path: Path = DATABASE_PATH,
    user_id: str = LOCAL_USER_ID,
) -> int:
    """Conta as transações reais persistidas do usuário."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    database_path = Path(
        database_path
    )

    if not database_path.exists():
        return 0

    transactions = load_transactions(
        database_path=database_path,
        table_name=(
            TRANSACTION_TABLE_NAME
        ),
        user_id=normalized_user_id,
        data_mode=USER_DATA_MODE,
    )

    return int(
        len(
            transactions
        )
    )


def summarize_user_transaction_data(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    database_path: Path = DATABASE_PATH,
    log_path: Path = LOG_PATH,
    user_id: str = LOCAL_USER_ID,
) -> dict[str, int | bool]:
    """Resume somente os dados transacionais do usuário."""
    processed_files = [
        Path(
            processed_dir
        )
        / "transacoes_processadas.csv",
        Path(
            processed_dir
        )
        / "transacoes_rejeitadas.csv",
    ]

    database_path = Path(
        database_path
    )

    return {
        "source_files": len(
            find_user_source_files(
                Path(
                    raw_dir
                )
            )
        ),
        "processed_files": sum(
            file_path.exists()
            for file_path
            in processed_files
        ),
        "transaction_rows": (
            count_user_transaction_rows(
                database_path=database_path,
                user_id=user_id,
            )
        ),
        "database_exists": (
            database_path.exists()
        ),
        "log_exists": (
            Path(
                log_path
            ).exists()
        ),
    }


def reset_user_transaction_data(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    database_path: Path = DATABASE_PATH,
    log_path: Path = LOG_PATH,
    user_id: str = LOCAL_USER_ID,
) -> dict[str, int | bool]:
    """Remove somente as transações reais do usuário."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    raw_dir = Path(
        raw_dir
    )

    processed_dir = Path(
        processed_dir
    )

    database_path = Path(
        database_path
    )

    log_path = Path(
        log_path
    )

    source_files = (
        find_user_source_files(
            raw_dir
        )
    )

    source_files_removed = 0

    for source_file in source_files:
        if _remove_file(
            source_file
        ):
            source_files_removed += 1

    processed_files = [
        processed_dir
        / "transacoes_processadas.csv",
        processed_dir
        / "transacoes_rejeitadas.csv",
    ]

    processed_files_removed = 0

    for processed_file in processed_files:
        if _remove_file(
            processed_file
        ):
            processed_files_removed += 1

    transaction_rows_removed = (
        delete_transactions(
            database_path=database_path,
            table_name=(
                TRANSACTION_TABLE_NAME
            ),
            user_id=normalized_user_id,
            data_mode=USER_DATA_MODE,
        )
    )

    # Fecha handlers antes de remover o log no Windows.
    logging.shutdown()

    log_removed = _remove_file(
        log_path
    )

    return {
        "source_files_removed": (
            source_files_removed
        ),
        "processed_files_removed": (
            processed_files_removed
        ),
        "transaction_rows_removed": (
            transaction_rows_removed
        ),
        "database_preserved": (
            database_path.exists()
        ),
        "log_removed": (
            log_removed
        ),
    }
    
def delete_user_financial_data(
    database_path: Path = DATABASE_PATH,
    user_id: str = LOCAL_USER_ID,
) -> dict[str, int | bool]:
    """Remove os dados financeiros e preserva a conta."""
    normalized_user_id = _normalize_user_id(
        user_id
    )

    database_path = Path(
        database_path
    )

    result: dict[str, int | bool] = {
        "transaction_rows_removed": 0,
        "profile_rows_removed": 0,
        "goal_rows_removed": 0,
        "goal_seed_rows_removed": 0,
        "budget_rows_removed": 0,
        "chat_rows_removed": 0,
        "database_preserved": database_path.exists(),
    }

    if not database_path.exists():
        return result

    try:
        with sqlite3.connect(
            database_path,
            timeout=5.0,
        ) as connection:
            result["transaction_rows_removed"] = _delete_user_rows(
                connection,
                TRANSACTION_TABLE_NAME,
                normalized_user_id,
                data_mode=USER_DATA_MODE,
            )

            result["profile_rows_removed"] = _delete_user_rows(
                connection,
                PROFILE_TABLE_NAME,
                normalized_user_id,
            )

            result["goal_rows_removed"] = _delete_user_rows(
                connection,
                GOAL_TABLE_NAME,
                normalized_user_id,
            )

            result["goal_seed_rows_removed"] = _delete_user_rows(
                connection,
                GOAL_SEED_TABLE_NAME,
                normalized_user_id,
            )

            result["budget_rows_removed"] = _delete_user_rows(
                connection,
                BUDGET_TABLE_NAME,
                normalized_user_id,
            )

            result["chat_rows_removed"] = _delete_user_rows(
                connection,
                CHAT_TABLE_NAME,
                normalized_user_id,
                data_mode=USER_DATA_MODE,
            )

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível apagar os dados financeiros do usuário."
        ) from error

    return result