"""Dashboard Streamlit do FinanTec."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from agent import gerar_resposta_finantec as generate_finantec_response
from analytics import (
    calcular_gastos_por_categoria as calculate_expenses_by_category,
    calcular_meta_mensal as calculate_monthly_goal,
    calcular_resumo_financeiro as calculate_financial_summary,
    calcular_simulacoes_de_metas as calculate_goal_simulations,
    formatar_moeda as format_currency,
)
from components.charts import (
    render_expenses_by_category,
    render_monthly_evolution,
)
from components.header import render_header
from components.metrics import (
    render_additional_metrics,
    render_financial_diagnosis,
    render_financial_summary,
)
from data_loader import (
    carregar_conceitos_financeiros as load_financial_concepts,
    carregar_historico_atendimento as load_service_history,
    carregar_perfil_usuario as load_user_profile,
    carregar_produtos_financeiros as load_financial_products,
    carregar_rejeicoes as load_rejections,
    carregar_transacoes as load_transactions,
)
from prompts import montar_contexto as build_context
from transaction_editor import (
    exibir_editor_transacoes_manuais as render_manual_transaction_editor,
)
from ui_components import (
    MONTH_NAMES_PT_BR,
    TRANSACTION_TYPE_LABELS,
    apply_visual_styles,
)


st.set_page_config(
    page_title="FinanTec",
    page_icon="💰",
    layout="wide",
)


@st.cache_data
def load_data() -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
    dict[str, Any],
    pd.DataFrame,
]:
    """Carrega e mantém em cache os dados utilizados pela interface."""
    return (
        load_user_profile(),
        load_transactions(),
        load_service_history(),
        load_financial_concepts(),
        load_financial_products(),
        load_rejections(),
    )


def select_period(
    transactions: pd.DataFrame,
) -> tuple[int, str, pd.DataFrame]:
    """Filtra as transações pelo ano e mês escolhidos na barra lateral."""
    if transactions.empty:
        st.error("Não há transações disponíveis.")
        st.stop()

    data = transactions.copy()

    data["data"] = pd.to_datetime(
        data["data"],
        errors="coerce",
    )

    data["ano"] = data["data"].dt.year
    data["mes"] = data["data"].dt.month

    years = sorted(
        data["ano"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    if not years:
        st.error("Nenhum ano válido foi encontrado na base.")
        st.stop()

    st.sidebar.title("Filtros")

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
        .dropna()
        .astype(int)
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

    year_filter = data["ano"] == selected_year

    if selected_month == 0:
        filtered_transactions = data.loc[
            year_filter
        ].copy()

        return (
            selected_month,
            str(selected_year),
            filtered_transactions,
        )

    month_filter = data["mes"] == selected_month

    period_label = (
        f"{MONTH_NAMES_PT_BR[selected_month]}/{selected_year}"
    )

    filtered_transactions = data.loc[
        year_filter & month_filter
    ].copy()

    return (
        selected_month,
        period_label,
        filtered_transactions,
    )


def create_initial_message(
    period: str,
) -> list[dict[str, str]]:
    """Cria a mensagem inicial do chat para o período selecionado."""
    return [
        {
            "role": "assistant",
            "content": (
                f"Olá! Sou o FinanTec. Estou analisando o período "
                f"{period}. Posso ajudar você a entender gastos, "
                "metas e conceitos financeiros básicos."
            ),
        }
    ]


def get_period_messages(
    period: str,
) -> list[dict[str, str]]:
    """Mantém um histórico de conversa independente para cada período."""
    messages_by_period = st.session_state.setdefault(
        "messages_by_period",
        {},
    )

    if period not in messages_by_period:
        messages_by_period[period] = create_initial_message(period)

    return messages_by_period[period]


def build_period_context(
    period: str,
    user_profile: dict[str, Any],
    summary: dict[str, Any],
    expenses_by_category: pd.Series,
    goal_simulations: list[dict[str, Any]],
    service_history: pd.DataFrame,
    financial_concepts: dict[str, Any],
    financial_products: dict[str, Any],
) -> str:
    """Monta o contexto enviado à IA com os dados do período."""
    context = build_context(
        perfil_usuario=user_profile,
        resumo_financeiro=summary,
        gastos_por_categoria=expenses_by_category,
        simulacoes_metas=goal_simulations,
        historico_atendimento=service_history,
        conceitos_financeiros=financial_concepts,
        produtos_financeiros=financial_products,
    )

    return (
        f"PERÍODO ANALISADO:\n"
        f"{period}\n\n"
        f"{context}"
    ).strip()


def prepare_transactions_for_display(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Formata as transações para apresentação nas tabelas."""
    table = transactions.copy()

    table["data"] = pd.to_datetime(
        table["data"],
        errors="coerce",
    ).dt.strftime("%d/%m/%Y")

    original_types = table["tipo"].copy()

    table["tipo"] = (
        table["tipo"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(TRANSACTION_TYPE_LABELS)
        .fillna(original_types)
    )

    table["descricao"] = (
        table["descricao"]
        .astype(str)
        .str.strip()
    )

    table["categoria"] = (
        table["categoria"]
        .astype(str)
        .str.strip()
    )

    table["valor"] = table["valor"].map(format_currency)

    table = table.rename(
        columns={
            "data": "Data",
            "tipo": "Tipo",
            "descricao": "Descrição",
            "categoria": "Categoria",
            "valor": "Valor",
        }
    )

    return table[
        [
            "Data",
            "Tipo",
            "Descrição",
            "Categoria",
            "Valor",
        ]
    ]


def render_category_ranking(
    expenses_by_category: pd.Series,
) -> None:
    """Exibe o ranking das categorias com maior consumo."""
    st.subheader("Ranking de categorias")

    if expenses_by_category.empty:
        st.info(
            "Não há categorias de consumo para listar neste período."
        )
        return

    ranking = (
        expenses_by_category
        .sort_values(ascending=False)
        .rename("Valor")
        .reset_index()
    )

    ranking.columns = [
        "Categoria",
        "Valor",
    ]

    ranking.insert(
        0,
        "Posição",
        range(1, len(ranking) + 1),
    )

    ranking["Valor"] = ranking["Valor"].map(
        format_currency
    )

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True,
    )


