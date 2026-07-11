"""Consulta e limpeza segura dos dados locais do usuário."""

from __future__ import annotations

import logging
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

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


def _remove_file(
    file_path: Path,
) -> bool:
    """Remove um arquivo e informa se ele existia."""
    if not file_path.exists():
        return False

    file_path.unlink()

    return True


def find_user_source_files(
    raw_dir: Path = RAW_DIR,
) -> list[Path]:
    """Localiza as fontes reais de transações do usuário."""
    if not raw_dir.exists():
        return []

    return sorted(
        raw_dir.rglob(
            "transacoes_*.csv"
        )
    )


def summarize_user_transaction_data(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    database_path: Path = DATABASE_PATH,
    log_path: Path = LOG_PATH,
) -> dict[str, int | bool]:
    """Resume os dados locais existentes no FinanTec."""
    processed_files = [
        processed_dir
        / "transacoes_processadas.csv",
        processed_dir
        / "transacoes_rejeitadas.csv",
    ]

    return {
        "source_files": len(
            find_user_source_files(
                raw_dir
            )
        ),
        "processed_files": sum(
            file_path.exists()
            for file_path in processed_files
        ),
        "database_exists": (
            database_path.exists()
        ),
        "log_exists": (
            log_path.exists()
        ),
    }


def reset_user_transaction_data(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    database_path: Path = DATABASE_PATH,
    log_path: Path = LOG_PATH,
) -> dict[str, int | bool]:
    """Remove dados do usuário sem apagar a demonstração."""
    source_files = (
        find_user_source_files(
            raw_dir
        )
    )

    source_files_removed = 0

    for source_file in source_files:
        if _remove_file(source_file):
            source_files_removed += 1

    processed_files = [
        processed_dir
        / "transacoes_processadas.csv",
        processed_dir
        / "transacoes_rejeitadas.csv",
    ]

    processed_files_removed = 0

    for processed_file in processed_files:
        if _remove_file(processed_file):
            processed_files_removed += 1

    database_removed = _remove_file(
        database_path
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
        "database_removed": database_removed,
        "log_removed": log_removed,
    }