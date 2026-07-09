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


def configurar_banco_temporario(monkeypatch, tmp_path):
    banco_teste = tmp_path / "finantec_teste.db"
    tabela_teste = "transacoes_processadas_teste"

    monkeypatch.setattr(etl_transacoes, "DATABASE_DIR", tmp_path)
    monkeypatch.setattr(etl_transacoes, "ARQUIVO_BANCO", banco_teste)
    monkeypatch.setattr(etl_transacoes, "TABELA_TRANSACOES", tabela_teste)

    return banco_teste, tabela_teste


def listar_colunas_tabela(conexao, tabela: str) -> list[str]:
    cursor = conexao.cursor()
    cursor.execute(f"PRAGMA table_info({tabela})")

    return [linha[1] for linha in cursor.fetchall()]


def test_salvar_em_sqlite_cria_banco_e_tabela_com_transacoes(monkeypatch, tmp_path):
    banco_teste, tabela_teste = configurar_banco_temporario(
        monkeypatch,
        tmp_path,
    )

    transacoes = criar_transacoes_processadas_teste()

    etl_transacoes.salvar_em_sqlite(transacoes)

    with sqlite3.connect(banco_teste) as conexao:
        total_linhas = pd.read_sql_query(
            f"SELECT COUNT(*) AS total FROM {tabela_teste}",
            conexao,
        ).loc[0, "total"]

        total_receitas = pd.read_sql_query(
            f"""
            SELECT SUM(valor) AS total
            FROM {tabela_teste}
            WHERE tipo = 'receita'
            """,
            conexao,
        ).loc[0, "total"]

        colunas = listar_colunas_tabela(conexao, tabela_teste)

    assert banco_teste.exists()
    assert total_linhas == 2
    assert total_receitas == 1600.00
    assert colunas == [
        "data",
        "tipo",
        "descricao",
        "categoria",
        "valor",
        "arquivo_origem",
        "ano_mes",
    ]


def test_salvar_em_sqlite_substitui_tabela_existente(monkeypatch, tmp_path):
    banco_teste, tabela_teste = configurar_banco_temporario(
        monkeypatch,
        tmp_path,
    )

    transacoes = criar_transacoes_processadas_teste()

    etl_transacoes.salvar_em_sqlite(transacoes)
    etl_transacoes.salvar_em_sqlite(transacoes.head(1))

    with sqlite3.connect(banco_teste) as conexao:
        total_linhas = pd.read_sql_query(
            f"SELECT COUNT(*) AS total FROM {tabela_teste}",
            conexao,
        ).loc[0, "total"]

    assert total_linhas == 1