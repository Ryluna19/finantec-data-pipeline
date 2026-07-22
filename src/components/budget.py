"""Planejamento mensal de gastos por categoria."""

from __future__ import annotations

from datetime import datetime
from html import escape
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
from components.header import (
    build_page_header_html,
    build_section_header_html,
)
from src.budget_repository import (
    DuplicateMonthlyBudgetError,
    MonthlyBudgetNotFoundError,
    create_monthly_budget,
    delete_monthly_budget,
    list_active_monthly_budgets,
    list_monthly_budget_periods,
    split_monthly_budget_from_period,
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

BUDGET_DURATION_CONTINUOUS = "Contínuo"

BUDGET_DURATION_TEMPORARY = "Temporário"

BUDGET_TEMPORARY_FUTURE_MONTHS = 12

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

def _shift_budget_period(
    period: str,
    month_offset: int,
) -> str:
    """Desloca um período mensal sem depender de transações."""
    try:
        year_text, month_text = period.split(
            "-",
            maxsplit=1,
        )

        year = int(year_text)
        month = int(month_text)

    except (
        AttributeError,
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "O período de referência deve estar no formato AAAA-MM."
        ) from error

    canonical_period = (
        f"{year:04d}-"
        f"{month:02d}"
    )

    if (
        month not in range(1, 13)
        or canonical_period != period
    ):
        raise ValueError(
            "O período de referência deve estar no formato AAAA-MM."
        )

    absolute_month = (
        year
        * 12
        + month
        - 1
        + int(month_offset)
    )

    shifted_year, shifted_month_index = divmod(
        absolute_month,
        12,
    )

    return (
        f"{shifted_year:04d}-"
        f"{shifted_month_index + 1:02d}"
    )


def _is_valid_budget_period(
    period: object,
) -> bool:
    """Indica se um valor representa um período mensal válido."""
    normalized_period = str(
        period
        if period is not None
        else ""
    ).strip()

    try:
        return (
            _shift_budget_period(
                normalized_period,
                0,
            )
            == normalized_period
        )

    except ValueError:
        return False


def build_budget_period_options(
    transactions: pd.DataFrame,
    *,
    budget_periods: list[str] | tuple[str, ...] | None = None,
    reference_period: str | None = None,
    future_months: int = 12,
) -> list[str]:
    """Lista o mês atual, meses futuros e períodos com histórico."""
    current_period = (
        reference_period
        or datetime.now().strftime(
            "%Y-%m"
        )
    )

    if future_months < 0:
        raise ValueError(
            "A quantidade de meses futuros não pode ser negativa."
        )

    generated_periods = [
        _shift_budget_period(
            current_period,
            month_offset,
        )
        for month_offset in range(
            future_months + 1
        )
    ]

    transaction_periods = (
        list_available_months(
            transactions
        )
        if not transactions.empty
        else []
    )

    stored_periods = [
        *(budget_periods or []),
        *transaction_periods,
    ]

    periods = {
        *generated_periods,
        *(
            str(period).strip()
            for period in stored_periods
            if _is_valid_budget_period(
                period
            )
        ),
    }

    current_and_future = sorted(
        (
            period
            for period in periods
            if period >= current_period
        )
    )

    historical = sorted(
        (
            period
            for period in periods
            if period < current_period
        ),
        reverse=True,
    )

    return [
        *current_and_future,
        *historical,
    ]


def build_budget_end_period_options(
    start_period: str,
    *,
    current_end_period: str | None = None,
    future_months: int = BUDGET_TEMPORARY_FUTURE_MONTHS,
) -> list[str]:
    """Lista possíveis meses finais para um limite temporário."""
    if future_months < 0:
        raise ValueError(
            "A quantidade de meses futuros não pode ser negativa."
        )

    periods = {
        _shift_budget_period(
            start_period,
            month_offset,
        )
        for month_offset in range(
            future_months + 1
        )
    }

    if (
        current_end_period
        and _is_valid_budget_period(
            current_end_period
        )
        and current_end_period >= start_period
    ):
        periods.add(
            current_end_period
        )

    return sorted(
        periods
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
) -> str:
    """Normaliza a categoria selecionada no orçamento."""
    category = " ".join(
        str(
            selected_category
        )
        .strip()
        .split()
    )

    if (
        category
        == CATEGORY_PLACEHOLDER
    ):
        return ""

    return category


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
    end_period: str | None = None,
) -> dict[str, Any]:
    """Monta o orçamento enviado ao repositório."""
    return {
        "period": period,
        "end_period": end_period,
        "category": category,
        "planned_amount": float(
            planned_amount
        ),
    }


