"""
Funções de carregamento de dados do FinanTec Data Pipeline.

Este módulo centraliza a leitura dos arquivos JSON, CSV e SQLite usados pelo
dashboard e pelo assistente.

A aplicação prioriza a tabela de transações armazenada no SQLite. Quando ela
ainda não existe, utiliza o CSV processado ou retorna uma estrutura vazia.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from src.goal_repository import (
    list_financial_goals,
    seed_financial_goals_if_needed,
)
from src.profile_repository import (
    seed_user_profile_if_missing,
)
from src.transaction_repository import (
    load_transactions,
)
from src.user_context import (
    LOCAL_USER_ID,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

DATA_DIR = (
    PROJECT_ROOT
    / "data"
)

PROCESSED_DIR = (
    DATA_DIR
    / "processed"
)

DATABASE_DIR = (
    PROJECT_ROOT
    / "database"
)

ARQUIVO_BANCO = (
    DATABASE_DIR
    / "finantec.db"
)

ARQUIVO_TRANSACOES_PROCESSADAS = (
    PROCESSED_DIR
    / "transacoes_processadas.csv"
)

ARQUIVO_REJEICOES = (
    PROCESSED_DIR
    / "transacoes_rejeitadas.csv"
)

TABELA_TRANSACOES = (
    "transacoes_processadas"
)

COLUNAS_TRANSACOES_VAZIAS = [
    "data",
    "tipo",
    "descricao",
    "categoria",
    "valor",
    "arquivo_origem",
    "ano_mes",
]


# -----------------------------------------------------------------------------
# Arquivos JSON
# -----------------------------------------------------------------------------


def carregar_json(
    nome_arquivo: str,
) -> dict:
    """Carrega um arquivo JSON da pasta data/."""
    caminho = (
        DATA_DIR
        / nome_arquivo
    )

    with caminho.open(
        "r",
        encoding="utf-8-sig",
    ) as arquivo:
        return json.load(
            arquivo
        )


def merge_profile_with_goals(
    profile: dict,
    goals: list[dict],
) -> dict:
    """Inclui as metas persistidas no perfil usado pela aplicação."""
    merged_profile = (
        profile.copy()
    )

    merged_profile[
        "objetivos_financeiros"
    ] = [
        goal.copy()
        for goal in goals
    ]

    return merged_profile


def merge_profile_with_legacy_goals(
    profile: dict,
    seed_profile: dict,
) -> dict:
    """Mantém compatibilidade com chamadas e testes antigos."""
    return merge_profile_with_goals(
        profile=profile,
        goals=list(
            seed_profile.get(
                "objetivos_financeiros",
                [],
            )
        ),
    )


def carregar_perfil_usuario(
    user_id: str,
) -> dict:
    """Carrega o perfil e as metas financeiras persistidas."""
    seed_profile = carregar_json(
        "perfil_usuario.json"
    )

    persisted_profile = (
        seed_user_profile_if_missing(
            database_path=(
                ARQUIVO_BANCO
            ),
            user_id=user_id,
            seed_profile=seed_profile,
        )
    )

    seed_financial_goals_if_needed(
        database_path=ARQUIVO_BANCO,
        user_id=user_id,
        seed_goals=list(
            seed_profile.get(
                "objetivos_financeiros",
                [],
            )
        ),
    )

    persisted_goals = (
        list_financial_goals(
            database_path=ARQUIVO_BANCO,
            user_id=user_id,
        )
    )

    return merge_profile_with_goals(
        profile=persisted_profile,
        goals=persisted_goals,
    )


def carregar_conceitos_financeiros() -> dict:
    """Carrega os conceitos usados pela IA."""
    return carregar_json(
        "conceitos_financeiros.json"
    )


def carregar_produtos_financeiros() -> dict:
    """Carrega produtos financeiros informativos."""
    return carregar_json(
        "produtos_financeiros.json"
    )


# -----------------------------------------------------------------------------
# Estrutura e localização das transações
# -----------------------------------------------------------------------------


def criar_dataframe_transacoes_vazio() -> pd.DataFrame:
    """Cria uma estrutura vazia compatível com o dashboard."""
    return pd.DataFrame(
        columns=(
            COLUNAS_TRANSACOES_VAZIAS
        )
    )


def obter_caminho_csv_transacoes() -> Path | None:
    """Retorna o CSV processado quando ele existir."""
    if (
        ARQUIVO_TRANSACOES_PROCESSADAS
        .exists()
    ):
        return (
            ARQUIVO_TRANSACOES_PROCESSADAS
        )

    return None


def sqlite_table_exists(
    database_path: Path,
    table_name: str,
) -> bool:
    """Verifica se uma tabela existe no banco SQLite."""
    if not database_path.exists():
        return False

    try:
        with sqlite3.connect(
            database_path
        ) as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE
                    type = 'table'
                    AND name = ?
                LIMIT 1
                """,
                (
                    table_name,
                ),
            ).fetchone()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível verificar "
            "a estrutura do banco local."
        ) from error

    return row is not None


