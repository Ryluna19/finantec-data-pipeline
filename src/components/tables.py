"""Componentes de tabelas, filtros e validação de transações."""

from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from analytics import formatar_moeda as format_currency
from ui_components import TRANSACTION_TYPE_LABELS


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
        ),
    }


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

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            height=calculate_table_height(
                len(table),
                maximum=300,
            ),
            column_config=(
                transaction_column_config()
            ),
        )


def render_data_validation(
    valid_count: int,
    rejections: pd.DataFrame,
) -> None:
    """Exibe a situação dos dados processados pelo ETL."""
    with st.container(
        border=True,
        key="data-validation-card",
    ):
        st.markdown(
            "### Validação dos dados"
        )

        st.caption(
            "Resumo das linhas aceitas e rejeitadas "
            "pelo pipeline ETL."
        )

        valid_column, rejected_column = (
            st.columns(
                2,
                gap="small",
            )
        )

        valid_column.metric(
            "Válidas no período",
            valid_count,
        )

        rejected_column.metric(
            "Rejeitadas no último ETL",
            len(rejections),
        )

        if rejections.empty:
            st.success(
                "Nenhuma transação foi rejeitada "
                "no último processamento."
            )
            return

        st.warning(
            "Existem transações rejeitadas. "
            "Consulte a tabela para conferir os motivos."
        )

        with st.expander(
            "Ver transações rejeitadas"
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
) -> None:
    """Exibe as transações e os totais dos filtros aplicados."""
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
            return

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

        total_column.metric(
            "Transações",
            len(filtered_transactions),
        )

        income_column.metric(
            "Receitas",
            format_currency(income),
        )

        expense_column.metric(
            "Despesas",
            format_currency(expenses),
        )

        if filtered_transactions.empty:
            st.info(
                "Nenhuma transação corresponde "
                "aos filtros selecionados."
            )
            return

        table = (
            prepare_transactions_for_display(
                filtered_transactions.sort_values(
                    by="data",
                    ascending=False,
                )
            )
        )

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            height=calculate_table_height(
                len(table),
            ),
            column_config=(
                transaction_column_config()
            ),
        )