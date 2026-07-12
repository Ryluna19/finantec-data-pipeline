"""Testes das operações nos arquivos-fonte de transações."""

from __future__ import annotations

from uuid import UUID

import pandas as pd
import pytest

from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
    create_transaction_id,
)
from src.transaction_sources import (
    DuplicateTransactionIdError,
    TransactionNotFoundError,
    delete_transaction_from_source,
    find_transaction_source,
    migrate_transaction_source_ids,
    update_transaction_in_source,
)


def build_transactions() -> pd.DataFrame:
    """Cria transações válidas para os testes."""
    return pd.DataFrame(
        [
            {
                "data": "2026-07-12",
                "tipo": "receita",
                "descricao": "Pagamento",
                "categoria": "Trabalho",
                "valor": 900.0,
            },
            {
                "data": "2026-07-13",
                "tipo": "despesa",
                "descricao": "Conta de luz",
                "categoria": "Serviços",
                "valor": 120.0,
            },
        ]
    )


def save_source(
    source_file,
    transactions: pd.DataFrame,
) -> None:
    """Salva um arquivo-fonte usado pelos testes."""
    source_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    transactions.to_csv(
        source_file,
        index=False,
        encoding="utf-8-sig",
    )


def test_migrate_transaction_source_ids_is_stable(
    tmp_path,
) -> None:
    source_file = (
        tmp_path
        / "transacoes_2026_07.csv"
    )

    save_source(
        source_file,
        build_transactions(),
    )

    first_summary = (
        migrate_transaction_source_ids(
            source_dir=tmp_path,
            project_root=tmp_path,
        )
    )

    first_result = pd.read_csv(
        source_file,
        encoding="utf-8-sig",
    )

    second_summary = (
        migrate_transaction_source_ids(
            source_dir=tmp_path,
            project_root=tmp_path,
        )
    )

    second_result = pd.read_csv(
        source_file,
        encoding="utf-8-sig",
    )

    assert first_summary[
        "files_scanned"
    ] == 1

    assert first_summary[
        "files_updated"
    ] == 1

    assert second_summary[
        "files_updated"
    ] == 0

    assert (
        first_result[
            TRANSACTION_ID_COLUMN
        ].tolist()
        == second_result[
            TRANSACTION_ID_COLUMN
        ].tolist()
    )

    for transaction_id in first_result[
        TRANSACTION_ID_COLUMN
    ]:
        assert str(
            UUID(transaction_id)
        ) == transaction_id


def test_find_transaction_source_locates_id(
    tmp_path,
) -> None:
    transaction_id = (
        create_transaction_id()
    )

    transactions = (
        build_transactions()
    )

    transactions[
        TRANSACTION_ID_COLUMN
    ] = [
        transaction_id,
        create_transaction_id(),
    ]

    source_file = (
        tmp_path
        / "transacoes_manuais.csv"
    )

    save_source(
        source_file,
        transactions,
    )

    match = find_transaction_source(
        transaction_id=transaction_id,
        source_dir=tmp_path,
        project_root=tmp_path,
    )

    assert (
        match.source_file
        == source_file
    )

    assert match.row_index == 0


def test_update_transaction_preserves_id(
    tmp_path,
) -> None:
    transaction_id = (
        create_transaction_id()
    )

    transactions = (
        build_transactions()
    )

    transactions[
        TRANSACTION_ID_COLUMN
    ] = [
        transaction_id,
        create_transaction_id(),
    ]

    source_file = (
        tmp_path
        / "transacoes_manuais.csv"
    )

    save_source(
        source_file,
        transactions,
    )

    updated_file = (
        update_transaction_in_source(
            transaction_id=transaction_id,
            updates={
                "tipo": "DESPESA",
                "descricao": "  Mercado  ",
                "categoria": "Alimentação",
                "valor": "250.50",
            },
            source_dir=tmp_path,
            project_root=tmp_path,
        )
    )

    updated_transactions = pd.read_csv(
        updated_file,
        encoding="utf-8-sig",
    )

    updated_transaction = (
        updated_transactions.loc[
            updated_transactions[
                TRANSACTION_ID_COLUMN
            ]
            == transaction_id
        ]
        .iloc[0]
    )

    assert (
        updated_transaction[
            TRANSACTION_ID_COLUMN
        ]
        == transaction_id
    )

    assert (
        updated_transaction["tipo"]
        == "despesa"
    )

    assert (
        updated_transaction["descricao"]
        == "Mercado"
    )
    assert (
        updated_transaction["data"]
        == "2026-07-12"
    )

    assert (
        updated_transaction["categoria"]
        == "Alimentação"
    )

    assert (
        updated_transaction["valor"]
        == pytest.approx(
            250.50
        )
    )


