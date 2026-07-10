"""Leitura e geração de arquivos de transações do FinanTec."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from src.transaction_validation import (
    REQUIRED_TRANSACTION_COLUMNS,
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
    """Lê transações de um arquivo CSV enviado ou armazenado localmente."""
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
            worksheet.column_dimensions[column].width = width

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