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
    CREDIT_COLUMN_ALIASES,
    DEBIT_COLUMN_ALIASES,
    TRANSACTION_COLUMN_ALIASES,
    TRANSACTION_SHEET_NAME,
    create_excel_template,
    export_transactions_to_excel,
    list_excel_sheet_names,
    normalize_transaction_column_name,
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
    uploaded_file: Any,
    sheet_names: list[str],
) -> int:
    """Prioriza a aba que mais se parece com uma tabela de transações."""
    preferred_terms = (
        "extrato",
        "transa",
        "moviment",
        "fatura",
        "conta",
        "lancament",
        "activity",
    )

    best_index = 0
    best_score = (
        -1,
        -1,
        -1,
    )

    for index, sheet_name in enumerate(
        sheet_names
    ):
        try:
            header_row = suggest_excel_header_row(
                uploaded_file,
                sheet_name=sheet_name,
            )

            table = read_excel_table(
                uploaded_file,
                sheet_name=sheet_name,
                header_row=header_row,
            )

        except (
            ValueError,
            OSError,
            KeyError,
        ):
            continue

        standard_mapping = (
            suggest_transaction_column_mapping(
                table.columns
            )
        )

        split_mapping = (
            suggest_split_amount_column_mapping(
                table.columns
            )
        )

        has_single_amount = (
            standard_mapping[
                "valor"
            ]
            is not None
        )

        has_split_amounts = (
            split_mapping[
                "debito"
            ]
            is not None
            and split_mapping[
                "credito"
            ]
            is not None
        )

        contract_score = sum(
            standard_mapping[field]
            is not None
            for field in (
                "data",
                "descricao",
            )
        )

        contract_score += int(
            has_single_amount
            or has_split_amounts
        )

        mapped_score = sum(
            value is not None
            for value in (
                standard_mapping.values()
            )
        )

        mapped_score += sum(
            value is not None
            for value in (
                split_mapping.values()
            )
        )

        normalized_sheet_name = (
            str(sheet_name)
            .strip()
            .lower()
        )

        name_score = int(
            any(
                term in normalized_sheet_name
                for term in preferred_terms
            )
        )

        current_score = (
            contract_score,
            mapped_score,
            name_score,
        )

        if current_score > best_score:
            best_score = current_score
            best_index = index

    return best_index

