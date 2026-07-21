"""Gerenciamento e simulação de metas financeiras."""

from __future__ import annotations

import calendar
import os
from datetime import date, datetime
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

SIMULATION_SOURCE_SAVED = "Meta salva"
SIMULATION_SOURCE_FREE = "Simulação livre"
GOAL_SIMULATION_SOURCE_KEY = "goal_simulation_source"

GOAL_REFERENCE_DATE_ENV = "FINANTEC_TEST_DATE"
AVERAGE_DAYS_PER_MONTH = 365.2425 / 12


def get_goal_reference_date() -> date:
    """Obtém a data real ou uma data artificial de teste."""
    configured_date = os.getenv(
        GOAL_REFERENCE_DATE_ENV,
        "",
    ).strip()

    if not configured_date:
        return date.today()

    try:
        return date.fromisoformat(configured_date)

    except ValueError:
        return date.today()


def _add_months(
    base_date: date,
    months: int,
) -> date:
    """Adiciona meses preservando um dia válido no destino."""
    month_index = base_date.month - 1 + int(months)

    target_year = base_date.year + month_index // 12

    target_month = month_index % 12 + 1

    target_day = min(
        base_date.day,
        calendar.monthrange(
            target_year,
            target_month,
        )[1],
    )

    return date(
        target_year,
        target_month,
        target_day,
    )


def _parse_goal_deadline(
    value: object,
) -> date | None:
    """Converte uma data limite conhecida para ``date``."""
    if isinstance(
        value,
        datetime,
    ):
        return value.date()

    if isinstance(
        value,
        date,
    ):
        return value

    normalized_value = str(value if value is not None else "").strip()

    if not normalized_value:
        return None

    try:
        return date.fromisoformat(normalized_value)

    except ValueError:
        try:
            return datetime.strptime(
                normalized_value,
                "%d/%m/%Y",
            ).date()

        except ValueError:
            return None


def resolve_goal_deadline_date(
    goal: dict[str, Any],
    *,
    reference_date: date | None = None,
) -> date:
    """Obtém a data limite, incluindo metas do formato legado."""
    current_date = (
        reference_date if reference_date is not None else get_goal_reference_date()
    )

    stored_deadline = _parse_goal_deadline(goal.get("data_limite"))

    if stored_deadline is not None:
        return stored_deadline

    legacy_months = max(
        int(
            goal.get(
                "prazo_meses",
                12,
            )
            or 12
        ),
        1,
    )

    return _add_months(
        current_date,
        legacy_months,
    )


def calculate_goal_deadline(
    *,
    deadline_date: date,
    reference_date: date | None = None,
) -> dict[str, float | int | bool]:
    """Calcula prazo e meses equivalentes usando uma data controlável."""
    current_date = (
        reference_date if reference_date is not None else get_goal_reference_date()
    )

    raw_days_remaining = (deadline_date - current_date).days

    days_remaining = max(
        raw_days_remaining,
        0,
    )

    calculation_months = max(
        1,
        ceil(days_remaining / AVERAGE_DAYS_PER_MONTH),
    )

    planning_months = max(
        days_remaining / AVERAGE_DAYS_PER_MONTH,
        1.0,
    )

    return {
        "days_remaining": days_remaining,
        "calculation_months": calculation_months,
        "planning_months": planning_months,
        "expired": raw_days_remaining < 0,
    }


def format_goal_deadline(
    deadline_date: date,
) -> str:
    """Formata a data limite no padrão brasileiro."""
    return deadline_date.strftime("%d/%m/%Y")


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
    deadline_months: int | None = None,
    deadline_date: date | None = None,
    reference_date: date | None = None,
) -> dict[str, float | bool]:
    """Resume os valores exibidos no cartão de uma meta salva."""
    remaining_amount = max(
        float(target_amount) - float(current_amount),
        0.0,
    )

    if remaining_amount <= 0:
        monthly_amount = 0.0

    elif deadline_date is not None:
        deadline_summary = calculate_goal_deadline(
            deadline_date=deadline_date,
            reference_date=reference_date,
        )

        monthly_amount = remaining_amount / float(deadline_summary["planning_months"])

    else:
        normalized_months = max(
            int(deadline_months or 1),
            1,
        )

        monthly_amount = remaining_amount / normalized_months

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
    priority: str,
    deadline_date: date | str | None = None,
    deadline_months: int | None = None,
) -> dict[str, Any]:
    """Monta os dados enviados ao repositório de metas."""
    payload: dict[str, Any] = {
        "nome": name,
        "valor_meta": float(target_amount),
        "valor_atual": float(current_amount),
        "prioridade": priority,
    }

    if deadline_date is not None:
        parsed_deadline = _parse_goal_deadline(deadline_date)

        if parsed_deadline is None:
            raise ValueError("A data limite da meta é inválida.")

        payload["data_limite"] = parsed_deadline.isoformat()

        return payload

    if deadline_months is None:
        raise ValueError("Informe a data limite da meta.")

    payload["prazo_meses"] = int(deadline_months)

    return payload


