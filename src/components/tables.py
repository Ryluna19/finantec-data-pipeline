"""Componentes de tabelas, filtros e validação de transações."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analytics import formatar_moeda as format_currency
from ui_components import TRANSACTION_TYPE_LABELS


def prepare_transactions_for_display(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Formata as transações para apresentação nas tabelas."""
    table = transactions.copy()

    table["data"] = pd.to_datetime(
        table["data"],
        errors="coerce",
    ).dt.strftime("%d/%m/%Y")

    original_types = table["tipo"].copy()

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

    table["valor"] = table["valor"].map(format_currency)

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
    st.subheader("Ranking de categorias")

    if expenses_by_category.empty:
        st.info(
            "Não há categorias de consumo para listar neste período."
        )
        return

    ranking = (
        expenses_by_category
        .sort_values(ascending=False)
        .rename("Valor")
        .reset_index()
    )

    ranking.columns = [
        "Categoria",
        "Valor",
    ]

    ranking.insert(
        0,
        "Posição",
        range(1, len(ranking) + 1),
    )

    ranking["Valor"] = ranking["Valor"].map(
        format_currency
    )

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True,
    )


def render_latest_transactions(
    transactions: pd.DataFrame,
    limit: int = 5,
) -> None:
    """Exibe as transações mais recentes do período."""
    st.subheader("Últimas transações")

    if transactions.empty:
        st.info(
            "Nenhuma transação encontrada para o período selecionado."
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

    table = prepare_transactions_for_display(
        latest_transactions
    )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )


def render_data_validation(
    valid_count: int,
    rejections: pd.DataFrame,
) -> None:
    """Exibe a situação dos dados processados pelo ETL."""
    st.subheader("Validação dos dados")

    valid_column, rejected_column = st.columns(2)

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

    with st.expander("Ver transações rejeitadas"):
        st.dataframe(
            rejections,
            use_container_width=True,
            hide_index=True,
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

    type_column, category_column, search_column = st.columns(
        [1, 1, 2]
    )

    selected_type = type_column.selectbox(
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

    selected_category = category_column.selectbox(
        "Categoria",
        [
            "Todas",
            *categories,
        ],
        key="transaction_category_filter",
    )

    search_text = search_column.text_input(
        "Buscar descrição",
        placeholder="Ex.: mercado, transporte, bolsa",
        key="transaction_description_filter",
    )

    result = transactions.copy()

    if selected_type != "Todos":
        result = result.loc[
            result["tipo"] == selected_type
        ]

    if selected_category != "Todas":
        result = result.loc[
            result["categoria"] == selected_category
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
    st.subheader("Transações do período")

    st.caption(
        "Use os filtros para consultar receitas, despesas, "
        "categorias ou descrições específicas."
    )

    if transactions.empty:
        st.info(
            "Nenhuma transação encontrada para o período selecionado."
        )
        return

    filtered_transactions = filter_transactions_table(
        transactions
    )

    income = filtered_transactions.loc[
        filtered_transactions["tipo"] == "receita",
        "valor",
    ].sum()

    expenses = filtered_transactions.loc[
        filtered_transactions["tipo"] == "despesa",
        "valor",
    ].sum()

    total_column, income_column, expense_column = st.columns(3)

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
            "Nenhuma transação corresponde aos filtros selecionados."
        )
        return

    table = prepare_transactions_for_display(
        filtered_transactions.sort_values(
            by="data",
            ascending=False,
        )
    )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )