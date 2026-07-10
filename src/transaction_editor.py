"""
Editor local de transações financeiras.

Este módulo permite cadastrar ou editar transações manuais pelo Streamlit,
em uma experiência parecida com uma planilha simples de gastos.

As transações são salvas em data/raw/transacoes_manuais.csv para que o pipeline
ETL consiga validar, processar e carregar os dados em SQLite.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.etl_transacoes import executar_etl


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

ARQUIVO_TRANSACOES_MANUAIS = RAW_DIR / "transacoes_manuais.csv"

COLUNAS_TRANSACOES = [
    "data",
    "tipo",
    "descricao",
    "categoria",
    "valor",
]

CATEGORIAS_SUGERIDAS = [
    "Trabalho",
    "Alimentação",
    "Transporte",
    "Serviços",
    "Assinaturas",
    "Educação",
    "Lazer",
    "Saúde",
    "Compras",
    "Reserva",
]


def criar_dataframe_vazio() -> pd.DataFrame:
    """
    Cria uma tabela vazia no formato esperado pelo contrato de dados.
    """
    return pd.DataFrame(columns=COLUNAS_TRANSACOES)


def carregar_transacoes_manuais() -> pd.DataFrame:
    """
    Carrega transações manuais já salvas, caso existam.
    """
    if not ARQUIVO_TRANSACOES_MANUAIS.exists():
        return criar_dataframe_vazio()

    transacoes = pd.read_csv(
        ARQUIVO_TRANSACOES_MANUAIS,
        encoding="utf-8-sig",
    )

    for coluna in COLUNAS_TRANSACOES:
        if coluna not in transacoes.columns:
            transacoes[coluna] = ""

    transacoes = transacoes[COLUNAS_TRANSACOES].copy()
    transacoes["data"] = pd.to_datetime(transacoes["data"], errors="coerce")

    return transacoes


def preparar_transacoes_para_salvar(transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara a tabela editada para salvar como CSV bruto.

    A validação completa continua sendo responsabilidade do ETL.
    """
    transacoes = transacoes[COLUNAS_TRANSACOES].copy()
    transacoes = transacoes.dropna(how="all")

    transacoes["data"] = (
        pd.to_datetime(transacoes["data"], errors="coerce")
        .dt.strftime("%Y-%m-%d")
        .fillna("")
    )

    transacoes["tipo"] = (
        transacoes["tipo"]
        .astype("string")
        .fillna("")
        .str.strip()
        .str.lower()
    )

    transacoes["descricao"] = (
        transacoes["descricao"]
        .astype("string")
        .fillna("")
        .str.strip()
    )

    transacoes["categoria"] = (
        transacoes["categoria"]
        .astype("string")
        .fillna("")
        .str.strip()
    )

    transacoes["valor"] = pd.to_numeric(
        transacoes["valor"],
        errors="coerce",
    )

    return transacoes


def salvar_transacoes_manuais(transacoes: pd.DataFrame) -> None:
    """
    Salva as transações manuais em data/raw/.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    transacoes_para_salvar = preparar_transacoes_para_salvar(transacoes)

    transacoes_para_salvar.to_csv(
        ARQUIVO_TRANSACOES_MANUAIS,
        index=False,
        encoding="utf-8-sig",
    )


def exibir_editor_transacoes_manuais() -> bool:
    """
    Exibe o editor de transações manuais.

    Retorna True quando o ETL for executado pelo botão da interface.
    """
    st.subheader("Entrada manual de transações")

    st.caption(
        "Use esta seção para cadastrar ou editar transações locais. "
        "Os dados serão salvos em CSV e depois processados pelo ETL."
    )

    transacoes = carregar_transacoes_manuais()

    transacoes_editadas = st.data_editor(
        transacoes,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "data": st.column_config.DateColumn(
                "Data",
                format="YYYY-MM-DD",
                help="Data da transação.",
            ),
            "tipo": st.column_config.SelectboxColumn(
                "Tipo",
                options=["receita", "despesa"],
                help="Use receita para entrada e despesa para saída.",
            ),
            "descricao": st.column_config.TextColumn(
                "Descrição",
                help="Descrição curta da transação.",
            ),
            "categoria": st.column_config.SelectboxColumn(
                "Categoria",
                options=CATEGORIAS_SUGERIDAS,
                help="Categoria usada nos indicadores financeiros.",
            ),
            "valor": st.column_config.NumberColumn(
                "Valor",
                min_value=0.01,
                step=1.0,
                format="%.2f",
                help="Valor positivo da transação.",
            ),
        },
    )

    coluna_salvar, coluna_processar = st.columns(2)

    with coluna_salvar:
        if st.button("Salvar transações manuais"):
            salvar_transacoes_manuais(transacoes_editadas)
            st.success("Transações manuais salvas em data/raw/transacoes_manuais.csv.")

    with coluna_processar:
        if st.button("Salvar e processar ETL"):
            salvar_transacoes_manuais(transacoes_editadas)
            executar_etl()
            st.success("Transações salvas e ETL executado com sucesso.")
            return True

    st.info(
        "Após salvar e processar o ETL, os dados entram no SQLite e passam a "
        "aparecer nos indicadores do dashboard."
    )

    return False