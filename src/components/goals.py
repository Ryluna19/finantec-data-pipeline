"""Gerenciamento e simulação de metas financeiras."""

from __future__ import annotations

from html import escape
from math import ceil
from typing import Any

import streamlit as st

from analytics import (
    calcular_meta_mensal as calculate_monthly_goal,
    formatar_moeda as format_currency,
)
from data_loader import ARQUIVO_BANCO
from src.goal_repository import (
    DuplicateFinancialGoalError,
    FinancialGoalNotFoundError,
    create_financial_goal,
    delete_financial_goal,
    update_financial_goal,
)
from ui_components import render_html

GOAL_FORM_OPEN_KEY = "financial_goal_form_open"
GOAL_EDIT_ID_KEY = "financial_goal_edit_id"
GOAL_DELETE_ID_KEY = "financial_goal_delete_id"
GOAL_FORM_VERSION_KEY = "financial_goal_form_version"
GOAL_FEEDBACK_KEY = "financial_goal_feedback"
SELECTED_GOAL_KEY = "selected_financial_goal"
GOAL_VIEW_KEY = "financial_goal_view"

GOAL_VIEW_MANAGEMENT = "Minhas metas"
GOAL_VIEW_SIMULATOR = "Simulador"
VALID_GOAL_VIEWS = {
    GOAL_VIEW_MANAGEMENT,
    GOAL_VIEW_SIMULATOR,
}

SIMULATION_MODE_DEADLINE = "Prazo desejado"
SIMULATION_MODE_MONTHLY = "Valor mensal disponível"


def calculate_goal_progress(
    current_value: float,
    goal_value: float,
) -> float:
    """Calcula o progresso visual da meta entre 0% e 100%."""
    if goal_value <= 0:
        return 0.0

    progress = current_value / goal_value * 100

    return max(
        0.0,
        min(
            progress,
            100.0,
        ),
    )


def calculate_goal_overview(
    *,
    target_amount: float,
    current_amount: float,
    deadline_months: int,
) -> dict[str, float | bool]:
    """Resume os valores exibidos no cartão de uma meta salva."""
    simulation = calculate_monthly_goal(
        valor_meta=target_amount,
        prazo_meses=deadline_months,
        valor_ja_reservado=current_amount,
    )

    remaining_amount = float(
        simulation["valor_restante"]
    )

    monthly_amount = float(
        simulation["valor_mensal_necessario"]
        or 0.0
    )

    return {
        "progress": calculate_goal_progress(
            current_value=current_amount,
            goal_value=target_amount,
        ),
        "remaining_amount": remaining_amount,
        "monthly_amount": monthly_amount,
        "completed": remaining_amount <= 0,
    }


def calculate_estimated_months(
    remaining_value: float,
    monthly_amount: float,
) -> int | None:
    """Calcula quantos meses são necessários para concluir uma meta."""
    if remaining_value <= 0:
        return 0

    if monthly_amount <= 0:
        return None

    return int(ceil(remaining_value / monthly_amount))


def build_goal_payload(
    *,
    name: str,
    target_amount: float,
    current_amount: float,
    deadline_months: int,
    priority: str,
) -> dict[str, Any]:
    """Monta os dados enviados ao repositório de metas."""
    return {
        "nome": name,
        "valor_meta": float(target_amount),
        "valor_atual": float(current_amount),
        "prazo_meses": int(deadline_months),
        "prioridade": priority,
    }


def format_currency_markdown(
    value: float,
) -> str:
    """Formata moeda sem ativar matemática no Markdown."""
    return format_currency(value).replace(
        "$",
        r"\$",
    )


def _get_goal_view() -> str:
    """Retorna a visualização ativa da tela de metas."""
    selected_view = st.session_state.get(
        GOAL_VIEW_KEY,
        GOAL_VIEW_MANAGEMENT,
    )

    if selected_view not in VALID_GOAL_VIEWS:
        selected_view = GOAL_VIEW_MANAGEMENT

    st.session_state[GOAL_VIEW_KEY] = selected_view

    return str(selected_view)


