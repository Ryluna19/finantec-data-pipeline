"""Componente de importação e exportação de arquivos de transações."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.transaction_files import (
    create_excel_template,
    export_transactions_to_excel,
    read_csv_transactions,
    read_excel_transactions,
)
from src.transaction_validation import (
    split_transactions_by_validity,
    validate_required_columns,
)


EXCEL_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet"
)


def read_uploaded_transactions(
    uploaded_file: Any,
) -> pd.DataFrame:
    """Lê as transações de acordo com a extensão do arquivo enviado."""
    file_name = uploaded_file.name
    file_extension = Path(file_name).suffix.lower()

    if file_extension == ".csv":
        return read_csv_transactions(uploaded_file)

    if file_extension == ".xlsx":
        try:
            return read_excel_transactions(uploaded_file)
        except ValueError as error:
            if "Worksheet named" in str(error):
                raise ValueError(
                    "O arquivo Excel precisa conter uma aba "
                    "chamada 'Transacoes'."
                ) from error

            raise

    raise ValueError(
        "Formato não suportado. Envie um arquivo CSV ou XLSX."
    )


def render_file_downloads(
    transactions: pd.DataFrame,
) -> None:
    """Exibe os downloads do modelo e das transações do período."""
    template_column, export_column = st.columns(2)

    with template_column:
        template_content = create_excel_template()

        st.download_button(
            label="Baixar modelo Excel",
            data=template_content,
            file_name="finantec_transacoes_template.xlsx",
            mime=EXCEL_MIME_TYPE,
            use_container_width=True,
        )

        st.caption(
            "Modelo vazio com as colunas e instruções necessárias."
        )

    with export_column:
        if transactions.empty:
            st.info(
                "Não há transações no período atual para exportar."
            )
            return

        export_content = export_transactions_to_excel(
            transactions
        )

        st.download_button(
            label="Exportar período atual",
            data=export_content,
            file_name="finantec_transacoes_periodo.xlsx",
            mime=EXCEL_MIME_TYPE,
            use_container_width=True,
        )

        st.caption(
            "Exporta somente as transações do período selecionado."
        )


def render_validation_summary(
    valid_transactions: pd.DataFrame,
    rejected_transactions: pd.DataFrame,
) -> None:
    """Exibe a quantidade de linhas válidas e rejeitadas."""
    valid_column, rejected_column = st.columns(2)

    valid_column.metric(
        "Linhas válidas",
        len(valid_transactions),
    )

    rejected_column.metric(
        "Linhas com erro",
        len(rejected_transactions),
    )

    if rejected_transactions.empty:
        st.success(
            "O arquivo passou pela validação e não possui linhas "
            "com erro."
        )
    else:
        st.warning(
            "O arquivo possui linhas que precisam ser corrigidas "
            "antes da importação."
        )


def render_uploaded_file_preview(
    uploaded_file: Any,
) -> None:
    """Lê, valida e exibe uma prévia do arquivo enviado."""
    try:
        transactions = read_uploaded_transactions(
            uploaded_file
        )

        validate_required_columns(
            transactions,
            Path(uploaded_file.name),
        )

    except (
        ValueError,
        OSError,
        pd.errors.EmptyDataError,
    ) as error:
        st.error(
            f"Não foi possível ler o arquivo: {error}"
        )
        return

    if transactions.empty:
        st.info(
            "O arquivo possui as colunas corretas, mas não contém "
            "nenhuma transação."
        )
        return

    (
        valid_transactions,
        rejected_transactions,
    ) = split_transactions_by_validity(
        transactions
    )

    render_validation_summary(
        valid_transactions,
        rejected_transactions,
    )

    valid_tab, rejected_tab = st.tabs(
        [
            "Linhas válidas",
            "Linhas com erro",
        ]
    )

    with valid_tab:
        if valid_transactions.empty:
            st.info(
                "Nenhuma linha válida foi encontrada."
            )
        else:
            st.dataframe(
                valid_transactions,
                use_container_width=True,
                hide_index=True,
            )

    with rejected_tab:
        if rejected_transactions.empty:
            st.success(
                "Nenhuma linha foi rejeitada."
            )
        else:
            st.dataframe(
                rejected_transactions,
                use_container_width=True,
                hide_index=True,
            )

    st.info(
        "Esta é apenas uma prévia. Nenhum dado foi salvo, "
        "processado pelo ETL ou inserido no banco."
    )


def render_transaction_file_tools(
    transactions: pd.DataFrame,
) -> None:
    """Exibe as ferramentas de download, exportação e prévia."""
    st.subheader("Importação e exportação")

    st.caption(
        "Baixe o modelo, exporte os dados atuais ou valide "
        "um arquivo antes de importá-lo."
    )

    render_file_downloads(transactions)

    st.divider()

    uploaded_file = st.file_uploader(
        "Selecionar arquivo de transações",
        type=[
            "xlsx",
            "csv",
        ],
        accept_multiple_files=False,
        key="transaction_file_upload",
        help=(
            "O arquivo deve seguir o contrato de dados do FinanTec."
        ),
    )

    if uploaded_file is None:
        return

    render_uploaded_file_preview(uploaded_file)