# -----------------------------------------------------------------------------
# Carregamento das transações
# -----------------------------------------------------------------------------


def carregar_transacoes_sqlite(
    user_id: str = LOCAL_USER_ID,
    data_mode: str = "user",
) -> pd.DataFrame:
    """Carrega a partição de transações do contexto atual."""
    return load_transactions(
        database_path=ARQUIVO_BANCO,
        table_name=TABELA_TRANSACOES,
        user_id=user_id,
        data_mode=data_mode,
    )


def carregar_transacoes_csv() -> pd.DataFrame:
    """Carrega o CSV processado ou retorna uma base vazia."""
    caminho = (
        obter_caminho_csv_transacoes()
    )

    if caminho is None:
        return (
            criar_dataframe_transacoes_vazio()
        )

    return pd.read_csv(
        caminho,
        encoding="utf-8-sig",
        parse_dates=[
            "data",
        ],
    )


def preparar_transacoes(
    transacoes: pd.DataFrame,
) -> pd.DataFrame:
    """Padroniza as transações depois da leitura."""
    transacoes = (
        transacoes.copy()
    )

    for coluna in (
        COLUNAS_TRANSACOES_VAZIAS
    ):
        if coluna not in transacoes.columns:
            transacoes[
                coluna
            ] = pd.Series(
                dtype="object"
            )

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

    if (
        "ano_mes"
        not in transacoes.columns
    ):
        transacoes[
            "ano_mes"
        ] = (
            transacoes["data"]
            .dt.to_period("M")
            .astype(str)
        )

    return transacoes


def carregar_transacoes(
    user_id: str = LOCAL_USER_ID,
    data_mode: str = "user",
) -> pd.DataFrame:
    """Carrega transações do usuário e modo selecionados."""
    normalized_data_mode = (
        str(
            data_mode
        )
        .strip()
        .lower()
    )

    if normalized_data_mode == "empty":
        return preparar_transacoes(
            criar_dataframe_transacoes_vazio()
        )

    if normalized_data_mode not in {
        "user",
        "demo",
    }:
        raise ValueError(
            "O modo dos dados deve ser "
            "'user', 'demo' ou 'empty'."
        )

    if sqlite_table_exists(
        database_path=ARQUIVO_BANCO,
        table_name=TABELA_TRANSACOES,
    ):
        transacoes = (
            carregar_transacoes_sqlite(
                user_id=user_id,
                data_mode=normalized_data_mode,
            )
        )

    elif (
        user_id == LOCAL_USER_ID
        and normalized_data_mode == "user"
    ):
        # Compatibilidade com instalações antigas,
        # antes da primeira carga particionada.
        transacoes = (
            carregar_transacoes_csv()
        )

    else:
        transacoes = (
            criar_dataframe_transacoes_vazio()
        )

    return preparar_transacoes(
        transacoes
    )

# -----------------------------------------------------------------------------
# Outros dados usados pelo dashboard
# -----------------------------------------------------------------------------


def carregar_historico_atendimento() -> pd.DataFrame:
    """Carrega o histórico simulado usado no contexto da IA."""
    caminho = (
        DATA_DIR
        / "historico_atendimento.csv"
    )

    return pd.read_csv(
        caminho,
        encoding="utf-8-sig",
        parse_dates=[
            "data",
        ],
    )


def carregar_rejeicoes() -> pd.DataFrame:
    """Carrega o relatório de transações rejeitadas."""
    if not ARQUIVO_REJEICOES.exists():
        return pd.DataFrame()

    return pd.read_csv(
        ARQUIVO_REJEICOES,
        encoding="utf-8-sig",
    )
