"""Leitura, geração e persistência de arquivos de transações."""

from __future__ import annotations

import hashlib
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from src.transaction_validation import (
    REQUIRED_TRANSACTION_COLUMNS,
    prepare_transactions,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

IMPORTED_RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "imported"
)

TRANSACTION_SHEET_NAME = "Transacoes"
INSTRUCTIONS_SHEET_NAME = "Instrucoes"

FileSource = str | Path | BinaryIO


def _rewind_file(source: FileSource) -> None:
    """Reposiciona arquivos em memória antes de uma nova leitura."""
    seek = getattr(source, "seek", None)

    if callable(seek):
        seek(0)


def read_csv_transactions(
    source: FileSource,
) -> pd.DataFrame:
    """Lê transações de um arquivo CSV."""
    _rewind_file(source)

    return pd.read_csv(
        source,
        encoding="utf-8-sig",
    )


def read_excel_transactions(
    source: FileSource,
    sheet_name: str = TRANSACTION_SHEET_NAME,
) -> pd.DataFrame:
    """Lê transações da planilha principal de um arquivo Excel."""
    _rewind_file(source)

    return pd.read_excel(
        source,
        sheet_name=sheet_name,
        engine="openpyxl",
    )


def prepare_transactions_for_export(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Seleciona e formata as colunas destinadas ao usuário."""
    missing_columns = [
        column
        for column in REQUIRED_TRANSACTION_COLUMNS
        if column not in transactions.columns
    ]

    if missing_columns:
        raise ValueError(
            "Não foi possível exportar as transações. "
            "Colunas obrigatórias ausentes: "
            f"{', '.join(missing_columns)}"
        )

    export_data = transactions[
        REQUIRED_TRANSACTION_COLUMNS
    ].copy()

    export_data["data"] = (
        pd.to_datetime(
            export_data["data"],
            errors="coerce",
        )
        .dt.strftime("%Y-%m-%d")
    )

    export_data["valor"] = pd.to_numeric(
        export_data["valor"],
        errors="coerce",
    )

    return export_data


def export_transactions_to_excel(
    transactions: pd.DataFrame,
) -> bytes:
    """Gera um arquivo Excel com as transações informadas."""
    export_data = prepare_transactions_for_export(
        transactions
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        export_data.to_excel(
            writer,
            sheet_name=TRANSACTION_SHEET_NAME,
            index=False,
        )

        worksheet = writer.sheets[
            TRANSACTION_SHEET_NAME
        ]

        worksheet.freeze_panes = "A2"

        column_widths = {
            "A": 14,
            "B": 14,
            "C": 36,
            "D": 22,
            "E": 16,
        }

        for column, width in column_widths.items():
            worksheet.column_dimensions[
                column
            ].width = width

    return output.getvalue()


def create_excel_template() -> bytes:
    """Gera um modelo Excel vazio com instruções de preenchimento."""
    transactions_template = pd.DataFrame(
        columns=REQUIRED_TRANSACTION_COLUMNS
    )

    instructions = pd.DataFrame(
        {
            "Campo": [
                "data",
                "tipo",
                "descricao",
                "categoria",
                "valor",
            ],
            "Orientação": [
                "Use o formato AAAA-MM-DD.",
                "Use apenas receita ou despesa.",
                "Informe uma descrição curta.",
                "Informe uma categoria financeira.",
                "Use um número positivo, sem R$.",
            ],
            "Exemplo": [
                "2026-08-05",
                "despesa",
                "Compra no mercado",
                "Alimentação",
                "200.50",
            ],
        }
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        transactions_template.to_excel(
            writer,
            sheet_name=TRANSACTION_SHEET_NAME,
            index=False,
        )

        instructions.to_excel(
            writer,
            sheet_name=INSTRUCTIONS_SHEET_NAME,
            index=False,
        )

        transactions_sheet = writer.sheets[
            TRANSACTION_SHEET_NAME
        ]

        instructions_sheet = writer.sheets[
            INSTRUCTIONS_SHEET_NAME
        ]

        transactions_sheet.freeze_panes = "A2"
        instructions_sheet.freeze_panes = "A2"

        transaction_widths = {
            "A": 14,
            "B": 14,
            "C": 36,
            "D": 22,
            "E": 16,
        }

        for column, width in transaction_widths.items():
            transactions_sheet.column_dimensions[
                column
            ].width = width

        instruction_widths = {
            "A": 18,
            "B": 46,
            "C": 28,
        }

        for column, width in instruction_widths.items():
            instructions_sheet.column_dimensions[
                column
            ].width = width

    return output.getvalue()


def normalize_transaction_keys(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Normaliza os campos usados na comparação de transações."""
    normalized = prepare_transactions(
        transactions
    )

    normalized = normalized[
        REQUIRED_TRANSACTION_COLUMNS
    ].copy()

    normalized["data"] = (
        normalized["data"]
        .dt.strftime("%Y-%m-%d")
    )

    normalized["valor"] = (
        normalized["valor"]
        .round(2)
    )

    return normalized


def create_transactions_fingerprint(
    transactions: pd.DataFrame,
) -> str:
    """Cria uma identificação estável baseada no conteúdo do lote."""
    normalized = normalize_transaction_keys(
        transactions
    )

    # A ordem das linhas não deve alterar a identidade do mesmo lote.
    canonical = (
        normalized
        .sort_values(
            by=REQUIRED_TRANSACTION_COLUMNS,
            kind="stable",
        )
        .reset_index(drop=True)
    )

    canonical_content = canonical.to_csv(
        index=False,
        lineterminator="\n",
    )

    return hashlib.sha256(
        canonical_content.encode("utf-8")
    ).hexdigest()


def build_import_file_path(
    transactions: pd.DataFrame,
    import_dir: Path = IMPORTED_RAW_DIR,
) -> Path:
    """Cria o caminho de um lote usando sua identificação de conteúdo."""
    fingerprint = create_transactions_fingerprint(
        transactions
    )

    file_name = (
        "transacoes_importadas_"
        f"{fingerprint[:16]}.csv"
    )

    return import_dir / file_name


def save_imported_transactions(
    transactions: pd.DataFrame,
    import_dir: Path = IMPORTED_RAW_DIR,
) -> Path:
    """Salva um lote validado sem substituir importações anteriores."""
    import_path = build_import_file_path(
        transactions,
        import_dir=import_dir,
    )

    if import_path.exists():
        raise FileExistsError(
            "Este mesmo lote de transações "
            "já foi importado anteriormente."
        )

    import_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    transactions_to_save = (
        prepare_transactions_for_export(
            transactions
        )
    )

    transactions_to_save.to_csv(
        import_path,
        index=False,
        encoding="utf-8-sig",
    )

    return import_path


def split_imported_transactions_by_match(
    imported_transactions: pd.DataFrame,
    existing_transactions: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa linhas novas de ocorrências já presentes na base."""
    if imported_transactions.empty:
        empty = imported_transactions.copy()
        return empty, empty

    if existing_transactions.empty:
        return (
            imported_transactions.copy(),
            imported_transactions.iloc[0:0].copy(),
        )

    imported_normalized = normalize_transaction_keys(
        imported_transactions
    )

    existing_normalized = normalize_transaction_keys(
        existing_transactions
    )

    existing_counts = Counter(
        existing_normalized.itertuples(
            index=False,
            name=None,
        )
    )

    new_positions: list[int] = []
    matching_positions: list[int] = []

    for position, row in enumerate(
        imported_normalized.itertuples(
            index=False,
            name=None,
        )
    ):
        if existing_counts[row] > 0:
            matching_positions.append(position)
            existing_counts[row] -= 1
        else:
            new_positions.append(position)

    new_transactions = imported_transactions.iloc[
        new_positions
    ].copy()

    matching_transactions = imported_transactions.iloc[
        matching_positions
    ].copy()

    return (
        new_transactions,
        matching_transactions,
    )


def find_matching_transactions(
    imported_transactions: pd.DataFrame,
    existing_transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Retorna as ocorrências importadas já presentes na base."""
    _, matching_transactions = (
        split_imported_transactions_by_match(
            imported_transactions,
            existing_transactions,
        )
    )

    return matching_transactions