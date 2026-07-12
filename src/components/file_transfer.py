"""Componente de importação e exportação de transações."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from scripts.etl_transacoes import run_etl_with_summary
from src.transaction_files import (
    build_import_file_path,
    create_excel_template,
    export_transactions_to_excel,
    read_csv_transactions,
    read_excel_transactions,
    save_imported_transactions,
    split_imported_transactions_by_match,
)
from src.transaction_validation import (
    split_transactions_by_validity,
    validate_required_columns,
)


EXCEL_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet"
)

SKIP_MATCHES = "skip_matches"
INCLUDE_MATCHES = "include_matches"


def read_uploaded_transactions(
    uploaded_file: Any,
) -> pd.DataFrame:
    """Lê as transações de acordo com a extensão enviada."""
    file_extension = Path(
        uploaded_file.name
    ).suffix.lower()

    if file_extension == ".csv":
        return read_csv_transactions(
            uploaded_file
        )

    if file_extension == ".xlsx":
        try:
            return read_excel_transactions(
                uploaded_file
            )
        except ValueError as error:
            if "Worksheet named" in str(error):
                raise ValueError(
                    "O arquivo Excel precisa conter uma aba "
                    "chamada 'Transacoes'."
                ) from error

            raise

    raise ValueError(
        "Formato não suportado. "
        "Envie um arquivo CSV ou XLSX."
    )


def render_import_result() -> None:
    """Exibe o resultado preservado após a atualização da página."""
    result = st.session_state.pop(
        "file_import_result",
        None,
    )

    if not result:
        return

    if result["success"]:
        st.success(
            f"{result['message']}\n\n"
            f"Linhas importadas: "
            f"{result['imported_transactions']} | "
            f"Total processado pelo ETL: "
            f"{result['processed_transactions']} | "
            f"Linhas rejeitadas pelo ETL: "
            f"{result['rejected_transactions']}"
        )
        return

    st.error(result["message"])


def render_file_downloads(
    transactions: pd.DataFrame,
) -> None:
    """Exibe downloads do modelo e do período atual."""
    with st.container(
        key="file-downloads",
    ):
        template_column, export_column = (
            st.columns(
                2,
                gap="small",
            )
        )

        with template_column:
            st.download_button(
                label="Baixar modelo Excel",
                data=create_excel_template(),
                file_name=(
                    "finantec_transacoes_template.xlsx"
                ),
                mime=EXCEL_MIME_TYPE,
                key="download-excel-template",
                use_container_width=True,
            )

            st.caption(
                "Modelo vazio com as colunas "
                "e instruções necessárias."
            )

        with export_column:
            if transactions.empty:
                st.info(
                    "Não há transações no período "
                    "atual para exportar."
                )
            else:
                st.download_button(
                    label="Exportar período atual",
                    data=export_transactions_to_excel(
                        transactions
                    ),
                    file_name=(
                        "finantec_transacoes_periodo.xlsx"
                    ),
                    mime=EXCEL_MIME_TYPE,
                    key="export-current-period",
                    use_container_width=True,
                )

                st.caption(
                    "Exporta somente as transações "
                    "do período selecionado."
                )


def render_validation_summary(
    valid_transactions: pd.DataFrame,
    rejected_transactions: pd.DataFrame,
) -> None:
    """Exibe a quantidade de linhas válidas e rejeitadas."""
    valid_count = len(
        valid_transactions
    )

    rejected_count = len(
        rejected_transactions
    )

    rejected_metric_key = (
        "import-validation-rejected-error"
        if rejected_count > 0
        else "import-validation-rejected-neutral"
    )

    valid_column, rejected_column = (
        st.columns(
            2,
            gap="small",
        )
    )

    with valid_column:
        with st.container(
            key="import-validation-valid",
        ):
            st.metric(
                "Linhas válidas",
                valid_count,
            )

    with rejected_column:
        with st.container(
            key=rejected_metric_key,
        ):
            st.metric(
                "Linhas com erro",
                rejected_count,
            )

    if rejected_transactions.empty:
        st.success(
            "O arquivo passou pela validação."
        )
    else:
        st.warning(
            "O arquivo possui linhas que precisam "
            "ser corrigidas antes da importação."
        )

def render_matching_transactions(
    matching_transactions: pd.DataFrame,
) -> str:
    """Exibe possíveis duplicatas e solicita a estratégia de importação."""
    st.warning(
        f"Foram encontradas "
        f"{len(matching_transactions)} ocorrência(s) "
        "correspondente(s) a transações já existentes."
    )

    with st.expander(
        "Ver possíveis duplicatas"
    ):
        preview = matching_transactions.copy()

        preview["data"] = (
            pd.to_datetime(
                preview["data"],
                errors="coerce",
            )
            .dt.strftime("%Y-%m-%d")
        )

        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True,
        )

    return st.radio(
        "Como deseja tratar essas linhas?",
        options=[
            SKIP_MATCHES,
            INCLUDE_MATCHES,
        ],
        format_func=lambda option: {
            SKIP_MATCHES: (
                "Ignorar linhas que já existem "
                "(recomendado)"
            ),
            INCLUDE_MATCHES: (
                "Importar todas as linhas, "
                "incluindo possíveis duplicatas"
            ),
        }[option],
        index=0,
        key="duplicate_import_strategy",
    )


def render_import_confirmation(
    valid_transactions: pd.DataFrame,
    existing_transactions: pd.DataFrame,
) -> bool:
    """Solicita confirmação e importa o lote selecionado."""
    (
        new_transactions,
        matching_transactions,
    ) = split_imported_transactions_by_match(
        valid_transactions,
        existing_transactions,
    )

    duplicate_strategy = SKIP_MATCHES

    if not matching_transactions.empty:
        duplicate_strategy = (
            render_matching_transactions(
                matching_transactions
            )
        )

    if duplicate_strategy == INCLUDE_MATCHES:
        transactions_to_import = (
            valid_transactions.copy()
        )
    else:
        transactions_to_import = (
            new_transactions.copy()
        )

    (
        total_column,
        import_column,
    ) = st.columns(
        2,
        gap="small",
    )

    with total_column:
        with st.container(
            key="import-file-valid-metric",
        ):
            st.metric(
                "Linhas válidas no arquivo",
                len(valid_transactions),
            )

    with import_column:
        with st.container(
            key="import-ready-metric",
        ):
            st.metric(
                "Linhas que serão importadas",
                len(transactions_to_import),
            )

    if transactions_to_import.empty:
        st.info(
            "Nenhuma linha nova está disponível para importação. "
            "Todas as transações do arquivo já existem na base."
        )
        return False

    import_path = build_import_file_path(
        transactions_to_import
    )

    batch_already_imported = (
        import_path.exists()
    )

    if batch_already_imported:
        st.warning(
            "Este mesmo lote de transações "
            "já foi importado anteriormente."
        )

    st.caption(
        "As linhas selecionadas serão salvas como um lote local "
        "e o pipeline ETL será executado novamente."
    )

    import_confirmed = st.button(
        "Confirmar importação",
        key="confirm-transaction-import",
        type="primary",
        disabled=batch_already_imported,
        use_container_width=False,
    )

    if not import_confirmed:
        return False

    try:
        saved_path = (
            save_imported_transactions(
                transactions_to_import
            )
        )

        result = (
            run_etl_with_summary()
        )

        st.session_state[
            "file_import_result"
        ] = {
            "success": True,
            "message": (
                "Lote importado e processado "
                f"com sucesso: {saved_path.name}"
            ),
            "imported_transactions": len(
                transactions_to_import
            ),
            "processed_transactions": result[
                "transacoes_processadas"
            ],
            "rejected_transactions": result[
                "transacoes_rejeitadas"
            ],
        }

        return True

    except Exception as error:
        st.session_state[
            "file_import_result"
        ] = {
            "success": False,
            "message": (
                "Não foi possível concluir "
                f"a importação: {error}"
            ),
        }

        return True


def render_uploaded_file_preview(
    uploaded_file: Any,
    existing_transactions: pd.DataFrame,
) -> bool:
    """Valida, exibe e permite confirmar o arquivo enviado."""
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
        return False

    if transactions.empty:
        st.info(
            "O arquivo possui as colunas corretas, "
            "mas não contém nenhuma transação."
        )
        return False

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
            valid_preview = valid_transactions.copy()

            valid_preview["data"] = (
                valid_preview["data"]
                .dt.strftime("%Y-%m-%d")
            )

            st.dataframe(
                valid_preview,
                use_container_width=True,
                hide_index=True,
            )

    with rejected_tab:
        if rejected_transactions.empty:
            st.success(
                "Nenhuma linha foi rejeitada."
            )
        else:
            rejected_preview = (
                rejected_transactions.copy()
            )

            rejected_preview["data"] = (
                rejected_preview["data"]
                .dt.strftime("%Y-%m-%d")
            )

            st.dataframe(
                rejected_preview,
                use_container_width=True,
                hide_index=True,
            )

    if not rejected_transactions.empty:
        st.info(
            "Corrija todas as linhas com erro e envie "
            "o arquivo novamente para liberar a importação."
        )
        return False

    if valid_transactions.empty:
        return False

    return render_import_confirmation(
        valid_transactions=valid_transactions,
        existing_transactions=existing_transactions,
    )


def render_transaction_file_tools(
    period_transactions: pd.DataFrame,
    existing_transactions: pd.DataFrame,
) -> bool:
    """Exibe download, prévia e confirmação de importação."""
    st.subheader("Importação e exportação")

    render_import_result()

    st.caption(
        "Baixe o modelo, exporte os dados atuais "
        "ou importe um novo lote de transações."
    )

    render_file_downloads(
        period_transactions
    )

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
            "O arquivo deve seguir o contrato "
            "de dados do FinanTec."
        ),
    )

    if uploaded_file is None:
        return False

    return render_uploaded_file_preview(
        uploaded_file=uploaded_file,
        existing_transactions=existing_transactions,
    )