"""Testes do repositório SQLite de transações."""

import pandas as pd

from src.transaction_repository import (
    load_transactions,
    replace_transactions,
)


def create_test_transactions() -> pd.DataFrame:
    """Cria transações processadas para os testes."""
    return pd.DataFrame(
        {
            "data": [
                "2026-06-01",
                "2026-06-02",
            ],
            "tipo": [
                "receita",
                "despesa",
            ],
            "descricao": [
                "Bolsa-estágio",
                "Mercado",
            ],
            "categoria": [
                "Trabalho",
                "Alimentação",
            ],
            "valor": [
                1600.00,
                200.00,
            ],
            "arquivo_origem": [
                "teste.csv",
                "teste.csv",
            ],
            "ano_mes": [
                "2026-06",
                "2026-06",
            ],
        }
    )


def test_replace_and_load_transactions(
    tmp_path,
) -> None:
    """Salva e carrega transações do SQLite."""
    database_path = (
        tmp_path
        / "finantec_test.db"
    )

    table_name = (
        "processed_transactions"
    )

    transactions = (
        create_test_transactions()
    )

    replace_transactions(
        transactions=transactions,
        database_path=database_path,
        table_name=table_name,
    )

    loaded_transactions = (
        load_transactions(
            database_path=database_path,
            table_name=table_name,
        )
    )

    assert database_path.exists()
    assert len(loaded_transactions) == 2

    assert (
        loaded_transactions[
            "descricao"
        ].tolist()
        == [
            "Bolsa-estágio",
            "Mercado",
        ]
    )

    assert (
        loaded_transactions[
            "valor"
        ].sum()
        == 1800.00
    )


def test_replace_transactions_replaces_existing_data(
    tmp_path,
) -> None:
    """Substitui os dados existentes na tabela."""
    database_path = (
        tmp_path
        / "finantec_test.db"
    )

    table_name = (
        "processed_transactions"
    )

    transactions = (
        create_test_transactions()
    )

    replace_transactions(
        transactions=transactions,
        database_path=database_path,
        table_name=table_name,
    )

    replace_transactions(
        transactions=transactions.head(1),
        database_path=database_path,
        table_name=table_name,
    )

    loaded_transactions = (
        load_transactions(
            database_path=database_path,
            table_name=table_name,
        )
    )

    assert len(loaded_transactions) == 1

    assert (
        loaded_transactions.loc[
            0,
            "descricao",
        ]
        == "Bolsa-estágio"
    )