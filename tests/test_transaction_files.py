"""Testes de leitura, exportação e persistência de transações."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from src.transaction_files import (
    INSTRUCTIONS_SHEET_NAME,
    TRANSACTION_SHEET_NAME,
    build_import_file_path,
    create_excel_template,
    create_transactions_fingerprint,
    export_transactions_to_excel,
    find_matching_transactions,
    prepare_transactions_for_export,
    read_csv_transactions,
    read_excel_transactions,
    save_imported_transactions,
    split_imported_transactions_by_match,
)
from src.transaction_validation import (
    REQUIRED_TRANSACTION_COLUMNS,
)


def create_test_transactions() -> pd.DataFrame:
    """Cria transações válidas com colunas técnicas adicionais."""
    return pd.DataFrame(
        {
            "data": pd.to_datetime(
                [
                    "2026-08-01",
                    "2026-08-02",
                ]
            ),
            "tipo": [
                "receita",
                "despesa",
            ],
            "descricao": [
                "Bolsa-estágio",
                "Compra no mercado",
            ],
            "categoria": [
                "Trabalho",
                "Alimentação",
            ],
            "valor": [
                1600.00,
                200.50,
            ],
            "arquivo_origem": [
                "transacoes_2026_08.csv",
                "transacoes_2026_08.csv",
            ],
            "ano_mes": [
                "2026-08",
                "2026-08",
            ],
        }
    )


def test_read_csv_transactions_reads_uploaded_content() -> None:
    """Verifica a leitura de um CSV enviado em memória."""
    csv_content = (
        "data,tipo,descricao,categoria,valor\n"
        "2026-08-01,receita,Bolsa-estágio,Trabalho,1600.00\n"
    )

    source = BytesIO(
        csv_content.encode("utf-8-sig")
    )

    transactions = read_csv_transactions(source)

    assert len(transactions) == 1

    assert (
        transactions.columns.tolist()
        == REQUIRED_TRANSACTION_COLUMNS
    )

    assert transactions.loc[0, "tipo"] == "receita"
    assert transactions.loc[0, "valor"] == 1600.00


def test_prepare_transactions_for_export_removes_technical_columns() -> None:
    """Verifica se colunas internas são removidas da exportação."""
    transactions = create_test_transactions()

    result = prepare_transactions_for_export(
        transactions
    )

    assert (
        result.columns.tolist()
        == REQUIRED_TRANSACTION_COLUMNS
    )

    assert "arquivo_origem" not in result.columns
    assert "ano_mes" not in result.columns

    assert result["data"].tolist() == [
        "2026-08-01",
        "2026-08-02",
    ]


def test_prepare_transactions_for_export_rejects_missing_columns() -> None:
    """Impede exportação quando uma coluna obrigatória está ausente."""
    transactions = pd.DataFrame(
        {
            "data": ["2026-08-01"],
            "tipo": ["receita"],
            "descricao": ["Bolsa-estágio"],
            "valor": [1600.00],
        }
    )

    with pytest.raises(ValueError) as error:
        prepare_transactions_for_export(
            transactions
        )

    assert "categoria" in str(error.value)


def test_export_transactions_to_excel_can_be_imported_again() -> None:
    """Verifica se um arquivo exportado pode ser lido novamente."""
    transactions = create_test_transactions()

    excel_content = export_transactions_to_excel(
        transactions
    )

    imported_transactions = read_excel_transactions(
        BytesIO(excel_content)
    )

    assert (
        imported_transactions.columns.tolist()
        == REQUIRED_TRANSACTION_COLUMNS
    )

    assert len(imported_transactions) == 2

    assert (
        imported_transactions.loc[
            0,
            "descricao",
        ]
        == "Bolsa-estágio"
    )

    assert (
        imported_transactions.loc[
            1,
            "valor",
        ]
        == 200.50
    )


def test_create_excel_template_contains_expected_sheets() -> None:
    """Verifica as abas existentes no modelo Excel."""
    template_content = create_excel_template()

    excel_file = pd.ExcelFile(
        BytesIO(template_content),
        engine="openpyxl",
    )

    assert excel_file.sheet_names == [
        TRANSACTION_SHEET_NAME,
        INSTRUCTIONS_SHEET_NAME,
    ]


def test_create_excel_template_has_transaction_contract_columns() -> None:
    """Verifica as colunas do contrato na aba de transações."""
    template_content = create_excel_template()

    transactions_template = pd.read_excel(
        BytesIO(template_content),
        sheet_name=TRANSACTION_SHEET_NAME,
        engine="openpyxl",
    )

    assert transactions_template.empty

    assert (
        transactions_template.columns.tolist()
        == REQUIRED_TRANSACTION_COLUMNS
    )


def test_create_excel_template_contains_instructions() -> None:
    """Verifica o conteúdo básico da aba de instruções."""
    template_content = create_excel_template()

    instructions = pd.read_excel(
        BytesIO(template_content),
        sheet_name=INSTRUCTIONS_SHEET_NAME,
        engine="openpyxl",
    )

    assert len(instructions) == 5

    assert instructions.columns.tolist() == [
        "Campo",
        "Orientação",
        "Exemplo",
    ]

    assert (
        instructions["Campo"].tolist()
        == REQUIRED_TRANSACTION_COLUMNS
    )


def test_fingerprint_does_not_depend_on_row_order() -> None:
    """Mantém a identificação quando apenas a ordem das linhas muda."""
    transactions = create_test_transactions()

    reversed_transactions = (
        transactions
        .iloc[::-1]
        .reset_index(drop=True)
    )

    assert create_transactions_fingerprint(
        transactions
    ) == create_transactions_fingerprint(
        reversed_transactions
    )


def test_build_import_file_path_is_content_based(
    tmp_path,
) -> None:
    """Usa o conteúdo do lote para construir o caminho."""
    transactions = create_test_transactions()

    reversed_transactions = (
        transactions
        .iloc[::-1]
        .reset_index(drop=True)
    )

    first_path = build_import_file_path(
        transactions,
        import_dir=tmp_path,
    )

    second_path = build_import_file_path(
        reversed_transactions,
        import_dir=tmp_path,
    )

    modified_transactions = transactions.copy()

    modified_transactions.loc[
        0,
        "valor",
    ] = 1700.00

    different_path = build_import_file_path(
        modified_transactions,
        import_dir=tmp_path,
    )

    assert first_path == second_path
    assert first_path != different_path

    assert first_path.name.startswith(
        "transacoes_importadas_"
    )

    assert first_path.suffix == ".csv"


def test_save_imported_transactions_rejects_same_batch(
    tmp_path,
) -> None:
    """Impede que o mesmo lote seja salvo novamente."""
    transactions = create_test_transactions()

    saved_path = save_imported_transactions(
        transactions=transactions,
        import_dir=tmp_path,
    )

    assert saved_path.exists()

    with pytest.raises(FileExistsError):
        save_imported_transactions(
            transactions=transactions.iloc[::-1],
            import_dir=tmp_path,
        )


def test_find_matching_transactions_detects_existing_rows() -> None:
    """Identifica linhas importadas iguais às transações existentes."""
    imported_transactions = create_test_transactions()

    existing_transactions = (
        create_test_transactions()
        .head(1)
        .copy()
    )

    matches = find_matching_transactions(
        imported_transactions,
        existing_transactions,
    )

    assert len(matches) == 1

    assert (
        matches.iloc[0]["descricao"]
        == "Bolsa-estágio"
    )


def test_split_matching_transactions_respects_occurrence_count() -> None:
    """Não marca mais duplicatas do que as ocorrências existentes."""
    base_transaction = (
        create_test_transactions()
        .head(1)
        .copy()
    )

    imported_transactions = pd.concat(
        [
            base_transaction,
            base_transaction,
        ],
        ignore_index=True,
    )

    existing_transactions = base_transaction.copy()

    (
        new_transactions,
        matching_transactions,
    ) = split_imported_transactions_by_match(
        imported_transactions,
        existing_transactions,
    )

    assert len(matching_transactions) == 1
    assert len(new_transactions) == 1