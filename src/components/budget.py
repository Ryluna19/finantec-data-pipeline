"""Planejamento mensal de gastos por categoria."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from analytics import (
    calcular_acompanhamento_orcamento as calculate_budget_tracking,
    calcular_resumo_orcamento as calculate_budget_summary,
    filtrar_transacoes_por_mes as filter_transactions_by_month,
    formatar_moeda as format_currency,
    listar_meses_disponiveis as list_available_months,
)
from data_loader import ARQUIVO_BANCO
from src.budget_repository import (
    DuplicateMonthlyBudgetError,
    create_monthly_budget,
    list_monthly_budgets,
)
from ui_components import MONTH_NAMES_PT_BR


BUDGET_FORM_OPEN_KEY = (
    "monthly_budget_form_open"
)

BUDGET_FORM_VERSION_KEY = (
    "monthly_budget_form_version"
)

BUDGET_FEEDBACK_KEY = (
    "monthly_budget_feedback"
)

BUDGET_PERIOD_KEY = (
    "monthly_budget_period"
)


def build_budget_period_options(
    transactions: pd.DataFrame,
    reference_period: str | None = None,
) -> list[str]:
    """Lista os meses disponíveis e inclui o mês atual."""
    current_period = (
        reference_period
        or datetime.now().strftime(
            "%Y-%m"
        )
    )

    available_periods = (
        list_available_months(
            transactions
        )
        if not transactions.empty
        else []
    )

    periods = {
        str(period).strip()
        for period in available_periods
        if str(period).strip()
    }

    periods.add(
        current_period
    )

    return sorted(
        periods,
        reverse=True,
    )


def format_budget_period(
    period: str,
) -> str:
    """Formata AAAA-MM para o nome legível do mês."""
    try:
        year_text, month_text = (
            period.split(
                "-",
                maxsplit=1,
            )
        )

        month = int(
            month_text
        )

        month_name = (
            MONTH_NAMES_PT_BR[
                month
            ]
        )

    except (
        ValueError,
        KeyError,
        IndexError,
    ):
        return period

    return (
        f"{month_name}/{year_text}"
    )


def build_budget_payload(
    *,
    period: str,
    category: str,
    planned_amount: float,
) -> dict[str, Any]:
    """Monta o orçamento enviado ao repositório."""
    return {
        "period": period,
        "category": category,
        "planned_amount": float(
            planned_amount
        ),
    }


def get_budget_status_label(
    status: str,
    usage_percentage: float,
) -> str:
    """Traduz o estado interno para a interface."""
    if status == "over_limit":
        return "Limite ultrapassado"

    if (
        status == "near_limit"
        and usage_percentage >= 100
    ):
        return "Limite atingido"

    if status == "near_limit":
        return "Próximo do limite"

    return "Dentro do limite"


def _get_form_version() -> int:
    """Retorna a versão atual do formulário."""
    return int(
        st.session_state.get(
            BUDGET_FORM_VERSION_KEY,
            0,
        )
    )


def _advance_form_version() -> None:
    """Troca as chaves dos campos após salvar ou cancelar."""
    st.session_state[
        BUDGET_FORM_VERSION_KEY
    ] = (
        _get_form_version()
        + 1
    )


def _open_budget_form() -> None:
    """Abre o formulário de novo limite."""
    st.session_state[
        BUDGET_FORM_OPEN_KEY
    ] = True

    _advance_form_version()


def _close_budget_form() -> None:
    """Fecha e reinicia o formulário."""
    st.session_state[
        BUDGET_FORM_OPEN_KEY
    ] = False

    _advance_form_version()


def _set_budget_feedback(
    message_type: str,
    message: str,
) -> None:
    """Guarda feedback para o próximo rerun."""
    st.session_state[
        BUDGET_FEEDBACK_KEY
    ] = {
        "type": message_type,
        "message": message,
    }


def _show_budget_feedback() -> None:
    """Exibe o resultado da operação anterior."""
    feedback = st.session_state.pop(
        BUDGET_FEEDBACK_KEY,
        None,
    )

    if not feedback:
        return

    message = str(
        feedback.get(
            "message",
            "",
        )
    )

    if feedback.get(
        "type"
    ) == "error":
        st.error(
            message
        )

        return

    st.success(
        message
    )


def _render_budget_form(
    *,
    user_id: str,
    selected_period: str,
) -> None:
    """Exibe o cadastro de um limite por categoria."""
    if not st.session_state.get(
        BUDGET_FORM_OPEN_KEY,
        False,
    ):
        return

    st.markdown(
        "### Novo limite"
    )

    st.caption(
        "Defina quanto pretende gastar em uma categoria "
        f"durante {format_budget_period(selected_period)}."
    )

    form_version = (
        _get_form_version()
    )

    with st.form(
        key=(
            "monthly-budget-form-"
            f"{selected_period}-"
            f"{form_version}"
        ),
        border=True,
    ):
        category = st.text_input(
            "Categoria",
            max_chars=100,
            placeholder=(
                "Ex.: Alimentação, Transporte ou Lazer"
            ),
        )

        planned_amount = (
            st.number_input(
                "Valor planejado",
                min_value=1.0,
                value=100.0,
                step=50.0,
                format="%.2f",
            )
        )

        (
            save_column,
            cancel_column,
        ) = st.columns(
            2,
            gap="small",
        )

        with save_column:
            submitted = (
                st.form_submit_button(
                    "Criar limite",
                    type="primary",
                    use_container_width=True,
                )
            )

        with cancel_column:
            cancelled = (
                st.form_submit_button(
                    "Cancelar",
                    use_container_width=True,
                )
            )

    if cancelled:
        _close_budget_form()
        st.rerun()

    if not submitted:
        return

    payload = build_budget_payload(
        period=selected_period,
        category=category,
        planned_amount=planned_amount,
    )

    try:
        create_monthly_budget(
            database_path=ARQUIVO_BANCO,
            user_id=user_id,
            budget=payload,
        )

    except (
        DuplicateMonthlyBudgetError,
        ValueError,
        RuntimeError,
    ) as error:
        st.error(
            str(error)
        )

        return

    _close_budget_form()

    _set_budget_feedback(
        "success",
        "Limite criado com sucesso.",
    )

    st.cache_data.clear()
    st.rerun()


def _render_budget_summary(
    summary: dict[str, float | int],
) -> None:
    """Exibe os totais das categorias planejadas."""
    (
        planned_column,
        spent_column,
        remaining_column,
        exceeded_column,
    ) = st.columns(
        4,
        gap="small",
    )

    with planned_column:
        st.metric(
            "Total planejado",
            format_currency(
                float(
                    summary[
                        "total_planned"
                    ]
                )
            ),
        )

    with spent_column:
        st.metric(
            "Gasto nas categorias",
            format_currency(
                float(
                    summary[
                        "total_spent"
                    ]
                )
            ),
        )

    with remaining_column:
        st.metric(
            "Saldo planejado",
            format_currency(
                float(
                    summary[
                        "total_remaining"
                    ]
                )
            ),
        )

    with exceeded_column:
        st.metric(
            "Acima do limite",
            int(
                summary[
                    "categories_over_limit"
                ]
            ),
        )

    st.caption(
        "Os totais consideram somente as categorias "
        "que possuem um limite cadastrado."
    )


def _render_budget_cards(
    tracking: list[
        dict[str, Any]
    ],
) -> None:
    """Exibe o acompanhamento por categoria."""
    if not tracking:
        st.info(
            "Nenhum limite foi cadastrado para este mês."
        )

        return

    for item in tracking:
        category = str(
            item[
                "category"
            ]
        )

        planned_amount = float(
            item[
                "planned_amount"
            ]
        )

        spent_amount = float(
            item[
                "spent_amount"
            ]
        )

        remaining_amount = float(
            item[
                "remaining_amount"
            ]
        )

        usage_percentage = float(
            item[
                "usage_percentage"
            ]
        )

        status = str(
            item[
                "status"
            ]
        )

        status_label = (
            get_budget_status_label(
                status,
                usage_percentage,
            )
        )

        with st.container(
            border=True,
            key=(
                "monthly-budget-card-"
                f"{item.get('budget_id')}"
            ),
        ):
            (
                title_column,
                status_column,
            ) = st.columns(
                [
                    3,
                    1,
                ],
                gap="small",
            )

            with title_column:
                st.markdown(
                    f"### {category}"
                )

            with status_column:
                if status == "over_limit":
                    st.error(
                        status_label
                    )

                elif status == "near_limit":
                    st.warning(
                        status_label
                    )

                else:
                    st.success(
                        status_label
                    )

            (
                planned_column,
                spent_column,
                balance_column,
            ) = st.columns(
                3,
                gap="small",
            )

            with planned_column:
                st.metric(
                    "Planejado",
                    format_currency(
                        planned_amount
                    ),
                )

            with spent_column:
                st.metric(
                    "Gasto",
                    format_currency(
                        spent_amount
                    ),
                )

            with balance_column:
                if remaining_amount >= 0:
                    st.metric(
                        "Disponível",
                        format_currency(
                            remaining_amount
                        ),
                    )

                else:
                    st.metric(
                        "Ultrapassado",
                        format_currency(
                            abs(
                                remaining_amount
                            )
                        ),
                    )

            visual_progress = min(
                max(
                    usage_percentage
                    / 100,
                    0.0,
                ),
                1.0,
            )

            st.progress(
                visual_progress
            )

            st.caption(
                f"{usage_percentage:.1f}% do limite utilizado."
            )


def render_monthly_budget(
    *,
    transactions: pd.DataFrame,
    user_id: str,
    data_mode: str,
) -> None:
    """Exibe o planejamento mensal por categoria."""
    st.subheader(
        "Orçamento"
    )

    st.caption(
        "Planeje limites mensais e acompanhe "
        "quanto já gastou em cada categoria."
    )

    if data_mode == "demo":
        st.info(
            "O orçamento está disponível somente "
            "para seus dados pessoais."
        )

        return

    _show_budget_feedback()

    period_options = (
        build_budget_period_options(
            transactions
        )
    )

    selected_period = str(
        st.selectbox(
            "Mês do planejamento",
            options=period_options,
            format_func=format_budget_period,
            key=BUDGET_PERIOD_KEY,
        )
    )

    budgets = list_monthly_budgets(
        database_path=ARQUIVO_BANCO,
        user_id=user_id,
        period=selected_period,
    )

    period_transactions = (
        filter_transactions_by_month(
            transactions,
            selected_period,
        )
    )

    tracking = (
        calculate_budget_tracking(
            transacoes=period_transactions,
            orcamentos=budgets,
        )
    )

    title_column, action_column = (
        st.columns(
            [
                3,
                1,
            ],
            gap="small",
        )
    )

    with title_column:
        st.markdown(
            "### Planejamento do mês"
        )

        st.caption(
            "Consulte primeiro os limites existentes "
            "ou adicione uma nova categoria."
        )

    with action_column:
        if st.button(
            "Novo limite",
            key="open-new-monthly-budget",
            type="primary",
            use_container_width=True,
        ):
            _open_budget_form()
            st.rerun()

    _render_budget_form(
        user_id=user_id,
        selected_period=selected_period,
    )

    if tracking:
        summary = (
            calculate_budget_summary(
                tracking
            )
        )

        _render_budget_summary(
            summary
        )

    _render_budget_cards(
        tracking
    )

    st.caption(
        "A edição e a exclusão de limites serão "
        "adicionadas em uma próxima etapa."
    )