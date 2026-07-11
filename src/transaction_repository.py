"""Persistência SQLite das transações do FinanTec."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def replace_transactions(
    transactions: pd.DataFrame,
    database_path: Path,
    table_name: str,
) -> None:
    """Substitui a tabela pelas transações processadas."""
    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        transactions.to_sql(
            table_name,
            connection,
            if_exists="replace",
            index=False,
        )


def load_transactions(
    database_path: Path,
    table_name: str,
) -> pd.DataFrame:
    """Carrega as transações armazenadas no SQLite."""
    query = (
        f"SELECT * FROM {table_name}"
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        return pd.read_sql_query(
            query,
            connection,
        )