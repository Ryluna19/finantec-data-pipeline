"""Componente responsável pela simulação de metas financeiras."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from analytics import (
    calcular_meta_mensal as calculate_monthly_goal,
    formatar_moeda as format_currency,
)
from ui_components import render_html


def calculate_goal_progress(
    current_value: float,
    goal_value: float,
) -> float:
    """Calcula o progresso visual da meta entre 0% e 100%."""
    if goal_value <= 0:
        return 0.0

    progress = (
        current_value
        / goal_value
        * 100
    )

    return max(
        0.0,
        min(progress, 100.0),
    )


def render_goal_simulator(
    user_profile: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    """Exibe a simulação mensal de uma meta financeira."""
    st.subheader(
        "Simulador de metas"
    )

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
        if goal["nome"]
        == selected_goal_name
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

    remaining_value = float(
        simulation["valor_restante"]
    )

    monthly_amount = simulation[
        "valor_mensal_necessario"
    ]

    monthly_amount_label = (
        format_currency(
            monthly_amount
        )
        if monthly_amount is not None
        else "Prazo inválido"
    )

    progress_percentage = (
        calculate_goal_progress(
            current_value=current_value,
            goal_value=goal_value,
        )
    )

    progress_description = (
        "Meta concluída"
        if progress_percentage >= 100
        else (
            f"{progress_percentage:.1f}% "
            "da meta alcançada"
        )
    )

    render_html(
        f"""
        <div class="finantec-goal-grid">
            <div class="finantec-goal-card neutral">
                <div class="finantec-goal-label">
                    Valor da meta
                </div>

                <div class="finantec-goal-value">
                    {escape(format_currency(goal_value))}
                </div>

                <div class="finantec-goal-description">
                    Objetivo financeiro total.
                </div>
            </div>

            <div class="finantec-goal-card current">
                <div class="finantec-goal-label">
                    Valor atual
                </div>

                <div class="finantec-goal-value">
                    {escape(format_currency(current_value))}
                </div>

                <div class="finantec-goal-description">
                    Valor já reservado.
                </div>
            </div>

            <div class="finantec-goal-card remaining">
                <div class="finantec-goal-label">
                    Falta guardar
                </div>

                <div class="finantec-goal-value">
                    {escape(format_currency(remaining_value))}
                </div>

                <div class="finantec-goal-description">
                    Valor restante para concluir.
                </div>
            </div>

            <div class="finantec-goal-card monthly">
                <div class="finantec-goal-label">
                    Necessário por mês
                </div>

                <div class="finantec-goal-value">
                    {escape(monthly_amount_label)}
                </div>

                <div class="finantec-goal-description">
                    Considerando o prazo informado.
                </div>
            </div>
        </div>

        <div class="finantec-goal-progress-panel">
            <div class="finantec-goal-progress-header">
                <div>
                    <div class="finantec-goal-progress-title">
                        Progresso da meta
                    </div>

                    <div class="finantec-goal-progress-name">
                        {escape(selected_goal_name)}
                    </div>
                </div>

                <strong>
                    {escape(progress_description)}
                </strong>
            </div>

            <div
                class="finantec-goal-progress-track"
                role="progressbar"
                aria-valuemin="0"
                aria-valuemax="100"
                aria-valuenow="{progress_percentage:.1f}"
            >
                <div
                    class="finantec-goal-progress-fill"
                    style="width: {progress_percentage:.1f}%;"
                >
                </div>
            </div>

            <div class="finantec-goal-progress-footer">
                <span>
                    {escape(format_currency(current_value))}
                </span>

                <span>
                    Meta:
                    {escape(format_currency(goal_value))}
                </span>
            </div>
        </div>
        """
    )

    if monthly_amount is None:
        st.warning(
            "Não foi possível calcular a meta "
            "porque o prazo é inválido."
        )
        return

    available_balance = float(
        summary["saldo_disponivel"]
    )

    if remaining_value <= 0:
        st.success(
            "A meta já foi alcançada."
        )

    elif monthly_amount > available_balance:
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