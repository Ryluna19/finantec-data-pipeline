"""Componentes gráficos utilizados no dashboard do FinanTec."""

from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from analytics import formatar_moeda as format_currency
from ui_components import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    MONTH_NAMES_PT_BR,
    render_alert,
)


def create_monthly_summary(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Agrupa receitas e despesas por mês para exibição no gráfico."""
    data = transactions.copy()

    data["month_number"] = data["data"].dt.month

    summary = (
        data.groupby(
            [
                "month_number",
                "tipo",
            ]
        )["valor"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("month_number")
    )

    # Garante que as duas séries existam mesmo sem dados de um dos tipos.
    for column in ("receita", "despesa"):
        if column not in summary.columns:
            summary[column] = 0.0

    summary["Mês"] = summary["month_number"].map(
        MONTH_NAMES_PT_BR
    )

    return summary


def render_expenses_by_category(
    expenses_by_category: pd.Series,
    summary: dict[str, Any],
) -> None:
    """Exibe um gráfico horizontal dos gastos por categoria."""
    st.subheader("Gastos por categoria")

    if expenses_by_category.empty:
        st.info(
            "Não há gastos de consumo para exibir neste período."
        )
        return

    chart_data = (
        expenses_by_category
        .rename("Valor")
        .reset_index()
    )

    chart_data.columns = [
        "Categoria",
        "Valor",
    ]

    chart = (
        alt.Chart(chart_data)
        .mark_bar(
            color=EXPENSE_COLOR,
            cornerRadiusEnd=4,
        )
        .encode(
            x=alt.X(
                "Valor:Q",
                title="Valor",
                axis=alt.Axis(format=",.0f"),
            ),
            y=alt.Y(
                "Categoria:N",
                sort="-x",
                title=None,
            ),
            tooltip=[
                alt.Tooltip(
                    "Categoria:N",
                    title="Categoria",
                ),
                alt.Tooltip(
                    "Valor:Q",
                    title="Valor",
                    format=",.2f",
                ),
            ],
        )
        .properties(
            height=max(
                260,
                len(chart_data) * 34,
            )
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )

    if summary["maior_categoria"]:
        render_alert(
            text=(
                "Maior categoria do período: "
                f"{summary['maior_categoria']} "
                f"({format_currency(summary['maior_gasto'])})."
            ),
            variant="info",
        )


def render_monthly_evolution(
    transactions: pd.DataFrame,
) -> None:
    """Compara receitas e despesas mês a mês."""
    if transactions.empty:
        return

    monthly_summary = create_monthly_summary(transactions)

    chart_data = monthly_summary.melt(
        id_vars=[
            "Mês",
            "month_number",
        ],
        value_vars=[
            "receita",
            "despesa",
        ],
        var_name="Tipo",
        value_name="Valor",
    )

    chart_data["Tipo"] = chart_data["Tipo"].map(
        {
            "receita": "Receitas",
            "despesa": "Despesas",
        }
    )

    month_order = monthly_summary["Mês"].tolist()

    st.subheader("Evolução mensal")

    chart = (
        alt.Chart(chart_data)
        .mark_line(
            point=True,
            strokeWidth=3,
        )
        .encode(
            x=alt.X(
                "Mês:N",
                sort=month_order,
                title=None,
            ),
            y=alt.Y(
                "Valor:Q",
                title="Valor",
                axis=alt.Axis(format=",.0f"),
            ),
            color=alt.Color(
                "Tipo:N",
                scale=alt.Scale(
                    domain=[
                        "Receitas",
                        "Despesas",
                    ],
                    range=[
                        INCOME_COLOR,
                        EXPENSE_COLOR,
                    ],
                ),
                title=None,
            ),
            tooltip=[
                alt.Tooltip(
                    "Mês:N",
                    title="Mês",
                ),
                alt.Tooltip(
                    "Tipo:N",
                    title="Tipo",
                ),
                alt.Tooltip(
                    "Valor:Q",
                    title="Valor",
                    format=",.2f",
                ),
            ],
        )
        .properties(height=320)
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )

    table = monthly_summary[
        [
            "Mês",
            "receita",
            "despesa",
        ]
    ].copy()

    table.columns = [
        "Mês",
        "Receitas",
        "Despesas",
    ]

    table["Receitas"] = table["Receitas"].map(
        format_currency
    )

    table["Despesas"] = table["Despesas"].map(
        format_currency
    )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )