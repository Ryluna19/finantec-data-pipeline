"""Testes da entrada rápida de transações."""

from __future__ import annotations

from datetime import date

import pandas as pd

import components.quick_transaction as quick_module


def test_build_quick_transaction_creates_independent_id(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        quick_module,
        "create_transaction_id",
        lambda: "transaction-quick-1",
    )

    transaction = (
        quick_module.build_quick_transaction(
            transaction_date=date(
                2026,
                7,
                19,
            ),
            transaction_type=" Despesa ",
            description=" Mercado ",
            category=" Alimentação ",
            amount=25.50,
        )
    )

    assert transaction.to_dict(
        orient="records"
    ) == [
        {
            "transaction_id": (
                "transaction-quick-1"
            ),
            "data": date(
                2026,
                7,
                19,
            ),
            "tipo": "despesa",
            "descricao": "Mercado",
            "categoria": "Alimentação",
            "valor": 25.50,
        }
    ]


def test_save_quick_transaction_uses_current_user(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        quick_module,
        "get_current_user_id",
        lambda: "user-1",
    )

    def fake_save(
        *,
        transactions,
        database_path,
        table_name,
        user_id,
    ):
        captured.update(
            transactions=transactions.copy(),
            database_path=database_path,
            table_name=table_name,
            user_id=user_id,
        )

        return {
            "inserted": 1,
            "updated": 0,
            "total": 1,
        }

    monkeypatch.setattr(
        quick_module,
        "save_manual_transactions_to_database",
        fake_save,
    )

    transaction = pd.DataFrame(
        [
            {
                "transaction_id": "transaction-1",
                "data": "2026-07-19",
                "tipo": "despesa",
                "descricao": "Mercado",
                "categoria": "Alimentação",
                "valor": 25.50,
            }
        ]
    )

    result = (
        quick_module.save_quick_transaction(
            transaction
        )
    )

    assert result == {
        "inserted": 1,
        "updated": 0,
        "total": 1,
    }

    assert captured[
        "user_id"
    ] == "user-1"

    assert captured[
        "database_path"
    ] == quick_module.ARQUIVO_BANCO

    assert captured[
        "table_name"
    ] == quick_module.TABELA_TRANSACOES

    assert captured[
        "transactions"
    ].equals(
        transaction
    )