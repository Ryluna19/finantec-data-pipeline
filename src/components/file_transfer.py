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
    TRANSACTION_SHEET_NAME,
    create_excel_template,
    export_transactions_to_excel,
    list_excel_sheet_names,
    read_excel_table,
    read_transaction_file,
    split_imported_transactions_by_match,
    suggest_excel_header_row,
    suggest_split_amount_column_mapping,
    suggest_transaction_column_mapping,
    translate_split_amount_transaction_table,
    translate_transaction_table,
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
SINGLE_AMOUNT_MODE = "single_amount"
SPLIT_AMOUNT_MODE = "split_amount"

AMOUNT_MODE_LABELS = {
    SINGLE_AMOUNT_MODE: "Uma única coluna de valor",
    SPLIT_AMOUNT_MODE: "Débito e crédito separados",
}


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
    """Encaminha o arquivo enviado para o leitor adequado."""
    return read_transaction_file(
        source=uploaded_file,
        file_name=uploaded_file.name,
    )

def _format_excel_mapping_option(
    column: object | None,
) -> str:
    """Formata as opções de coluna exibidas no mapeamento."""
    if column is None:
        return "Não usar"

    return str(column)


def _get_excel_mapping_option_index(
    options: list[object | None],
    suggested_column: object | None,
) -> int:
    """Localiza a sugestão dentro das opções do seletor."""
    if suggested_column not in options:
        return 0

    return options.index(
        suggested_column
    )


def _suggest_excel_sheet_index(
    sheet_names: list[str],
) -> int:
    """Prioriza abas que aparentam conter transações."""
    preferred_terms = (
        "extrato",
        "transa",
        "moviment",
        "fatura",
    )

    for index, sheet_name in enumerate(
        sheet_names
    ):
        normalized_name = (
            str(sheet_name)
            .strip()
            .lower()
        )

        if any(
            term in normalized_name
            for term in preferred_terms
        ):
            return index

    return 0


