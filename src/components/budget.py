"""Planejamento mensal de gastos por categoria."""

from __future__ import annotations

from datetime import datetime
from typing import Any
import unicodedata

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
    MonthlyBudgetNotFoundError,
    create_monthly_budget,
    delete_monthly_budget,
    list_monthly_budgets,
    update_monthly_budget,
)
from ui_components import MONTH_NAMES_PT_BR

BUDGET_FORM_OPEN_KEY = "monthly_budget_form_open"

BUDGET_EDIT_ID_KEY = "monthly_budget_edit_id"

BUDGET_DELETE_ID_KEY = "monthly_budget_delete_id"

BUDGET_FORM_VERSION_KEY = "monthly_budget_form_version"

BUDGET_FEEDBACK_KEY = "monthly_budget_feedback"

BUDGET_PERIOD_KEY = "monthly_budget_period"

CATEGORY_PLACEHOLDER = (
    "Selecione uma categoria"
)

DEFAULT_BUDGET_CATEGORIES = (
    "Alimentação",
    "Moradia",
    "Transporte",
    "Saúde",
    "Educação",
    "Lazer",
    "Contas",
    "Assinaturas",
    "Compras",
    "Outros",
)

def build_budget_period_options(
    transactions: pd.DataFrame,
    reference_period: str | None = None,
) -> list[str]:
    """Lista os meses disponíveis e inclui o mês atual."""
    current_period = reference_period or datetime.now().strftime("%Y-%m")

    available_periods = (
        list_available_months(transactions) if not transactions.empty else []
    )

    periods = {
        str(period).strip() for period in available_periods if str(period).strip()
    }

    periods.add(current_period)

    return sorted(
        periods,
        reverse=True,
    )

def _normalize_category_key(
    value: object,
) -> str:
    """Cria uma chave comparável para uma categoria."""
    text = " ".join(
        str(
            value
            if value is not None
            else ""
        )
        .strip()
        .split()
    )

    normalized_text = unicodedata.normalize(
        "NFKD",
        text,
    )

    return "".join(
        character
        for character in normalized_text
        if not unicodedata.combining(
            character
        )
    ).casefold()


def build_budget_category_options(
    transactions: pd.DataFrame,
) -> list[str]:
    """Combina categorias sugeridas e categorias usadas nas despesas."""
    categories_by_key = {
        _normalize_category_key(category): category
        for category in DEFAULT_BUDGET_CATEGORIES
    }

    required_columns = {
        "tipo",
        "categoria",
    }

    if (
        transactions.empty
        or not required_columns.issubset(
            transactions.columns
        )
    ):
        return list(
            categories_by_key.values()
        )

    transaction_types = (
        transactions["tipo"]
        .astype("string")
        .str.strip()
        .str.casefold()
    )

    expense_categories = transactions.loc[
        transaction_types == "despesa",
        "categoria",
    ]

    for value in expense_categories:
        if pd.isna(value):
            continue

        category = " ".join(
            str(value)
            .strip()
            .split()
        )

        if not category:
            continue

        category_key = _normalize_category_key(
            category
        )

        if (
            not category_key
            or category_key == "reserva"
        ):
            continue

        categories_by_key.setdefault(
            category_key,
            category,
        )

    return sorted(
        categories_by_key.values(),
        key=_normalize_category_key,
    )


def resolve_budget_category(
    *,
    selected_category: str,
    custom_category: str,
) -> str:
    """Define a categoria final usada pelo orçamento."""
    normalized_custom_category = (
        " ".join(
            str(
                custom_category
            )
            .strip()
            .split()
        )
    )

    if normalized_custom_category:
        return normalized_custom_category

    normalized_selected_category = (
        " ".join(
            str(
                selected_category
            )
            .strip()
            .split()
        )
    )

    if (
        normalized_selected_category
        == CATEGORY_PLACEHOLDER
    ):
        return ""

    return normalized_selected_category

def format_budget_period(
    period: str,
) -> str:
    """Formata AAAA-MM para o nome legível do mês."""
    try:
        year_text, month_text = period.split(
            "-",
            maxsplit=1,
        )

        month = int(month_text)

        month_name = MONTH_NAMES_PT_BR[month]

    except (
        ValueError,
        KeyError,
        IndexError,
    ):
        return period

    return f"{month_name}/{year_text}"


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
        "planned_amount": float(planned_amount),
    }


