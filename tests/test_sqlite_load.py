"""Testes da carga de transações no SQLite."""

from __future__ import annotations

import sqlite3

import pandas as pd

from scripts import etl_transacoes
from src.user_context import (
    LOCAL_USER_ID,
)


def criar_transacoes_processadas_teste() -> pd.DataFrame:
    """Cria transações processadas com IDs persistentes."""
    return pd.DataFrame(
        {
            "transaction_id": [
                "transaction-1",
                "transaction-2",
            ],
            "data": pd.to_datetime(
                [
                    "2026-06-01",
                    "2026-06-02",
                ]
            ),
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


def configurar_banco_temporario(
    monkeypatch,
    tmp_path,
):
    """Configura o ETL para usar um banco temporário."""
    banco_teste = (
        tmp_path
        / "finantec_teste.db"
    )

    tabela_teste = (
        "transacoes_processadas_teste"
    )

    monkeypatch.setattr(
        etl_transacoes,
        "DATABASE_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        etl_transacoes,
        "ARQUIVO_BANCO",
        banco_teste,
    )

    monkeypatch.setattr(
        etl_transacoes,
        "TABELA_TRANSACOES",
        tabela_teste,
    )

    return (
        banco_teste,
        tabela_teste,
    )


def listar_colunas_tabela(
    conexao: sqlite3.Connection,
    tabela: str,
) -> list[str]:
    """Lista as colunas existentes em uma tabela SQLite."""
    cursor = conexao.cursor()

    cursor.execute(
        f"PRAGMA table_info({tabela})"
    )

    return [
        linha[1]
        for linha in cursor.fetchall()
    ]


def test_salvar_em_sqlite_cria_banco_e_tabela_com_transacoes(
    monkeypatch,
    tmp_path,
):
    banco_teste, tabela_teste = (
        configurar_banco_temporario(
            monkeypatch,
            tmp_path,
        )
    )

    transacoes = (
        criar_transacoes_processadas_teste()
    )

    inserted_count = (
        etl_transacoes
        .salvar_em_sqlite(
            transacoes
        )
    )

    with sqlite3.connect(
        banco_teste
    ) as conexao:
        total_linhas = (
            pd.read_sql_query(
                f"""
                SELECT COUNT(*) AS total
                FROM {tabela_teste}
                """,
                conexao,
            )
            .loc[
                0,
                "total",
            ]
        )

        total_receitas = (
            pd.read_sql_query(
                f"""
                SELECT SUM(valor) AS total
                FROM {tabela_teste}
                WHERE tipo = 'receita'
                """,
                conexao,
            )
            .loc[
                0,
                "total",
            ]
        )

        colunas = listar_colunas_tabela(
            conexao,
            tabela_teste,
        )

        contextos = pd.read_sql_query(
            f"""
            SELECT DISTINCT
                user_id,
                data_mode
            FROM {tabela_teste}
            """,
            conexao,
        )

    assert banco_teste.exists()
    assert inserted_count == 2
    assert total_linhas == 2
    assert total_receitas == 1600.00

    assert colunas == [
        "transaction_id",
        "data",
        "tipo",
        "descricao",
        "categoria",
        "valor",
        "arquivo_origem",
        "ano_mes",
        "user_id",
        "data_mode",
    ]

    assert contextos.to_dict(
        orient="records"
    ) == [
        {
            "user_id": LOCAL_USER_ID,
            "data_mode": "user",
        }
    ]


def test_etl_do_usuario_nao_remove_transacoes_existentes(
    monkeypatch,
    tmp_path,
):
    banco_teste, tabela_teste = (
        configurar_banco_temporario(
            monkeypatch,
            tmp_path,
        )
    )

    transacoes = (
        criar_transacoes_processadas_teste()
    )

    first_inserted = (
        etl_transacoes
        .salvar_em_sqlite(
            transacoes
        )
    )

    second_inserted = (
        etl_transacoes
        .salvar_em_sqlite(
            transacoes.head(
                1
            )
        )
    )

    with sqlite3.connect(
        banco_teste
    ) as conexao:
        total_linhas = (
            pd.read_sql_query(
                f"""
                SELECT COUNT(*) AS total
                FROM {tabela_teste}
                WHERE
                    user_id = ?
                    AND data_mode = ?
                """,
                conexao,
                params=(
                    LOCAL_USER_ID,
                    "user",
                ),
            )
            .loc[
                0,
                "total",
            ]
        )

    assert first_inserted == 2
    assert second_inserted == 0
    assert total_linhas == 2


def test_etl_do_usuario_insere_somente_ids_novos(
    monkeypatch,
    tmp_path,
):
    banco_teste, tabela_teste = (
        configurar_banco_temporario(
            monkeypatch,
            tmp_path,
        )
    )

    transacoes = (
        criar_transacoes_processadas_teste()
    )

    etl_transacoes.salvar_em_sqlite(
        transacoes
    )

    nova_transacao = pd.DataFrame(
        {
            "transaction_id": [
                "transaction-3",
            ],
            "data": pd.to_datetime(
                [
                    "2026-06-03",
                ]
            ),
            "tipo": [
                "despesa",
            ],
            "descricao": [
                "Transporte",
            ],
            "categoria": [
                "Transporte",
            ],
            "valor": [
                50.00,
            ],
            "arquivo_origem": [
                "novo.csv",
            ],
            "ano_mes": [
                "2026-06",
            ],
        }
    )

    lote_misto = pd.concat(
        [
            transacoes.tail(
                1
            ),
            nova_transacao,
        ],
        ignore_index=True,
    )

    inserted_count = (
        etl_transacoes
        .salvar_em_sqlite(
            lote_misto
        )
    )

    with sqlite3.connect(
        banco_teste
    ) as conexao:
        transacoes_salvas = (
            pd.read_sql_query(
                f"""
                SELECT
                    transaction_id,
                    descricao
                FROM {tabela_teste}
                WHERE
                    user_id = ?
                    AND data_mode = ?
                ORDER BY transaction_id
                """,
                conexao,
                params=(
                    LOCAL_USER_ID,
                    "user",
                ),
            )
        )

    assert inserted_count == 1

    assert (
        transacoes_salvas[
            "transaction_id"
        ].tolist()
        == [
            "transaction-1",
            "transaction-2",
            "transaction-3",
        ]
    )


def test_etl_demo_substitui_particao_existente(
    monkeypatch,
    tmp_path,
):
    banco_teste, tabela_teste = (
        configurar_banco_temporario(
            monkeypatch,
            tmp_path,
        )
    )

    transacoes = (
        criar_transacoes_processadas_teste()
    )

    first_saved = (
        etl_transacoes
        .salvar_em_sqlite(
            transactions=transacoes,
            user_id=LOCAL_USER_ID,
            data_mode="demo",
        )
    )

    second_saved = (
        etl_transacoes
        .salvar_em_sqlite(
            transactions=(
                transacoes.head(
                    1
                )
            ),
            user_id=LOCAL_USER_ID,
            data_mode="demo",
        )
    )

    with sqlite3.connect(
        banco_teste
    ) as conexao:
        total_demo = (
            pd.read_sql_query(
                f"""
                SELECT COUNT(*) AS total
                FROM {tabela_teste}
                WHERE
                    user_id = ?
                    AND data_mode = ?
                """,
                conexao,
                params=(
                    LOCAL_USER_ID,
                    "demo",
                ),
            )
            .loc[
                0,
                "total",
            ]
        )

    assert first_saved == 2
    assert second_saved == 1
    assert total_demo == 1


def test_filter_new_transactions_preserva_apenas_ids_desconhecidos():
    incoming = (
        criar_transacoes_processadas_teste()
    )

    existing = incoming.head(
        1
    ).copy()

    result = (
        etl_transacoes
        .filter_new_transactions(
            transactions=incoming,
            existing_transactions=existing,
        )
    )

    assert len(
        result
    ) == 1

    assert (
        result.iloc[0][
            "transaction_id"
        ]
        == "transaction-2"
    )