def _render_import_section(
    title: str,
    description: str | None = None,
) -> None:
    """Exibe um título de seção no fluxo de importação."""
    section_title = (
        '<div style="'
        "margin:1.25rem 0 0.35rem;"
        "padding-left:0.65rem;"
        "border-left:3px solid "
        "var(--accent, #f97316);"
        "color:var(--text-main);"
        "font-size:1rem;"
        "font-weight:800;"
        "line-height:1.3;"
        '">'
        f"{escape(title)}"
        "</div>"
    )

    st.markdown(
        section_title,
        unsafe_allow_html=True,
    )

    if description:
        st.caption(
            description
        )

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
    _render_import_section(
        "Identificação da planilha",
        (
            "Confirme a aba e a linha de cabeçalho "
            "sugeridas automaticamente."
        ),
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
            uploaded_file,
            sheet_names,
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
    st.caption(
        "Sugestão automática: "
        f"aba “{sheet_name}” e cabeçalho na linha "
        f"{suggested_header_row + 1}. "
        "Altere somente se a prévia estiver incorreta."
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

    _render_import_section(
        "Prévia dos dados encontrados",
        (
            "Confira se os nomes das colunas e os "
            "primeiros registros foram identificados corretamente."
        ),
    )

    render_transaction_preview_table(
        external_table.head(
            8
        )
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

    _render_import_section(
        "Mapeamento das colunas",
        (
            "Associe as colunas da planilha aos campos "
            "utilizados pelo FinanTec."
        ),
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

    use_split_amount_columns = st.toggle(
    "Usar colunas separadas de débito e crédito",
    value=(
        suggested_amount_mode
        == SPLIT_AMOUNT_MODE
    ),
    key=(
        "assisted-excel-split-amounts-"
        f"{mapping_identity}"
    ),
    help=(
        "Ative quando a planilha possui uma coluna "
        "para débitos e outra para créditos. "
        "Deixe desativado quando existe apenas uma "
        "coluna de valor."
    ),
)

    amount_mode = (
        SPLIT_AMOUNT_MODE
        if use_split_amount_columns
        else SINGLE_AMOUNT_MODE
    )

    st.caption(
        (
            "Formato detectado: débito e crédito "
            "em colunas separadas."
        )
        if use_split_amount_columns
        else (
            "Formato detectado: uma única coluna "
            "de valor."
        )
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

def _get_preview_column_role(
    column: str,
) -> str:
    """Identifica o papel visual de uma coluna na prévia."""
    normalized_column = (
        normalize_transaction_column_name(
            column
        )
    )

    if (
        normalized_column
        in TRANSACTION_COLUMN_ALIASES[
            "data"
        ]
    ):
        return "date"

    if normalized_column in DEBIT_COLUMN_ALIASES:
        return "debit"

    if normalized_column in CREDIT_COLUMN_ALIASES:
        return "credit"

    if (
        normalized_column
        in TRANSACTION_COLUMN_ALIASES[
            "valor"
        ]
    ):
        return "amount"

    return "text"

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
        str(
            column
        )
        .replace(
            "_",
            " ",
        )
        .strip(),
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
            "color:var(--text-main);"
            "border-bottom:2px solid var(--border-light);"
            "text-align:left;"
            "font-size:0.75rem;"
            "font-weight:800;"
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

            column_role = (
                _get_preview_column_role(
                    column
                )
            )

            if pd.isna(
                raw_value
            ):
                display_value = "—"

            elif column_role == "date":
                display_value = _format_preview_date(
                    raw_value
                )

            elif column_role in {
                "amount",
                "debit",
                "credit",
            }:
                display_value = _format_preview_amount(
                    raw_value
                )

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

            if column_role in {
                "amount",
                "debit",
                "credit",
            }:
                numeric_value = pd.to_numeric(
                    raw_value,
                    errors="coerce",
                )

                if column_role == "debit":
                    value_color = "var(--danger)"

                elif column_role == "credit":
                    value_color = "var(--success)"

                elif transaction_type == "receita":
                    value_color = "var(--success)"

                elif transaction_type == "despesa":
                    value_color = "var(--danger)"

                elif (
                    pd.notna(
                        numeric_value
                    )
                    and float(
                        numeric_value
                    ) > 0
                ):
                    value_color = "var(--success)"

                elif (
                    pd.notna(
                        numeric_value
                    )
                    and float(
                        numeric_value
                    ) < 0
                ):
                    value_color = "var(--danger)"

                else:
                    value_color = "var(--text-main)"

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
                width="stretch",
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
                    width="stretch",
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
) -> str:
    """Exibe duplicatas e permite incluí-las explicitamente."""
    matching_count = len(
        matching_transactions
    )

    st.warning(
        "Foram encontradas "
        f"{matching_count} ocorrência(s) "
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

    include_matches = st.toggle(
        "Importar também as possíveis duplicatas",
        value=False,
        key=(
            "include-duplicate-import-"
            f"{widget_version}"
        ),
        help=(
            "Quando ativado, o FinanTec também importa "
            "as linhas que correspondem a transações "
            "já existentes."
        ),
    )

    if include_matches:
        st.caption(
            f"As {matching_count} possível(is) duplicata(s) "
            "também serão importadas."
        )

        return INCLUDE_MATCHES

    st.caption(
        "Somente as linhas novas serão importadas. "
        "As possíveis duplicatas serão ignoradas."
    )

    return SKIP_MATCHES


def render_import_confirmation(
    valid_transactions: pd.DataFrame,
    existing_transactions: pd.DataFrame,
) -> bool:
    """Solicita uma decisão e importa o lote selecionado."""
    _render_import_section(
        "Confirmação da importação",
        (
            "Confira possíveis duplicatas e quantas linhas "
            "serão adicionadas ao banco."
        ),
    )
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
            width="content",
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
        width="content",
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
    _render_import_section(
        "Resultado da conversão",
        (
            "Revise as transações no formato do FinanTec "
            "antes de confirmar a importação."
        ),
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
