from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from prompts import SYSTEM_PROMPT, montar_mensagem_usuario


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "gemini-2.5-flash"

load_dotenv(PROJECT_ROOT / ".env")


def obter_cliente() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "A variável GEMINI_API_KEY não foi encontrada. "
            "Verifique se o arquivo .env existe e se a chave foi preenchida."
        )

    return genai.Client(api_key=api_key)

def limpar_formatacao_resposta(resposta: str) -> str:
    resposta_limpa = resposta.replace("`", "")
    resposta_limpa = resposta_limpa.replace("$", r"\$")

    return resposta_limpa.strip()

def gerar_resposta_finantec(
    pergunta_usuario: str,
    contexto: str
) -> str:
    pergunta = pergunta_usuario.strip()

    if not pergunta:
        return "Digite uma pergunta para que eu possa ajudar."

    try:
        cliente = obter_cliente()

        interacao = cliente.interactions.create(
            model=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT,
            input=montar_mensagem_usuario(pergunta, contexto),
            generation_config={
                "temperature": 0.2,
                "thinking_level": "low"
            }
        )

        resposta = interacao.output_text

        if not resposta:
            return (
                "Não consegui gerar uma resposta com os dados disponíveis. "
                "Tente reformular sua pergunta."
            )

        return limpar_formatacao_resposta(resposta)

    except Exception as erro:
        raise RuntimeError(
            "Não foi possível consultar a IA. "
            "Verifique sua chave da Gemini e a conexão com a internet."
        ) from erro
