"""Persistência direta de importações no SQLite."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
    create_transaction_id,
)
from src.transaction_repository import (
    PERSISTED_TRANSACTION_COLUMNS,
    insert_transactions,
)
from src.transaction_validation import (
    REQUIRED_TRANSACTION_COLUMNS,
    build_rejection_message,
    prepare_valid_transactions_for_database,
    split_transactions_by_validity,
)
from src.user_context import (
    LOCAL_USER_ID,
)


IMPORT_DATABASE_SOURCE = (
    "database:import"
)


def prepare_imported_transactions_for_database(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Prepara um lote importado para inserção direta."""
    if transactions.empty:
        return pd.DataFrame(
            columns=(
                PERSISTED_TRANSACTION_COLUMNS
            )
        )

    (
        valid_transactions,
        rejected_transactions,
    ) = split_transactions_by_validity(
        transactions
    )

    if not rejected_transactions.empty:
        raise ValueError(
            build_rejection_message(
                rejected_transactions,
                default_message=(
                    "O lote importado possui "
                    "dados inválidos."
                ),
            )
        )

    prepared_transactions = (
        valid_transactions[
            REQUIRED_TRANSACTION_COLUMNS
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    prepared_transactions.insert(
        0,
        TRANSACTION_ID_COLUMN,
        [
            create_transaction_id()
            for _ in range(
                len(
                    prepared_transactions
                )
            )
        ],
    )

    prepared_transactions = (
        prepare_valid_transactions_for_database(
            prepared_transactions,
            source=IMPORT_DATABASE_SOURCE,
        )
    )

    return (
        prepared_transactions[
            PERSISTED_TRANSACTION_COLUMNS
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


def save_imported_transactions_to_database(
    transactions: pd.DataFrame,
    database_path: Path,
    table_name: str,
    user_id: str = LOCAL_USER_ID,
) -> int:
    """Insere diretamente no SQLite as linhas selecionadas."""
    prepared_transactions = (
        prepare_imported_transactions_for_database(
            transactions
        )
    )

    if prepared_transactions.empty:
        return 0

    return insert_transactions(
        transactions=prepared_transactions,
        database_path=database_path,
        table_name=table_name,
        user_id=user_id,
        data_mode="user",
    )