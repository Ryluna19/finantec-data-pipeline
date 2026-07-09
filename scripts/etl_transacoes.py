from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

ARQUIVO_SAIDA = PROCESSED_DIR / "transacoes_processadas.csv"
ARQUIVO_LOG = LOGS_DIR / "etl_transacoes.log"

COLUNAS_OBRIGATORIAS = ["data", "tipo", "descricao", "categoria", "valor"]
TIPOS_VALIDOS = {"receita", "despesa"}


def configurar_logs() -> None:
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
    colunas_ausentes = [
        coluna for coluna in COLUNAS_OBRIGATORIAS
        if coluna not in transacoes.columns
    ]

    if colunas_ausentes:
        raise ValueError(
            f"O arquivo {arquivo.name} não possui as colunas obrigatórias: "
            f"{', '.join(colunas_ausentes)}"
        )


def ler_transacoes_raw(arquivo: Path) -> pd.DataFrame:
    logging.info("Lendo arquivo: %s", arquivo.name)

    transacoes = pd.read_csv(arquivo, encoding="utf-8-sig")
    validar_colunas(transacoes, arquivo)

    transacoes = transacoes[COLUNAS_OBRIGATORIAS].copy()
    transacoes["arquivo_origem"] = arquivo.name

    return transacoes


def transformar_transacoes(transacoes: pd.DataFrame) -> pd.DataFrame:
    transacoes = transacoes.copy()

    transacoes["data"] = pd.to_datetime(
        transacoes["data"],
        errors="coerce"
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
        errors="coerce"
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
            linhas_removidas
        )

    transacoes["ano_mes"] = transacoes["data"].dt.to_period("M").astype(str)

    transacoes = transacoes.sort_values(
        by=["data", "tipo", "categoria"]
    ).reset_index(drop=True)

    return transacoes


def executar_etl() -> pd.DataFrame:
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

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    transacoes_processadas.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig"
    )

    logging.info(
        "Pipeline concluído. %s transação(ões) processada(s).",
        len(transacoes_processadas)
    )

    logging.info(
        "Arquivo gerado: %s",
        ARQUIVO_SAIDA
    )

    return transacoes_processadas


if __name__ == "__main__":
    executar_etl()
