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
    split_transactions_by_validity,
)
from src.user_context import (
    LOCAL_USER_ID,
)


IMPORT_DATABASE_SOURCE = (
    "database:import"
)


def _build_rejection_message(
    rejected_transactions: pd.DataFrame,
) -> str:
    """Monta uma mensagem com os erros encontrados."""
    if (
        rejected_transactions.empty
        or "motivo_rejeicao"
        not in rejected_transactions.columns
    ):
        return (
            "O lote importado possui dados inválidos."
        )

    reasons = (
        rejected_transactions[
            "motivo_rejeicao"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if not reasons:
        return (
            "O lote importado possui dados inválidos."
        )

    return "; ".join(
        reasons
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
            _build_rejection_message(
                rejected_transactions
            )
        )

    prepared = (
        valid_transactions[
            REQUIRED_TRANSACTION_COLUMNS
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    prepared.insert(
        0,
        TRANSACTION_ID_COLUMN,
        [
            create_transaction_id()
            for _ in range(
                len(
                    prepared
                )
            )
        ],
    )

    prepared["data"] = pd.to_datetime(
        prepared["data"],
        errors="coerce",
    )

    if prepared["data"].isna().any():
        raise ValueError(
            "Uma ou mais transações possuem "
            "data inválida."
        )

    prepared["tipo"] = (
        prepared["tipo"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    prepared["descricao"] = (
        prepared["descricao"]
        .astype("string")
        .str.strip()
    )

    prepared["categoria"] = (
        prepared["categoria"]
        .astype("string")
        .str.strip()
    )

    prepared["valor"] = pd.to_numeric(
        prepared["valor"],
        errors="coerce",
    )

    if (
        prepared["valor"].isna().any()
        or prepared["valor"].le(0).any()
    ):
        raise ValueError(
            "Uma ou mais transações possuem "
            "valor inválido."
        )

    prepared[
        "arquivo_origem"
    ] = IMPORT_DATABASE_SOURCE

    prepared["ano_mes"] = (
        prepared["data"]
        .dt.to_period(
            "M"
        )
        .astype(str)
    )

    prepared["data"] = (
        prepared["data"]
        .dt.strftime(
            "%Y-%m-%d"
        )
    )

    return (
        prepared[
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