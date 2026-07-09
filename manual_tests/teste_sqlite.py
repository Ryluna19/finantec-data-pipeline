"""
Teste manual de leitura da base SQLite.

Este script verifica se o banco local gerado pelo ETL existe e executa uma
consulta simples agrupando receitas, despesas e total de transações por período.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import _path_setup  # noqa: F401
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "finantec.db"
TABELA_TRANSACOES = "transacoes_processadas"


def validar_banco_existe() -> None:
    """
    Verifica se o banco SQLite local já foi gerado.
    """
    if DATABASE_PATH.exists():
        return

    raise FileNotFoundError(
        "Banco SQLite não encontrado. Rode primeiro: python main.py etl"
    )


def consultar_resumo_por_periodo() -> pd.DataFrame:
    """
    Consulta um resumo financeiro agrupado por período no SQLite.
    """
    consulta = f"""
    SELECT
        ano_mes,
        COUNT(*) AS total_transacoes,
        SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END) AS receitas,
        SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END) AS despesas
    FROM {TABELA_TRANSACOES}
    GROUP BY ano_mes
    ORDER BY ano_mes;
    """

    with sqlite3.connect(DATABASE_PATH) as conexao:
        return pd.read_sql_query(consulta, conexao)


def main() -> None:
    """
    Executa o teste manual de leitura do SQLite.
    """
    validar_banco_existe()

    resultado = consultar_resumo_por_periodo()

    print("=== DADOS CARREGADOS NO SQLITE ===")

    if resultado.empty:
        print("Nenhum dado encontrado na tabela de transações.")
        return

    print(resultado.to_string(index=False))


if __name__ == "__main__":
    main()