def render_latest_transactions(
    transactions: pd.DataFrame,
    limit: int = 5,
) -> None:
    """Exibe as transações mais recentes do período."""
    st.subheader("Últimas transações")

    if transactions.empty:
        st.info(
            "Nenhuma transação encontrada para o período selecionado."
        )
        return

    latest_transactions = (
        transactions
        .sort_values(
            by="data",
            ascending=False,
        )
        .head(limit)
    )

    table = prepare_transactions_for_display(
        latest_transactions
    )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )


def render_data_validation(
    valid_count: int,
    rejections: pd.DataFrame,
) -> None:
    """Exibe a situação dos dados processados pelo ETL."""
    st.subheader("Validação dos dados")

    valid_column, rejected_column = st.columns(2)

    valid_column.metric(
        "Válidas no período",
        valid_count,
    )

    rejected_column.metric(
        "Rejeitadas no último ETL",
        len(rejections),
    )

    if rejections.empty:
        st.success(
            "Nenhuma transação foi rejeitada "
            "no último processamento."
        )
        return

    st.warning(
        "Existem transações rejeitadas. "
        "Consulte a tabela para conferir os motivos."
    )

    with st.expander("Ver transações rejeitadas"):
        st.dataframe(
            rejections,
            use_container_width=True,
            hide_index=True,
        )


