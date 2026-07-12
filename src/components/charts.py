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


CHART_TEXT_COLOR = "#d4d4d8"
CHART_MUTED_COLOR = "#a1a1aa"
CHART_GRID_COLOR = "#27272a"


def apply_chart_theme(
    chart: alt.Chart,
) -> alt.Chart:
    """Aplica o tema visual escuro usado pelo dashboard."""
    return (
        chart
        .properties(
            background="transparent",
        )
        .configure_view(
            stroke=None,
        )
        .configure_axis(
            domainColor=CHART_GRID_COLOR,
            gridColor=CHART_GRID_COLOR,
            gridOpacity=0.55,
            labelColor=CHART_MUTED_COLOR,
            titleColor=CHART_TEXT_COLOR,
            tickColor=CHART_GRID_COLOR,
            labelFont="Inter",
            titleFont="Inter",
            labelFontSize=12,
            titleFontSize=12,
            titleFontWeight=600,
        )
        .configure_legend(
            labelColor=CHART_TEXT_COLOR,
            titleColor=CHART_TEXT_COLOR,
            labelFont="Inter",
            titleFont="Inter",
            labelFontSize=12,
            symbolStrokeWidth=3,
        )
    )


def create_monthly_summary(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Agrupa receitas e despesas por mês."""
    data = transactions.copy()

    data["month_number"] = (
        data["data"].dt.month
    )

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

    # Mantém as duas séries mesmo quando uma delas não possui dados.
    for column in (
        "receita",
        "despesa",
    ):
        if column not in summary.columns:
            summary[column] = 0.0

    summary["Mês"] = (
        summary["month_number"]
        .map(MONTH_NAMES_PT_BR)
    )

    return summary


def render_expenses_by_category(
    expenses_by_category: pd.Series,
    summary: dict[str, Any],
) -> None:
    """Exibe os gastos de consumo agrupados por categoria."""
    with st.container(
        border=True,
        key="expenses-category-card",
    ):
        st.markdown(
            "### Gastos por categoria"
        )

        st.caption(
            "Distribuição das despesas de consumo "
            "no período selecionado."
        )

        if expenses_by_category.empty:
            st.info(
                "Não há gastos de consumo "
                "para exibir neste período."
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

        chart_data[
            "Valor formatado"
        ] = chart_data["Valor"].map(
            format_currency
        )

        chart = (
            alt.Chart(chart_data)
            .mark_bar(
                color=EXPENSE_COLOR,
                cornerRadiusEnd=5,
                size=21,
            )
            .encode(
                x=alt.X(
                    "Valor:Q",
                    title="Valor",
                    axis=alt.Axis(
                        format=",.0f",
                        tickCount=5,
                        titlePadding=12,
                    ),
                ),
                y=alt.Y(
                    "Categoria:N",
                    sort="-x",
                    title=None,
                    axis=alt.Axis(
                        labelLimit=170,
                        labelPadding=8,
                    ),
                ),
                tooltip=[
                    alt.Tooltip(
                        "Categoria:N",
                        title="Categoria",
                    ),
                    alt.Tooltip(
                        "Valor formatado:N",
                        title="Valor",
                    ),
                ],
            )
            .properties(
                height=max(
                    230,
                    len(chart_data) * 32,
                )
            )
        )

        st.altair_chart(
            apply_chart_theme(chart),
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

    monthly_summary = (
        create_monthly_summary(
            transactions
        )
    )

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

    chart_data["Tipo"] = (
        chart_data["Tipo"].map(
            {
                "receita": "Receitas",
                "despesa": "Despesas",
            }
        )
    )

    chart_data[
        "Valor formatado"
    ] = chart_data["Valor"].map(
        format_currency
    )

    month_order = (
        monthly_summary["Mês"]
        .tolist()
    )

    with st.container(
        border=True,
        key="monthly-evolution-card",
    ):
        st.markdown(
            "### Evolução mensal"
        )

        st.caption(
            "Comparação entre receitas e despesas "
            "ao longo dos meses disponíveis."
        )

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
                    axis=alt.Axis(
                        labelAngle=0,
                        labelPadding=8,
                    ),
                ),
                y=alt.Y(
                    "Valor:Q",
                    title="Valor",
                    axis=alt.Axis(
                        format=",.0f",
                        tickCount=5,
                        titlePadding=12,
                    ),
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
                    legend=alt.Legend(
                        title=None,
                        orient="top",
                        direction="horizontal",
                    ),
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
                        "Valor formatado:N",
                        title="Valor",
                    ),
                ],
            )
            .properties(
                height=300,
            )
        )

        st.altair_chart(
            apply_chart_theme(chart),
            use_container_width=True,
        )

        st.markdown(
            "#### Resumo mensal"
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

        table["Receitas"] = (
            table["Receitas"].map(
                format_currency
            )
        )

        table["Despesas"] = (
            table["Despesas"].map(
                format_currency
            )
        )

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mês": st.column_config.TextColumn(
                    "Mês",
                    width="medium",
                ),
                "Receitas": st.column_config.TextColumn(
                    "Receitas",
                    width="medium",
                ),
                "Despesas": st.column_config.TextColumn(
                    "Despesas",
                    width="medium",
                ),
            },
        )