def _set_goal_view(
    selected_view: str,
) -> None:
    """Ativa uma das visualizações disponíveis para metas."""
    if selected_view not in VALID_GOAL_VIEWS:
        selected_view = GOAL_VIEW_MANAGEMENT

    st.session_state[GOAL_VIEW_KEY] = selected_view


def _render_goal_view_selector(
    active_view: str,
) -> None:
    """Exibe os comandos para alternar entre metas e simulador."""
    management_column, simulator_column = st.columns(
        2,
        gap="small",
    )

    with management_column:
        st.button(
            GOAL_VIEW_MANAGEMENT,
            key="show-financial-goals",
            type=(
                "primary"
                if active_view == GOAL_VIEW_MANAGEMENT
                else "secondary"
            ),
            use_container_width=True,
            on_click=_set_goal_view,
            args=(GOAL_VIEW_MANAGEMENT,),
        )

    with simulator_column:
        st.button(
            GOAL_VIEW_SIMULATOR,
            key="show-goal-simulator",
            type=(
                "primary"
                if active_view == GOAL_VIEW_SIMULATOR
                else "secondary"
            ),
            use_container_width=True,
            on_click=_set_goal_view,
            args=(GOAL_VIEW_SIMULATOR,),
        )


def _get_form_version() -> int:
    """Retorna a versão atual do formulário."""
    return int(
        st.session_state.get(
            GOAL_FORM_VERSION_KEY,
            0,
        )
    )


def _advance_form_version() -> None:
    """Atualiza as chaves dos widgets do formulário."""
    st.session_state[GOAL_FORM_VERSION_KEY] = _get_form_version() + 1


def _open_goal_form(
    goal_id: str | None = None,
) -> None:
    """Abre o formulário para criação ou edição."""
    st.session_state[GOAL_FORM_OPEN_KEY] = True

    st.session_state[GOAL_EDIT_ID_KEY] = goal_id

    _advance_form_version()


def _close_goal_form() -> None:
    """Fecha e reinicia o formulário de metas."""
    st.session_state[GOAL_FORM_OPEN_KEY] = False

    st.session_state[GOAL_EDIT_ID_KEY] = None

    _advance_form_version()


def _set_goal_feedback(
    message_type: str,
    message: str,
) -> None:
    """Guarda uma mensagem para o próximo rerun."""
    st.session_state[GOAL_FEEDBACK_KEY] = {
        "type": message_type,
        "message": message,
    }