def test_invalid_update_does_not_change_source(
    tmp_path,
) -> None:
    transaction_id = (
        create_transaction_id()
    )

    transactions = (
        build_transactions()
    )

    transactions[
        TRANSACTION_ID_COLUMN
    ] = [
        transaction_id,
        create_transaction_id(),
    ]

    source_file = (
        tmp_path
        / "transacoes_manuais.csv"
    )

    save_source(
        source_file,
        transactions,
    )

    before_update = source_file.read_text(
        encoding="utf-8-sig",
    )

    with pytest.raises(
        ValueError,
        match="valor menor ou igual a zero",
    ):
        update_transaction_in_source(
            transaction_id=transaction_id,
            updates={
                "valor": 0,
            },
            source_dir=tmp_path,
            project_root=tmp_path,
        )

    after_update = source_file.read_text(
        encoding="utf-8-sig",
    )

    assert (
        after_update
        == before_update
    )


def test_delete_transaction_removes_only_target(
    tmp_path,
) -> None:
    deleted_id = (
        create_transaction_id()
    )

    remaining_id = (
        create_transaction_id()
    )

    transactions = (
        build_transactions()
    )

    transactions[
        TRANSACTION_ID_COLUMN
    ] = [
        deleted_id,
        remaining_id,
    ]

    source_file = (
        tmp_path
        / "transacoes_manuais.csv"
    )

    save_source(
        source_file,
        transactions,
    )

    delete_transaction_from_source(
        transaction_id=deleted_id,
        source_dir=tmp_path,
        project_root=tmp_path,
    )

    remaining_transactions = pd.read_csv(
        source_file,
        encoding="utf-8-sig",
    )

    assert len(
        remaining_transactions
    ) == 1

    assert (
        remaining_transactions.loc[
            0,
            TRANSACTION_ID_COLUMN,
        ]
        == remaining_id
    )


def test_duplicate_transaction_id_is_rejected(
    tmp_path,
) -> None:
    transaction_id = (
        create_transaction_id()
    )

    first_source = (
        tmp_path
        / "transacoes_primeiro.csv"
    )

    second_source = (
        tmp_path
        / "imported"
        / "transacoes_segundo.csv"
    )

    first_transactions = (
        build_transactions()
        .iloc[
            [0]
        ]
        .copy()
    )

    second_transactions = (
        build_transactions()
        .iloc[
            [1]
        ]
        .copy()
    )

    first_transactions[
        TRANSACTION_ID_COLUMN
    ] = transaction_id

    second_transactions[
        TRANSACTION_ID_COLUMN
    ] = transaction_id

    save_source(
        first_source,
        first_transactions,
    )

    save_source(
        second_source,
        second_transactions,
    )

    with pytest.raises(
        DuplicateTransactionIdError,
    ):
        find_transaction_source(
            transaction_id=transaction_id,
            source_dir=tmp_path,
            project_root=tmp_path,
        )


def test_missing_transaction_is_rejected(
    tmp_path,
) -> None:
    source_file = (
        tmp_path
        / "transacoes_manuais.csv"
    )

    save_source(
        source_file,
        build_transactions(),
    )

    with pytest.raises(
        TransactionNotFoundError,
    ):
        find_transaction_source(
            transaction_id=(
                create_transaction_id()
            ),
            source_dir=tmp_path,
            project_root=tmp_path,
        )