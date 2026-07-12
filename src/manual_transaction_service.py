"""Regras e persistência das transações manuais."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
    create_transaction_id,
    ensure_transaction_ids,
)
from src.transaction_validation import (
    split_transactions_by_validity,
)


MANUAL_TRANSACTION_COLUMNS = [
    "data",
    "tipo",
    "descricao",
    "categoria",
    "valor",
]

STORED_TRANSACTION_COLUMNS = [
    TRANSACTION_ID_COLUMN,
    *MANUAL_TRANSACTION_COLUMNS,
]


def build_manual_transaction_source_key(
    source_file: Path,
    project_root: Path,
) -> str:
    """Cria uma identificação estável para a fonte manual."""
    try:
        return (
            source_file.resolve()
            .relative_to(
                project_root.resolve()
            )
            .as_posix()
        )

    except ValueError:
        # Arquivos temporários dos testes podem
        # ficar fora da pasta principal do projeto.
        return source_file.name


def create_empty_manual_transactions() -> pd.DataFrame:
    """Cria uma tabela vazia com o contrato de armazenamento."""
    return pd.DataFrame(
        columns=(
            STORED_TRANSACTION_COLUMNS
        )
    )


def identify_manual_transactions(
    transactions: pd.DataFrame,
    source_file: Path,
    project_root: Path,
) -> pd.DataFrame:
    """Preserva IDs existentes e identifica linhas antigas."""
    identified_transactions = (
        transactions.copy()
    )

    for column in MANUAL_TRANSACTION_COLUMNS:
        if column not in identified_transactions.columns:
            identified_transactions[column] = ""

    if (
        TRANSACTION_ID_COLUMN
        not in identified_transactions.columns
    ):
        identified_transactions[
            TRANSACTION_ID_COLUMN
        ] = ""

    identified_transactions = (
        ensure_transaction_ids(
            transactions=identified_transactions,
            source_key=(
                build_manual_transaction_source_key(
                    source_file=source_file,
                    project_root=project_root,
                )
            ),
            identity_columns=(
                MANUAL_TRANSACTION_COLUMNS
            ),
        )
    )

    return (
        identified_transactions[
            STORED_TRANSACTION_COLUMNS
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


def load_manual_transactions(
    source_file: Path,
    project_root: Path,
) -> pd.DataFrame:
    """Carrega transações manuais preservando seus IDs."""
    if not source_file.exists():
        return (
            create_empty_manual_transactions()
        )

    transactions = pd.read_csv(
        source_file,
        encoding="utf-8-sig",
    )

    identified_transactions = (
        identify_manual_transactions(
            transactions=transactions,
            source_file=source_file,
            project_root=project_root,
        )
    )

    identified_transactions["data"] = (
        pd.to_datetime(
            identified_transactions["data"],
            errors="coerce",
        )
    )

    return identified_transactions


def prepare_manual_transactions_for_storage(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Normaliza dados manuais antes da validação ou gravação."""
    prepared_transactions = (
        transactions.copy()
    )

    for column in MANUAL_TRANSACTION_COLUMNS:
        if column not in prepared_transactions.columns:
            prepared_transactions[column] = ""

    if (
        TRANSACTION_ID_COLUMN
        not in prepared_transactions.columns
    ):
        prepared_transactions[
            TRANSACTION_ID_COLUMN
        ] = ""

    prepared_transactions = (
        prepared_transactions[
            STORED_TRANSACTION_COLUMNS
        ].copy()
    )

    prepared_transactions[
        TRANSACTION_ID_COLUMN
    ] = (
        prepared_transactions[
            TRANSACTION_ID_COLUMN
        ]
        .astype("string")
        .fillna("")
        .str.strip()
    )

    prepared_transactions["data"] = (
        pd.to_datetime(
            prepared_transactions["data"],
            errors="coerce",
        )
        .dt.strftime("%Y-%m-%d")
        .fillna("")
    )

    prepared_transactions["tipo"] = (
        prepared_transactions["tipo"]
        .astype("string")
        .fillna("")
        .str.strip()
        .str.lower()
    )

    prepared_transactions["descricao"] = (
        prepared_transactions["descricao"]
        .astype("string")
        .fillna("")
        .str.strip()
    )

    prepared_transactions["categoria"] = (
        prepared_transactions["categoria"]
        .astype("string")
        .fillna("")
        .str.strip()
    )

    prepared_transactions["valor"] = (
        pd.to_numeric(
            prepared_transactions["valor"],
            errors="coerce",
        )
    )

    return prepared_transactions


