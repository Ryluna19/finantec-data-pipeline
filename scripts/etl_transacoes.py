from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd


"""
Pipeline ETL de transações financeiras simuladas.

O objetivo deste script é transformar arquivos CSV mensais da pasta data/raw/
em uma base tratada para análise no dashboard.

Etapas:
- Extract: leitura dos arquivos CSV brutos.
- Transform: validação, limpeza e padronização dos dados.
- Load: geração de CSV processado e carga em SQLite.
"""


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"
LOGS_DIR = PROJECT_ROOT / "logs"

ARQUIVO_SAIDA = PROCESSED_DIR / "transacoes_processadas.csv"
ARQUIVO_BANCO = DATABASE_DIR / "finantec.db"
ARQUIVO_LOG = LOGS_DIR / "etl_transacoes.log"

TABELA_TRANSACOES = "transacoes_processadas"

COLUNAS_OBRIGATORIAS = ["data", "tipo", "descricao", "categoria", "valor"]
TIPOS_VALIDOS = {"receita", "despesa"}


def configurar_logs() -> None:
    """
    Configura logs no terminal e em arquivo.

    Os logs ajudam a acompanhar quais arquivos foram lidos, quantas linhas foram
    processadas e se alguma linha foi removida por inconsistência.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(ARQUIVO_LOG, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def validar_colunas(transacoes: pd.DataFrame, arquivo: Path) -> None:
    """
    Valida se o arquivo possui as colunas mínimas esperadas.

    Essa validação evita que o pipeline processe arquivos fora do padrão e gere
    análises incorretas no dashboard.
    """
    colunas_ausentes = [
        coluna
        for coluna in COLUNAS_OBRIGATORIAS
        if coluna not in transacoes.columns
    ]

    if colunas_ausentes:
        raise ValueError(
            f"O arquivo {arquivo.name} não possui as colunas obrigatórias: "
            f"{', '.join(colunas_ausentes)}"
        )


def ler_transacoes_raw(arquivo: Path) -> pd.DataFrame:
    """
    Lê um arquivo CSV bruto da pasta data/raw/.

    A coluna arquivo_origem é adicionada para manter rastreabilidade,
    permitindo saber de qual arquivo cada transação veio.
    """
    logging.info("Lendo arquivo: %s", arquivo.name)

    transacoes = pd.read_csv(arquivo, encoding="utf-8-sig")
    validar_colunas(transacoes, arquivo)

    transacoes = transacoes[COLUNAS_OBRIGATORIAS].copy()
    transacoes["arquivo_origem"] = arquivo.name

    return transacoes


def transformar_transacoes(transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e padroniza os dados de transações.

    Regras aplicadas:
    - converte datas inválidas para nulo;
    - padroniza tipo como receita/despesa;
    - remove espaços extras de textos;
    - converte valores para número;
    - remove linhas inválidas;
    - cria a coluna ano_mes para permitir filtro mensal.
    """
    transacoes = transacoes.copy()

    transacoes["data"] = pd.to_datetime(
        transacoes["data"],
        errors="coerce",
    )

    transacoes["tipo"] = (
        transacoes["tipo"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    transacoes["descricao"] = (
        transacoes["descricao"]
        .astype(str)
        .str.strip()
    )

    transacoes["categoria"] = (
        transacoes["categoria"]
        .astype(str)
        .str.strip()
    )

    transacoes["valor"] = pd.to_numeric(
        transacoes["valor"],
        errors="coerce",
    )

    linhas_antes = len(transacoes)

    transacoes = transacoes.dropna(
        subset=["data", "tipo", "descricao", "categoria", "valor"]
    )

    transacoes = transacoes[
        transacoes["tipo"].isin(TIPOS_VALIDOS)
    ]

    transacoes = transacoes[
        transacoes["valor"] > 0
    ]

    linhas_depois = len(transacoes)
    linhas_removidas = linhas_antes - linhas_depois

    if linhas_removidas > 0:
        logging.warning(
            "%s linha(s) foram removidas por dados inválidos.",
            linhas_removidas,
        )

    transacoes["ano_mes"] = transacoes["data"].dt.to_period("M").astype(str)

    transacoes = transacoes.sort_values(
        by=["data", "tipo", "categoria"]
    ).reset_index(drop=True)

    return transacoes


def salvar_csv_processado(transacoes: pd.DataFrame) -> None:
    """
    Salva as transações tratadas em data/processed/.

    Esse arquivo facilita inspeção manual e também pode ser usado como fallback
    pelo dashboard.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    transacoes.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig",
    )

    logging.info("Arquivo processado gerado: %s", ARQUIVO_SAIDA)


def salvar_em_sqlite(transacoes: pd.DataFrame) -> None:
    """
    Carrega as transações tratadas em uma base SQLite local.

    O SQLite funciona bem para esta versão porque não exige servidor externo e
    permite demonstrar a etapa de Load do ETL de forma simples.
    """
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(ARQUIVO_BANCO) as conexao:
        transacoes.to_sql(
            TABELA_TRANSACOES,
            conexao,
            if_exists="replace",
            index=False,
        )

    logging.info(
        "Dados carregados no SQLite: %s | tabela: %s",
        ARQUIVO_BANCO,
        TABELA_TRANSACOES,
    )


def executar_etl() -> pd.DataFrame:
    """
    Executa o pipeline completo de transações.
    """
    configurar_logs()

    logging.info("Iniciando pipeline ETL de transações.")

    arquivos_csv = sorted(RAW_DIR.glob("transacoes_*.csv"))

    if not arquivos_csv:
        raise FileNotFoundError(
            "Nenhum arquivo transacoes_*.csv foi encontrado em data/raw/."
        )

    bases = [
        ler_transacoes_raw(arquivo)
        for arquivo in arquivos_csv
    ]

    transacoes_brutas = pd.concat(bases, ignore_index=True)
    transacoes_processadas = transformar_transacoes(transacoes_brutas)

    salvar_csv_processado(transacoes_processadas)
    salvar_em_sqlite(transacoes_processadas)

    logging.info(
        "Pipeline concluído. %s transação(ões) processada(s).",
        len(transacoes_processadas),
    )

    return transacoes_processadas


if __name__ == "__main__":
    executar_etl()