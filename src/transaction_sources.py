"""Operações sobre os arquivos-fonte de transações."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd

from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
    ensure_transaction_ids,
    is_valid_transaction_id,
    normalize_transaction_id,
)
from src.transaction_validation import (
    REQUIRED_TRANSACTION_COLUMNS,
    split_transactions_by_validity,
    validate_required_columns,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


class TransactionNotFoundError(LookupError):
    """Indica que uma transação não existe nas fontes pesquisadas."""


class DuplicateTransactionIdError(RuntimeError):
    """Indica que o mesmo ID foi encontrado em mais de uma linha."""


@dataclass(frozen=True)
class TransactionSourceMatch:
    """Representa a localização de uma transação em um arquivo."""

    source_file: Path
    row_index: int


def build_transaction_source_key(
    source_file: Path,
    project_root: Path = PROJECT_ROOT,
) -> str:
    """Cria uma identificação estável para um arquivo de origem."""
    try:
        return (
            source_file.resolve()
            .relative_to(
                project_root.resolve()
            )
            .as_posix()
        )

    except ValueError:
        # Arquivos temporários usados nos testes podem
        # estar fora do diretório principal do projeto.
        return source_file.name


def list_transaction_source_files(
    source_dir: Path = RAW_DIR,
) -> list[Path]:
    """Lista os arquivos de transação existentes na fonte."""
    if not source_dir.exists():
        return []

    return sorted(
        source_dir.rglob(
            "transacoes_*.csv"
        )
    )


def read_transaction_source(
    source_file: Path,
) -> pd.DataFrame:
    """Lê e valida estruturalmente um arquivo-fonte."""
    transactions = pd.read_csv(
        source_file,
        encoding="utf-8-sig",
    )

    validate_required_columns(
        transactions,
        source_file,
    )

    return transactions


def write_transaction_source(
    source_file: Path,
    transactions: pd.DataFrame,
) -> None:
    """Salva um arquivo-fonte mantendo seu contrato interno."""
    source_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ordered_columns = [
        TRANSACTION_ID_COLUMN,
        *[
            column
            for column in transactions.columns
            if column != TRANSACTION_ID_COLUMN
        ],
    ]

    transactions_to_save = (
        transactions[
            ordered_columns
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    transactions_to_save.to_csv(
        source_file,
        index=False,
        encoding="utf-8-sig",
    )


def ensure_source_transaction_ids(
    source_file: Path,
    project_root: Path = PROJECT_ROOT,
) -> tuple[pd.DataFrame, bool]:
    """Adiciona IDs ausentes e informa se o arquivo foi alterado."""
    transactions = read_transaction_source(
        source_file
    )

    had_id_column = (
        TRANSACTION_ID_COLUMN
        in transactions.columns
    )

    if had_id_column:
        previous_ids = [
            (
                normalize_transaction_id(
                    value
                )
                if is_valid_transaction_id(
                    value
                )
                else ""
            )
            for value in transactions[
                TRANSACTION_ID_COLUMN
            ]
        ]

    else:
        previous_ids = []

    identified_transactions = (
        ensure_transaction_ids(
            transactions=transactions,
            source_key=(
                build_transaction_source_key(
                    source_file,
                    project_root=project_root,
                )
            ),
            identity_columns=(
                REQUIRED_TRANSACTION_COLUMNS
            ),
        )
    )

    current_ids = (
        identified_transactions[
            TRANSACTION_ID_COLUMN
        ]
        .astype(str)
        .tolist()
    )

    source_changed = (
        not had_id_column
        or previous_ids != current_ids
    )

    if source_changed:
        write_transaction_source(
            source_file,
            identified_transactions,
        )

    return (
        identified_transactions,
        source_changed,
    )


def migrate_transaction_source_ids(
    source_dir: Path = RAW_DIR,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, int]:
    """Persiste IDs nos arquivos antigos que ainda não os possuem."""
    files_scanned = 0
    files_updated = 0
    transactions_identified = 0

    for source_file in (
        list_transaction_source_files(
            source_dir
        )
    ):
        (
            identified_transactions,
            source_changed,
        ) = ensure_source_transaction_ids(
            source_file,
            project_root=project_root,
        )

        files_scanned += 1

        transactions_identified += len(
            identified_transactions
        )

        if source_changed:
            files_updated += 1

    return {
        "files_scanned": files_scanned,
        "files_updated": files_updated,
        "transactions_identified": (
            transactions_identified
        ),
    }


def find_transaction_source(
    transaction_id: str,
    source_dir: Path = RAW_DIR,
    project_root: Path = PROJECT_ROOT,
) -> TransactionSourceMatch:
    """Localiza uma transação pelo ID nos arquivos reais."""
    normalized_id = (
        normalize_transaction_id(
            transaction_id
        )
    )

    matches: list[
        TransactionSourceMatch
    ] = []

    for source_file in (
        list_transaction_source_files(
            source_dir
        )
    ):
        transactions, _ = (
            ensure_source_transaction_ids(
                source_file,
                project_root=project_root,
            )
        )

        matching_rows = (
            transactions.index[
                transactions[
                    TRANSACTION_ID_COLUMN
                ].astype(str)
                == normalized_id
            ]
            .tolist()
        )

        for row_index in matching_rows:
            matches.append(
                TransactionSourceMatch(
                    source_file=source_file,
                    row_index=int(
                        row_index
                    ),
                )
            )

    if not matches:
        raise TransactionNotFoundError(
            "A transação informada não foi encontrada "
            "nos arquivos do usuário."
        )

    if len(matches) > 1:
        raise DuplicateTransactionIdError(
            "O mesmo transaction_id foi encontrado "
            "em mais de uma linha."
        )

    return matches[0]


def _build_rejection_message(
    rejected_transactions: pd.DataFrame,
) -> str:
    """Cria uma mensagem com os erros da atualização."""
    if (
        rejected_transactions.empty
        or "motivo_rejeicao"
        not in rejected_transactions.columns
    ):
        return (
            "Os novos dados da transação são inválidos."
        )

    reasons = (
        rejected_transactions[
            "motivo_rejeicao"
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

    if not reasons:
        return (
            "Os novos dados da transação são inválidos."
        )

    return "; ".join(
        reasons
    )


def update_transaction_in_source(
    transaction_id: str,
    updates: Mapping[str, object],
    source_dir: Path = RAW_DIR,
    project_root: Path = PROJECT_ROOT,
) -> Path:
    """Atualiza uma transação sem alterar seu identificador."""
    if not updates:
        raise ValueError(
            "Nenhum campo foi informado para atualização."
        )

    invalid_columns = sorted(
        set(updates)
        - set(
            REQUIRED_TRANSACTION_COLUMNS
        )
    )

    if invalid_columns:
        raise ValueError(
            "Campos não permitidos na atualização: "
            f"{', '.join(invalid_columns)}"
        )

    normalized_id = (
        normalize_transaction_id(
            transaction_id
        )
    )

    match = find_transaction_source(
        transaction_id=normalized_id,
        source_dir=source_dir,
        project_root=project_root,
    )

    transactions, _ = (
        ensure_source_transaction_ids(
            match.source_file,
            project_root=project_root,
        )
    )

    candidate = (
    transactions.loc[
        [
            match.row_index
        ],
        REQUIRED_TRANSACTION_COLUMNS,
    ]
    .copy()
    .astype("object")
    )

    for column, value in (
        updates.items()
    ):
        candidate.loc[
            match.row_index,
            column,
        ] = value
    (
        valid_transactions,
        rejected_transactions,
    ) = split_transactions_by_validity(
        candidate
    )

    if not rejected_transactions.empty:
        raise ValueError(
            _build_rejection_message(
                rejected_transactions
            )
        )

    prepared_transaction = (
        valid_transactions.iloc[0]
    )

    for column in (
        REQUIRED_TRANSACTION_COLUMNS
    ):
        value = prepared_transaction[
            column
        ]

        if column == "data":
            value = pd.Timestamp(
                value
            ).strftime(
                "%Y-%m-%d"
            )

        transactions.loc[
            match.row_index,
            column,
        ] = value

    transactions.loc[
        match.row_index,
        TRANSACTION_ID_COLUMN,
    ] = normalized_id

    write_transaction_source(
        match.source_file,
        transactions,
    )
    
    

    return match.source_file


def delete_transaction_from_source(
    transaction_id: str,
    source_dir: Path = RAW_DIR,
    project_root: Path = PROJECT_ROOT,
) -> Path:
    """Exclui uma transação pelo ID no arquivo de origem."""
    normalized_id = (
        normalize_transaction_id(
            transaction_id
        )
    )

    match = find_transaction_source(
        transaction_id=normalized_id,
        source_dir=source_dir,
        project_root=project_root,
    )

    transactions, _ = (
        ensure_source_transaction_ids(
            match.source_file,
            project_root=project_root,
        )
    )

    remaining_transactions = (
        transactions.drop(
            index=match.row_index
        )
        .reset_index(
            drop=True
        )
    )

    write_transaction_source(
        match.source_file,
        remaining_transactions,
    )

    return match.source_file