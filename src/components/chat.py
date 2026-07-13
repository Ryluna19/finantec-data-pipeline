"""Componente de conversa contextual com o assistente FinanTec."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from agent import (
    gerar_resposta_finantec as generate_finantec_response,
)
from prompts import (
    montar_contexto as build_context,
)
from scripts.etl_transacoes import (
    ARQUIVO_BANCO,
)
from src.chat_repository import (
    clear_chat_messages,
    load_chat_messages,
    save_chat_exchange,
)
from src.financial_responses import (
    build_local_financial_response,
)


CHAT_MESSAGES_STATE_KEY = (
    "messages_by_period"
)

CHAT_PERSISTENCE_WARNING_KEY = (
    "chat_persistence_warning"
)


def create_initial_message(
    period: str,
) -> list[dict[str, str]]:
    """Cria a mensagem inicial do chat para o período."""
    return [
        {
            "role": "assistant",
            "content": (
                f"Olá! Sou o FinanTec. Estou analisando o período "
                f"{period}. Posso ajudar você a entender gastos, "
                "metas e conceitos financeiros básicos."
            ),
            "source": "system",
        }
    ]


def _build_conversation_key(
    period: str,
    data_mode: str,
) -> str:
    """Cria uma chave isolada por modo e período."""
    return (
        f"{data_mode.strip().lower()}"
        f"::{period.strip()}"
    )


def get_period_messages(
    period: str,
    data_mode: str,
    database_path: Path = ARQUIVO_BANCO,
) -> list[dict[str, str]]:
    """Carrega e mantém o histórico do contexto atual."""
    messages_by_period = (
        st.session_state.setdefault(
            CHAT_MESSAGES_STATE_KEY,
            {},
        )
    )

    conversation_key = (
        _build_conversation_key(
            period=period,
            data_mode=data_mode,
        )
    )

    if (
        conversation_key
        in messages_by_period
    ):
        return messages_by_period[
            conversation_key
        ]

    try:
        persisted_messages = (
            load_chat_messages(
                database_path=database_path,
                period=period,
                data_mode=data_mode,
            )
        )

    except RuntimeError as error:
        persisted_messages = []

        st.session_state[
            CHAT_PERSISTENCE_WARNING_KEY
        ] = str(
            error
        )

    messages_by_period[
        conversation_key
    ] = [
        *create_initial_message(
            period
        ),
        *persisted_messages,
    ]

    return messages_by_period[
        conversation_key
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
    """Monta o contexto enviado ao modelo de IA."""
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


def _render_response_source(
    source: str,
) -> None:
    """Exibe uma indicação discreta da origem da resposta."""
    if source == "local":
        st.caption(
            "Resposta calculada localmente "
            "com os dados do período."
        )

    elif source == "ai":
        st.caption(
            "Resposta gerada com IA usando "
            "o contexto calculado pelo FinanTec."
        )


def _render_chat_message(
    message: dict[str, str],
) -> None:
    """Renderiza uma mensagem e sua origem."""
    role = message.get(
        "role",
        "assistant",
    )

    content = message.get(
        "content",
        "",
    )

    source = message.get(
        "source",
        "",
    )

    with st.chat_message(
        role
    ):
        st.markdown(
            content
        )

        if role == "assistant":
            _render_response_source(
                source
            )


def _clear_current_conversation(
    messages: list[dict[str, str]],
    period: str,
    data_mode: str,
    database_path: Path,
) -> None:
    """Limpa o SQLite e reinicia a conversa da sessão."""
    try:
        clear_chat_messages(
            database_path=database_path,
            period=period,
            data_mode=data_mode,
        )

    except RuntimeError as error:
        st.error(
            str(
                error
            )
        )

        return

    messages.clear()

    messages.extend(
        create_initial_message(
            period
        )
    )

    st.rerun()


def render_chat(
    messages: list[dict[str, str]],
    context: str,
    period: str,
    data_mode: str,
    summary: dict[str, Any],
    expenses_by_category: pd.Series,
    database_path: Path = ARQUIVO_BANCO,
) -> None:
    """Exibe, processa e persiste a conversa."""
    (
        title_column,
        action_column,
    ) = st.columns(
        [
            4,
            1,
        ],
        gap="small",
        vertical_alignment="center",
    )

    with title_column:
        st.subheader(
            "Converse com o FinanTec"
        )

    with action_column:
        if st.button(
            "Limpar conversa",
            key=(
                "clear-finantec-chat-"
                f"{data_mode}-"
                f"{period}"
            ),
            disabled=(
                len(messages) <= 1
            ),
            use_container_width=True,
        ):
            _clear_current_conversation(
                messages=messages,
                period=period,
                data_mode=data_mode,
                database_path=database_path,
            )

    persistence_warning = (
        st.session_state.pop(
            CHAT_PERSISTENCE_WARNING_KEY,
            None,
        )
    )

    if persistence_warning:
        st.warning(
            persistence_warning
        )

    st.caption(
        "Consultas simples são respondidas pelos cálculos locais. "
        "Perguntas explicativas usam a IA. "
        "O histórico é salvo neste dispositivo."
    )

    chat_history = st.container(
        key="finantec-chat-history",
    )

    with chat_history:
        for message in messages:
            _render_chat_message(
                message
            )

    user_question = st.chat_input(
        "Digite sua pergunta sobre organização financeira",
        key="finantec_question",
    )

    if not user_question:
        return

    user_message = {
        "role": "user",
        "content": user_question,
        "source": "",
    }

    with chat_history:
        _render_chat_message(
            user_message
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

                response_source = (
                    "local"
                )

                st.markdown(
                    response
                )

                _render_response_source(
                    response_source
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
                                historico_conversa=(
                                    messages
                                ),
                            )
                        )

                        response_source = (
                            "ai"
                        )

                        st.markdown(
                            response
                        )

                        _render_response_source(
                            response_source
                        )

                    except RuntimeError as error:
                        response = str(
                            error
                        )

                        response_source = (
                            "error"
                        )

                        st.error(
                            response
                        )

    assistant_message = {
        "role": "assistant",
        "content": response,
        "source": response_source,
    }

    messages.extend(
        [
            user_message,
            assistant_message,
        ]
    )

    try:
        save_chat_exchange(
            database_path=database_path,
            period=period,
            data_mode=data_mode,
            question=user_question,
            response=response,
            response_source=(
                response_source
            ),
        )

    except RuntimeError as error:
        st.warning(
            str(
                error
            )
        )