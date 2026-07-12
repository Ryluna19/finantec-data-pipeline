"""Componente de conversa contextual com o assistente FinanTec."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from agent import (
    gerar_resposta_finantec as generate_finantec_response,
)
from prompts import (
    montar_contexto as build_context,
)
from src.financial_responses import (
    build_local_financial_response,
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
    """Mantém um histórico independente para cada período."""
    messages_by_period = (
        st.session_state.setdefault(
            "messages_by_period",
            {},
        )
    )

    if period not in messages_by_period:
        messages_by_period[
            period
        ] = create_initial_message(
            period
        )

    return messages_by_period[
        period
    ]


def build_period_context(
    period: str,
    user_profile: dict[str, Any],
    summary: dict[str, Any],
    expenses_by_category: pd.Series,
    goal_simulations: list[
        dict[str, Any]
    ],
    service_history: pd.DataFrame,
    financial_concepts: dict[str, Any],
    financial_products: dict[str, Any],
) -> str:
    """Monta o contexto financeiro enviado ao modelo de IA."""
    context = build_context(
        perfil_usuario=user_profile,
        resumo_financeiro=summary,
        gastos_por_categoria=(
            expenses_by_category
        ),
        simulacoes_metas=(
            goal_simulations
        ),
        historico_atendimento=(
            service_history
        ),
        conceitos_financeiros=(
            financial_concepts
        ),
        produtos_financeiros=(
            financial_products
        ),
    )

    return (
        "PERÍODO ANALISADO:\n"
        f"{period}\n\n"
        f"{context}"
    ).strip()


def _generate_chat_response(
    user_question: str,
    context: str,
    summary: dict[str, Any],
    expenses_by_category: pd.Series,
) -> tuple[str, bool]:
    """Gera resposta local ou encaminha a pergunta para a IA."""
    local_response = (
        build_local_financial_response(
            question=user_question,
            summary=summary,
            expenses_by_category=(
                expenses_by_category
            ),
        )
    )

    if local_response is not None:
        return (
            local_response,
            True,
        )

    response = (
        generate_finantec_response(
            pergunta_usuario=(
                user_question
            ),
            contexto=context,
        )
    )

    return (
        response,
        False,
    )


def render_chat(
    messages: list[dict[str, str]],
    context: str,
    summary: dict[str, Any],
    expenses_by_category: pd.Series,
) -> None:
    """Exibe o histórico e processa novas perguntas."""
    st.subheader(
        "Converse com o FinanTec"
    )

    st.caption(
        "Você pode perguntar de forma direta ou informal. "
        "Consultas simples são respondidas pelos cálculos locais; "
        "perguntas explicativas usam a IA."
    )

    chat_history = st.container(
        key="finantec-chat-history",
    )

    with chat_history:
        for message in messages:
            with st.chat_message(
                message["role"]
            ):
                st.markdown(
                    message["content"]
                )

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

    with chat_history:
        with st.chat_message(
            "user"
        ):
            st.markdown(
                user_question
            )

        with st.chat_message(
            "assistant"
        ):
            local_response = (
                build_local_financial_response(
                    question=user_question,
                    summary=summary,
                    expenses_by_category=(
                        expenses_by_category
                    ),
                )
            )

            if local_response is not None:
                response = (
                    local_response
                )

                st.markdown(
                    response
                )

            else:
                with st.spinner(
                    "Analisando os dados disponíveis..."
                ):
                    try:
                        response = (
                            generate_finantec_response(
                                pergunta_usuario=(
                                    user_question
                                ),
                                contexto=context,
                            )
                        )

                        st.markdown(
                            response
                        )

                    except RuntimeError as error:
                        response = str(
                            error
                        )

                        st.error(
                            response
                        )

    messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )