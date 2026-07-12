"""Componentes de resumo e indicadores financeiros do dashboard."""

from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from analytics import formatar_moeda as format_currency
from ui_components import render_html


def calculate_percentage(
    part: float,
    total: float,
) -> float:
    """Calcula a representação percentual sem dividir por zero."""
    return (
        (part / total) * 100
        if total > 0
        else 0.0
    )


def render_financial_summary(
    summary: dict[str, Any],
) -> None:
    """Exibe saldo, receitas, consumo e reserva do período."""
    st.subheader(
        "Resumo financeiro"
    )

    income = summary[
        "receitas_totais"
    ]

    consumption = summary[
        "despesas_do_mes"
    ]

    reserve = summary[
        "valor_guardado_reserva"
    ]

    balance = summary[
        "saldo_disponivel"
    ]

    if balance > 0:
        balance_state = "positive"
    elif balance < 0:
        balance_state = "negative"
    else:
        balance_state = "neutral"

    balance_description = (
        "Saldo disponível após gastos "
        "de consumo e reserva."
        if balance >= 0
        else "O período fechou com saldo negativo."
    )

    render_html(
        f"""
        <div class="finantec-overview-grid">
            <div
                class="finantec-balance-panel {balance_state}"
            >
                <div class="finantec-balance-label">
                    Saldo do período
                </div>

                <div
                    class="finantec-balance-value {balance_state}"
                >
                    {escape(format_currency(balance))}
                </div>

                <div class="finantec-balance-desc">
                    {escape(balance_description)}
                </div>
            </div>

            <div class="finantec-mini-grid">
                <div class="finantec-mini-card receita">
                    <div class="finantec-mini-title">
                        Receitas
                    </div>

                    <div class="finantec-mini-value">
                        {escape(format_currency(income))}
                    </div>

                    <div class="finantec-mini-desc">
                        Total recebido no período.
                    </div>
                </div>

                <div class="finantec-mini-card consumo">
                    <div class="finantec-mini-title">
                        Consumo
                    </div>

                    <div class="finantec-mini-value">
                        {escape(format_currency(consumption))}
                    </div>

                    <div class="finantec-mini-desc">
                        Despesas sem contar reserva.
                    </div>
                </div>

                <div class="finantec-mini-card reserva">
                    <div class="finantec-mini-title">
                        Reserva
                    </div>

                    <div class="finantec-mini-value">
                        {escape(format_currency(reserve))}
                    </div>

                    <div class="finantec-mini-desc">
                        Valor separado para guardar.
                    </div>
                </div>
            </div>
        </div>
        """
    )


def render_financial_diagnosis(
    summary: dict[str, Any],
) -> None:
    """Resume a situação financeira e a distribuição da renda."""
    st.subheader(
        "Diagnóstico rápido"
    )

    income = summary[
        "receitas_totais"
    ]

    consumption = summary[
        "despesas_do_mes"
    ]

    reserve = summary[
        "valor_guardado_reserva"
    ]

    balance = summary[
        "saldo_disponivel"
    ]

    consumption_percentage = (
        calculate_percentage(
            consumption,
            income,
        )
    )

    reserve_percentage = (
        calculate_percentage(
            reserve,
            income,
        )
    )

    if balance > 0:
        title = (
            "Período com sobra financeira"
        )

        description = (
            f"O período fechou com "
            f"{format_currency(balance)} disponíveis. "
            f"O consumo usou "
            f"{consumption_percentage:.1f}% da renda e "
            f"{reserve_percentage:.1f}% foi separado "
            "para reserva."
        )

    elif balance == 0:
        title = (
            "Período sem sobra"
        )

        description = (
            "As receitas cobriram exatamente "
            "os gastos e a reserva. "
            "Não houve saldo disponível ao final."
        )

    else:
        title = (
            "Período negativo"
        )

        description = (
            f"O período fechou negativo em "
            f"{format_currency(abs(balance))}. "
            "Os gastos e reservas ultrapassaram "
            "as receitas."
        )

    # Evita que percentuais acima de 100% ultrapassem o painel.
    consumption_bar_width = min(
        consumption_percentage,
        100,
    )

    reserve_bar_width = min(
        reserve_percentage,
        100,
    )

    render_html(
        f"""
        <div class="finantec-diagnosis-panel">
            <div class="finantec-diagnosis-title">
                {escape(title)}
            </div>

            <div class="finantec-diagnosis-text">
                {escape(description)}
            </div>

            <div class="finantec-diagnosis-grid">
                <div>
                    <div class="finantec-bar-label">
                        Consumo da renda:
                        {consumption_percentage:.1f}%
                    </div>

                    <div class="finantec-bar-track">
                        <div
                            class="finantec-bar-fill expense"
                            style="
                                width:
                                {consumption_bar_width:.1f}%;
                            "
                        >
                        </div>
                    </div>
                </div>

                <div>
                    <div class="finantec-bar-label">
                        Reserva da renda:
                        {reserve_percentage:.1f}%
                    </div>

                    <div class="finantec-bar-track">
                        <div
                            class="finantec-bar-fill green"
                            style="
                                width:
                                {reserve_bar_width:.1f}%;
                            "
                        >
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    )


def render_additional_metrics(
    transactions: pd.DataFrame,
    summary: dict[str, Any],
) -> None:
    """Exibe quantidade, gasto médio e renda reservada."""
    expenses = transactions.loc[
        transactions["tipo"]
        == "despesa"
    ]

    average_expense = (
        expenses["valor"].mean()
        if not expenses.empty
        else 0.0
    )

    reserve_percentage = (
        calculate_percentage(
            summary[
                "valor_guardado_reserva"
            ],
            summary[
                "receitas_totais"
            ],
        )
    )

    (
        total_column,
        average_column,
        reserve_column,
    ) = st.columns(
        3
    )

    total_column.metric(
        "Transações",
        len(transactions),
    )

    average_column.metric(
        "Gasto médio",
        format_currency(
            average_expense
        ),
    )

    reserve_column.metric(
        "Renda reservada",
        f"{reserve_percentage:.1f}%",
    )