def _render_assisted_excel_transactions(
    uploaded_file: Any,
) -> pd.DataFrame | None:
    """Converte uma planilha externa pelo mapeamento escolhido."""
    sheet_names = list_excel_sheet_names(
        uploaded_file
    )

    if not sheet_names:
        raise ValueError(
            "O arquivo Excel não possui abas disponíveis."
        )

    if TRANSACTION_SHEET_NAME in sheet_names:
        return read_uploaded_transactions(
            uploaded_file
        )

    st.info(
        "A planilha não usa o modelo do FinanTec. "
        "Selecione a aba, informe onde está o cabeçalho "
        "e confirme quais colunas representam cada campo."
    )

    widget_version = (
        _get_import_widget_version()
    )

    file_identity = (
        f"{widget_version}-"
        f"{uploaded_file.name}-"
        f"{getattr(uploaded_file, 'size', 0)}"
    )

    sheet_name = st.selectbox(
        "Aba com as transações",
        options=sheet_names,
        index=_suggest_excel_sheet_index(
            sheet_names
        ),
        key=(
            "assisted-excel-sheet-"
            f"{file_identity}"
        ),
    )

    suggested_header_row = (
    suggest_excel_header_row(
        uploaded_file,
        sheet_name=sheet_name,
    )
)

    header_row_number = st.number_input(
        "Linha do cabeçalho no Excel",
        min_value=1,
        value=(
            suggested_header_row + 1
        ),
        step=1,
        key=(
            "assisted-excel-header-"
            f"{file_identity}-"
            f"{sheet_name}"
        ),
        help=(
            "O FinanTec tenta identificar essa linha "
            "automaticamente. Altere somente se os nomes "
            "das colunas não tiverem sido encontrados."
        ),
    )

    external_table = read_excel_table(
        uploaded_file,
        sheet_name=sheet_name,
        header_row=(
            int(header_row_number) - 1
        ),
    )
     
    mapping_identity = (
        f"{file_identity}-"
        f"{sheet_name}-"
        f"{int(header_row_number)}"
    )
    if len(
        external_table.columns
    ) == 0:
        st.warning(
            "Nenhuma coluna foi encontrada nessa linha."
        )

        return None

    st.caption(
        "Prévia da tabela encontrada antes da conversão"
    )

    st.dataframe(
        external_table.head(
            8
        ),
        hide_index=True,
        use_container_width=True,
    )

    suggested_mapping = (
        suggest_transaction_column_mapping(
            external_table.columns
        )
    )

    split_amount_mapping = (
        suggest_split_amount_column_mapping(
            external_table.columns
        )
    )

    column_options: list[
        object | None
    ] = [
        None,
        *external_table.columns.tolist(),
    ]

    st.markdown(
        "#### Mapeamento das colunas"
    )

    data_column, description_column = (
        st.columns(
            2
        )
    )

    with data_column:
        mapped_date = st.selectbox(
            "Data",
            options=column_options,
            index=(
                _get_excel_mapping_option_index(
                    column_options,
                    suggested_mapping[
                        "data"
                    ],
                )
            ),
            format_func=(
                _format_excel_mapping_option
            ),
            key=(
                "assisted-excel-date-"
                f"{mapping_identity}"
            ),
        )

    with description_column:
        mapped_description = st.selectbox(
            "Descrição",
            options=column_options,
            index=(
                _get_excel_mapping_option_index(
                    column_options,
                    suggested_mapping[
                        "descricao"
                    ],
                )
            ),
            format_func=(
                _format_excel_mapping_option
            ),
            key=(
                "assisted-excel-description-"
                f"{mapping_identity}"
            ),
        )

    has_suggested_split_amounts = (
        split_amount_mapping[
            "debito"
        ]
        is not None
        and split_amount_mapping[
            "credito"
        ]
        is not None
    )

    suggested_amount_mode = (
        SPLIT_AMOUNT_MODE
        if (
            has_suggested_split_amounts
            and suggested_mapping[
                "valor"
            ]
            is None
        )
        else SINGLE_AMOUNT_MODE
    )

    amount_modes = [
        SINGLE_AMOUNT_MODE,
        SPLIT_AMOUNT_MODE,
    ]

    amount_mode = st.radio(
        "Como os valores estão organizados?",
        options=amount_modes,
        index=amount_modes.index(
            suggested_amount_mode
        ),
        format_func=lambda mode: (
            AMOUNT_MODE_LABELS[
                mode
            ]
        ),
        horizontal=True,
        key=(
            "assisted-excel-amount-mode-"
            f"{mapping_identity}"
        ),
    )

    mapped_type: object | None = None
    mapped_amount: object | None = None
    mapped_debit: object | None = None
    mapped_credit: object | None = None

    if amount_mode == SINGLE_AMOUNT_MODE:
        type_column, amount_column = (
            st.columns(
                2
            )
        )

        with type_column:
            mapped_type = st.selectbox(
                "Tipo — opcional",
                options=column_options,
                index=(
                    _get_excel_mapping_option_index(
                        column_options,
                        suggested_mapping[
                            "tipo"
                        ],
                    )
                ),
                format_func=(
                    _format_excel_mapping_option
                ),
                key=(
                    "assisted-excel-type-"
                    f"{mapping_identity}"
                ),
                help=(
                    "Use quando a planilha possui uma coluna "
                    "que identifica receitas e despesas."
                ),
            )

        with amount_column:
            mapped_amount = st.selectbox(
                "Valor",
                options=column_options,
                index=(
                    _get_excel_mapping_option_index(
                        column_options,
                        suggested_mapping[
                            "valor"
                        ],
                    )
                ),
                format_func=(
                    _format_excel_mapping_option
                ),
                key=(
                    "assisted-excel-amount-"
                    f"{mapping_identity}"
                ),
            )

    else:
        debit_column, credit_column = (
            st.columns(
                2
            )
        )

        with debit_column:
            mapped_debit = st.selectbox(
                "Coluna de débito",
                options=column_options,
                index=(
                    _get_excel_mapping_option_index(
                        column_options,
                        split_amount_mapping[
                            "debito"
                        ],
                    )
                ),
                format_func=(
                    _format_excel_mapping_option
                ),
                key=(
                    "assisted-excel-debit-"
                    f"{mapping_identity}"
                ),
            )

        with credit_column:
            mapped_credit = st.selectbox(
                "Coluna de crédito",
                options=column_options,
                index=(
                    _get_excel_mapping_option_index(
                        column_options,
                        split_amount_mapping[
                            "credito"
                        ],
                    )
                ),
                format_func=(
                    _format_excel_mapping_option
                ),
                key=(
                    "assisted-excel-credit-"
                    f"{mapping_identity}"
                ),
            )

    mapped_category = st.selectbox(
        "Categoria — opcional",
        options=column_options,
        index=(
            _get_excel_mapping_option_index(
                column_options,
                suggested_mapping[
                    "categoria"
                ],
            )
        ),
        format_func=(
            _format_excel_mapping_option
        ),
        key=(
            "assisted-excel-category-"
            f"{mapping_identity}"
        ),
    )

    common_mapping_missing = (
        mapped_date is None
        or mapped_description is None
    )

    if common_mapping_missing:
        st.warning(
            "Selecione as colunas de Data "
            "e Descrição para continuar."
        )

        return None

    if amount_mode == SINGLE_AMOUNT_MODE:
        if mapped_amount is None:
            st.warning(
                "Selecione a coluna de Valor "
                "para continuar."
            )

            return None

        column_mapping = {
            "data": mapped_date,
            "tipo": mapped_type,
            "descricao": mapped_description,
            "categoria": mapped_category,
            "valor": mapped_amount,
        }

        if mapped_type is None:
            st.caption(
                "Como nenhuma coluna de tipo foi selecionada, "
                "valores positivos serão tratados como receitas "
                "e valores negativos como despesas."
            )

        else:
            st.caption(
                "Receitas e despesas serão identificadas pela "
                "coluna de tipo selecionada. Os valores serão "
                "convertidos para números positivos."
            )

        return translate_transaction_table(
            external_table,
            column_mapping,
        )

    if (
        mapped_debit is None
        or mapped_credit is None
    ):
        st.warning(
            "Selecione as colunas de Débito "
            "e Crédito para continuar."
        )

        return None

    if mapped_debit == mapped_credit:
        st.warning(
            "Débito e Crédito precisam usar "
            "colunas diferentes."
        )

        return None

    st.caption(
        "Linhas com débito serão convertidas em despesas. "
        "Linhas com crédito serão convertidas em receitas."
    )

    return translate_split_amount_transaction_table(
        external_table,
        date_column=str(
            mapped_date
        ),
        description_column=str(
            mapped_description
        ),
        debit_column=str(
            mapped_debit
        ),
        credit_column=str(
            mapped_credit
        ),
        category_column=(
            str(
                mapped_category
            )
            if mapped_category is not None
            else None
        ),
    )


def _read_uploaded_transactions_for_preview(
    uploaded_file: Any,
) -> pd.DataFrame | None:
    """Lê o arquivo e ativa o modo assistido para Excel externo."""
    file_suffix = Path(
        uploaded_file.name
    ).suffix.lower()

    if file_suffix != ".xlsx":
        return read_uploaded_transactions(
            uploaded_file
        )

    return _render_assisted_excel_transactions(
        uploaded_file
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
            _read_uploaded_transactions_for_preview(
                uploaded_file
            )
        )

        if transactions is None:
            return False

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
            "ofx",
        ],
        accept_multiple_files=False,
        key=(
            "transaction_file_upload_"
            f"{widget_version}"
        ),
        help=(
            "Arquivos CSV podem usar o modelo do FinanTec. "
            "Planilhas Excel externas podem ter suas colunas "
            "mapeadas durante a importação. Extratos OFX são "
            "convertidos automaticamente."
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
        "Envie um arquivo CSV, Excel ou OFX para adicionar um novo lote de transações."
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
