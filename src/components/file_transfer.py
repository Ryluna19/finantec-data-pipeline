"""Componente de importação e exportação de transações."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from components.data_management import (
    DATA_MODE_KEY,
)
from scripts.etl_transacoes import (
    ARQUIVO_BANCO,
    TABELA_TRANSACOES,
)
from src.import_transaction_database_service import (
    save_imported_transactions_to_database,
)
from src.transaction_files import (
    create_excel_template,
    export_transactions_to_excel,
    read_csv_transactions,
    read_excel_transactions,
    split_imported_transactions_by_match,
)
from src.transaction_validation import (
    split_transactions_by_validity,
    validate_required_columns,
)
from src.user_context import (
    get_current_user_id,
)


EXCEL_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet"
)

SKIP_MATCHES = "skip_matches"
INCLUDE_MATCHES = "include_matches"
IMPORT_WIDGET_VERSION_KEY = (
    "transaction_import_widget_version"
)

def _get_import_widget_version() -> int:
    """Retorna a versão atual dos widgets de importação."""
    if (
        IMPORT_WIDGET_VERSION_KEY
        not in st.session_state
    ):
        st.session_state[
            IMPORT_WIDGET_VERSION_KEY
        ] = 0

    return int(
        st.session_state[
            IMPORT_WIDGET_VERSION_KEY
        ]
    )


def _advance_import_widget_version() -> None:
    """Recria os widgets após uma importação concluída."""
    current_version = (
        _get_import_widget_version()
    )

    st.session_state[
        IMPORT_WIDGET_VERSION_KEY
    ] = (
        current_version + 1
    )


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
            if (
                "Worksheet named"
                in str(
                    error
                )
            ):
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
            "Linhas importadas: "
            f"{result['imported_transactions']}."
        )

        return

    st.error(
        result["message"]
    )


def render_file_downloads(
    transactions: pd.DataFrame,
) -> None:
    """Exibe downloads do modelo e do período atual."""
    with st.container(
        key="file-downloads",
    ):
        (
            template_column,
            export_column,
        ) = st.columns(
            2,
            gap="small",
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

    (
        valid_column,
        rejected_column,
    ) = st.columns(
        2,
        gap="small",
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
) -> str | None:
    """Exibe duplicatas e exige uma escolha explícita."""
    st.warning(
        "Foram encontradas "
        f"{len(matching_transactions)} ocorrência(s) "
        "correspondente(s) a transações já existentes."
    )

    with st.expander(
        "Ver possíveis duplicatas"
    ):
        preview = (
            matching_transactions.copy()
        )

        preview["data"] = (
            pd.to_datetime(
                preview["data"],
                errors="coerce",
            )
            .dt.strftime(
                "%Y-%m-%d"
            )
        )

        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True,
        )

    widget_version = (
        _get_import_widget_version()
    )

    return st.radio(
        "Como deseja tratar essas linhas?",
        options=[
            SKIP_MATCHES,
            INCLUDE_MATCHES,
        ],
        index=None,
        format_func=lambda option: {
            SKIP_MATCHES: (
                "Ignorar linhas que já existem"
            ),
            INCLUDE_MATCHES: (
                "Importar todas as linhas, "
                "incluindo possíveis duplicatas"
            ),
        }[
            option
        ],
        key=(
            "duplicate_import_strategy_"
            f"{widget_version}"
        ),
    )


def render_import_confirmation(
    valid_transactions: pd.DataFrame,
    existing_transactions: pd.DataFrame,
) -> bool:
    """Solicita uma decisão e importa o lote selecionado."""
    (
        new_transactions,
        matching_transactions,
    ) = split_imported_transactions_by_match(
        valid_transactions,
        existing_transactions,
    )

    duplicate_strategy: str | None = (
        SKIP_MATCHES
    )

    if not matching_transactions.empty:
        duplicate_strategy = (
            render_matching_transactions(
                matching_transactions
            )
        )

        if duplicate_strategy is None:
            st.info(
                "Escolha como tratar as linhas "
                "já existentes para continuar."
            )

            return False

    if (
        duplicate_strategy
        == INCLUDE_MATCHES
    ):
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
                len(
                    valid_transactions
                ),
            )

    with import_column:
        with st.container(
            key="import-ready-metric",
        ):
            st.metric(
                "Linhas que serão importadas",
                len(
                    transactions_to_import
                ),
            )

    widget_version = (
        _get_import_widget_version()
    )

    if transactions_to_import.empty:
        st.info(
            "Com a opção escolhida, nenhuma linha "
            "será importada porque todas já existem."
        )

        st.button(
            "Confirmar importação",
            key=(
                "confirm-transaction-import-"
                f"{widget_version}"
            ),
            type="primary",
            disabled=True,
            use_container_width=False,
        )

        return False

    st.caption(
        "As linhas selecionadas serão inseridas "
        "diretamente no banco local."
    )

    import_confirmed = st.button(
        "Confirmar importação",
        key=(
            "confirm-transaction-import-"
            f"{widget_version}"
        ),
        type="primary",
        use_container_width=False,
    )

    if not import_confirmed:
        return False

    try:
        inserted_count = (
            save_imported_transactions_to_database(
                transactions=(
                    transactions_to_import
                ),
                database_path=ARQUIVO_BANCO,
                table_name=(
                    TABELA_TRANSACOES
                ),
                user_id=(
                    get_current_user_id()
                ),
            )
        )

        st.session_state[
            DATA_MODE_KEY
        ] = "user"

        st.session_state[
            "file_import_result"
        ] = {
            "success": True,
            "message": (
                "Transações importadas diretamente "
                "para o banco local."
            ),
            "imported_transactions": (
                inserted_count
            ),
        }

        _advance_import_widget_version()

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
        transactions = (
            read_uploaded_transactions(
                uploaded_file
            )
        )

        validate_required_columns(
            transactions,
            Path(
                uploaded_file.name
            ),
        )

    except (
        ValueError,
        OSError,
        pd.errors.EmptyDataError,
    ) as error:
        st.error(
            "Não foi possível ler o arquivo: "
            f"{error}"
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

    (
        valid_tab,
        rejected_tab,
    ) = st.tabs(
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
            valid_preview = (
                valid_transactions.copy()
            )

            valid_preview["data"] = (
                valid_preview["data"]
                .dt.strftime(
                    "%Y-%m-%d"
                )
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
                .dt.strftime(
                    "%Y-%m-%d"
                )
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
        valid_transactions=(
            valid_transactions
        ),
        existing_transactions=(
            existing_transactions
        ),
    )


def render_transaction_file_tools(
    period_transactions: pd.DataFrame,
    existing_transactions: pd.DataFrame,
) -> bool:
    """Exibe download, prévia e confirmação de importação."""
    st.subheader(
        "Importação e exportação"
    )

    render_import_result()

    st.caption(
        "Baixe o modelo, exporte os dados atuais "
        "ou importe um novo lote de transações."
    )

    render_file_downloads(
        period_transactions
    )

    st.divider()

    widget_version = (
        _get_import_widget_version()
    )

    uploaded_file = st.file_uploader(
        "Selecionar arquivo de transações",
        type=[
            "xlsx",
            "csv",
        ],
        accept_multiple_files=False,
        key=(
            "transaction_file_upload_"
            f"{widget_version}"
        ),
        help=(
            "O arquivo deve seguir o contrato "
            "de dados do FinanTec."
        ),
    )

    if uploaded_file is None:
        return False

    return render_uploaded_file_preview(
        uploaded_file=uploaded_file,
        existing_transactions=(
            existing_transactions
        ),
    )