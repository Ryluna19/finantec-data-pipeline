"""Dashboard Streamlit do FinanTec."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from analytics import (
    calcular_gastos_por_categoria as calculate_expenses_by_category,
    calcular_resumo_financeiro as calculate_financial_summary,
)
from components.charts import (
    render_expenses_by_category,
    render_monthly_evolution,
)
from components.navigation import (
    DATA_SECTION,
    PROFILE_SECTION,
    render_user_navigation,
)
from components.data_management import (
    DATA_MODE_KEY,
    render_data_management,
)
from components.file_transfer import (
    render_transaction_downloads,
    render_transaction_import,
)
from components.goals import render_goal_simulator
from components.budget import (
    render_budget_dashboard_summary,
    render_monthly_budget,
)
from components.header import render_header
from components.metrics import (
    render_additional_metrics,
    render_financial_diagnosis,
    render_financial_summary,
)
from components.tables import (
    render_category_ranking,
    render_data_validation,
    render_latest_transactions,
    render_period_transactions,
)
from components.auth import (
    render_account_sidebar,
    render_authentication_gate,
)
from data_loader import (
    carregar_perfil_usuario as load_user_profile,
    carregar_rejeicoes as load_rejections,
    carregar_transacoes as load_transactions,
)
from transaction_editor import (
    DATA_REFRESH_REQUESTED_KEY,
    exibir_editor_transacoes_manuais as render_manual_transaction_editor,
)
from ui_components import (
    MONTH_NAMES_PT_BR,
    apply_visual_styles,
)

from components.transaction_management import (
    render_persisted_transaction_management,
)

from components.profile import (
    render_user_profile,
)

from src.user_context import (
    get_current_user_id,
)

st.set_page_config(
    page_title="FinanTec",
    page_icon=":material/account_balance_wallet:",
    layout="wide",
)


TRANSACTION_ACTION_KEY = (
    "active_transaction_action"
)

TRANSACTION_ACTION_NEW = "new"
TRANSACTION_ACTION_IMPORT = "import"
TRANSACTION_ACTION_EXPORT = "export"

VALID_TRANSACTION_ACTIONS = {
    TRANSACTION_ACTION_NEW,
    TRANSACTION_ACTION_IMPORT,
    TRANSACTION_ACTION_EXPORT,
}

MAIN_TAB_LABELS = (
    "Visão geral",
    "Transações",
    "Orçamento",
    "Metas",
)


@st.cache_data
def load_data(
    user_id: str,
    data_mode: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
]:
    """Carrega e mantém em cache os dados utilizados pela interface."""
    active_profile = load_user_profile(
        user_id=user_id,
        data_mode=data_mode,
    )

    personal_profile = (
        load_user_profile(
            user_id=user_id,
            data_mode="user",
        )
        if data_mode == "demo"
        else active_profile
    )

    return (
        personal_profile,
        active_profile,
        load_transactions(
            user_id=user_id,
            data_mode=data_mode,
        ),
        load_rejections(),
    )


def select_period(
    transactions: pd.DataFrame,
) -> tuple[int, str, pd.DataFrame]:
    """Filtra transações sem bloquear a aplicação quando a base está vazia."""
    st.sidebar.title("Filtros")

    if transactions.empty:
        st.sidebar.info(
            "Adicione transações ou carregue "
            "os dados de demonstração."
        )

        return (
            0,
            "Sem dados",
            transactions.copy(),
        )

    data = transactions.copy()

    data["data"] = pd.to_datetime(
        data["data"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["data"]
    ).copy()

    if data.empty:
        st.sidebar.warning(
            "Nenhuma transação possui uma data válida."
        )

        return (
            0,
            "Sem período válido",
            data,
        )

    data["ano"] = (
        data["data"]
        .dt.year
        .astype(int)
    )

    data["mes"] = (
        data["data"]
        .dt.month
        .astype(int)
    )

    years = sorted(
        data["ano"]
        .unique()
        .tolist()
    )

    selected_year = st.sidebar.selectbox(
        "Ano",
        years,
        index=len(years) - 1,
        key="year_filter",
    )

    months = sorted(
        data.loc[
            data["ano"] == selected_year,
            "mes",
        ]
        .unique()
        .tolist()
    )

    selected_month = st.sidebar.selectbox(
        "Mês",
        [0, *months],
        format_func=lambda value: (
            "Todos"
            if value == 0
            else MONTH_NAMES_PT_BR[value]
        ),
        key="month_filter",
    )

    year_filter = (
        data["ano"] == selected_year
    )

    if selected_month == 0:
        filtered_transactions = data.loc[
            year_filter
        ].copy()

        return (
            selected_month,
            str(selected_year),
            filtered_transactions,
        )

    month_filter = (
        data["mes"] == selected_month
    )

    period_label = (
        f"{MONTH_NAMES_PT_BR[selected_month]}"
        f"/{selected_year}"
    )

    filtered_transactions = data.loc[
        year_filter & month_filter
    ].copy()

    return (
        selected_month,
        period_label,
        filtered_transactions,
    )


def render_empty_dashboard() -> None:
    """Exibe uma orientação quando ainda não existem transações."""
    st.header(
        "Visão geral"
    )

    st.info(
        "O dashboard ainda não possui transações para analisar."
    )

    st.markdown(
        """
        Para começar, você pode:

        - cadastrar uma transação na aba **Transações**;
        - importar um arquivo CSV ou Excel;
        - carregar a base simulada em **Dados e privacidade**.
        """
    )

    st.caption(
        "Os dados de demonstração são opcionais "
        "e ficam separados dos dados reais."
    )


def render_dashboard_tab(
    transactions: pd.DataFrame,
    summary: dict[str, Any],
    expenses_by_category: pd.Series,
    show_yearly_evolution: bool,
    user_id: str,
    data_mode: str,
    show_budget_summary: bool,
) -> None:
    """Compõe a visão geral do dashboard."""
    st.header(
        "Visão geral"
    )

    with st.container(
        key="dashboard-summary-section",
    ):
        render_financial_summary(
            summary
        )

    with st.container(
        key="dashboard-diagnosis-section",
    ):
        render_financial_diagnosis(
            summary
        )
    if show_budget_summary:
        with st.container(
            key="dashboard-budget-section",
        ):
            render_budget_dashboard_summary(
                transactions=transactions,
                user_id=user_id,
                data_mode=data_mode,
            )

    with st.container(
        key="dashboard-metrics-section",
    ):
        render_additional_metrics(
            transactions,
            summary,
        )

    with st.container(
        key="dashboard-categories-section",
    ):
        chart_column, ranking_column = st.columns(
            [2, 1],
            gap="medium",
        )

        with chart_column:
            render_expenses_by_category(
                expenses_by_category,
                summary,
            )

        with ranking_column:
            render_category_ranking(
                expenses_by_category
            )

    if show_yearly_evolution:
        with st.container(
            key="dashboard-evolution-section",
        ):
            render_monthly_evolution(
                transactions
            )

    with st.container(
        key="dashboard-latest-section",
    ):
        render_latest_transactions(
            transactions
        )

def _get_active_transaction_action() -> str | None:
    """Retorna a ação ativa e recupera painéis com feedback."""
    if "resultado_etl" in st.session_state:
        active_action = (
            TRANSACTION_ACTION_NEW
        )

    elif "file_import_result" in st.session_state:
        active_action = (
            TRANSACTION_ACTION_IMPORT
        )

    else:
        active_action = (
            st.session_state.get(
                TRANSACTION_ACTION_KEY
            )
        )

    if active_action not in VALID_TRANSACTION_ACTIONS:
        st.session_state.pop(
            TRANSACTION_ACTION_KEY,
            None,
        )

        return None

    st.session_state[
        TRANSACTION_ACTION_KEY
    ] = active_action

    return str(
        active_action
    )


def _toggle_transaction_action(
    selected_action: str,
) -> None:
    """Alterna o único painel secundário visível."""
    current_action = (
        _get_active_transaction_action()
    )

    st.session_state[
        TRANSACTION_ACTION_KEY
    ] = (
        None
        if current_action == selected_action
        else selected_action
    )


def _render_transaction_action_bar() -> str | None:
    """Exibe os comandos da tela e retorna a ação ativa."""
    active_action = (
        _get_active_transaction_action()
    )

    (
        new_column,
        import_column,
        export_column,
    ) = st.columns(
        3,
        gap="small",
    )

    with new_column:
        st.button(
            "Nova transação",
            key="open-new-transaction",
            type=(
                "primary"
                if active_action
                == TRANSACTION_ACTION_NEW
                else "secondary"
            ),
            use_container_width=True,
            on_click=(
                _toggle_transaction_action
            ),
            args=(
                TRANSACTION_ACTION_NEW,
            ),
        )

    with import_column:
        st.button(
            "Importar",
            key="open-transaction-import",
            type=(
                "primary"
                if active_action
                == TRANSACTION_ACTION_IMPORT
                else "secondary"
            ),
            use_container_width=True,
            on_click=(
                _toggle_transaction_action
            ),
            args=(
                TRANSACTION_ACTION_IMPORT,
            ),
        )

    with export_column:
        st.button(
            "Exportar",
            key="open-transaction-export",
            type=(
                "primary"
                if active_action
                == TRANSACTION_ACTION_EXPORT
                else "secondary"
            ),
            use_container_width=True,
            on_click=(
                _toggle_transaction_action
            ),
            args=(
                TRANSACTION_ACTION_EXPORT,
            ),
        )

    return _get_active_transaction_action()


def _render_transaction_action_panel(
    active_action: str | None,
    period_transactions: pd.DataFrame,
    all_transactions: pd.DataFrame,
) -> bool:
    """Exibe somente o fluxo secundário solicitado."""
    if active_action is None:
        return False

    with st.container(
        border=True,
        key=(
            "transaction-action-panel-"
            f"{active_action}"
        ),
    ):
        if (
            active_action
            == TRANSACTION_ACTION_NEW
        ):
            render_manual_transaction_editor()
            return False

        if (
            active_action
            == TRANSACTION_ACTION_IMPORT
        ):
            st.markdown(
                "### Importar transações"
            )

            return render_transaction_import(
                all_transactions
            )

        st.markdown(
            "### Exportar transações"
        )

        st.caption(
            "Baixe o modelo ou exporte somente "
            "as transações do período selecionado."
        )

        render_transaction_downloads(
            period_transactions
        )

    return False


def render_transactions_tab(
    period_transactions: pd.DataFrame,
    all_transactions: pd.DataFrame,
    rejections: pd.DataFrame,
) -> None:
    """Compõe consulta e ações secundárias de transações."""
    st.subheader(
        "Transações"
    )

    st.caption(
        "Consulte seus lançamentos ou use as ações "
        "para adicionar, importar e exportar dados."
    )

    active_action = (
        _render_transaction_action_bar()
    )

    file_import_executed = (
        _render_transaction_action_panel(
            active_action=active_action,
            period_transactions=(
                period_transactions
            ),
            all_transactions=(
                all_transactions
            ),
        )
    )

    if file_import_executed:
        load_data.clear()
        st.rerun()
        return

    with st.container(
        key="transactions-period-section",
    ):
        visible_transactions = (
            render_period_transactions(
                period_transactions
            )
        )

        render_persisted_transaction_management(
            visible_transactions
        )

    with st.container(
        key="transactions-validation-section",
    ):
        render_data_validation(
            len(period_transactions),
            rejections,
        )


def main() -> None:
    """Executa a interface principal."""
    apply_visual_styles()

    authenticated_account = (
        render_authentication_gate()
    )

    if authenticated_account is None:
        return

    render_account_sidebar(
        authenticated_account
    )

    current_user_id = (
        get_current_user_id()
    )

    data_mode = (
        st.session_state.get(
            DATA_MODE_KEY,
            "user",
        )
    )

    if data_mode not in {
        "user",
        "demo",
        "empty",
    }:
        data_mode = "user"

        st.session_state[
            DATA_MODE_KEY
        ] = data_mode

    refresh_requested = (
        st.session_state.pop(
            DATA_REFRESH_REQUESTED_KEY,
            False,
        )
    )

    if refresh_requested:
        load_data.clear()

    (
        personal_profile,
        user_profile,
        transactions,
        rejections,
    ) = load_data(
        current_user_id,
        data_mode,
    )
    active_section = (
        render_user_navigation(
            personal_profile,
            data_mode=data_mode,
        )
    )

    if active_section == PROFILE_SECTION:
        render_header()

        render_user_profile(
            user_profile,
            user_id=current_user_id,
            data_mode=data_mode,
        )

        return

    if active_section == DATA_SECTION:
        render_header()

        render_data_management()

        return

    (
        selected_month,
        period,
        filtered_transactions,
    ) = select_period(
        transactions
    )

    has_transactions = (
        not filtered_transactions.empty
    )

    render_header(
        period
    )

    (
        dashboard_tab,
        transactions_tab,
        budget_tab,
        goals_tab,
    ) = st.tabs(
        MAIN_TAB_LABELS
    )

    if not has_transactions:
        with dashboard_tab:
            render_empty_dashboard()

        with transactions_tab:
            render_transactions_tab(
                period_transactions=filtered_transactions,
                all_transactions=transactions,
                rejections=rejections,
            )
        with budget_tab:
            render_monthly_budget(
                transactions=transactions,
                user_id=current_user_id,
                data_mode=data_mode,
            )

        with goals_tab:
            render_goal_simulator(
                user_profile=user_profile,
                summary={
                    "saldo_disponivel": 0.0,
                },
                user_id=current_user_id,
                data_mode=data_mode,
            )
        return

    summary = calculate_financial_summary(
        filtered_transactions
    )

    expenses_by_category = (
        calculate_expenses_by_category(
            filtered_transactions
        )
    )

    with dashboard_tab:
        render_dashboard_tab(
            transactions=filtered_transactions,
            summary=summary,
            expenses_by_category=expenses_by_category,
            show_yearly_evolution=(
                selected_month == 0
            ),
            user_id=current_user_id,
            data_mode=data_mode,
            show_budget_summary=(
                selected_month != 0
            ),
        )

    with transactions_tab:
        render_transactions_tab(
            period_transactions=filtered_transactions,
            all_transactions=transactions,
            rejections=rejections,
        )
    with budget_tab:
        render_monthly_budget(
            transactions=transactions,
            user_id=current_user_id,
            data_mode=data_mode,
        )

    with goals_tab:
        render_goal_simulator(
            user_profile=user_profile,
            summary=summary,
            user_id=current_user_id,
            data_mode=data_mode,
        )

if __name__ == "__main__":
    main()