def filter_transactions_table(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Aplica filtros de tipo, categoria e descrição."""
    types = sorted(
        transactions["tipo"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    categories = sorted(
        transactions["categoria"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    type_column, category_column, search_column = st.columns(
        [1, 1, 2]
    )

    selected_type = type_column.selectbox(
        "Tipo",
        [
            "Todos",
            *types,
        ],
        format_func=lambda value: (
            value
            if value == "Todos"
            else TRANSACTION_TYPE_LABELS.get(
                value,
                value.title(),
            )
        ),
        key="transaction_type_filter",
    )

    selected_category = category_column.selectbox(
        "Categoria",
        [
            "Todas",
            *categories,
        ],
        key="transaction_category_filter",
    )

    search_text = search_column.text_input(
        "Buscar descrição",
        placeholder="Ex.: mercado, transporte, bolsa",
        key="transaction_description_filter",
    )

    result = transactions.copy()

    if selected_type != "Todos":
        result = result.loc[
            result["tipo"] == selected_type
        ]

    if selected_category != "Todas":
        result = result.loc[
            result["categoria"] == selected_category
        ]

    if search_text.strip():
        result = result.loc[
            result["descricao"]
            .astype(str)
            .str.contains(
                search_text.strip(),
                case=False,
                na=False,
            )
        ]

    return result


def render_period_transactions(
    transactions: pd.DataFrame,
) -> None:
    """Exibe as transações e os totais dos filtros aplicados."""
    st.subheader("Transações do período")

    st.caption(
        "Use os filtros para consultar receitas, despesas, "
        "categorias ou descrições específicas."
    )

    if transactions.empty:
        st.info(
            "Nenhuma transação encontrada para o período selecionado."
        )
        return

    filtered_transactions = filter_transactions_table(
        transactions
    )

    income = filtered_transactions.loc[
        filtered_transactions["tipo"] == "receita",
        "valor",
    ].sum()

    expenses = filtered_transactions.loc[
        filtered_transactions["tipo"] == "despesa",
        "valor",
    ].sum()

    total_column, income_column, expense_column = st.columns(3)

    total_column.metric(
        "Transações",
        len(filtered_transactions),
    )

    income_column.metric(
        "Receitas",
        format_currency(income),
    )

    expense_column.metric(
        "Despesas",
        format_currency(expenses),
    )

    if filtered_transactions.empty:
        st.info(
            "Nenhuma transação corresponde aos filtros selecionados."
        )
        return

    table = prepare_transactions_for_display(
        filtered_transactions.sort_values(
            by="data",
            ascending=False,
        )
    )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )


def render_goal_simulator(
    user_profile: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    """Exibe a simulação de uma meta financeira."""
    st.subheader("Simulador de metas")

    st.caption(
        "Escolha uma meta para estimar quanto "
        "ainda precisa ser guardado por mês."
    )

    goals = user_profile["objetivos_financeiros"]

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
            "Não foi possível calcular a meta porque o prazo é inválido."
        )
    elif monthly_amount > summary["saldo_disponivel"]:
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


def render_chat(
    messages: list[dict[str, str]],
    context: str,
) -> None:
    """Exibe o chat contextual do FinanTec."""
    st.subheader("Converse com o FinanTec")

    st.caption(
        "Exemplos: “Em qual categoria eu mais gastei?”, "
        "“Qual é meu saldo?” ou "
        "“Quanto preciso guardar para o notebook?”"
    )

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.chat_input(
        "Digite sua pergunta sobre organização financeira",
        key="finantec_question",
    )

    if not user_question:
        return

    messages.append(
        {
            "role": "user",
            "content": user_question,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Analisando os dados disponíveis..."):
            try:
                response = generate_finantec_response(
                    pergunta_usuario=user_question,
                    contexto=context,
                )

                st.markdown(response)
            except RuntimeError as error:
                response = str(error)
                st.error(response)

    messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )


def render_dashboard_tab(
    transactions: pd.DataFrame,
    summary: dict[str, Any],
    expenses_by_category: pd.Series,
    show_yearly_evolution: bool,
) -> None:
    """Compõe a visão geral do dashboard."""
    st.header("Visão geral")

    render_financial_summary(summary)

    st.divider()

    render_financial_diagnosis(summary)

    st.divider()

    render_additional_metrics(
        transactions,
        summary,
    )

    st.divider()

    chart_column, ranking_column = st.columns(
        [2, 1]
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
        st.divider()

        render_monthly_evolution(
            transactions
        )

    st.divider()

    render_latest_transactions(
        transactions
    )


def render_transactions_tab(
    transactions: pd.DataFrame,
    rejections: pd.DataFrame,
) -> None:
    """Compõe entrada, validação e consulta de transações."""
    should_expand_editor = (
        "resultado_etl" in st.session_state
    )

    with st.expander(
        "Entrada manual de transações",
        expanded=should_expand_editor,
    ):
        etl_executed = render_manual_transaction_editor()

    if etl_executed:
        load_data.clear()
        st.rerun()

    st.caption(
        "Transações manuais aparecem nos indicadores "
        "após o processamento do ETL e no período "
        "correspondente à data cadastrada."
    )

    st.divider()

    render_data_validation(
        len(transactions),
        rejections,
    )

    st.divider()

    render_period_transactions(
        transactions
    )


def main() -> None:
    """Executa a interface principal."""
    apply_visual_styles()

    (
        user_profile,
        transactions,
        service_history,
        financial_concepts,
        financial_products,
        rejections,
    ) = load_data()

    (
        selected_month,
        period,
        filtered_transactions,
    ) = select_period(transactions)

    summary = calculate_financial_summary(
        filtered_transactions
    )

    expenses_by_category = calculate_expenses_by_category(
        filtered_transactions
    )

    goal_simulations = calculate_goal_simulations(
        user_profile
    )

    context = build_period_context(
        period=period,
        user_profile=user_profile,
        summary=summary,
        expenses_by_category=expenses_by_category,
        goal_simulations=goal_simulations,
        service_history=service_history,
        financial_concepts=financial_concepts,
        financial_products=financial_products,
    )

    messages = get_period_messages(period)

    render_header(period)

    (
        dashboard_tab,
        transactions_tab,
        goals_tab,
        ai_tab,
    ) = st.tabs(
        [
            "Dashboard",
            "Transações",
            "Metas",
            "IA",
        ]
    )

    with dashboard_tab:
        render_dashboard_tab(
            transactions=filtered_transactions,
            summary=summary,
            expenses_by_category=expenses_by_category,
            show_yearly_evolution=selected_month == 0,
        )

    with transactions_tab:
        render_transactions_tab(
            transactions=filtered_transactions,
            rejections=rejections,
        )

    with goals_tab:
        render_goal_simulator(
            user_profile=user_profile,
            summary=summary,
        )

    with ai_tab:
        render_chat(
            messages=messages,
            context=context,
        )


if __name__ == "__main__":
    main()