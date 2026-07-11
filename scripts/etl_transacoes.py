"""Pipeline ETL de transações financeiras do FinanTec.

Etapas:
- Extract: lê os arquivos CSV da pasta data/raw.
- Transform: valida, limpa e padroniza as transações.
- Load: salva os dados processados em CSV e SQLite.

O pipeline também gera um relatório com as linhas rejeitadas.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

from src.transaction_validation import (
    REQUIRED_TRANSACTION_COLUMNS,
    VALID_TRANSACTION_TYPES,
    add_rejection_reason,
    finalize_valid_transactions,
    identify_rejection_reasons,
    prepare_transactions,
    split_transactions_by_validity,
    validate_required_columns,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"
LOGS_DIR = PROJECT_ROOT / "logs"

ARQUIVO_SAIDA = (
    PROCESSED_DIR
    / "transacoes_processadas.csv"
)

ARQUIVO_REJEICOES = (
    PROCESSED_DIR
    / "transacoes_rejeitadas.csv"
)

ARQUIVO_BANCO = DATABASE_DIR / "finantec.db"
ARQUIVO_LOG = LOGS_DIR / "etl_transacoes.log"

TABELA_TRANSACOES = "transacoes_processadas"

# Aliases temporários preservam os testes e imports anteriores.
COLUNAS_OBRIGATORIAS = REQUIRED_TRANSACTION_COLUMNS
TIPOS_VALIDOS = VALID_TRANSACTION_TYPES


def configure_logging() -> None:
    """Configura os logs do ETL no terminal e em arquivo."""
    LOGS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(
                ARQUIVO_LOG,
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )


def read_raw_transactions(
    source_file: Path,
) -> pd.DataFrame:
    """Lê e identifica a origem de um arquivo CSV bruto."""
    logging.info(
        "Lendo arquivo: %s",
        source_file.name,
    )

    transactions = pd.read_csv(
        source_file,
        encoding="utf-8-sig",
    )

    validate_required_columns(
        transactions,
        source_file,
    )

    transactions = transactions[
        REQUIRED_TRANSACTION_COLUMNS
    ].copy()

    transactions["arquivo_origem"] = (
        source_file.name
    )

    return transactions


def transform_transactions(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Valida e finaliza apenas as transações aceitas."""
    (
        valid_transactions,
        rejected_transactions,
    ) = split_transactions_by_validity(
        transactions
    )

    if not rejected_transactions.empty:
        logging.warning(
            "%s linha(s) foram removidas "
            "por dados inválidos.",
            len(rejected_transactions),
        )

    return finalize_valid_transactions(
        valid_transactions
    )


def generate_rejection_report(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Retorna apenas as transações rejeitadas."""
    _, rejected_transactions = (
        split_transactions_by_validity(
            transactions
        )
    )

    return rejected_transactions


def save_processed_csv(
    transactions: pd.DataFrame,
) -> None:
    """Salva as transações processadas em CSV."""
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    transactions.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig",
    )

    logging.info(
        "Arquivo processado gerado: %s",
        ARQUIVO_SAIDA,
    )


def save_rejection_report(
    rejected_transactions: pd.DataFrame,
) -> None:
    """Salva ou remove o relatório local de rejeições."""
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if rejected_transactions.empty:
        if ARQUIVO_REJEICOES.exists():
            ARQUIVO_REJEICOES.unlink()

        logging.info(
            "Nenhuma linha rejeitada no pipeline."
        )
        return

    rejected_transactions.to_csv(
        ARQUIVO_REJEICOES,
        index=False,
        encoding="utf-8-sig",
    )

    logging.warning(
        "Relatório de rejeições gerado "
        "com %s linha(s): %s",
        len(rejected_transactions),
        ARQUIVO_REJEICOES,
    )


def save_to_sqlite(
    transactions: pd.DataFrame,
) -> None:
    """Substitui a tabela SQLite pelas transações processadas."""
    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(
        ARQUIVO_BANCO
    ) as connection:
        transactions.to_sql(
            TABELA_TRANSACOES,
            connection,
            if_exists="replace",
            index=False,
        )

    logging.info(
        "Dados carregados no SQLite: %s | tabela: %s",
        ARQUIVO_BANCO,
        TABELA_TRANSACOES,
    )


def run_etl() -> pd.DataFrame:
    """Executa todas as etapas do pipeline ETL."""
    configure_logging()

    logging.info(
        "Iniciando pipeline ETL de transações."
    )

    # Inclui fontes mensais, manuais e lotes importados.
    csv_files = sorted(
        RAW_DIR.rglob("transacoes_*.csv")
    )

    if not csv_files:
        raise FileNotFoundError(
            "Nenhum arquivo transacoes_*.csv "
            "foi encontrado em data/raw/."
        )

    raw_sources = [
        read_raw_transactions(source_file)
        for source_file in csv_files
    ]

    raw_transactions = pd.concat(
        raw_sources,
        ignore_index=True,
    )

    processed_transactions = (
        transform_transactions(
            raw_transactions
        )
    )

    rejected_transactions = (
        generate_rejection_report(
            raw_transactions
        )
    )

    save_processed_csv(
        processed_transactions
    )

    save_rejection_report(
        rejected_transactions
    )

    save_to_sqlite(
        processed_transactions
    )

    logging.info(
        "Pipeline concluído. "
        "%s transação(ões) processada(s).",
        len(processed_transactions),
    )

    return processed_transactions


def run_etl_with_summary() -> dict[str, int | bool]:
    """Executa o ETL e retorna um resumo para a interface."""
    processed_transactions = run_etl()

    rejection_count = 0

    if ARQUIVO_REJEICOES.exists():
        rejected_transactions = pd.read_csv(
            ARQUIVO_REJEICOES,
            encoding="utf-8-sig",
        )

        rejection_count = len(
            rejected_transactions
        )

    return {
        "sucesso": True,
        "transacoes_processadas": len(
            processed_transactions
        ),
        "transacoes_rejeitadas": (
            rejection_count
        ),
    }


# Compatibilidade temporária com testes e módulos ainda não migrados.
configurar_logs = configure_logging
validar_colunas = validate_required_columns
ler_transacoes_raw = read_raw_transactions
preparar_transacoes = prepare_transactions
adicionar_motivo = add_rejection_reason
identificar_motivos_rejeicao = (
    identify_rejection_reasons
)
separar_transacoes_por_validade = (
    split_transactions_by_validity
)
finalizar_transacoes_validas = (
    finalize_valid_transactions
)
transformar_transacoes = transform_transactions
gerar_relatorio_rejeicoes = (
    generate_rejection_report
)
salvar_csv_processado = save_processed_csv
salvar_relatorio_rejeicoes = (
    save_rejection_report
)
salvar_em_sqlite = save_to_sqlite
executar_etl = run_etl
executar_etl_com_resumo = run_etl_with_summary


if __name__ == "__main__":
    run_etl()