def format_budget_validity(
    *,
    start_period: str,
    end_period: str | None,
) -> str:
    """Descreve a vigência mensal de um limite."""
    formatted_start = format_budget_period(
        start_period
    )

    if end_period is None:
        return (
            "Contínuo desde "
            f"{formatted_start}"
        )

    formatted_end = format_budget_period(
        end_period
    )

    if end_period == start_period:
        return (
            "Temporário · somente "
            f"{formatted_start}"
        )

    return (
        "Temporário · "
        f"{formatted_start} até "
        f"{formatted_end}"
    )


def is_budget_inherited_period(
    *,
    start_period: str,
    selected_period: str,
) -> bool:
    """Indica se o limite começou antes do mês selecionado."""
    normalized_start = _shift_budget_period(
        start_period,
        0,
    )

    normalized_selected = _shift_budget_period(
        selected_period,
        0,
    )

    return (
        normalized_start
        < normalized_selected
    )


def build_budget_removal_dialog_copy(
    *,
    category: str,
    is_inherited_period: bool,
    selected_period: str,
) -> dict[str, str]:
    """Monta os textos da confirmação de exclusão ou encerramento."""
    normalized_category = " ".join(
        str(
            category
        )
        .strip()
        .split()
    )

    if is_inherited_period:
        return {
            "title": "Encerrar limite",
            "question": (
                "Deseja encerrar o limite de "
                f"“{normalized_category}” a partir de "
                f"{format_budget_period(selected_period)}?"
            ),
            "description": (
                "Os meses anteriores serão preservados."
            ),
            "confirm_label": "Sim, encerrar",
        }

    return {
        "title": "Excluir limite",
        "question": (
            "Deseja excluir o limite de "
            f"“{normalized_category}”?"
        ),
        "description": (
            "Essa ação não pode ser desfeita."
        ),
        "confirm_label": "Sim, excluir",
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


def build_budget_card_html(
    *,
    category: str,
    validity_label: str,
    status: str,
    planned_amount: float,
    spent_amount: float,
    remaining_amount: float,
    usage_percentage: float,
) -> str:
    """Monta o conteúdo compacto de um card de orçamento."""
    status_tone = {
        "over_limit": "danger",
        "near_limit": "warning",
    }.get(
        status,
        "success",
    )

    status_label = get_budget_status_label(
        status,
        usage_percentage,
    )

    balance_label = (
        "Disponível"
        if remaining_amount >= 0
        else "Ultrapassado"
    )

    balance_tone = (
        "positive"
        if remaining_amount >= 0
        else "danger"
    )

    balance_amount = (
        remaining_amount
        if remaining_amount >= 0
        else abs(remaining_amount)
    )

    visual_progress = min(
        max(
            usage_percentage,
            0.0,
        ),
        100.0,
    )

    safe_category = escape(
        category
    )

    safe_validity = escape(
        validity_label
    )

    safe_status_label = escape(
        status_label
    )

    spent_text = escape(
        format_currency(
            spent_amount
        )
    )

    planned_text = escape(
        format_currency(
            planned_amount
        )
    )

    balance_text = escape(
        format_currency(
            balance_amount
        )
    )

    return (
        '<div class="finantec-budget-card-content">'
        '<div class="finantec-budget-card-header">'
        '<div class="finantec-budget-card-heading">'
        f'<h3>{safe_category}</h3>'
        f'<p>{safe_validity}</p>'
        '</div>'
        '<span class="finantec-budget-status '
        f'{status_tone}">'
        f'{safe_status_label}'
        '</span>'
        '</div>'
        '<div class="finantec-budget-card-body">'
        '<div class="finantec-budget-card-tracking">'
        '<div class="finantec-budget-usage-row">'
        '<p>'
        '<strong class="finantec-budget-spent">'
        f'{spent_text}'
        '</strong> gastos de '
        f'<strong>{planned_text}</strong>'
        '</p>'
        '<strong class="finantec-budget-percentage '
        f'{status_tone}">'
        f'{usage_percentage:.1f}%'
        '</strong>'
        '</div>'
        '<div class="finantec-budget-progress-track" '
        'role="progressbar" '
        'aria-label="Percentual do limite utilizado" '
        'aria-valuemin="0" '
        'aria-valuemax="100" '
        f'aria-valuenow="{visual_progress:.1f}">'
        '<div class="finantec-budget-progress-fill '
        f'{status_tone}" '
        f'style="width: {visual_progress:.2f}%">'
        '</div>'
        '</div>'
        '</div>'
        '<div class="finantec-budget-balance '
        f'{balance_tone}">'
        f'<span>{balance_label}</span>'
        f'<strong>{balance_text}</strong>'
        '</div>'
        '</div>'
        '</div>'
    )


def build_budget_summary_html(
    summary: dict[str, float | int],
) -> str:
    """Monta o painel compacto com os totais do orçamento."""
    total_planned = float(
        summary["total_planned"]
    )

    total_spent = float(
        summary["total_spent"]
    )

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

    planned_text = escape(
        format_currency(
            total_planned
        )
    )

    spent_text = escape(
        format_currency(
            total_spent
        )
    )

    remaining_text = escape(
        format_currency(
            total_remaining
        )
    )

    return (
        '<div class="finantec-budget-summary-panel" '
        'role="group" '
        'aria-label="Resumo do orçamento do mês">'
        '<div class="finantec-budget-summary-item planned">'
        '<span>Planejado</span>'
        f'<strong>{planned_text}</strong>'
        '</div>'
        '<div class="finantec-budget-summary-item spent">'
        '<span>Gasto</span>'
        f'<strong>{spent_text}</strong>'
        '</div>'
        '<div class="finantec-budget-summary-item '
        f'{remaining_tone}">'
        '<span>Disponível</span>'
        f'<strong>{remaining_text}</strong>'
        '</div>'
        '<div class="finantec-budget-summary-item '
        f'{exceeded_tone}">'
        '<span>Acima do limite</span>'
        f'<strong>{categories_over_limit}</strong>'
        '</div>'
        '</div>'
    )


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
    transactions: pd.DataFrame,
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

    editing_start_period = (
        str(
            editing_budget[
                "period"
            ]
        )
        if editing_budget
        else selected_period
    )

    is_split_edit = (
        is_editing
        and is_budget_inherited_period(
            start_period=editing_start_period,
            selected_period=selected_period,
        )
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

    default_end_period = (
        editing_budget.get(
            "end_period"
        )
        if editing_budget
        else None
    )

    category_options = (
        build_budget_category_options(
            transactions
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

    if is_split_edit:
        title = (
            "Alterar limite a partir deste mês"
        )

    elif is_editing:
        title = "Editar limite"

    else:
        title = "Novo limite"

    form_version = (
        _get_form_version()
    )

    widget_key_suffix = (
        f"{selected_period}-"
        f"{form_version}"
    )

    with st.container(
        border=True,
        key="monthly-budget-form-card",
    ):
        form_description = (
            (
                "A nova configuração valerá a partir de "
                f"{format_budget_period(selected_period)}. "
                "Os meses anteriores permanecerão inalterados."
            )
            if is_split_edit
            else (
                "Defina quanto pretende gastar em uma categoria "
                f"durante {format_budget_period(selected_period)}."
            )
        )

        st.markdown(
            build_section_header_html(
                title=title,
                description=form_description,
                compact=True,
            ),
            unsafe_allow_html=True,
        )

        selected_category = st.selectbox(
            "Categoria",
            options=selectable_categories,
            index=default_category_index,
            key=(
                "monthly-budget-category-"
                f"{widget_key_suffix}"
            ),
            help=(
                "Escolha uma categoria sugerida ou "
                "uma categoria já usada nas transações."
            ),
        )

        st.caption(
            "Categorias novas ficam disponíveis aqui "
            "depois de serem usadas em uma transação "
            "de despesa."
        )

        planned_amount = st.number_input(
            "Valor planejado",
            min_value=1.0,
            value=default_amount,
            step=50.0,
            format="%.2f",
            key=(
                "monthly-budget-amount-"
                f"{widget_key_suffix}"
            ),
        )

        default_duration_index = (
            0
            if default_end_period is None
            else 1
        )

        duration = st.radio(
            "Duração do limite",
            options=(
                BUDGET_DURATION_CONTINUOUS,
                BUDGET_DURATION_TEMPORARY,
            ),
            index=default_duration_index,
            horizontal=True,
            key=(
                "monthly-budget-duration-"
                f"{widget_key_suffix}"
            ),
        )

        if (
            duration
            == BUDGET_DURATION_TEMPORARY
        ):
            end_period_options = (
                build_budget_end_period_options(
                    selected_period,
                    current_end_period=(
                        str(
                            default_end_period
                        )
                        if default_end_period
                        else None
                    ),
                )
            )

            default_end_period_value = (
                str(
                    default_end_period
                )
                if (
                    default_end_period
                    and str(
                        default_end_period
                    )
                    in end_period_options
                )
                else selected_period
            )

            end_period = str(
                st.selectbox(
                    "Válido até",
                    options=end_period_options,
                    index=(
                        end_period_options.index(
                            default_end_period_value
                        )
                    ),
                    format_func=(
                        format_budget_period
                    ),
                    key=(
                        "monthly-budget-end-period-"
                        f"{widget_key_suffix}"
                    ),
                    help=(
                        "O limite será aplicado em todos "
                        "os meses até o período escolhido."
                    ),
                )
            )

            st.caption(
                "Escolha o mesmo mês inicial para criar "
                "um limite válido somente neste mês."
            )

        else:
            end_period = None

            st.caption(
                "O limite continuará nos próximos meses "
                "até ser encerrado manualmente."
            )

        (
            save_column,
            cancel_column,
        ) = st.columns(
            2,
            gap="small",
        )

        with save_column:
            submitted = st.button(
                (
                    "Aplicar a partir deste mês"
                    if is_split_edit
                    else (
                        "Salvar alterações"
                        if is_editing
                        else "Criar limite"
                    )
                ),
                key=(
                    "save-monthly-budget-"
                    f"{widget_key_suffix}"
                ),
                type="primary",
                use_container_width=True,
            )

        with cancel_column:
            cancelled = st.button(
                "Cancelar",
                key=(
                    "cancel-monthly-budget-"
                    f"{widget_key_suffix}"
                ),
                use_container_width=True,
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
    )

    payload = build_budget_payload(
        period=selected_period,
        category=category,
        planned_amount=planned_amount,
        end_period=end_period,
    )

    try:
        if is_split_edit:
            split_monthly_budget_from_period(
                database_path=ARQUIVO_BANCO,
                user_id=user_id,
                budget_id=str(
                    editing_budget[
                        "budget_id"
                    ]
                ),
                split_period=selected_period,
                budget=payload,
            )

            feedback_message = (
                "Limite alterado a partir de "
                f"{format_budget_period(selected_period)}."
            )

        elif is_editing:
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
    summary_html = build_budget_summary_html(
        summary
    )

    st.markdown(
        summary_html,
        unsafe_allow_html=True,
    )

    st.caption(
        "Os totais consideram somente as categorias "
        "que possuem um limite cadastrado."
    )


def _remove_budget_from_period(
    *,
    budget: dict[str, Any],
    user_id: str,
    selected_period: str,
) -> None:
    """Exclui ou encerra um limite a partir do mês selecionado."""
    budget_id = str(
        budget["budget_id"]
    )

    start_period = str(
        budget["period"]
    )

    try:
        if selected_period <= start_period:
            deleted = delete_monthly_budget(
                database_path=ARQUIVO_BANCO,
                user_id=user_id,
                budget_id=budget_id,
            )

            if not deleted:
                st.error(
                    "O limite informado não foi encontrado."
                )

                return

            feedback_message = (
                "Limite excluído com sucesso."
            )

        else:
            previous_period = (
                _shift_budget_period(
                    selected_period,
                    -1,
                )
            )

            update_monthly_budget(
                database_path=ARQUIVO_BANCO,
                user_id=user_id,
                budget_id=budget_id,
                budget=build_budget_payload(
                    period=start_period,
                    end_period=previous_period,
                    category=str(
                        budget["category"]
                    ),
                    planned_amount=float(
                        budget[
                            "planned_amount"
                        ]
                    ),
                ),
            )

            feedback_message = (
                "Limite encerrado a partir de "
                f"{format_budget_period(selected_period)}."
            )

    except (
        MonthlyBudgetNotFoundError,
        ValueError,
        RuntimeError,
    ) as error:
        st.error(
            str(error)
        )

        return

    st.session_state[
        BUDGET_DELETE_ID_KEY
    ] = None

    _set_budget_feedback(
        "success",
        feedback_message,
    )

    st.cache_data.clear()
    st.rerun()


def _close_budget_removal_dialog() -> None:
    """Limpa a confirmação de remoção aberta."""
    st.session_state[
        BUDGET_DELETE_ID_KEY
    ] = None


def _render_budget_removal_dialog_content(
    *,
    budget: dict[str, Any],
    user_id: str,
    selected_period: str,
    is_inherited_period: bool,
) -> None:
    """Exibe o conteúdo compartilhado da confirmação."""
    dialog_copy = (
        build_budget_removal_dialog_copy(
            category=str(
                budget[
                    "category"
                ]
            ),
            is_inherited_period=(
                is_inherited_period
            ),
            selected_period=(
                selected_period
            ),
        )
    )

    st.markdown(
        f"**{dialog_copy['question']}**"
    )

    st.caption(
        dialog_copy[
            "description"
        ]
    )

    with st.container(
        key=(
            "monthly-budget-removal-"
            "dialog-actions"
        ),
    ):
        (
            cancel_column,
            confirm_column,
        ) = st.columns(
            2,
            gap="small",
        )

        with cancel_column:
            if st.button(
                "Manter limite",
                key=(
                    "cancel-monthly-budget-"
                    "dialog"
                ),
                use_container_width=True,
            ):
                _close_budget_removal_dialog()
                st.rerun()

        with confirm_column:
            if st.button(
                dialog_copy[
                    "confirm_label"
                ],
                key=(
                    "confirm-monthly-budget-"
                    "dialog"
                ),
                use_container_width=True,
            ):
                _remove_budget_from_period(
                    budget=budget,
                    user_id=user_id,
                    selected_period=(
                        selected_period
                    ),
                )


@st.dialog(
    "Excluir limite",
    width="medium",
    on_dismiss=(
        _close_budget_removal_dialog
    ),
)
def _render_delete_budget_dialog(
    *,
    budget: dict[str, Any],
    user_id: str,
    selected_period: str,
) -> None:
    """Confirma a exclusão integral de um limite."""
    _render_budget_removal_dialog_content(
        budget=budget,
        user_id=user_id,
        selected_period=selected_period,
        is_inherited_period=False,
    )


@st.dialog(
    "Encerrar limite",
    width="medium",
    on_dismiss=(
        _close_budget_removal_dialog
    ),
)
def _render_end_budget_dialog(
    *,
    budget: dict[str, Any],
    user_id: str,
    selected_period: str,
) -> None:
    """Confirma o encerramento de uma vigência recorrente."""
    _render_budget_removal_dialog_content(
        budget=budget,
        user_id=user_id,
        selected_period=selected_period,
        is_inherited_period=True,
    )


def _render_pending_budget_removal_dialog(
    *,
    budgets: list[dict[str, Any]],
    user_id: str,
    selected_period: str,
) -> None:
    """Abre o diálogo referente ao limite selecionado."""
    pending_budget_id = (
        st.session_state.get(
            BUDGET_DELETE_ID_KEY
        )
    )

    if not pending_budget_id:
        return

    pending_budget = _find_budget(
        budgets,
        str(
            pending_budget_id
        ),
    )

    if pending_budget is None:
        _close_budget_removal_dialog()
        return

    is_inherited_period = (
        is_budget_inherited_period(
            start_period=str(
                pending_budget[
                    "period"
                ]
            ),
            selected_period=(
                selected_period
            ),
        )
    )

    dialog_arguments = {
        "budget": pending_budget,
        "user_id": user_id,
        "selected_period": (
            selected_period
        ),
    }

    if is_inherited_period:
        _render_end_budget_dialog(
            **dialog_arguments
        )
        return

    _render_delete_budget_dialog(
        **dialog_arguments
    )


def _render_budget_cards(
    *,
    tracking: list[dict[str, Any]],
    budgets: list[dict[str, Any]],
    user_id: str,
    selected_period: str,
) -> None:
    """Exibe o acompanhamento e as ações por categoria."""
    if not tracking:
        st.info(
            "Nenhum limite foi cadastrado para este mês."
        )
        return

    for item in tracking:
        budget_id = str(
            item["budget_id"]
        )

        budget = _find_budget(
            budgets,
            budget_id,
        )

        if budget is None:
            continue

        category = str(
            item["category"]
        )

        start_period = str(
            budget["period"]
        )

        raw_end_period = budget.get(
            "end_period"
        )

        end_period = (
            str(
                raw_end_period
            )
            if raw_end_period is not None
            else None
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

        validity_label = format_budget_validity(
            start_period=start_period,
            end_period=end_period,
        )

        is_inherited_period = (
            is_budget_inherited_period(
                start_period=start_period,
                selected_period=selected_period,
            )
        )

        with st.container(
            border=True,
            key=(
                "monthly-budget-card-"
                f"{budget_id}"
            ),
        ):
            card_html = build_budget_card_html(
                category=category,
                validity_label=validity_label,
                status=status,
                planned_amount=planned_amount,
                spent_amount=spent_amount,
                remaining_amount=remaining_amount,
                usage_percentage=usage_percentage,
            )

            st.markdown(
                card_html,
                unsafe_allow_html=True,
            )

            edit_label = (
                "Alterar a partir deste mês"
                if is_inherited_period
                else "Editar"
            )

            remove_label = (
                "Encerrar"
                if is_inherited_period
                else "Excluir"
            )

            with st.container(
                key=(
                    "monthly-budget-actions-"
                    f"{budget_id}"
                ),
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
                        edit_label,
                        key=(
                            "edit-monthly-budget-"
                            f"{budget_id}"
                        ),
                        use_container_width=True,
                        help=(
                            "Cria uma nova vigência sem modificar "
                            "os meses anteriores."
                            if is_inherited_period
                            else None
                        ),
                    ):
                        _open_budget_form(
                            budget_id
                        )

                        st.rerun()

                with delete_column:
                    with st.container(
                        key=(
                            "monthly-budget-danger-action-"
                            f"{budget_id}"
                        ),
                    ):
                        if st.button(
                            remove_label,
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

    _render_pending_budget_removal_dialog(
        budgets=budgets,
        user_id=user_id,
        selected_period=selected_period,
    )


def render_monthly_budget(
    *,
    transactions: pd.DataFrame,
    user_id: str,
    data_mode: str,
) -> None:
    """Exibe o planejamento mensal por categoria."""
    st.markdown(
        build_page_header_html(
            title="Orçamento",
            description=(
                "Planeje limites mensais e acompanhe quanto "
                "já gastou em cada categoria."
            ),
        ),
        unsafe_allow_html=True,
    )

    if data_mode == "demo":
        st.info("O orçamento está disponível somente " "para seus dados pessoais.")

        return

    _show_budget_feedback()

    budget_periods = (
        list_monthly_budget_periods(
            database_path=ARQUIVO_BANCO,
            user_id=user_id,
        )
    )

    period_options = (
        build_budget_period_options(
            transactions,
            budget_periods=budget_periods,
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

    budgets = list_active_monthly_budgets(
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

    with st.container(
        key="monthly-budget-section-header",
    ):
        title_column, action_column = st.columns(
            [
                3,
                1,
            ],
            gap="small",
        )

        with title_column:
            period_label = (
                format_budget_period(
                    selected_period
                )
            )

            st.markdown(
                build_section_header_html(
                    title="Planejamento do mês",
                    description=(
                        "Consulte os limites de "
                        f"{period_label} ou adicione "
                        "uma nova categoria."
                    ),
                ),
                unsafe_allow_html=True,
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
        transactions=transactions,
        user_id=user_id,
        selected_period=selected_period,
    )

    if tracking:
        summary = calculate_budget_summary(tracking)

        _render_budget_summary(summary)

    _render_budget_cards(
        tracking=tracking,
        budgets=budgets,
        user_id=user_id,
        selected_period=selected_period,
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

    budgets = list_active_monthly_budgets(
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
        st.markdown(
            build_section_header_html(
                title="Orçamento do mês",
                description=(
                    "Resumo dos limites cadastrados "
                    f"para {format_budget_period(selected_period)}."
                ),
                compact=True,
            ),
            unsafe_allow_html=True,
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