"""Componentes de tabelas, filtros e validação de transações."""

from __future__ import annotations

from collections.abc import Callable
from html import escape
from typing import Any

import pandas as pd
import streamlit as st
from pandas.io.formats.style import Styler

from analytics import formatar_moeda as format_currency
from ui_components import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    TRANSACTION_TYPE_LABELS,
)


def calculate_table_height(
    row_count: int,
    maximum: int = 420,
) -> int:
    """Calcula uma altura compacta para tabelas do Streamlit."""
    estimated_height = (
        38 * (row_count + 1)
        + 4
    )

    return min(
        max(estimated_height, 120),
        maximum,
    )


def transaction_column_config() -> dict:
    """Configura larguras das colunas de transações."""
    return {
        "Data": st.column_config.TextColumn(
            "Data",
            width="small",
        ),
        "Tipo": st.column_config.TextColumn(
            "Tipo",
            width="small",
        ),
        "Descrição": st.column_config.TextColumn(
            "Descrição",
            width="large",
        ),
        "Categoria": st.column_config.TextColumn(
            "Categoria",
            width="medium",
        ),
        "Valor": st.column_config.TextColumn(
            "Valor",
            width="small",
            alignment="right",
        ),
    }


CellStyleResolver = Callable[
    [str, Any, pd.Series],
    str,
]


def build_read_only_table_html(
    table: pd.DataFrame,
    *,
    table_label: str,
    maximum_height: int | None = None,
    cell_style_resolver: CellStyleResolver | None = None,
) -> str:
    """Monta uma tabela HTML segura e adaptada aos temas visuais."""
    header_cells = "".join(
        (
            "<th scope=\"col\">"
            f"{escape(str(column))}"
            "</th>"
        )
        for column in table.columns
    )

    body_rows: list[str] = []

    for _, row in table.iterrows():
        cells: list[str] = []

        for column in table.columns:
            value = row[column]

            style = (
                cell_style_resolver(
                    str(column),
                    value,
                    row,
                )
                if cell_style_resolver
                else ""
            )

            style_attribute = (
                f' style="{escape(style, quote=True)}"'
                if style
                else ""
            )

            cells.append(
                "<td"
                f"{style_attribute}"
                ">"
                f"{escape(str(value))}"
                "</td>"
            )

        body_rows.append(
            "<tr>"
            + "".join(cells)
            + "</tr>"
        )

    wrapper_styles = [
        "overflow: auto",
    ]

    if maximum_height is not None:
        safe_height = max(
            120,
            int(maximum_height),
        )

        wrapper_styles.append(
            f"max-height: {safe_height}px"
        )

    wrapper_style = "; ".join(
        wrapper_styles
    )

    return (
        '<div class="finantec-table-panel" '
        f'style="{wrapper_style};">'
        '<table class="finantec-table" '
        f'aria-label="{escape(table_label, quote=True)}">'
        '<thead style="position: sticky; top: 0; z-index: 2;">'
        "<tr>"
        f"{header_cells}"
        "</tr>"
        "</thead>"
        "<tbody>"
        + "".join(body_rows)
        + "</tbody>"
        "</table>"
        "</div>"
    )


def render_read_only_table(
    table: pd.DataFrame,
    *,
    table_label: str,
    maximum_height: int | None = None,
    cell_style_resolver: CellStyleResolver | None = None,
) -> None:
    """Renderiza uma tabela somente de consulta com tema consistente."""
    st.markdown(
        build_read_only_table_html(
            table,
            table_label=table_label,
            maximum_height=maximum_height,
            cell_style_resolver=cell_style_resolver,
        ),
        unsafe_allow_html=True,
    )


def transaction_cell_style(
    column: str,
    _value: Any,
    row: pd.Series,
) -> str:
    """Define alinhamento e cor semântica da tabela de transações."""
    if column != "Valor":
        return ""

    transaction_type = str(
        row.get(
            "Tipo",
            "",
        )
    ).strip()

    if transaction_type == "Receita":
        return (
            f"color: {INCOME_COLOR} !important; "
            "font-weight: 700; "
            "text-align: right;"
        )

    if transaction_type == "Despesa":
        return (
            f"color: {EXPENSE_COLOR} !important; "
            "font-weight: 700; "
            "text-align: right;"
        )

    return "text-align: right;"


