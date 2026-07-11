"""Leitura, geração e persistência de arquivos de transações."""

from __future__ import annotations

import hashlib
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd
import unicodedata

from src.transaction_validation import (
    REQUIRED_TRANSACTION_COLUMNS,
    prepare_transactions,
)

from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import (
    Table,
    TableStyleInfo,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

IMPORTED_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "imported"

TRANSACTION_SHEET_NAME = "Transacoes"
INSTRUCTIONS_SHEET_NAME = "Instrucoes"

TRANSACTION_HEADER_LABELS = {
    "data": "DATA",
    "tipo": "TIPO",
    "descricao": "DESCRIÇÃO",
    "categoria": "CATEGORIA",
    "valor": "VALOR",
}

EXCEL_HEADER_COLOR = "1F2937"
EXCEL_HEADER_TEXT_COLOR = "FFFFFF"
EXCEL_ACCENT_COLOR = "F97316"
EXCEL_BORDER_COLOR = "D1D5DB"

EXCEL_TRANSACTION_COLUMN_WIDTHS = {
    "A": 16,
    "B": 14,
    "C": 38,
    "D": 24,
    "E": 18,
}

EXCEL_INSTRUCTION_COLUMN_WIDTHS = {
    "A": 18,
    "B": 48,
    "C": 30,
}

FileSource = str | Path | BinaryIO


def _rewind_file(source: FileSource) -> None:
    """Reposiciona arquivos em memória antes de uma nova leitura."""
    seek = getattr(source, "seek", None)

    if callable(seek):
        seek(0)


def normalize_transaction_headers(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Normaliza os cabeçalhos recebidos para o contrato interno."""
    normalized_transactions = transactions.copy()

    normalized_columns = []

    for column in normalized_transactions.columns:
        normalized_column = unicodedata.normalize(
            "NFKD",
            str(column),
        )

        normalized_column = normalized_column.encode(
            "ascii",
            "ignore",
        ).decode("ascii")

        normalized_column = normalized_column.strip().lower().replace(" ", "_")

        normalized_columns.append(normalized_column)

    normalized_transactions.columns = normalized_columns

    return normalized_transactions


def read_csv_transactions(
    source: FileSource,
) -> pd.DataFrame:
    """Lê e normaliza transações de um arquivo CSV."""
    _rewind_file(source)

    transactions = pd.read_csv(
        source,
        encoding="utf-8-sig",
    )

    return normalize_transaction_headers(transactions)


def read_excel_transactions(
    source: FileSource,
    sheet_name: str = TRANSACTION_SHEET_NAME,
) -> pd.DataFrame:
    """Lê e normaliza a planilha principal de um arquivo Excel."""
    _rewind_file(source)

    transactions = pd.read_excel(
        source,
        sheet_name=sheet_name,
        engine="openpyxl",
    )

    return normalize_transaction_headers(transactions)


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

    export_data = transactions[REQUIRED_TRANSACTION_COLUMNS].copy()

    export_data["data"] = pd.to_datetime(
        export_data["data"],
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")

    export_data["valor"] = pd.to_numeric(
        export_data["valor"],
        errors="coerce",
    )

    return export_data


def _style_header(
    worksheet,
    column_count: int,
) -> None:
    """Aplica cabeçalho grafite com detalhe inferior laranja."""
    header_fill = PatternFill(
        fill_type="solid",
        fgColor=EXCEL_HEADER_COLOR,
    )

    header_font = Font(
        color=EXCEL_HEADER_TEXT_COLOR,
        bold=True,
    )

    regular_side = Side(
        style="thin",
        color=EXCEL_BORDER_COLOR,
    )

    accent_side = Side(
        style="medium",
        color=EXCEL_ACCENT_COLOR,
    )

    header_border = Border(
        left=regular_side,
        right=regular_side,
        bottom=accent_side,
    )

    for cell in worksheet[1][:column_count]:
        cell.fill = header_fill
        cell.font = header_font
        cell.border = header_border
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    worksheet.row_dimensions[1].height = 26


def _set_column_widths(
    worksheet,
    widths: dict[str, int],
) -> None:
    """Define larguras adequadas para as colunas da planilha."""
    for column, width in widths.items():
        worksheet.column_dimensions[column].width = width


def _add_transaction_type_validation(
    worksheet,
    last_row: int = 1000,
) -> None:
    """Adiciona uma lista suspensa para o tipo da transação."""
    type_validation = DataValidation(
        type="list",
        formula1='"receita,despesa"',
        allow_blank=True,
    )

    type_validation.error = "Use somente receita ou despesa."

    type_validation.errorTitle = "Tipo de transação inválido"

    type_validation.prompt = "Selecione receita ou despesa."

    type_validation.promptTitle = "Tipo da transação"

    type_validation.showErrorMessage = True
    type_validation.showInputMessage = True

    worksheet.add_data_validation(type_validation)

    type_validation.add(f"B2:B{last_row}")


def _add_transaction_date_validation(
    worksheet,
    last_row: int = 1000,
) -> None:
    """Restringe a coluna de data a valores válidos."""
    date_validation = DataValidation(
        type="date",
        operator="between",
        formula1="DATE(2000,1,1)",
        formula2="DATE(2100,12,31)",
        allow_blank=True,
    )

    date_validation.error = "Informe uma data válida no formato DD/MM/AAAA."

    date_validation.errorTitle = "Data inválida"

    date_validation.prompt = "Informe a data da transação no formato DD/MM/AAAA."

    date_validation.promptTitle = "Data da transação"
    date_validation.showErrorMessage = True
    date_validation.showInputMessage = True

    worksheet.add_data_validation(date_validation)

    date_validation.add(f"A2:A{last_row}")


def _add_transaction_amount_validation(
    worksheet,
    last_row: int = 1000,
) -> None:
    """Restringe a coluna de valor a números positivos."""
    amount_validation = DataValidation(
        type="decimal",
        operator="greaterThan",
        formula1="0",
        allow_blank=True,
    )

    amount_validation.error = "Informe um valor numérico maior que zero."

    amount_validation.errorTitle = "Valor inválido"

    amount_validation.prompt = "Informe somente o valor numérico, sem escrever R$."

    amount_validation.promptTitle = "Valor da transação"
    amount_validation.showErrorMessage = True
    amount_validation.showInputMessage = True

    worksheet.add_data_validation(amount_validation)

    amount_validation.add(f"E2:E{last_row}")


def _format_transaction_columns(
    worksheet,
    last_row: int,
) -> None:
    """Aplica formatos e alinhamentos por tipo de informação."""
    centered_alignment = Alignment(
        horizontal="center",
        vertical="center",
    )

    left_alignment = Alignment(
        horizontal="left",
        vertical="center",
        wrap_text=True,
    )

    right_alignment = Alignment(
        horizontal="right",
        vertical="center",
    )

    for row_number in range(
        2,
        last_row + 1,
    ):
        date_cell = worksheet[f"A{row_number}"]
        type_cell = worksheet[f"B{row_number}"]
        description_cell = worksheet[f"C{row_number}"]
        category_cell = worksheet[f"D{row_number}"]
        amount_cell = worksheet[f"E{row_number}"]

        date_cell.number_format = "dd/mm/yyyy"
        amount_cell.number_format = "R$ #,##0.00"

        date_cell.alignment = centered_alignment
        type_cell.alignment = centered_alignment

        description_cell.alignment = left_alignment
        category_cell.alignment = left_alignment

        # Valores à direita facilitam comparar quantias verticalmente.
        amount_cell.alignment = right_alignment

        worksheet.row_dimensions[row_number].height = 22


def _style_transaction_sheet(
    worksheet,
    data_row_count: int,
    enable_input_validation: bool = False,
) -> None:
    """Configura aparência e validações da aba de transações."""
    _style_header(
        worksheet,
        column_count=5,
    )

    _set_column_widths(
        worksheet,
        EXCEL_TRANSACTION_COLUMN_WIDTHS,
    )

    worksheet.freeze_panes = "A2"

    # As linhas de grade ajudam no preenchimento manual.
    worksheet.sheet_view.showGridLines = True

    worksheet.sheet_properties.tabColor = EXCEL_ACCENT_COLOR

    if enable_input_validation:
        last_row = 1000

        worksheet.auto_filter.ref = f"A1:E{last_row}"

        _add_transaction_date_validation(
            worksheet,
            last_row=last_row,
        )

        _add_transaction_type_validation(
            worksheet,
            last_row=last_row,
        )

        _add_transaction_amount_validation(
            worksheet,
            last_row=last_row,
        )

        _format_transaction_columns(
            worksheet,
            last_row=last_row,
        )

        return

    last_row = data_row_count + 1

    if data_row_count <= 0:
        return

    table_reference = f"A1:E{last_row}"

    worksheet.auto_filter.ref = table_reference

    _format_transaction_columns(
        worksheet,
        last_row=last_row,
    )

    transactions_table = Table(
        displayName="FinanTecTransactions",
        ref=table_reference,
    )

    transactions_table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )

    worksheet.add_table(transactions_table)


def _style_instructions_sheet(
    worksheet,
) -> None:
    """Organiza visualmente a aba de instruções."""
    _style_header(
        worksheet,
        column_count=3,
    )

    _set_column_widths(
        worksheet,
        EXCEL_INSTRUCTION_COLUMN_WIDTHS,
    )

    worksheet.freeze_panes = "A2"
    worksheet.sheet_view.showGridLines = False
    worksheet.auto_filter.ref = "A1:C6"

    for row in worksheet.iter_rows(
        min_row=2,
        max_row=6,
        min_col=1,
        max_col=3,
    ):
        for cell in row:
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )


def export_transactions_to_excel(
    transactions: pd.DataFrame,
) -> bytes:
    """Gera um arquivo Excel formatado com as transações."""
    export_data = prepare_transactions_for_export(transactions)

    excel_data = export_data.copy()

    # Mantém datas como valores reais do Excel, não apenas texto.
    excel_data["data"] = pd.to_datetime(
        excel_data["data"],
        errors="coerce",
    )
    excel_data = excel_data.rename(columns=TRANSACTION_HEADER_LABELS)

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        excel_data.to_excel(
            writer,
            sheet_name=TRANSACTION_SHEET_NAME,
            index=False,
        )

        worksheet = writer.sheets[TRANSACTION_SHEET_NAME]

        _style_transaction_sheet(
            worksheet,
            data_row_count=len(excel_data),
        )

    return output.getvalue()


def create_excel_template() -> bytes:
    """Gera um modelo Excel formatado com instruções."""
    transactions_template = pd.DataFrame(
        columns=[
            TRANSACTION_HEADER_LABELS[column] for column in REQUIRED_TRANSACTION_COLUMNS
        ]
    )

    instructions = pd.DataFrame(
        {
            "CAMPO": [
                "data",
                "tipo",
                "descricao",
                "categoria",
                "valor",
            ],
            "ORIENTAÇÃO": [
                (
                    "Use uma data válida. "
                    "A planilha exibirá DD/MM/AAAA."
                ),
                "Selecione receita ou despesa.",
                "Informe uma descrição curta.",
                "Informe uma categoria financeira.",
                "Use um número positivo, sem R$.",
            ],
            "EXEMPLO": [
                "05/08/2026",
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

        transactions_sheet = writer.sheets[TRANSACTION_SHEET_NAME]

        instructions_sheet = writer.sheets[INSTRUCTIONS_SHEET_NAME]

        _style_transaction_sheet(
            transactions_sheet,
            data_row_count=0,
            enable_input_validation=True,
        )

        _style_instructions_sheet(instructions_sheet)

    return output.getvalue()


def normalize_transaction_keys(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Normaliza os campos usados na comparação de transações."""
    normalized = prepare_transactions(transactions)

    normalized = normalized[REQUIRED_TRANSACTION_COLUMNS].copy()

    normalized["data"] = normalized["data"].dt.strftime("%Y-%m-%d")

    normalized["valor"] = normalized["valor"].round(2)

    return normalized


def create_transactions_fingerprint(
    transactions: pd.DataFrame,
) -> str:
    """Cria uma identificação estável baseada no conteúdo do lote."""
    normalized = normalize_transaction_keys(transactions)

    # A ordem das linhas não deve alterar a identidade do mesmo lote.
    canonical = normalized.sort_values(
        by=REQUIRED_TRANSACTION_COLUMNS,
        kind="stable",
    ).reset_index(drop=True)

    canonical_content = canonical.to_csv(
        index=False,
        lineterminator="\n",
    )

    return hashlib.sha256(canonical_content.encode("utf-8")).hexdigest()


def build_import_file_path(
    transactions: pd.DataFrame,
    import_dir: Path = IMPORTED_RAW_DIR,
) -> Path:
    """Cria o caminho de um lote usando sua identificação de conteúdo."""
    fingerprint = create_transactions_fingerprint(transactions)

    file_name = "transacoes_importadas_" f"{fingerprint[:16]}.csv"

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
            "Este mesmo lote de transações " "já foi importado anteriormente."
        )

    import_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    transactions_to_save = prepare_transactions_for_export(transactions)

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

    imported_normalized = normalize_transaction_keys(imported_transactions)

    existing_normalized = normalize_transaction_keys(existing_transactions)

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

    new_transactions = imported_transactions.iloc[new_positions].copy()

    matching_transactions = imported_transactions.iloc[matching_positions].copy()

    return (
        new_transactions,
        matching_transactions,
    )


def find_matching_transactions(
    imported_transactions: pd.DataFrame,
    existing_transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Retorna as ocorrências importadas já presentes na base."""
    _, matching_transactions = split_imported_transactions_by_match(
        imported_transactions,
        existing_transactions,
    )

    return matching_transactions