def _show_goal_feedback() -> None:
    """Exibe o resultado da operação anterior."""
    feedback = st.session_state.pop(
        GOAL_FEEDBACK_KEY,
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

    if feedback.get("type") == "error":
        st.error(message)

    else:
        st.success(message)


def _find_goal(
    goals: list[dict[str, Any]],
    goal_id: str | None,
) -> dict[str, Any] | None:
    """Localiza uma meta pelo identificador."""
    if not goal_id:
        return None

    return next(
        (goal for goal in goals if goal.get("goal_id") == goal_id),
        None,
    )


def _render_goal_form(
    goals: list[dict[str, Any]],
    user_id: str,
) -> None:
    """Exibe o formulário de criação ou edição."""
    if not st.session_state.get(
        GOAL_FORM_OPEN_KEY,
        False,
    ):
        return

    edit_goal_id = st.session_state.get(GOAL_EDIT_ID_KEY)

    editing_goal = _find_goal(
        goals,
        edit_goal_id,
    )

    is_editing = editing_goal is not None

    if edit_goal_id and editing_goal is None:
        _close_goal_form()

        st.warning("A meta selecionada para edição " "não foi encontrada.")

        return

    default_name = (
        str(
            editing_goal.get(
                "nome",
                "",
            )
        )
        if editing_goal
        else ""
    )

    default_target = (
        float(
            editing_goal.get(
                "valor_meta",
                1000.0,
            )
        )
        if editing_goal
        else 1000.0
    )

    default_current = (
        float(
            editing_goal.get(
                "valor_atual",
                0.0,
            )
        )
        if editing_goal
        else 0.0
    )

    default_deadline = (
        int(
            editing_goal.get(
                "prazo_meses",
                12,
            )
        )
        if editing_goal
        else 12
    )

    default_priority = (
        str(
            editing_goal.get(
                "prioridade",
                "média",
            )
        )
        if editing_goal
        else "média"
    )

    title = "Editar meta" if is_editing else "Nova meta"

    st.markdown(f"### {title}")

    form_version = _get_form_version()

    with st.form(
        key=("financial-goal-form-" f"{form_version}"),
        border=True,
    ):
        name = st.text_input(
            "Nome da meta",
            value=default_name,
            max_chars=120,
            placeholder=("Ex.: Viagem, notebook ou reserva"),
        )

        (
            target_column,
            current_column,
        ) = st.columns(
            2,
            gap="medium",
        )

        with target_column:
            target_amount = st.number_input(
                "Valor da meta",
                min_value=1.0,
                value=default_target,
                step=100.0,
                format="%.2f",
            )

        with current_column:
            current_amount = st.number_input(
                "Valor já guardado",
                min_value=0.0,
                value=default_current,
                step=50.0,
                format="%.2f",
            )

        deadline_months = st.number_input(
            "Prazo em meses",
            min_value=1,
            max_value=600,
            value=default_deadline,
            step=1,
        )

        (
            save_column,
            cancel_column,
        ) = st.columns(
            2,
            gap="small",
        )

        with save_column:
            submitted = st.form_submit_button(
                ("Salvar alterações" if is_editing else "Criar meta"),
                type="primary",
                use_container_width=True,
            )

        with cancel_column:
            cancelled = st.form_submit_button(
                "Cancelar",
                use_container_width=True,
            )

    if cancelled:
        _close_goal_form()
        st.rerun()

    if not submitted:
        return

    goal_payload = build_goal_payload(
        name=name,
        target_amount=target_amount,
        current_amount=current_amount,
        deadline_months=(int(deadline_months)),
        priority=default_priority,
    )

    try:
        if is_editing:
            update_financial_goal(
                database_path=ARQUIVO_BANCO,
                user_id=user_id,
                goal_id=str(editing_goal["goal_id"]),
                goal=goal_payload,
            )

            feedback_message = "Meta atualizada com sucesso."

        else:
            create_financial_goal(
                database_path=ARQUIVO_BANCO,
                user_id=user_id,
                goal=goal_payload,
            )

            feedback_message = "Meta criada com sucesso."

    except (
        DuplicateFinancialGoalError,
        FinancialGoalNotFoundError,
        ValueError,
        RuntimeError,
    ) as error:
        st.error(str(error))

        return

    _close_goal_form()

    _set_goal_feedback(
        "success",
        feedback_message,
    )

    st.cache_data.clear()
    st.rerun()


def _delete_goal(
    goal_id: str,
    user_id: str,
) -> None:
    """Exclui uma meta após confirmação."""
    try:
        deleted = delete_financial_goal(
            database_path=ARQUIVO_BANCO,
            user_id=user_id,
            goal_id=goal_id,
        )

    except RuntimeError as error:
        st.error(str(error))

        return

    if not deleted:
        st.error("A meta informada não foi encontrada.")

        return

    if st.session_state.get(SELECTED_GOAL_KEY) == goal_id:
        st.session_state.pop(
            SELECTED_GOAL_KEY,
            None,
        )

    st.session_state[GOAL_DELETE_ID_KEY] = None

    _set_goal_feedback(
        "success",
        "Meta excluída com sucesso.",
    )

    st.cache_data.clear()
    st.rerun()


def _render_goal_management_cards(
    goals: list[dict[str, Any]],
    user_id: str,
    read_only: bool = False,
) -> None:
    """Exibe as metas cadastradas e suas ações."""
    if not goals:
        st.info(
            "Nenhuma meta financeira foi cadastrada. "
            "Crie sua primeira meta para começar."
        )

        return

    pending_delete_id = st.session_state.get(GOAL_DELETE_ID_KEY)

    for goal in goals:
        goal_id = str(goal["goal_id"])

        name = str(goal["nome"])

        target_amount = float(goal["valor_meta"])

        current_amount = float(goal["valor_atual"])

        deadline_months = int(goal["prazo_meses"])

        overview = calculate_goal_overview(
            target_amount=target_amount,
            current_amount=current_amount,
            deadline_months=deadline_months,
        )

        progress = float(overview["progress"])

        remaining_amount = float(
            overview["remaining_amount"]
        )

        monthly_amount = float(
            overview["monthly_amount"]
        )

        completed = bool(overview["completed"])

        with st.container(
            border=True,
            key=("financial-goal-card-" f"{goal_id}"),
        ):
            (
                details_column,
                progress_column,
            ) = st.columns(
                [
                    2,
                    1,
                ],
                gap="medium",
            )

            with details_column:
                st.markdown(f"### {name}")

                st.caption(
                    "Meta: "
                    f"{format_currency_markdown(target_amount)} · "
                    f"Prazo: {deadline_months} meses"
                )

            with progress_column:
                if completed:
                    st.success("Meta concluída")

                else:
                    st.caption("Em andamento")

            (
                current_column,
                remaining_column,
                monthly_column,
            ) = st.columns(
                3,
                gap="small",
            )

            with current_column:
                st.metric(
                    "Valor guardado",
                    format_currency(current_amount),
                )

            with remaining_column:
                st.metric(
                    "Falta guardar",
                    format_currency(remaining_amount),
                )

            with monthly_column:
                st.metric(
                    "Necessário por mês",
                    format_currency(monthly_amount),
                )

            st.caption(
                "Meta concluída"
                if completed
                else f"{progress:.1f}% concluído"
            )

            render_html(f"""
                <div
                    class="finantec-goal-progress-track"
                    role="progressbar"
                    aria-valuemin="0"
                    aria-valuemax="100"
                    aria-valuenow="{progress:.1f}"
                >
                    <div
                        class="finantec-goal-progress-fill"
                        style="width: {progress:.1f}%;"
                    >
                    </div>
                </div>
                """)

            if not read_only:
                (
                    edit_column,
                    delete_column,
                ) = st.columns(
                    2,
                    gap="small",
                )

                with edit_column:
                    if st.button(
                        "Editar",
                        key=("edit-financial-goal-" f"{goal_id}"),
                        use_container_width=True,
                    ):
                        _open_goal_form(goal_id)

                        st.rerun()

                with delete_column:
                    if st.button(
                        "Excluir",
                        key=("delete-financial-goal-" f"{goal_id}"),
                        use_container_width=True,
                    ):
                        st.session_state[GOAL_DELETE_ID_KEY] = goal_id

                        st.rerun()

                if pending_delete_id == goal_id:
                    st.markdown(
                        f"**Excluir a meta “{name}”?** "
                        "Essa ação não pode ser desfeita."
                    )

                    (
                        confirm_column,
                        cancel_column,
                    ) = st.columns(
                        2,
                        gap="small",
                    )

                    with confirm_column:
                        if st.button(
                            "Sim, excluir",
                            key=("confirm-delete-goal-" f"{goal_id}"),
                            type="primary",
                            use_container_width=True,
                        ):
                            _delete_goal(
                                goal_id,
                                user_id,
                            )

                    with cancel_column:
                        if st.button(
                            "Manter meta",
                            key=("cancel-delete-goal-" f"{goal_id}"),
                            use_container_width=True,
                        ):
                            st.session_state[GOAL_DELETE_ID_KEY] = None

                            st.rerun()


def _render_goal_management_view(
    goals: list[dict[str, Any]],
    user_id: str,
    read_only: bool = False,
) -> None:
    """Exibe a consulta e as ações das metas salvas."""
    if read_only:
        st.markdown("### Metas de demonstração")

        st.caption(
            "Acompanhe as metas fictícias ou use o simulador."
        )

        _render_goal_management_cards(
            goals,
            user_id,
            read_only=True,
        )

        return

    title_column, action_column = st.columns(
        [
            3,
            1,
        ],
        gap="small",
    )

    with title_column:
        st.markdown("### Minhas metas")

        st.caption(
            "Acompanhe o progresso e atualize "
            "suas metas quando precisar."
        )

    with action_column:
        if st.button(
            "Nova meta",
            key="open-new-financial-goal",
            type="primary",
            use_container_width=True,
        ):
            _open_goal_form()
            st.rerun()

    _render_goal_form(
        goals,
        user_id,
    )

    _render_goal_management_cards(
        goals,
        user_id,
    )


def _render_goal_summary(
    *,
    goal_name: str,
    goal_value: float,
    current_value: float,
    remaining_value: float,
    fourth_label: str,
    fourth_value: str,
    fourth_description: str,
) -> None:
    """Exibe os cartões e a barra de progresso da meta."""
    progress_percentage = calculate_goal_progress(
        current_value=current_value,
        goal_value=goal_value,
    )

    progress_description = (
        "Meta concluída"
        if progress_percentage >= 100
        else (f"{progress_percentage:.1f}% " "da meta alcançada")
    )

    render_html(f"""
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
                    {escape(fourth_label)}
                </div>

                <div class="finantec-goal-value">
                    {escape(fourth_value)}
                </div>

                <div class="finantec-goal-description">
                    {escape(fourth_description)}
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
                        {escape(goal_name)}
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
        """)


def _render_balance_evaluation(
    monthly_amount: float,
    available_balance: float,
) -> None:
    """Compara o esforço mensal com o saldo do período."""
    if available_balance <= 0:
        st.info(
            "Não há saldo disponível positivo no período "
            "para comparar com esta simulação."
        )

    elif monthly_amount > available_balance:
        st.error("O valor mensal simulado ultrapassa " "o saldo disponível do período.")

    else:
        st.success("O valor mensal simulado cabe " "no saldo disponível do período.")


def _render_goal_simulation(
    goal: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    """Exibe a simulação interativa da meta selecionada."""
    goal_id = str(goal["goal_id"])

    goal_name = str(goal["nome"])

    goal_value = float(goal["valor_meta"])

    current_value = float(goal["valor_atual"])

    stored_deadline = int(goal["prazo_meses"])

    remaining_value = max(
        goal_value - current_value,
        0.0,
    )

    available_balance = float(
        summary.get(
            "saldo_disponivel",
            0.0,
        )
        or 0.0
    )

    if remaining_value <= 0:
        _render_goal_summary(
            goal_name=goal_name,
            goal_value=goal_value,
            current_value=current_value,
            remaining_value=0.0,
            fourth_label="Situação",
            fourth_value="Concluída",
            fourth_description=("O valor da meta já foi alcançado."),
        )

        st.success("Esta meta já foi concluída.")

        return

    simulation_mode = st.radio(
        "Simular por",
        options=[
            SIMULATION_MODE_DEADLINE,
            SIMULATION_MODE_MONTHLY,
        ],
        horizontal=True,
        key=("goal-simulation-mode-" f"{goal_id}"),
    )

    if simulation_mode == SIMULATION_MODE_DEADLINE:
        maximum_deadline = max(
            60,
            min(
                max(
                    stored_deadline * 2,
                    stored_deadline,
                ),
                600,
            ),
        )

        selected_deadline = st.slider(
            "Em quantos meses deseja concluir?",
            min_value=1,
            max_value=maximum_deadline,
            value=min(
                stored_deadline,
                maximum_deadline,
            ),
            step=1,
            key=("goal-deadline-slider-" f"{goal_id}"),
        )

        simulation = calculate_monthly_goal(
            valor_meta=goal_value,
            prazo_meses=(selected_deadline),
            valor_ja_reservado=(current_value),
        )

        monthly_amount = float(simulation["valor_mensal_necessario"] or 0.0)

        _render_goal_summary(
            goal_name=goal_name,
            goal_value=goal_value,
            current_value=current_value,
            remaining_value=remaining_value,
            fourth_label=("Necessário por mês"),
            fourth_value=(format_currency(monthly_amount)),
            fourth_description=(f"Para concluir em " f"{selected_deadline} meses."),
        )

        _render_balance_evaluation(
            monthly_amount=monthly_amount,
            available_balance=(available_balance),
        )

    else:
        maximum_monthly_amount = max(
            500.0,
            float(ceil(remaining_value / 50) * 50),
        )

        suggested_monthly_amount = remaining_value / max(
            stored_deadline,
            1,
        )

        suggested_monthly_amount = round(suggested_monthly_amount / 50) * 50

        suggested_monthly_amount = min(
            max(
                suggested_monthly_amount,
                50.0,
            ),
            maximum_monthly_amount,
        )

        selected_monthly_amount = st.slider(
            "Quanto consegue guardar por mês?",
            min_value=50.0,
            max_value=(maximum_monthly_amount),
            value=float(suggested_monthly_amount),
            step=50.0,
            format="R$ %.2f",
            key=("goal-monthly-slider-" f"{goal_id}"),
        )

        estimated_months = calculate_estimated_months(
            remaining_value=(remaining_value),
            monthly_amount=(selected_monthly_amount),
        )

        months_label = (
            "Prazo inválido"
            if estimated_months is None
            else (
                f"{estimated_months} " + ("mês" if estimated_months == 1 else "meses")
            )
        )

        _render_goal_summary(
            goal_name=goal_name,
            goal_value=goal_value,
            current_value=current_value,
            remaining_value=remaining_value,
            fourth_label="Prazo estimado",
            fourth_value=months_label,
            fourth_description=("Considerando o valor mensal selecionado."),
        )

        _render_balance_evaluation(
            monthly_amount=(selected_monthly_amount),
            available_balance=(available_balance),
        )

    st.caption(
        "A simulação não altera a meta salva. "
        "Use a ação Editar para atualizar valores ou prazo."
    )


def _render_goal_simulator_view(
    goals: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """Exibe o simulador separado do gerenciamento de metas."""
    st.markdown("### Simulador")

    st.caption(
        "Selecione uma meta e ajuste o prazo "
        "ou o valor mensal disponível."
    )

    if not goals:
        st.info(
            "Crie uma meta em Minhas metas "
            "antes de iniciar uma simulação."
        )

        return

    goal_ids = [str(goal["goal_id"]) for goal in goals]

    selected_goal_id = st.session_state.get(SELECTED_GOAL_KEY)

    if selected_goal_id not in goal_ids:
        st.session_state[SELECTED_GOAL_KEY] = goal_ids[0]

    selected_goal_id = st.selectbox(
        "Meta",
        options=goal_ids,
        key=SELECTED_GOAL_KEY,
        format_func=(
            lambda goal_id: str(
                _find_goal(
                    goals,
                    goal_id,
                )["nome"]
            )
        ),
    )

    selected_goal = _find_goal(
        goals,
        selected_goal_id,
    )

    if selected_goal is None:
        st.warning("A meta selecionada não foi encontrada.")

        return

    _render_goal_simulation(
        goal=selected_goal,
        summary=summary,
    )


def render_goal_simulator(
    user_profile: dict[str, Any],
    summary: dict[str, Any],
    user_id: str,
    data_mode: str,
) -> None:
    """Exibe gerenciamento e simulação das metas financeiras."""
    st.subheader("Metas")

    st.caption(
        "Acompanhe seus objetivos ou simule "
        "diferentes formas de alcançá-los."
    )

    _show_goal_feedback()

    is_demo = data_mode == "demo"

    if is_demo:
        st.info(
            "Metas de demonstração. "
            "Os dados são fictícios e somente leitura."
        )

    goals = list(
        user_profile.get(
            "objetivos_financeiros",
            [],
        )
    )

    active_view = _get_goal_view()

    _render_goal_view_selector(active_view)

    active_view = _get_goal_view()

    if active_view == GOAL_VIEW_SIMULATOR:
        _render_goal_simulator_view(
            goals,
            summary,
        )

        return

    _render_goal_management_view(
        goals,
        user_id,
        read_only=is_demo,
    )
