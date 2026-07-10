"""Componente responsável pela simulação de metas financeiras."""

from __future__ import annotations

from typing import Any

import streamlit as st

from analytics import (
    calcular_meta_mensal as calculate_monthly_goal,
    formatar_moeda as format_currency,
)


def render_goal_simulator(
    user_profile: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    """Exibe a simulação mensal de uma meta financeira."""
    st.subheader("Simulador de metas")

    st.caption(
        "Escolha uma meta para estimar quanto "
        "ainda precisa ser guardado por mês."
    )

    goals = user_profile.get(
        "objetivos_financeiros",
        [],
    )

    if not goals:
        st.info(
            "Nenhuma meta financeira foi cadastrada."
        )
        return

    goal_names = [
        goal["nome"]
        for goal in goals
    ]

    selected_goal_name = st.selectbox(
        "Meta",
        goal_names,
        key="selected_goal",
    )

    selected_goal = next(
        goal
        for goal in goals
        if goal["nome"] == selected_goal_name
    )

    goal_value = float(
        selected_goal["valor_meta"]
    )

    current_value = float(
        selected_goal["valor_atual"]
    )

    deadline_months = int(
        selected_goal["prazo_meses"]
    )

    simulation = calculate_monthly_goal(
        valor_meta=goal_value,
        prazo_meses=deadline_months,
        valor_ja_reservado=current_value,
    )

    monthly_amount = simulation[
        "valor_mensal_necessario"
    ]

    monthly_amount_label = (
        format_currency(monthly_amount)
        if monthly_amount is not None
        else "Prazo inválido"
    )

    (
        goal_column,
        current_column,
        remaining_column,
        monthly_column,
    ) = st.columns(4)

    goal_column.metric(
        "Valor da meta",
        format_currency(goal_value),
    )

    current_column.metric(
        "Valor atual",
        format_currency(current_value),
    )

    remaining_column.metric(
        "Falta guardar",
        format_currency(
            simulation["valor_restante"]
        ),
    )

    monthly_column.metric(
        "Necessário por mês",
        monthly_amount_label,
    )

    if monthly_amount is None:
        st.warning(
            "Não foi possível calcular a meta "
            "porque o prazo é inválido."
        )
        return

    available_balance = summary[
        "saldo_disponivel"
    ]

    if monthly_amount > available_balance:
        st.error(
            "O valor mensal necessário ultrapassa "
            "o saldo disponível do período. "
            "Considere ajustar o prazo, os gastos ou a renda."
        )
    else:
        st.success(
            "O valor mensal necessário cabe "
            "no saldo disponível do período."
        )

    st.caption(
        "A análise considera uma meta por vez. "
        "Para várias metas, some os valores mensais necessários."
    )