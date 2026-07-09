"""
Funções de carregamento de dados do FinanTec Data Pipeline.

Este módulo centraliza a leitura dos arquivos JSON, CSV e SQLite usados pelo
dashboard e pelo assistente.

A aplicação prioriza a base SQLite gerada pelo ETL, mas mantém fallback para CSV
processado e CSV original. Isso permite que o projeto continue funcionando mesmo
quando o banco local ainda não foi gerado.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"

ARQUIVO_BANCO = DATABASE_DIR / "finantec.db"
ARQUIVO_TRANSACOES_PROCESSADAS = PROCESSED_DIR / "transacoes_processadas.csv"
ARQUIVO_REJEICOES = PROCESSED_DIR / "transacoes_rejeitadas.csv"
ARQUIVO_TRANSACOES_ORIGINAL = DATA_DIR / "transacoes.csv"

TABELA_TRANSACOES = "transacoes_processadas"


def carregar_json(nome_arquivo: str) -> dict:
    """
    Carrega um arquivo JSON da pasta data/.
    """
    caminho = DATA_DIR / nome_arquivo

    with caminho.open("r", encoding="utf-8-sig") as arquivo:
        return json.load(arquivo)


def carregar_perfil_usuario() -> dict:
    """
    Carrega o perfil financeiro simulado usado no projeto.
    """
    return carregar_json("perfil_usuario.json")


def carregar_conceitos_financeiros() -> dict:
    """
    Carrega conceitos financeiros usados como base de conhecimento da IA.
    """
    return carregar_json("conceitos_financeiros.json")


def carregar_produtos_financeiros() -> dict:
    """
    Carrega informações simuladas sobre produtos financeiros.
    """
    return carregar_json("produtos_financeiros.json")


def obter_caminho_csv_transacoes() -> Path:
    """
    Retorna o melhor CSV de transações disponível.

    Ordem de prioridade:
    1. CSV processado pelo ETL;
    2. CSV original da primeira versão do projeto.
    """
    if ARQUIVO_TRANSACOES_PROCESSADAS.exists():
        return ARQUIVO_TRANSACOES_PROCESSADAS

    return ARQUIVO_TRANSACOES_ORIGINAL


def carregar_transacoes_sqlite() -> pd.DataFrame:
    """
    Carrega transações da base SQLite gerada pelo pipeline ETL.
    """
    consulta = f"SELECT * FROM {TABELA_TRANSACOES}"

    with sqlite3.connect(ARQUIVO_BANCO) as conexao:
        return pd.read_sql_query(consulta, conexao)


def carregar_transacoes_csv() -> pd.DataFrame:
    """
    Carrega transações a partir do CSV processado ou do CSV original.
    """
    caminho = obter_caminho_csv_transacoes()

    return pd.read_csv(
        caminho,
        encoding="utf-8-sig",
        parse_dates=["data"],
    )


def preparar_transacoes(transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza os dados de transações após a leitura.

    Mesmo quando os dados vêm do ETL, esta etapa garante que o dashboard receba
    datas, tipos, categorias e valores em formatos consistentes.
    """
    transacoes = transacoes.copy()

    transacoes["data"] = pd.to_datetime(
        transacoes["data"],
        errors="coerce",
    )

    transacoes["tipo"] = (
        transacoes["tipo"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    transacoes["descricao"] = (
        transacoes["descricao"]
        .astype("string")
        .str.strip()
    )

    transacoes["categoria"] = (
        transacoes["categoria"]
        .astype("string")
        .str.strip()
    )

    transacoes["valor"] = pd.to_numeric(
        transacoes["valor"],
        errors="coerce",
    )

    if "ano_mes" not in transacoes.columns:
        transacoes["ano_mes"] = (
            transacoes["data"]
            .dt.to_period("M")
            .astype(str)
        )

    return transacoes


def carregar_transacoes() -> pd.DataFrame:
    """
    Carrega transações priorizando SQLite.

    Ordem de leitura:
    1. SQLite gerado pelo ETL;
    2. CSV processado;
    3. CSV original.
    """
    if ARQUIVO_BANCO.exists():
        transacoes = carregar_transacoes_sqlite()
    else:
        transacoes = carregar_transacoes_csv()

    return preparar_transacoes(transacoes)


def carregar_historico_atendimento() -> pd.DataFrame:
    """
    Carrega o histórico simulado de atendimento usado no contexto da IA.
    """
    caminho = DATA_DIR / "historico_atendimento.csv"

    return pd.read_csv(
        caminho,
        encoding="utf-8-sig",
        parse_dates=["data"],
    )


def carregar_rejeicoes() -> pd.DataFrame:
    """
    Carrega o relatório de transações rejeitadas, caso ele exista.

    O arquivo é gerado pelo pipeline ETL apenas quando existem linhas inválidas.
    Quando não existe relatório, retorna um DataFrame vazio para simplificar o
    uso no dashboard.
    """
    if not ARQUIVO_REJEICOES.exists():
        return pd.DataFrame()

    return pd.read_csv(
        ARQUIVO_REJEICOES,
        encoding="utf-8-sig",
    )