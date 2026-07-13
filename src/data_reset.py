"""Consulta e limpeza segura dos dados locais do usuário."""

from __future__ import annotations

import logging
from pathlib import Path

from src.transaction_repository import (
    delete_transactions,
    load_transactions,
)
from src.user_context import (
    LOCAL_USER_ID,
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