def validate_manual_transactions(
    transactions: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Valida transações manuais usando as regras do ETL."""
    prepared_transactions = (
        prepare_manual_transactions_for_storage(
            transactions
        )
    )

    prepared_transactions = (
        prepared_transactions.dropna(
            how="all",
            subset=(
                MANUAL_TRANSACTION_COLUMNS
            ),
        )
    )

    if prepared_transactions.empty:
        return (
            prepared_transactions,
            pd.DataFrame(),
        )

    return split_transactions_by_validity(
        prepared_transactions
    )


def save_manual_transactions(
    transactions: pd.DataFrame,
    source_file: Path,
    project_root: Path,
) -> None:
    """Salva transações manuais com IDs persistentes."""
    source_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    transactions_to_save = (
        prepare_manual_transactions_for_storage(
            transactions
        )
    )

    transactions_to_save = (
        identify_manual_transactions(
            transactions=transactions_to_save,
            source_file=source_file,
            project_root=project_root,
        )
    )

    transactions_to_save.to_csv(
        source_file,
        index=False,
        encoding="utf-8-sig",
    )


def clear_manual_transactions(
    source_file: Path,
) -> None:
    """Remove o arquivo de transações manuais."""
    if source_file.exists():
        source_file.unlink()


def add_pending_transaction(
    transactions: pd.DataFrame,
    transaction: dict,
) -> pd.DataFrame:
    """Adiciona uma transação identificada ao rascunho."""
    current_transactions = (
        transactions.copy()
    )

    for column in STORED_TRANSACTION_COLUMNS:
        if column not in current_transactions.columns:
            current_transactions[column] = ""

    current_transactions = (
        current_transactions[
            STORED_TRANSACTION_COLUMNS
        ].copy()
    )

    new_transaction_data = {
        column: transaction.get(
            column,
            "",
        )
        for column in (
            STORED_TRANSACTION_COLUMNS
        )
    }

    if not new_transaction_data[
        TRANSACTION_ID_COLUMN
    ]:
        new_transaction_data[
            TRANSACTION_ID_COLUMN
        ] = create_transaction_id()

    new_transaction = pd.DataFrame(
        [
            new_transaction_data
        ],
        columns=(
            STORED_TRANSACTION_COLUMNS
        ),
    )

    return pd.concat(
        [
            current_transactions,
            new_transaction,
        ],
        ignore_index=True,
    )


def update_pending_transaction(
    transactions: pd.DataFrame,
    index: int,
    transaction: dict,
) -> pd.DataFrame:
    """Atualiza dados sem alterar o ID da transação."""
    if (
        index < 0
        or index >= len(transactions)
    ):
        raise IndexError(
            "Índice de transação inválido."
        )

    updated_transactions = (
        transactions.copy()
    )

    for column in STORED_TRANSACTION_COLUMNS:
        if column not in updated_transactions.columns:
            updated_transactions[column] = ""

    updated_transactions = (
        updated_transactions[
            STORED_TRANSACTION_COLUMNS
        ].copy()
    )

    for column in MANUAL_TRANSACTION_COLUMNS:
        updated_transactions.loc[
            index,
            column,
        ] = transaction[column]

    return (
        updated_transactions
        .reset_index(
            drop=True
        )
    )


def remove_pending_transaction(
    transactions: pd.DataFrame,
    index: int,
) -> pd.DataFrame:
    """Remove uma transação do rascunho."""
    if (
        index < 0
        or index >= len(transactions)
    ):
        raise IndexError(
            "Índice de transação inválido."
        )

    return (
        transactions
        .drop(
            index=index
        )
        .reset_index(
            drop=True
        )
    )