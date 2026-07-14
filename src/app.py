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
from components.chat import (
    get_period_messages,
    render_chat,
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
    render_transaction_file_tools,
)
from components.goals import render_goal_simulator
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


@st.cache_data
def load_data(
    user_id: str,
    data_mode: str,
) -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
]:
    """Carrega e mantém em cache os dados utilizados pela interface."""
    return (
        load_user_profile(),
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


def render_unavailable_feature(
    title="Insights financeiros",
    message=(
        "Os insights precisam de transações "
        "para analisar o período."
    ),
) -> None:
    """Exibe um estado vazio para recursos que dependem de transações."""
    st.header(title)

    st.info(message)

    st.caption(
        "Adicione transações reais ou carregue "
        "a demonstração em Dados e privacidade."
    )


def render_dashboard_tab(
    transactions: pd.DataFrame,
    summary: dict[str, Any],
    expenses_by_category: pd.Series,
    show_yearly_evolution: bool,
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

def render_transactions_tab(
    period_transactions: pd.DataFrame,
    all_transactions: pd.DataFrame,
    rejections: pd.DataFrame,
) -> None:
    """Compõe entrada, arquivos, validação e consulta de transações."""
    should_expand_editor = (
        "resultado_etl"
        in st.session_state
    )

    with st.expander(
        "Entrada manual de transações",
        expanded=should_expand_editor,
    ):
        render_manual_transaction_editor()

    should_expand_files = (
        "file_import_result"
        in st.session_state
    )

    with st.expander(
        "Importar ou exportar transações",
        expanded=should_expand_files,
    ):
        file_import_executed = (
            render_transaction_file_tools(
                period_transactions=period_transactions,
                existing_transactions=all_transactions,
            )
        )

    if file_import_executed:
        load_data.clear()
        st.rerun()

    st.caption(
        "Transações manuais e importadas são salvas "
        "diretamente no banco e aparecem nos indicadores."
    )

    with st.container(
        key="transactions-validation-section",
    ):
        render_data_validation(
            len(period_transactions),
            rejections,
        )

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


def main() -> None:
    """Executa a interface principal."""
    apply_visual_styles()

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
        user_profile,
        transactions,
        rejections,
    ) = load_data(
        current_user_id,
        data_mode,
    )
    active_section = (
        render_user_navigation(
            user_profile
        )
    )

    if active_section == PROFILE_SECTION:
        render_header()

        render_user_profile(
            user_profile
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
        goals_tab,
        insights_tab,
    ) = st.tabs(
        [
            "Visão geral",
            "Transações",
            "Metas",
            "Insights",
        ]
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

        with goals_tab:
            render_goal_simulator(
                user_profile=user_profile,
                summary={
                    "saldo_disponivel": 0.0,
                },
            )

        with insights_tab:
            render_unavailable_feature(
                title="Assistente financeiro",
                message=(
                    "O assistente precisa de transações "
                    "para criar o contexto financeiro do período."
                ),
            ),
        return

    summary = calculate_financial_summary(
        filtered_transactions
    )

    expenses_by_category = (
        calculate_expenses_by_category(
            filtered_transactions
        )
    )

    messages = get_period_messages(
        user_id=current_user_id,
        period=period,
        data_mode=data_mode,
    )

    with dashboard_tab:
        render_dashboard_tab(
            transactions=filtered_transactions,
            summary=summary,
            expenses_by_category=expenses_by_category,
            show_yearly_evolution=(
                selected_month == 0
            ),
        )

    with transactions_tab:
        render_transactions_tab(
            period_transactions=filtered_transactions,
            all_transactions=transactions,
            rejections=rejections,
        )

    with goals_tab:
        render_goal_simulator(
            user_profile=user_profile,
            summary=summary,
        )
    
    with insights_tab:
        render_chat(
            messages=messages,
            user_id=current_user_id,
            period=period,
            data_mode=data_mode,
            summary=summary,
            expenses_by_category=(
                expenses_by_category
            ),
        )
        
if __name__ == "__main__":
    main()