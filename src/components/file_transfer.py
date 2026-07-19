"""Componente de importação e exportação de transações."""

from __future__ import annotations

from html import escape
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

def _format_preview_date(
    value: object,
) -> str:
    """Formata uma data para exibição na prévia."""
    parsed_date = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(
        parsed_date
    ):
        return "—"

    return parsed_date.strftime(
        "%d/%m/%Y"
    )


def _format_preview_amount(
    value: object,
) -> str:
    """Formata um valor monetário no padrão brasileiro."""
    numeric_value = pd.to_numeric(
        value,
        errors="coerce",
    )

    if pd.isna(
        numeric_value
    ):
        return escape(
            str(value)
        )

    formatted_value = (
        f"{float(numeric_value):,.2f}"
        .replace(
            ",",
            "_",
        )
        .replace(
            ".",
            ",",
        )
        .replace(
            "_",
            ".",
        )
    )

    return f"R$ {formatted_value}"


def _get_preview_columns(
    transactions: pd.DataFrame,
) -> list[str]:
    """Seleciona as colunas úteis da prévia."""
    preferred_columns = (
        "data",
        "tipo",
        "descricao",
        "categoria",
        "valor",
    )

    hidden_columns = {
        "transaction_id",
        "user_id",
        "data_mode",
        "arquivo_origem",
        "ano_mes",
    }

    columns = [
        column
        for column in preferred_columns
        if column in transactions.columns
    ]

    extra_columns = [
        str(column)
        for column in transactions.columns
        if (
            str(column) not in columns
            and str(column) not in hidden_columns
        )
    ]

    return [
        *columns,
        *extra_columns,
    ]


def _get_preview_column_label(
    column: str,
) -> str:
    """Retorna o nome visível de uma coluna."""
    labels = {
        "data": "Data",
        "tipo": "Tipo",
        "descricao": "Descrição",
        "categoria": "Categoria",
        "valor": "Valor",
        "motivo": "Motivo",
        "motivo_rejeicao": "Motivo",
        "motivos_rejeicao": "Motivos",
        "erro": "Erro",
        "erro_validacao": "Erro de validação",
    }

    return labels.get(
        column,
        column.replace(
            "_",
            " ",
        ).strip().capitalize(),
    )


def render_transaction_preview_table(
    transactions: pd.DataFrame,
) -> None:
    """Exibe uma tabela de prévia compatível com os temas."""
    columns = _get_preview_columns(
        transactions
    )

    header_cells = "".join(
        (
            '<th style="'
            "position:sticky;"
            "top:0;"
            "z-index:1;"
            "padding:0.72rem 0.8rem;"
            "background:var(--bg-table-head);"
            "color:var(--text-soft);"
            "border-bottom:1px solid var(--border-light);"
            "text-align:left;"
            "font-size:0.72rem;"
            "font-weight:700;"
            "letter-spacing:0.02em;"
            "text-transform:uppercase;"
            '">'
            f"{escape(_get_preview_column_label(column))}"
            "</th>"
        )
        for column in columns
    )

    body_rows: list[str] = []

    for row_index, transaction in enumerate(
        transactions.to_dict(
            orient="records"
        )
    ):
        transaction_type = str(
            transaction.get(
                "tipo",
                "",
            )
        ).strip().lower()

        row_background = (
            "var(--bg-table-row)"
            if row_index % 2 == 0
            else "var(--bg-table-row-alt)"
        )

        cells: list[str] = []

        for column in columns:
            raw_value = transaction.get(
                column,
                "",
            )

            if column == "data":
                display_value = _format_preview_date(
                    raw_value
                )

            elif column == "valor":
                display_value = _format_preview_amount(
                    raw_value
                )

            elif pd.isna(
                raw_value
            ):
                display_value = "—"

            else:
                display_value = escape(
                    str(raw_value)
                )

            cell_style = (
                "padding:0.7rem 0.8rem;"
                f"background:{row_background};"
                "color:var(--text-main);"
                "border-bottom:1px solid var(--border);"
                "vertical-align:middle;"
            )

            if column == "valor":
                value_color = (
                    "var(--success)"
                    if transaction_type == "receita"
                    else (
                        "var(--danger)"
                        if transaction_type == "despesa"
                        else "var(--text-main)"
                    )
                )

                cell_style += (
                    "text-align:right;"
                    "white-space:nowrap;"
                    "font-weight:700;"
                    f"color:{value_color};"
                )

            cells.append(
                (
                    f'<td style="{cell_style}">'
                    f"{display_value}"
                    "</td>"
                )
            )

        body_rows.append(
            "<tr>"
            f"{''.join(cells)}"
            "</tr>"
        )

    table_html = (
        '<div style="'
        "width:100%;"
        "max-height:360px;"
        "overflow:auto;"
        "border:1px solid var(--border-light);"
        "border-radius:12px;"
        '">'
        '<table style="'
        "width:100%;"
        "min-width:720px;"
        "border-collapse:separate;"
        "border-spacing:0;"
        "font-size:0.82rem;"
        '">'
        "<thead>"
        "<tr>"
        f"{header_cells}"
        "</tr>"
        "</thead>"
        "<tbody>"
        f"{''.join(body_rows)}"
        "</tbody>"
        "</table>"
        "</div>"
    )

    st.markdown(
        table_html,
        unsafe_allow_html=True,
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


def render_transaction_downloads(
    period_transactions: pd.DataFrame,
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
            if period_transactions.empty:
                st.info(
                    "Não há transações no período "
                    "atual para exportar."
                )

            else:
                st.download_button(
                    label="Exportar período atual",
                    data=export_transactions_to_excel(
                        period_transactions
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
     render_transaction_preview_table(
            matching_transactions
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
            render_transaction_preview_table(
                valid_transactions
            )

    with rejected_tab:
        if rejected_transactions.empty:
            st.success(
                "Nenhuma linha foi rejeitada."
            )

        else:
            render_transaction_preview_table(
                rejected_transactions
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


def _render_transaction_import_controls(
    existing_transactions: pd.DataFrame,
) -> bool:
    """Exibe o seletor e a prévia do arquivo importado."""
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
            "O arquivo deve usar as colunas "
            "do modelo do FinanTec."
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


def render_transaction_import(
    existing_transactions: pd.DataFrame,
) -> bool:
    """Exibe feedback, seleção e confirmação da importação."""
    render_import_result()

    st.caption(
        "Envie um arquivo CSV ou Excel para adicionar "
        "um novo lote de transações."
    )

    return _render_transaction_import_controls(
        existing_transactions
    )


def render_transaction_file_tools(
    period_transactions: pd.DataFrame,
    existing_transactions: pd.DataFrame,
) -> bool:
    """Mantém o fluxo combinado de arquivos por compatibilidade."""
    st.subheader(
        "Importação e exportação"
    )

    render_import_result()

    st.caption(
        "Baixe o modelo, exporte os dados atuais "
        "ou importe um novo lote de transações."
    )

    render_transaction_downloads(
        period_transactions
    )

    st.divider()

    return _render_transaction_import_controls(
        existing_transactions
    )
