"""Persistência direta das transações manuais no SQLite."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.manual_transaction_service import (
    MANUAL_TRANSACTION_COLUMNS,
    validate_manual_transactions,
)
from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
    ensure_transaction_ids,
)
from src.transaction_repository import (
    PERSISTED_TRANSACTION_COLUMNS,
    insert_transactions,
    load_transactions,
    update_transaction,
)
from src.transaction_validation import (
    build_rejection_message,
    prepare_valid_transactions_for_database,
)
from src.user_context import (
    LOCAL_USER_ID,
)


MANUAL_DATABASE_SOURCE = (
    "database:manual"
)

def _normalize_transaction_ids(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Garante IDs válidos e únicos no lote manual."""
    identified_transactions = (
        ensure_transaction_ids(
            transactions=transactions,
            source_key=(
                MANUAL_DATABASE_SOURCE
            ),
            identity_columns=(
                MANUAL_TRANSACTION_COLUMNS
            ),
        )
    )

    transaction_ids = (
        identified_transactions[
            TRANSACTION_ID_COLUMN
        ]
        .astype("string")
        .fillna("")
        .str.strip()
    )

    if transaction_ids.eq("").any():
        raise ValueError(
            "Uma ou mais transações não possuem "
            "um identificador válido."
        )

    if transaction_ids.duplicated().any():
        raise ValueError(
            "O rascunho possui "
            "transaction_id duplicado."
        )

    identified_transactions[
        TRANSACTION_ID_COLUMN
    ] = transaction_ids

    return identified_transactions


def prepare_manual_transactions_for_database(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Prepara o rascunho para persistência direta."""
    if transactions.empty:
        return pd.DataFrame(
            columns=(
                PERSISTED_TRANSACTION_COLUMNS
            )
        )

    (
        valid_transactions,
        rejected_transactions,
    ) = validate_manual_transactions(
        transactions
    )

    if not rejected_transactions.empty:
        raise ValueError(
            build_rejection_message(
                rejected_transactions,
                default_message=(
                    "As transações manuais possuem "
                    "dados inválidos."
                ),
            )
        )

    identified_transactions = (
        _normalize_transaction_ids(
            valid_transactions
        )
    )

    prepared_transactions = (
        prepare_valid_transactions_for_database(
            identified_transactions,
            source=MANUAL_DATABASE_SOURCE,
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


def _get_existing_transaction_ids(
    existing_transactions: pd.DataFrame,
) -> set[str]:
    """Retorna os IDs já persistidos pelo usuário."""
    if (
        existing_transactions.empty
        or TRANSACTION_ID_COLUMN
        not in existing_transactions.columns
    ):
        return set()

    return set(
        existing_transactions[
            TRANSACTION_ID_COLUMN
        ]
        .astype("string")
        .fillna("")
        .str.strip()
        .tolist()
    )

def _update_existing_manual_transactions(
    transactions: pd.DataFrame,
    *,
    database_path: Path,
    table_name: str,
    user_id: str,
) -> int:
    """Atualiza transações manuais que já existem no banco."""
    updated_count = 0

    for _, transaction in (
        transactions.iterrows()
    ):
        transaction_id = str(
            transaction[
                TRANSACTION_ID_COLUMN
            ]
        ).strip()

        update_transaction(
            database_path=database_path,
            table_name=table_name,
            transaction_id=transaction_id,
            user_id=user_id,
            data_mode="user",
            updates={
                "data": str(
                    transaction["data"]
                ),
                "tipo": str(
                    transaction["tipo"]
                ),
                "descricao": str(
                    transaction["descricao"]
                ),
                "categoria": str(
                    transaction["categoria"]
                ),
                "valor": float(
                    transaction["valor"]
                ),
                "arquivo_origem": (
                    MANUAL_DATABASE_SOURCE
                ),
                "ano_mes": str(
                    transaction["ano_mes"]
                ),
            },
        )

        updated_count += 1

    return updated_count


def save_manual_transactions_to_database(
    transactions: pd.DataFrame,
    database_path: Path,
    table_name: str,
    user_id: str = LOCAL_USER_ID,
) -> dict[str, int]:
    """Insere transações novas e atualiza IDs existentes."""
    prepared_transactions = (
        prepare_manual_transactions_for_database(
            transactions
        )
    )

    if prepared_transactions.empty:
        return {
            "inserted": 0,
            "updated": 0,
            "total": 0,
        }

    existing_transactions = (
        load_transactions(
            database_path=database_path,
            table_name=table_name,
            user_id=user_id,
            data_mode="user",
        )
    )

    existing_ids = (
        _get_existing_transaction_ids(
            existing_transactions
        )
    )

    incoming_ids = (
        prepared_transactions[
            TRANSACTION_ID_COLUMN
        ]
        .astype("string")
        .fillna("")
        .str.strip()
    )

    existing_rows = (
        prepared_transactions.loc[
            incoming_ids.isin(
                existing_ids
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    new_rows = (
        prepared_transactions.loc[
            ~incoming_ids.isin(
                existing_ids
            )
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    updated_count = (
        _update_existing_manual_transactions(
            existing_rows,
            database_path=database_path,
            table_name=table_name,
            user_id=user_id,
        )
    )

    inserted_count = (
        insert_transactions(
            transactions=new_rows,
            database_path=database_path,
            table_name=table_name,
            user_id=user_id,
            data_mode="user",
        )
    )

    return {
        "inserted": int(
            inserted_count
        ),
        "updated": int(
            updated_count
        ),
        "total": int(
            len(
                prepared_transactions
            )
        ),
    }