def prepare_transactions_for_display(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Formata as transações para apresentação."""
    table = transactions.copy()

    table["data"] = pd.to_datetime(
        table["data"],
        errors="coerce",
    ).dt.strftime("%d/%m/%Y")

    original_types = (
        table["tipo"].copy()
    )

    table["tipo"] = (
        table["tipo"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(TRANSACTION_TYPE_LABELS)
        .fillna(original_types)
    )

    table["descricao"] = (
        table["descricao"]
        .astype(str)
        .str.strip()
    )

    table["categoria"] = (
        table["categoria"]
        .astype(str)
        .str.strip()
    )

    table["valor"] = (
        table["valor"].map(
            format_currency
        )
    )

    table = table.rename(
        columns={
            "data": "Data",
            "tipo": "Tipo",
            "descricao": "Descrição",
            "categoria": "Categoria",
            "valor": "Valor",
        }
    )

    return table[
        [
            "Data",
            "Tipo",
            "Descrição",
            "Categoria",
            "Valor",
        ]
    ]


def style_transactions_table(
    table: pd.DataFrame,
) -> Styler:
    """Aplica cores semânticas somente aos valores monetários."""

    def style_transaction_row(
        row: pd.Series,
    ) -> pd.Series:
        """Define o estilo do valor conforme o tipo da transação."""
        styles = pd.Series(
            "",
            index=row.index,
        )

        transaction_type = str(
            row.get(
                "Tipo",
                "",
            )
        ).strip()

        if transaction_type == "Receita":
            styles["Valor"] = (
                f"color: {INCOME_COLOR}; "
                "font-weight: 700;"
            )

        elif transaction_type == "Despesa":
            styles["Valor"] = (
                f"color: {EXPENSE_COLOR}; "
                "font-weight: 700;"
            )

        return styles

    return table.style.apply(
        style_transaction_row,
        axis=1,
    )


def render_category_ranking(
    expenses_by_category: pd.Series,
) -> None:
    """Exibe o ranking das categorias com maior consumo."""
    with st.container(
        border=True,
        key="category-ranking-card",
    ):
        st.markdown(
            "### Ranking de categorias"
        )

        st.caption(
            "Categorias ordenadas pelo maior "
            "valor de consumo."
        )

        if expenses_by_category.empty:
            st.info(
                "Não há categorias de consumo "
                "para listar neste período."
            )
            return

        ranking = (
            expenses_by_category
            .sort_values(
                ascending=False
            )
            .rename("Valor")
            .reset_index()
        )

        ranking.columns = [
            "Categoria",
            "Valor",
        ]

        ranking_items = []

        for position, row in enumerate(
            ranking.itertuples(
                index=False
            ),
            start=1,
        ):
            category = escape(
                str(row.Categoria)
            )

            formatted_value = (
                format_currency(
                    row.Valor
                )
            )

            item_class = (
                "finantec-ranking-item top-one"
                if position == 1
                else "finantec-ranking-item"
            )

            ranking_items.append(
                f'<div class="{item_class}">'
                '<span class="finantec-ranking-position">'
                f"{position}"
                "</span>"
                '<span class="finantec-ranking-category">'
                f"{category}"
                "</span>"
                '<strong class="finantec-ranking-value">'
                f"{formatted_value}"
                "</strong>"
                "</div>"
            )

        ranking_html = (
            '<div class="finantec-ranking-list">'
            + "".join(ranking_items)
            + "</div>"
        )

        st.markdown(
            ranking_html,
            unsafe_allow_html=True,
        )


def render_latest_transactions(
    transactions: pd.DataFrame,
    limit: int = 5,
) -> None:
    """Exibe as transações mais recentes do período."""
    with st.container(
        border=True,
        key="latest-transactions-card",
    ):
        st.markdown(
            "### Últimas transações"
        )

        st.caption(
            "Movimentações mais recentes "
            "do período selecionado."
        )

        if transactions.empty:
            st.info(
                "Nenhuma transação encontrada "
                "para o período selecionado."
            )
            return

        latest_transactions = (
            transactions
            .sort_values(
                by="data",
                ascending=False,
            )
            .head(limit)
        )

        table = (
            prepare_transactions_for_display(
                latest_transactions
            )
        )


        render_read_only_table(
            table,
            table_label="Últimas transações",
            maximum_height=300,
            cell_style_resolver=transaction_cell_style,
        )


def render_data_validation(
    valid_count: int,
    rejections: pd.DataFrame,
) -> None:
    """Exibe somente transações que precisam de correção."""
    if rejections.empty:
        return

    rejected_count = len(
        rejections
    )

    rejection_label = (
        "transação precisa"
        if rejected_count == 1
        else "transações precisam"
    )

    usage_label = (
        "ser usada"
        if rejected_count == 1
        else "serem usadas"
    )

    st.warning(
        f"{rejected_count} {rejection_label} de correção "
        f"antes de {usage_label} no painel."
    )

    with st.expander(
        "Ver transações que precisam de correção"
    ):
        st.dataframe(
            rejections,
            use_container_width=True,
            hide_index=True,
            height=calculate_table_height(
                len(rejections),
            ),
        )


def filter_transactions_table(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Aplica filtros de tipo, categoria e descrição."""
    transaction_types = sorted(
        transactions["tipo"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    categories = sorted(
        transactions["categoria"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    (
        type_column,
        category_column,
        search_column,
    ) = st.columns(
        [1, 1, 2],
        gap="small",
    )

    selected_type = (
        type_column.selectbox(
            "Tipo",
            [
                "Todos",
                *transaction_types,
            ],
            format_func=lambda value: (
                value
                if value == "Todos"
                else TRANSACTION_TYPE_LABELS.get(
                    value,
                    value.title(),
                )
            ),
            key="transaction_type_filter",
        )
    )

    selected_category = (
        category_column.selectbox(
            "Categoria",
            [
                "Todas",
                *categories,
            ],
            key="transaction_category_filter",
        )
    )

    search_text = (
        search_column.text_input(
            "Buscar descrição",
            placeholder=(
                "Ex.: mercado, transporte, bolsa"
            ),
            key=(
                "transaction_description_filter"
            ),
        )
    )

    result = transactions.copy()

    if selected_type != "Todos":
        result = result.loc[
            result["tipo"]
            == selected_type
        ]

    if selected_category != "Todas":
        result = result.loc[
            result["categoria"]
            == selected_category
        ]

    if search_text.strip():
        result = result.loc[
            result["descricao"]
            .astype(str)
            .str.contains(
                search_text.strip(),
                case=False,
                na=False,
            )
        ]

    return result


def render_period_transactions(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Exibe as transações e retorna as linhas filtradas."""
    with st.container(
        border=True,
        key="period-transactions-card",
    ):
        st.markdown(
            "### Transações do período"
        )

        st.caption(
            "Use os filtros para consultar receitas, despesas, "
            "categorias ou descrições específicas."
        )

        if transactions.empty:
            st.info(
                "Nenhuma transação encontrada "
                "para o período selecionado."
            )

            return (
                transactions.iloc[
                    0:0
                ].copy()
            )

        filtered_transactions = (
            filter_transactions_table(
                transactions
            )
        )

        income = filtered_transactions.loc[
            filtered_transactions["tipo"]
            == "receita",
            "valor",
        ].sum()

        expenses = filtered_transactions.loc[
            filtered_transactions["tipo"]
            == "despesa",
            "valor",
        ].sum()

        (
            total_column,
            income_column,
            expense_column,
        ) = st.columns(
            3,
            gap="small",
        )

        with total_column:
            with st.container(
                key="period-total-metric",
            ):
                st.metric(
                    "Transações",
                    len(
                        filtered_transactions
                    ),
                )

        with income_column:
            with st.container(
                key="period-income-metric",
            ):
                st.metric(
                    "Receitas",
                    format_currency(
                        income
                    ),
                )

        with expense_column:
            with st.container(
                key="period-expense-metric",
            ):
                st.metric(
                    "Despesas",
                    format_currency(
                        expenses
                    ),
                )

        if filtered_transactions.empty:
            st.info(
                "Nenhuma transação corresponde "
                "aos filtros selecionados."
            )

            return (
                filtered_transactions.copy()
            )

        sorted_transactions = (
            filtered_transactions
            .sort_values(
                by="data",
                ascending=False,
            )
            .copy()
        )

        table = (
            prepare_transactions_for_display(
                sorted_transactions
            )
        )

        render_read_only_table(
            table,
            table_label="Transações do período",
            maximum_height=420,
            cell_style_resolver=transaction_cell_style,
        )

        return (
            sorted_transactions
            .reset_index(
                drop=True
            )
        )