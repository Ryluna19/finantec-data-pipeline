"""Integração entre o FinanTec e a Gemini API.

Este módulo é responsável por:
- carregar a chave da Gemini a partir do arquivo .env;
- criar o cliente da API;
- classificar localmente a intenção da pergunta;
- enviar a pergunta com o contexto financeiro;
- tratar erros de configuração ou comunicação;
- limpar formatações que atrapalhem o Streamlit.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from typing import Any

from prompts import (
    SYSTEM_PROMPT,
    montar_mensagem_usuario,
)
from src.financial_intents import (
    build_intent_prompt_context,
    classify_financial_intent,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

ENV_PATH = (
    PROJECT_ROOT
    / ".env"
)

MODEL_NAME = (
    "gemini-2.5-flash"
)

load_dotenv(
    ENV_PATH
)


def obter_chave_api() -> str:
    """Obtém a chave da Gemini das variáveis de ambiente."""
    api_key = os.getenv(
        "GEMINI_API_KEY",
        "",
    ).strip()

    if not ENV_PATH.exists():
        raise RuntimeError(
            "Arquivo .env não encontrado. "
            "Crie um arquivo .env na raiz do projeto "
            "com base no .env.example."
        )

    if not api_key:
        raise RuntimeError(
            "A variável GEMINI_API_KEY está vazia "
            "ou não foi encontrada. Verifique se a chave "
            "foi preenchida corretamente no arquivo .env."
        )

    return api_key


def obter_cliente() -> genai.Client:
    """Cria o cliente da Gemini API."""
    api_key = obter_chave_api()

    return genai.Client(
        api_key=api_key
    )


def limpar_formatacao_resposta(
    resposta: str,
) -> str:
    """Limpa formatações que atrapalhem o Streamlit."""
    resposta_limpa = resposta.replace(
        "`",
        "",
    )

    resposta_limpa = (
        resposta_limpa.replace(
            "$",
            r"\$",
        )
    )

    return resposta_limpa.strip()


def gerar_resposta_finantec(
    pergunta_usuario: str,
    contexto: str,
    historico_conversa: (
        list[dict[str, Any]]
        | None
    ) = None,
) -> str:
    """Envia a pergunta e o contexto calculado para a IA."""
    pergunta = (
        pergunta_usuario.strip()
    )

    if not pergunta:
        return (
            "Digite uma pergunta para que eu possa ajudar."
        )

    classification = (
        classify_financial_intent(
            pergunta
        )
    )

    intent_context = (
        build_intent_prompt_context(
            classification
        )
    )

    user_message = (
        montar_mensagem_usuario(
            pergunta_usuario=pergunta,
            contexto=contexto,
            contexto_intencao=(
                intent_context
            ),
            historico_conversa=(
                historico_conversa
            ),
        )
    )

    try:
        cliente = obter_cliente()

        interacao = (
            cliente.interactions.create(
                model=MODEL_NAME,
                system_instruction=(
                    SYSTEM_PROMPT
                ),
                input=user_message,
                generation_config={
                    "temperature": 0.2,
                    "thinking_level": "low",
                },
            )
        )

        resposta = (
            interacao.output_text
        )

        if not resposta:
            return (
                "Não consegui gerar uma resposta "
                "com os dados disponíveis. "
                "Tente reformular sua pergunta."
            )

        return (
            limpar_formatacao_resposta(
                resposta
            )
        )

    except RuntimeError:
        # Preserva mensagens específicas de configuração.
        raise

    except Exception as erro:
        raise RuntimeError(
            "Não foi possível consultar a IA. "
            "Verifique sua conexão com a internet, "
            "sua chave da Gemini e se a API está "
            "disponível no momento."
        ) from erro