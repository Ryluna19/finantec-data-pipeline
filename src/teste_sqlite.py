from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "finantec.db"
TABELA_TRANSACOES = "transacoes_processadas"


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            "Banco SQLite não encontrado. Rode primeiro: python scripts/etl_transacoes.py"
        )

    with sqlite3.connect(DATABASE_PATH) as conexao:
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

        resultado = pd.read_sql_query(consulta, conexao)

    print("=== DADOS CARREGADOS NO SQLITE ===")
    print(resultado)


if __name__ == "__main__":
    main()