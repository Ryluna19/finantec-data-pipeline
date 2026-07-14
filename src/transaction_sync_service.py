"""Sincronização temporária entre arquivos-fonte e SQLite."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import pandas as pd

from src.transaction_repository import (
    TransactionNotFoundError as DatabaseTransactionNotFoundError,
    delete_transaction as delete_transaction_from_database,
    load_transaction as load_transaction_from_database,
    update_transaction as update_transaction_in_database,
)
from src.transaction_sources import (
    PROJECT_ROOT,
    RAW_DIR,
    TransactionNotFoundError,
    delete_transaction_from_source,
    update_transaction_in_source,
)
from src.transaction_validation import (
    REQUIRED_TRANSACTION_COLUMNS,
    split_transactions_by_validity,
)


class PartialTransactionSyncError(
    RuntimeError
):
    """Indica que apenas uma das fontes foi alterada."""


def _build_rejection_message(
    rejected_transactions: pd.DataFrame,
) -> str:
    """Monta uma mensagem com os erros da transação."""
    if (
        rejected_transactions.empty
        or "motivo_rejeicao"
        not in rejected_transactions.columns
    ):
        return (
            "Os dados informados para a transação "
            "não são válidos."
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
            "Os dados informados para a transação "
            "não são válidos."
        )

    return "; ".join(
        reasons
    )


def prepare_persisted_transaction_updates(
    updates: Mapping[str, object],
) -> dict[str, object]:
    """Valida e normaliza uma atualização persistida."""
    missing_columns = [
        column
        for column
        in REQUIRED_TRANSACTION_COLUMNS
        if column not in updates
    ]

    if missing_columns:
        raise ValueError(
            "Campos obrigatórios ausentes: "
            + ", ".join(
                missing_columns
            )
        )

    candidate = pd.DataFrame(
        [
            {
                column: updates[
                    column
                ]
                for column
                in REQUIRED_TRANSACTION_COLUMNS
            }
        ]
    )

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

    prepared = (
        valid_transactions.iloc[
            0
        ]
    )

    transaction_date = pd.Timestamp(
        prepared["data"]
    )

    return {
        "data": transaction_date.strftime(
            "%Y-%m-%d"
        ),
        "tipo": str(
            prepared["tipo"]
        ).strip().lower(),
        "descricao": str(
            prepared["descricao"]
        ).strip(),
        "categoria": str(
            prepared["categoria"]
        ).strip(),
        "valor": float(
            prepared["valor"]
        ),
        "ano_mes": str(
            transaction_date.to_period(
                "M"
            )
        ),
    }


def _is_database_source(
    source_name: str,
) -> bool:
    """Informa se a transação existe somente no banco."""
    return source_name.startswith(
        "database:"
    )


def _get_database_source_after_update(
    source_name: str,
    source_file: Path | None,
) -> str:
    """Mantém ou atualiza a identificação da fonte persistida."""
    if _is_database_source(
        source_name
    ):
        return source_name

    if source_file is not None:
        return source_name

    return "database:migrated"


def update_persisted_transaction(
    *,
    transaction_id: str,
    updates: Mapping[str, object],
    database_path: Path,
    table_name: str,
    user_id: str,
    data_mode: str = "user",
    source_dir: Path = RAW_DIR,
    project_root: Path = PROJECT_ROOT,
) -> Path | None:
    """Atualiza a transação no SQLite e, quando existir, no arquivo."""
    if data_mode != "user":
        raise ValueError(
            "Somente transações reais podem ser editadas."
        )

    prepared_updates = (
        prepare_persisted_transaction_updates(
            updates
        )
    )

    stored_transaction = (
        load_transaction_from_database(
            database_path=database_path,
            table_name=table_name,
            transaction_id=transaction_id,
            user_id=user_id,
            data_mode=data_mode,
        )
    )

    if stored_transaction is None:
        raise TransactionNotFoundError(
            "A transação informada não foi encontrada."
        )

    source_name = str(
        stored_transaction.get(
            "arquivo_origem",
            "",
        )
        or ""
    ).strip()

    source_file: Path | None = None

    if not _is_database_source(
        source_name
    ):
        source_updates = {
            column: prepared_updates[
                column
            ]
            for column
            in REQUIRED_TRANSACTION_COLUMNS
        }

        try:
            source_file = (
                update_transaction_in_source(
                    transaction_id=transaction_id,
                    updates=source_updates,
                    source_dir=source_dir,
                    project_root=project_root,
                )
            )

        except TransactionNotFoundError:
            # Arquivos antigos podem ter sido removidos.
            # Nesse caso, o banco assume a fonte principal.
            source_file = None

    updated_source_name = (
        _get_database_source_after_update(
            source_name=source_name,
            source_file=source_file,
        )
    )

    try:
        update_transaction_in_database(
            database_path=database_path,
            table_name=table_name,
            transaction_id=transaction_id,
            updates={
                **prepared_updates,
                "arquivo_origem": (
                    updated_source_name
                ),
            },
            user_id=user_id,
            data_mode=data_mode,
        )

    except DatabaseTransactionNotFoundError as error:
        if source_file is not None:
            raise PartialTransactionSyncError(
                "O arquivo de origem foi atualizado, "
                "mas a transação não foi encontrada no SQLite. "
                f"Fonte alterada: {source_file.name}."
            ) from error

        raise TransactionNotFoundError(
            "A transação informada não foi encontrada."
        ) from error

    except Exception as error:
        if source_file is not None:
            raise PartialTransactionSyncError(
                "O arquivo de origem foi atualizado, "
                "mas o SQLite não pôde ser sincronizado. "
                f"Fonte alterada: {source_file.name}. "
                f"Detalhes: {error}"
            ) from error

        raise

    return source_file


def delete_persisted_transaction(
    *,
    transaction_id: str,
    database_path: Path,
    table_name: str,
    user_id: str,
    data_mode: str = "user",
    source_dir: Path = RAW_DIR,
    project_root: Path = PROJECT_ROOT,
) -> Path | None:
    """Exclui a transação do SQLite e do arquivo quando necessário."""
    if data_mode != "user":
        raise ValueError(
            "Somente transações reais podem ser excluídas."
        )

    stored_transaction = (
        load_transaction_from_database(
            database_path=database_path,
            table_name=table_name,
            transaction_id=transaction_id,
            user_id=user_id,
            data_mode=data_mode,
        )
    )

    if stored_transaction is None:
        raise TransactionNotFoundError(
            "A transação informada não foi encontrada."
        )

    source_name = str(
        stored_transaction.get(
            "arquivo_origem",
            "",
        )
        or ""
    ).strip()

    source_file: Path | None = None

    if not _is_database_source(
        source_name
    ):
        try:
            source_file = (
                delete_transaction_from_source(
                    transaction_id=transaction_id,
                    source_dir=source_dir,
                    project_root=project_root,
                )
            )

        except TransactionNotFoundError:
            # O arquivo pode já ter sido removido.
            # A exclusão no banco ainda deve continuar.
            source_file = None

    try:
        deleted = (
            delete_transaction_from_database(
                database_path=database_path,
                table_name=table_name,
                transaction_id=transaction_id,
                user_id=user_id,
                data_mode=data_mode,
            )
        )

    except Exception as error:
        if source_file is not None:
            raise PartialTransactionSyncError(
                "A transação foi removida do arquivo, "
                "mas não pôde ser excluída do SQLite. "
                f"Fonte alterada: {source_file.name}. "
                f"Detalhes: {error}"
            ) from error

        raise

    if not deleted:
        if source_file is not None:
            raise PartialTransactionSyncError(
                "A transação foi removida do arquivo, "
                "mas não foi encontrada no SQLite. "
                f"Fonte alterada: {source_file.name}."
            )

        raise TransactionNotFoundError(
            "A transação não foi encontrada no SQLite."
        )

    return source_file