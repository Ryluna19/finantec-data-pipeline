"""Pipeline ETL de transações financeiras do FinanTec.

Etapas:
- Extract: lê os arquivos CSV da pasta data/raw.
- Transform: valida, limpa e padroniza as transações.
- Load: salva os dados processados em CSV e SQLite.

O pipeline também gera um relatório com as linhas rejeitadas.
"""

from __future__ import annotations

import logging
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

from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
    ensure_transaction_ids,
)

from src.transaction_repository import (
    insert_transactions,
    load_transactions,
    replace_transactions,
)

from src.transaction_sources import (
    build_transaction_source_key,
)

from src.user_context import (
    get_current_user_id,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEMO_DIR = PROJECT_ROOT / "data" / "demo"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"
LOGS_DIR = PROJECT_ROOT / "logs"
TABELA_TRANSACOES = "transacoes_processadas"

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
        force=True,
    )


def read_raw_transactions(
    source_file: Path,
) -> pd.DataFrame:
    """Lê, identifica e registra a origem de um arquivo CSV bruto."""
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

    selected_columns = [
        *REQUIRED_TRANSACTION_COLUMNS,
    ]

    if (
        TRANSACTION_ID_COLUMN
        in transactions.columns
    ):
        selected_columns.append(
            TRANSACTION_ID_COLUMN
        )

    transactions = transactions[
        selected_columns
    ].copy()

    transactions = ensure_transaction_ids(
        transactions=transactions,
        source_key=(
            build_transaction_source_key(
                source_file
            )
        ),
        identity_columns=(
            REQUIRED_TRANSACTION_COLUMNS
        ),
    )

    transactions[
        "arquivo_origem"
    ] = source_file.name

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

def filter_new_transactions(
    transactions: pd.DataFrame,
    existing_transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Mantém apenas IDs ainda não persistidos no contexto."""
    if transactions.empty:
        return transactions.copy()

    if (
        TRANSACTION_ID_COLUMN
        not in transactions.columns
    ):
        raise ValueError(
            "As transações processadas não possuem "
            "a coluna transaction_id."
        )

    if (
        existing_transactions.empty
        or TRANSACTION_ID_COLUMN
        not in existing_transactions.columns
    ):
        return (
            transactions.copy()
            .reset_index(
                drop=True
            )
        )

    incoming_ids = (
        transactions[
            TRANSACTION_ID_COLUMN
        ]
        .astype("string")
        .fillna("")
        .str.strip()
    )

    existing_ids = set(
        existing_transactions[
            TRANSACTION_ID_COLUMN
        ]
        .astype("string")
        .fillna("")
        .str.strip()
        .tolist()
    )

    new_rows = (
        ~incoming_ids.isin(
            existing_ids
        )
    )

    return (
        transactions.loc[
            new_rows
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

def save_to_sqlite(
    transactions: pd.DataFrame,
    user_id: str | None = None,
    data_mode: str = "user",
) -> int:
    """Persiste transações sem sobrescrever dados reais existentes."""
    current_user_id = (
        user_id
        or get_current_user_id()
    )

    if data_mode == "demo":
        replace_transactions(
            transactions=transactions,
            database_path=ARQUIVO_BANCO,
            table_name=TABELA_TRANSACOES,
            user_id=current_user_id,
            data_mode=data_mode,
        )

        saved_count = len(
            transactions
        )

    else:
        existing_transactions = (
            load_transactions(
                database_path=ARQUIVO_BANCO,
                table_name=TABELA_TRANSACOES,
                user_id=current_user_id,
                data_mode=data_mode,
            )
        )

        new_transactions = (
            filter_new_transactions(
                transactions=transactions,
                existing_transactions=(
                    existing_transactions
                ),
            )
        )

        saved_count = (
            insert_transactions(
                transactions=new_transactions,
                database_path=ARQUIVO_BANCO,
                table_name=TABELA_TRANSACOES,
                user_id=current_user_id,
                data_mode=data_mode,
            )
        )

    logging.info(
        "Dados carregados no SQLite: %s | "
        "tabela: %s | usuário: %s | modo: %s | "
        "novas linhas: %s",
        ARQUIVO_BANCO,
        TABELA_TRANSACOES,
        current_user_id,
        data_mode,
        saved_count,
    )

    return int(
        saved_count
    )

def find_transaction_files(
    use_demo_data: bool = False,
) -> list[Path]:
    """Localiza arquivos reais ou de demonstração."""
    source_dir = (
        DEMO_DIR
        if use_demo_data
        else RAW_DIR
    )

    return sorted(
        source_dir.rglob(
            "transacoes_*.csv"
        )
    )

def run_etl(
    use_demo_data: bool = False,
    user_id: str | None = None,
) -> pd.DataFrame:
    """Executa todas as etapas do pipeline ETL."""
    configure_logging()

    current_user_id = (
        user_id
        or get_current_user_id()
    )

    transaction_data_mode = (
        "demo"
        if use_demo_data
        else "user"
    )

    data_mode_label = (
        "demonstração"
        if use_demo_data
        else "usuário"
    )

    logging.info(
        "Iniciando pipeline ETL "
        "com dados de %s para o usuário %s.",
        data_mode_label,
        current_user_id,
    )

    csv_files = find_transaction_files(
        use_demo_data=use_demo_data
    )

    if not csv_files:
        source_dir = (
            DEMO_DIR
            if use_demo_data
            else RAW_DIR
        )

        raise FileNotFoundError(
            "Nenhum arquivo transacoes_*.csv "
            f"foi encontrado em {source_dir}."
        )

    raw_sources = [
        read_raw_transactions(
            source_file
        )
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
        transactions=processed_transactions,
        user_id=current_user_id,
        data_mode=transaction_data_mode,
    )

    logging.info(
        "Pipeline concluído. "
        "%s transação(ões) processada(s).",
        len(processed_transactions),
    )

    return processed_transactions


def run_etl_with_summary(
    use_demo_data: bool = False,
    user_id: str | None = None,
) -> dict[str, int | bool]:
    """Executa o ETL e retorna um resumo para a interface."""
    processed_transactions = run_etl(
        use_demo_data=use_demo_data,
        user_id=user_id,
    )

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