def build_free_simulation_goal(
    *,
    name: str,
    target_amount: float,
    current_amount: float,
    deadline_date: date | str,
    reference_date: date | None = None,
) -> dict[str, Any]:
    """Monta uma meta temporária usada somente pelo simulador."""
    normalized_name = " ".join(str(name).strip().split())

    if not normalized_name:
        normalized_name = "Simulação livre"

    normalized_target = float(target_amount)

    normalized_current = float(current_amount)

    if normalized_target <= 0:
        raise ValueError("O valor da meta deve ser maior que zero.")

    if normalized_current < 0:
        raise ValueError("O valor já guardado não pode ser negativo.")

    parsed_deadline = _parse_goal_deadline(deadline_date)

    if parsed_deadline is None:
        raise ValueError("A data limite da simulação é inválida.")

    current_date = (
        reference_date if reference_date is not None else get_goal_reference_date()
    )

    if parsed_deadline < current_date:
        raise ValueError("A data limite da simulação não pode estar no passado.")

    deadline_summary = calculate_goal_deadline(
        deadline_date=parsed_deadline,
        reference_date=current_date,
    )

    return {
        "goal_id": "free-goal-simulation",
        "nome": normalized_name,
        "valor_meta": normalized_target,
        "valor_atual": normalized_current,
        "data_limite": parsed_deadline.isoformat(),
        "prazo_meses": int(deadline_summary["calculation_months"]),
        "prioridade": "média",
        "status": (
            "completed" if normalized_current >= normalized_target else "active"
        ),
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
            type=("primary" if active_view == GOAL_VIEW_MANAGEMENT else "secondary"),
            use_container_width=True,
            on_click=_set_goal_view,
            args=(GOAL_VIEW_MANAGEMENT,),
        )

    with simulator_column:
        st.button(
            GOAL_VIEW_SIMULATOR,
            key="show-goal-simulator",
            type=("primary" if active_view == GOAL_VIEW_SIMULATOR else "secondary"),
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


def _render_goal_form_content(
    *,
    editing_goal: dict[str, Any] | None,
    user_id: str,
) -> None:
    """Exibe os campos compartilhados de criação e edição."""
    is_editing = editing_goal is not None

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

    reference_date = get_goal_reference_date()

    default_deadline = (
        resolve_goal_deadline_date(
            editing_goal,
            reference_date=reference_date,
        )
        if editing_goal
        else _add_months(
            reference_date,
            12,
        )
    )

    default_deadline = max(
        default_deadline,
        reference_date,
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

    st.caption(
        (
            "Atualize os valores e o prazo desta meta."
            if is_editing
            else ("Defina o objetivo, quanto já foi guardado " "e o prazo planejado.")
        )
    )

    form_version = _get_form_version()

    with st.form(
        key=("financial-goal-form-" f"{form_version}"),
        border=False,
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

        deadline_date = st.date_input(
            "Data limite",
            value=default_deadline,
            min_value=reference_date,
            max_value=_add_months(
                reference_date,
                600,
            ),
            format="DD/MM/YYYY",
        )

        deadline_summary = calculate_goal_deadline(
            deadline_date=deadline_date,
            reference_date=reference_date,
        )

        days_remaining = int(deadline_summary["days_remaining"])

        day_label = "dia" if days_remaining == 1 else "dias"

        st.caption(f"Faltam {days_remaining} {day_label} " "até a data planejada.")

        with st.container(
            key="financial-goal-dialog-actions",
        ):
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
        deadline_date=deadline_date,
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


@st.dialog(
    "Nova meta",
    width="medium",
    on_dismiss=_close_goal_form,
)
def _render_new_goal_dialog(
    *,
    user_id: str,
) -> None:
    """Exibe a criação de meta em um diálogo."""
    _render_goal_form_content(
        editing_goal=None,
        user_id=user_id,
    )


@st.dialog(
    "Editar meta",
    width="medium",
    on_dismiss=_close_goal_form,
)
def _render_edit_goal_dialog(
    *,
    editing_goal: dict[str, Any],
    user_id: str,
) -> None:
    """Exibe a edição de meta em um diálogo."""
    _render_goal_form_content(
        editing_goal=editing_goal,
        user_id=user_id,
    )


def _render_goal_form(
    goals: list[dict[str, Any]],
    user_id: str,
) -> None:
    """Abre o diálogo correspondente ao estado atual."""
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

    if edit_goal_id and editing_goal is None:
        _close_goal_form()

        st.warning("A meta selecionada para edição " "não foi encontrada.")

        return

    if editing_goal is None:
        _render_new_goal_dialog(
            user_id=user_id,
        )

        return

    _render_edit_goal_dialog(
        editing_goal=editing_goal,
        user_id=user_id,
    )


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

    reference_date = get_goal_reference_date()

    for goal in goals:
        goal_id = str(goal["goal_id"])

        name = str(goal["nome"])

        target_amount = float(goal["valor_meta"])

        current_amount = float(goal["valor_atual"])

        deadline_date = resolve_goal_deadline_date(
            goal,
            reference_date=reference_date,
        )

        deadline_summary = calculate_goal_deadline(
            deadline_date=deadline_date,
            reference_date=reference_date,
        )

        overview = calculate_goal_overview(
            target_amount=target_amount,
            current_amount=current_amount,
            deadline_date=deadline_date,
            reference_date=reference_date,
        )

        progress = float(overview["progress"])

        remaining_amount = float(overview["remaining_amount"])

        monthly_amount = float(overview["monthly_amount"])

        completed = bool(overview["completed"])

        days_remaining = int(deadline_summary["days_remaining"])

        expired = bool(deadline_summary["expired"])

        day_label = "dia" if days_remaining == 1 else "dias"

        if completed:
            status_label = "Meta concluída"

            status_class = "success"

            deadline_description = "Objetivo alcançado"

            projection_text = "Objetivo alcançado. " "Nenhum novo aporte é necessário."

            projection_class = "completed"

        elif expired:
            status_label = "Prazo encerrado"

            status_class = "danger"

            deadline_description = "Prazo encerrado"

            projection_text = (
                "Prazo encerrado · " "Restante: " f"{format_currency(remaining_amount)}"
            )

            projection_class = "expired"

        else:
            status_label = "Em andamento"

            status_class = "neutral"

            deadline_description = f"Faltam {days_remaining} " f"{day_label}"

            projection_text = (
                "Necessário para manter o prazo: "
                f"{format_currency(monthly_amount)} "
                "por mês"
            )

            projection_class = "active"

        metadata = (
            "Meta: "
            f"{format_currency(target_amount)}"
            " · Data limite: "
            f"{format_goal_deadline(deadline_date)}"
            " · "
            f"{deadline_description}"
        )

        progress_label = "Meta concluída" if completed else f"{progress:.1f}% concluído"

        with st.container(
            border=True,
            key=("financial-goal-card-" f"{goal_id}"),
        ):
            render_html(f"""
                <article class="finantec-saved-goal">
                    <header class="finantec-saved-goal-header">
                        <div class="finantec-saved-goal-heading">
                            <h3>
                                {escape(name)}
                            </h3>

                            <p>
                                {escape(metadata)}
                            </p>
                        </div>

                        <span
                            class="
                                finantec-goal-status
                                {status_class}
                            "
                        >
                            {escape(status_label)}
                        </span>
                    </header>

                    <div class="finantec-saved-goal-values">
                        <div
                            class="
                                finantec-saved-goal-value-block
                                current
                            "
                        >
                            <span>
                                Valor guardado
                            </span>

                            <strong>
                                {escape(format_currency(current_amount))}
                            </strong>
                        </div>

                        <div
                            class="
                                finantec-saved-goal-value-block
                                remaining
                            "
                        >
                            <span>
                                Falta guardar
                            </span>

                            <strong>
                                {escape(format_currency(remaining_amount))}
                            </strong>
                        </div>
                    </div>

                    <div class="finantec-saved-goal-progress">
                        <div
                            class="finantec-saved-goal-progress-header"
                        >
                            <span>
                                Progresso
                            </span>

                            <strong>
                                {escape(progress_label)}
                            </strong>
                        </div>

                        <div
                            class="finantec-saved-goal-progress-track"
                            role="progressbar"
                            aria-label="Progresso da meta"
                            aria-valuemin="0"
                            aria-valuemax="100"
                            aria-valuenow="{progress:.1f}"
                        >
                            <div
                                class="finantec-saved-goal-progress-fill"
                                style="width: {progress:.1f}%;"
                            >
                            </div>
                        </div>
                    </div>

                    <p
                        class="
                            finantec-saved-goal-projection
                            {projection_class}
                        "
                    >
                        {escape(projection_text)}
                    </p>
                </article>
                """)

            if not read_only:
                with st.container(
                    key=("financial-goal-actions-" f"{goal_id}"),
                ):
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
                    with st.container(
                        key=("financial-goal-delete-confirmation-" f"{goal_id}"),
                    ):
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

        st.caption("Acompanhe as metas fictícias ou use o simulador.")

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

        st.caption("Acompanhe o progresso e atualize " "suas metas quando precisar.")

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
    *,
    temporary: bool = False,
) -> None:
    """Exibe a simulação interativa da meta selecionada."""
    goal_id = str(goal["goal_id"])

    goal_name = str(goal["nome"])

    goal_value = float(goal["valor_meta"])

    current_value = float(goal["valor_atual"])

    reference_date = get_goal_reference_date()

    deadline_date = resolve_goal_deadline_date(
        goal,
        reference_date=reference_date,
    )

    deadline_summary = calculate_goal_deadline(
        deadline_date=deadline_date,
        reference_date=reference_date,
    )

    stored_deadline = int(deadline_summary["calculation_months"])

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
        (
            "Esta simulação é temporária e não cria uma meta."
            if temporary
            else (
                "A simulação não altera a meta salva. "
                "Use a ação Editar para atualizar valores "
                "ou a data limite."
            )
        )
    )


def _render_free_goal_simulation(
    summary: dict[str, Any],
) -> None:
    """Exibe uma simulação que não depende de meta persistida."""
    reference_date = get_goal_reference_date()

    with st.container(
        border=True,
        key="free-goal-simulation-card",
    ):
        st.markdown("#### Dados da simulação")

        st.caption(
            "Preencha os valores abaixo para testar um objetivo "
            "sem salvar nada no banco."
        )

        name = st.text_input(
            "Nome da simulação",
            value="",
            max_chars=120,
            placeholder="Ex.: Notebook, viagem ou reserva",
            key="free-goal-simulation-name",
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
                "Valor desejado",
                min_value=1.0,
                value=5000.0,
                step=100.0,
                format="%.2f",
                key="free-goal-simulation-target",
            )

        with current_column:
            current_amount = st.number_input(
                "Valor já guardado",
                min_value=0.0,
                value=0.0,
                step=50.0,
                format="%.2f",
                key="free-goal-simulation-current",
            )

        deadline_date = st.date_input(
            "Data limite",
            value=_add_months(
                reference_date,
                12,
            ),
            min_value=reference_date,
            max_value=_add_months(
                reference_date,
                600,
            ),
            format="DD/MM/YYYY",
            key="free-goal-simulation-deadline",
        )

    try:
        temporary_goal = build_free_simulation_goal(
            name=name,
            target_amount=target_amount,
            current_amount=current_amount,
            deadline_date=deadline_date,
            reference_date=reference_date,
        )

    except ValueError as error:
        st.error(str(error))
        return

    _render_goal_simulation(
        goal=temporary_goal,
        summary=summary,
        temporary=True,
    )


def _render_goal_simulator_view(
    goals: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """Exibe o simulador separado do gerenciamento de metas."""
    st.markdown("### Simulador")

    st.caption(
        "Use uma meta salva ou monte uma simulação livre " "sem alterar seus dados."
    )

    if not goals:
        st.info(
            "Nenhuma meta foi cadastrada. "
            "A simulação livre continua disponível abaixo."
        )

        st.session_state[GOAL_SIMULATION_SOURCE_KEY] = SIMULATION_SOURCE_FREE

        _render_free_goal_simulation(summary)

        return

    selected_source = st.session_state.get(
        GOAL_SIMULATION_SOURCE_KEY,
        SIMULATION_SOURCE_SAVED,
    )

    if selected_source not in {
        SIMULATION_SOURCE_SAVED,
        SIMULATION_SOURCE_FREE,
    }:
        selected_source = SIMULATION_SOURCE_SAVED

        st.session_state[GOAL_SIMULATION_SOURCE_KEY] = selected_source

    simulation_source = st.radio(
        "Usar",
        options=[
            SIMULATION_SOURCE_SAVED,
            SIMULATION_SOURCE_FREE,
        ],
        horizontal=True,
        key=GOAL_SIMULATION_SOURCE_KEY,
    )

    if simulation_source == SIMULATION_SOURCE_FREE:
        _render_free_goal_simulation(summary)

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
        "Acompanhe seus objetivos ou simule " "diferentes formas de alcançá-los."
    )

    _show_goal_feedback()

    is_demo = data_mode == "demo"

    if is_demo:
        st.info("Metas de demonstração. " "Os dados são fictícios e somente leitura.")

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
