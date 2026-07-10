"""Testes de leitura e geração de arquivos de transações."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from src.transaction_files import (
    INSTRUCTIONS_SHEET_NAME,
    TRANSACTION_SHEET_NAME,
    create_excel_template,
    export_transactions_to_excel,
    prepare_transactions_for_export,
    read_csv_transactions,
    read_excel_transactions,
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


def test_read_csv_transactions_reads_uploaded_content():
    csv_content = (
        "data,tipo,descricao,categoria,valor\n"
        "2026-08-01,receita,Bolsa-estágio,Trabalho,1600.00\n"
    )

    source = BytesIO(
        csv_content.encode("utf-8-sig")
    )

    transactions = read_csv_transactions(source)

    assert len(transactions) == 1
    assert transactions.columns.tolist() == (
        REQUIRED_TRANSACTION_COLUMNS
    )
    assert transactions.loc[0, "tipo"] == "receita"
    assert transactions.loc[0, "valor"] == 1600.00


def test_prepare_transactions_for_export_removes_technical_columns():
    transactions = create_test_transactions()

    result = prepare_transactions_for_export(
        transactions
    )

    assert result.columns.tolist() == (
        REQUIRED_TRANSACTION_COLUMNS
    )

    assert "arquivo_origem" not in result.columns
    assert "ano_mes" not in result.columns

    assert result["data"].tolist() == [
        "2026-08-01",
        "2026-08-02",
    ]


def test_prepare_transactions_for_export_rejects_missing_columns():
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


def test_export_transactions_to_excel_can_be_imported_again():
    transactions = create_test_transactions()

    excel_content = export_transactions_to_excel(
        transactions
    )

    imported_transactions = read_excel_transactions(
        BytesIO(excel_content)
    )

    assert imported_transactions.columns.tolist() == (
        REQUIRED_TRANSACTION_COLUMNS
    )

    assert len(imported_transactions) == 2

    assert imported_transactions.loc[
        0,
        "descricao",
    ] == "Bolsa-estágio"

    assert imported_transactions.loc[
        1,
        "valor",
    ] == 200.50


def test_create_excel_template_contains_expected_sheets():
    template_content = create_excel_template()

    excel_file = pd.ExcelFile(
        BytesIO(template_content),
        engine="openpyxl",
    )

    assert excel_file.sheet_names == [
        TRANSACTION_SHEET_NAME,
        INSTRUCTIONS_SHEET_NAME,
    ]


def test_create_excel_template_has_transaction_contract_columns():
    template_content = create_excel_template()

    transactions_template = pd.read_excel(
        BytesIO(template_content),
        sheet_name=TRANSACTION_SHEET_NAME,
        engine="openpyxl",
    )

    assert transactions_template.empty

    assert transactions_template.columns.tolist() == (
        REQUIRED_TRANSACTION_COLUMNS
    )


def test_create_excel_template_contains_instructions():
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

    assert instructions["Campo"].tolist() == (
        REQUIRED_TRANSACTION_COLUMNS
    )