def get_budget_status_label(
    status: str,
    usage_percentage: float,
) -> str:
    """Traduz o estado interno para a interface."""
    if status == "over_limit":
        return "Limite ultrapassado"

    if status == "near_limit" and usage_percentage >= 100:
        return "Limite atingido"

    if status == "near_limit":
        return "Próximo do limite"

    return "Dentro do limite"


def build_budget_dashboard_summary(
    *,
    transactions: pd.DataFrame,
    budgets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Monta o resumo do orçamento exibido no painel."""
    if not budgets:
        return {
            "remaining_amount": 0.0,
            "over_limit_categories": [],
            "planned_categories": 0,
        }

    tracking = calculate_budget_tracking(
        transacoes=transactions,
        orcamentos=budgets,
    )

    summary = calculate_budget_summary(
        tracking
    )

    over_limit_categories = [
        str(
            item[
                "category"
            ]
        )
        for item in tracking
        if item.get(
            "status"
        ) == "over_limit"
    ]

    return {
        "remaining_amount": float(
            summary[
                "total_remaining"
            ]
        ),
        "over_limit_categories": (
            over_limit_categories
        ),
        "planned_categories": int(
            summary[
                "planned_categories"
            ]
        ),
    }


def _find_budget(
    budgets: list[dict[str, Any]],
    budget_id: str | None,
) -> dict[str, Any] | None:
    """Localiza um orçamento pelo identificador."""
    if not budget_id:
        return None

    return next(
        (budget for budget in budgets if budget.get("budget_id") == budget_id),
        None,
    )


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
    st.session_state[BUDGET_FORM_VERSION_KEY] = _get_form_version() + 1


def _open_budget_form(
    budget_id: str | None = None,
) -> None:
    """Abre o formulário para criação ou edição."""
    st.session_state[BUDGET_FORM_OPEN_KEY] = True

    st.session_state[BUDGET_EDIT_ID_KEY] = budget_id

    _advance_form_version()


def _close_budget_form() -> None:
    """Fecha e reinicia o formulário."""
    st.session_state[BUDGET_FORM_OPEN_KEY] = False

    st.session_state[BUDGET_EDIT_ID_KEY] = None

    _advance_form_version()


def _set_budget_feedback(
    message_type: str,
    message: str,
) -> None:
    """Guarda feedback para o próximo rerun."""
    st.session_state[BUDGET_FEEDBACK_KEY] = {
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

    if feedback.get("type") == "error":
        st.error(message)

        return

    st.success(message)


def _render_budget_form(
    *,
    budgets: list[dict[str, Any]],
    period_transactions: pd.DataFrame,
    user_id: str,
    selected_period: str,
) -> None:
    """Exibe o formulário de criação ou edição."""
    if not st.session_state.get(
        BUDGET_FORM_OPEN_KEY,
        False,
    ):
        return

    edit_budget_id = (
        st.session_state.get(
            BUDGET_EDIT_ID_KEY
        )
    )

    editing_budget = _find_budget(
        budgets,
        edit_budget_id,
    )

    is_editing = (
        editing_budget is not None
    )

    if (
        edit_budget_id
        and editing_budget is None
    ):
        _close_budget_form()

        st.warning(
            "O limite selecionado para edição "
            "não foi encontrado."
        )

        return

    default_category = (
        str(
            editing_budget.get(
                "category",
                "",
            )
        )
        if editing_budget
        else ""
    )

    default_amount = (
        float(
            editing_budget.get(
                "planned_amount",
                100.0,
            )
        )
        if editing_budget
        else 100.0
    )

    category_options = (
        build_budget_category_options(
            period_transactions
        )
    )

    category_keys = {
        _normalize_category_key(
            category
        )
        for category in category_options
    }

    if (
        default_category
        and _normalize_category_key(
            default_category
        )
        not in category_keys
    ):
        category_options.insert(
            0,
            default_category,
        )

    selectable_categories = [
        CATEGORY_PLACEHOLDER,
        *category_options,
    ]

    default_category_index = 0

    if default_category:
        default_category_key = (
            _normalize_category_key(
                default_category
            )
        )

        for (
            index,
            category_option,
        ) in enumerate(
            selectable_categories
        ):
            if (
                _normalize_category_key(
                    category_option
                )
                == default_category_key
            ):
                default_category_index = (
                    index
                )

                break

    title = (
        "Editar limite"
        if is_editing
        else "Novo limite"
    )

    form_version = (
        _get_form_version()
    )

    with st.container(
        border=True,
        key="monthly-budget-form-card",
    ):
        st.markdown(
            f"### {title}"
        )

        st.caption(
            "Defina quanto pretende gastar em uma categoria "
            f"durante {format_budget_period(selected_period)}."
        )

        with st.form(
            key=(
                "monthly-budget-form-"
                f"{selected_period}-"
                f"{form_version}"
            ),
            border=False,
        ):
            selected_category = st.selectbox(
                "Categoria",
                options=selectable_categories,
                index=default_category_index,
                help=(
                    "Escolha uma categoria sugerida ou "
                    "uma categoria já usada nas transações."
                ),
            )

            custom_category = st.text_input(
                "Ou informe uma categoria personalizada",
                max_chars=100,
                placeholder="Ex.: Pet, Viagem ou Academia",
            )

            st.caption(
                "Quando uma nova categoria for informada, "
                "ela substitui a opção selecionada acima."
            )

            planned_amount = (
                st.number_input(
                    "Valor planejado",
                    min_value=1.0,
                    value=default_amount,
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
                        (
                            "Salvar alterações"
                            if is_editing
                            else "Criar limite"
                        ),
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

    category = resolve_budget_category(
        selected_category=(
            selected_category
        ),
        custom_category=(
            custom_category
        ),
    )

    payload = build_budget_payload(
        period=selected_period,
        category=category,
        planned_amount=planned_amount,
    )

    try:
        if is_editing:
            update_monthly_budget(
                database_path=ARQUIVO_BANCO,
                user_id=user_id,
                budget_id=str(
                    editing_budget[
                        "budget_id"
                    ]
                ),
                budget=payload,
            )

            feedback_message = (
                "Limite atualizado com sucesso."
            )

        else:
            create_monthly_budget(
                database_path=ARQUIVO_BANCO,
                user_id=user_id,
                budget=payload,
            )

            feedback_message = (
                "Limite criado com sucesso."
            )

    except (
        DuplicateMonthlyBudgetError,
        MonthlyBudgetNotFoundError,
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
        feedback_message,
    )

    st.cache_data.clear()
    st.rerun()


def _render_budget_summary(
    summary: dict[str, float | int],
) -> None:
    """Exibe os totais das categorias planejadas."""
    total_remaining = float(
        summary["total_remaining"]
    )

    categories_over_limit = int(
        summary["categories_over_limit"]
    )

    remaining_tone = (
        "positive"
        if total_remaining >= 0
        else "danger"
    )

    exceeded_tone = (
        "danger"
        if categories_over_limit > 0
        else "neutral"
    )

    with st.container(
        key="monthly-budget-summary-grid",
    ):
        (
            planned_column,
            spent_column,
        ) = st.columns(
            2,
            gap="small",
        )

        with planned_column:
            with st.container(
                key="monthly-budget-summary-planned",
            ):
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
            with st.container(
                key="monthly-budget-summary-spent",
            ):
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

        (
            remaining_column,
            exceeded_column,
        ) = st.columns(
            2,
            gap="small",
        )

        with remaining_column:
            with st.container(
                key=(
                    "monthly-budget-summary-remaining-"
                    f"{remaining_tone}"
                ),
            ):
                st.metric(
                    "Saldo planejado",
                    format_currency(
                        total_remaining
                    ),
                )

        with exceeded_column:
            with st.container(
                key=(
                    "monthly-budget-summary-exceeded-"
                    f"{exceeded_tone}"
                ),
            ):
                st.metric(
                    "Categorias acima do limite",
                    categories_over_limit,
                )

    st.caption(
        "Os totais consideram somente as categorias "
        "que possuem um limite cadastrado."
    )


def _delete_budget(
    *,
    budget_id: str,
    user_id: str,
) -> None:
    """Exclui um limite mensal após confirmação."""
    try:
        deleted = delete_monthly_budget(
            database_path=ARQUIVO_BANCO,
            user_id=user_id,
            budget_id=budget_id,
        )

    except RuntimeError as error:
        st.error(str(error))

        return

    if not deleted:
        st.error("O limite informado não foi encontrado.")

        return

    st.session_state[BUDGET_DELETE_ID_KEY] = None

    _set_budget_feedback(
        "success",
        "Limite excluído com sucesso.",
    )

    st.cache_data.clear()
    st.rerun()


def _render_budget_cards(
    *,
    tracking: list[dict[str, Any]],
    user_id: str,
) -> None:
    """Exibe o acompanhamento e as ações por categoria."""
    if not tracking:
        st.info(
            "Nenhum limite foi cadastrado para este mês."
        )
        return

    pending_delete_id = st.session_state.get(
        BUDGET_DELETE_ID_KEY
    )

    for item in tracking:
        budget_id = str(
            item["budget_id"]
        )

        category = str(
            item["category"]
        )

        planned_amount = float(
            item["planned_amount"]
        )

        spent_amount = float(
            item["spent_amount"]
        )

        remaining_amount = float(
            item["remaining_amount"]
        )

        usage_percentage = float(
            item["usage_percentage"]
        )

        status = str(
            item["status"]
        )

        status_label = get_budget_status_label(
            status,
            usage_percentage,
        )

        if status == "over_limit":
            status_tone = "danger"

        elif status == "near_limit":
            status_tone = "warning"

        else:
            status_tone = "success"

        with st.container(
            border=True,
            key=(
                "monthly-budget-card-"
                f"{budget_id}"
            ),
        ):
            (
                title_column,
                status_column,
            ) = st.columns(
                [
                    4,
                    1,
                ],
                gap="small",
            )

            with title_column:
                st.markdown(
                    f"### {category}"
                )

                with st.container(
                    key=(
                        "monthly-budget-usage-"
                        f"{budget_id}"
                    ),
                ):
                    spent_text = format_currency(
                        spent_amount
                    )

                    planned_text = format_currency(
                        planned_amount
                    )

                    usage_html = (
                        '<p class="finantec-budget-usage-text">'
                        f'<strong>{spent_text}</strong> '
                        f'de <strong>{planned_text}</strong> '
                        'utilizados '
                        '<span aria-hidden="true">·</span> '
                        '<strong class="finantec-budget-usage-'
                        f'{status_tone}">'
                        f'{usage_percentage:.1f}%'
                        '</strong>'
                        '</p>'
                    )

                    st.markdown(
                        usage_html,
                        unsafe_allow_html=True,
                    )

            with status_column:
                with st.container(
                    key=(
                        "monthly-budget-status-"
                        f"{status_tone}-"
                        f"{budget_id}"
                    ),
                ):
                    st.markdown(
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
                with st.container(
                    key=(
                        "monthly-budget-metric-"
                        f"planned-{budget_id}"
                    ),
                ):
                    st.metric(
                        "Planejado",
                        format_currency(
                            planned_amount
                        ),
                    )

            with spent_column:
                with st.container(
                    key=(
                        "monthly-budget-metric-"
                        f"spent-{budget_id}"
                    ),
                ):
                    st.metric(
                        "Gasto",
                        format_currency(
                            spent_amount
                        ),
                    )

            with balance_column:
                balance_key = (
                    "available"
                    if remaining_amount >= 0
                    else "exceeded"
                )

                with st.container(
                    key=(
                        "monthly-budget-metric-"
                        f"{balance_key}-"
                        f"{budget_id}"
                    ),
                ):
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
                    usage_percentage,
                    0.0,
                ),
                100.0,
            )

            progress_html = (
                '<div class="finantec-budget-progress-track">'
                '<div class="finantec-budget-progress-fill '
                f'{status_tone}" '
                f'style="width: {visual_progress:.2f}%">'
                '</div>'
                '</div>'
            )

            st.markdown(
                progress_html,
                unsafe_allow_html=True,
            )

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
                    key=(
                        "edit-monthly-budget-"
                        f"{budget_id}"
                    ),
                    use_container_width=True,
                ):
                    _open_budget_form(
                        budget_id
                    )

                    st.rerun()

            with delete_column:
                if st.button(
                    "Excluir",
                    key=(
                        "delete-monthly-budget-"
                        f"{budget_id}"
                    ),
                    use_container_width=True,
                ):
                    st.session_state[
                        BUDGET_DELETE_ID_KEY
                    ] = budget_id

                    st.rerun()

            if pending_delete_id == budget_id:
                st.markdown(
                    f"**Excluir o limite de “{category}”?** "
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
                        key=(
                            "confirm-delete-budget-"
                            f"{budget_id}"
                        ),
                        type="primary",
                        use_container_width=True,
                    ):
                        _delete_budget(
                            budget_id=budget_id,
                            user_id=user_id,
                        )

                with cancel_column:
                    if st.button(
                        "Manter limite",
                        key=(
                            "cancel-delete-budget-"
                            f"{budget_id}"
                        ),
                        use_container_width=True,
                    ):
                        st.session_state[
                            BUDGET_DELETE_ID_KEY
                        ] = None

                        st.rerun()


def render_monthly_budget(
    *,
    transactions: pd.DataFrame,
    user_id: str,
    data_mode: str,
) -> None:
    """Exibe o planejamento mensal por categoria."""
    st.subheader("Orçamento")

    st.caption(
        "Planeje limites mensais e acompanhe " "quanto já gastou em cada categoria."
    )

    if data_mode == "demo":
        st.info("O orçamento está disponível somente " "para seus dados pessoais.")

        return

    _show_budget_feedback()

    period_options = build_budget_period_options(transactions)

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

    period_transactions = filter_transactions_by_month(
        transactions,
        selected_period,
    )

    tracking = calculate_budget_tracking(
        transacoes=period_transactions,
        orcamentos=budgets,
    )

    title_column, action_column = st.columns(
        [
            3,
            1,
        ],
        gap="small",
    )

    with title_column:
        st.markdown("### Planejamento do mês")

        st.caption(
            "Consulte primeiro os limites existentes " "ou adicione uma nova categoria."
        )

    with action_column:
        if st.button(
            "Novo limite",
            key="open-new-monthly-budget-v6",
            type="primary",
            use_container_width=True,
        ):
            _open_budget_form()

            st.rerun()

    _render_budget_form(
            budgets=budgets,
            period_transactions=(
                period_transactions
            ),
            user_id=user_id,
            selected_period=selected_period,
         )

    if tracking:
        summary = calculate_budget_summary(tracking)

        _render_budget_summary(summary)

    _render_budget_cards(
        tracking=tracking,
        user_id=user_id,
    )


def render_budget_dashboard_summary(
    *,
    transactions: pd.DataFrame,
    user_id: str,
    data_mode: str,
) -> None:
    """Exibe um resumo mensal do orçamento na Visão geral."""
    if data_mode == "demo" or transactions.empty:
        return

    available_periods = list_available_months(transactions)

    if len(available_periods) != 1:
        return

    selected_period = str(available_periods[0])

    budgets = list_monthly_budgets(
        database_path=ARQUIVO_BANCO,
        user_id=user_id,
        period=selected_period,
    )

    if not budgets:
        return

    dashboard_summary = build_budget_dashboard_summary(
        transactions=transactions,
        budgets=budgets,
    )

    remaining_amount = float(dashboard_summary["remaining_amount"])

    over_limit_categories = list(dashboard_summary["over_limit_categories"])

    with st.container(
        border=True,
        key=("dashboard-budget-summary-" f"{selected_period}"),
    ):
        st.markdown("### Orçamento do mês")

        st.caption(
            "Resumo dos limites cadastrados "
            f"para {format_budget_period(selected_period)}."
        )

        (
            balance_column,
            exceeded_column,
        ) = st.columns(
            2,
            gap="small",
        )

        with balance_column:
            st.metric(
                "Saldo planejado",
                format_currency(remaining_amount),
            )

        with exceeded_column:
            st.metric(
                "Categorias acima do limite",
                len(over_limit_categories),
            )

        if over_limit_categories:
            st.warning("Acima do limite: " + ", ".join(over_limit_categories) + ".")

        else:
            st.success("Nenhuma categoria ultrapassou " "o limite planejado.")