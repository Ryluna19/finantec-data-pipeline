import sqlite3

import pandas as pd

from scripts import etl_transacoes


def criar_transacoes_processadas_teste():
    return pd.DataFrame(
        {
            "data": pd.to_datetime(["2026-06-01", "2026-06-02"]),
            "tipo": ["receita", "despesa"],
            "descricao": ["Bolsa-estágio", "Mercado"],
            "categoria": ["Trabalho", "Alimentação"],
            "valor": [1600.00, 200.00],
            "arquivo_origem": ["teste.csv", "teste.csv"],
            "ano_mes": ["2026-06", "2026-06"],
        }
    )


def test_salvar_em_sqlite_cria_tabela_com_transacoes(monkeypatch, tmp_path):
    banco_teste = tmp_path / "finantec_teste.db"

    monkeypatch.setattr(etl_transacoes, "DATABASE_DIR", tmp_path)
    monkeypatch.setattr(etl_transacoes, "ARQUIVO_BANCO", banco_teste)
    monkeypatch.setattr(
        etl_transacoes,
        "TABELA_TRANSACOES",
        "transacoes_processadas_teste",
    )

    transacoes = criar_transacoes_processadas_teste()

    etl_transacoes.salvar_em_sqlite(transacoes)

    with sqlite3.connect(banco_teste) as conexao:
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM transacoes_processadas_teste"
        )
        total_linhas = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT SUM(valor)
            FROM transacoes_processadas_teste
            WHERE tipo = 'receita'
            """
        )
        total_receitas = cursor.fetchone()[0]

    assert banco_teste.exists()
    assert total_linhas == 2
    assert total_receitas == 1600.00
