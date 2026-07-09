"""
Integração entre o FinanTec e a Gemini API.

Este módulo é responsável por:
- carregar a chave da Gemini a partir do arquivo .env;
- criar o cliente da API;
- enviar a pergunta do usuário com o contexto do projeto;
- tratar erros de configuração ou comunicação com a IA;
- limpar pequenas formatações que podem atrapalhar o Streamlit.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from prompts import SYSTEM_PROMPT, montar_mensagem_usuario


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

MODEL_NAME = "gemini-2.5-flash"

load_dotenv(ENV_PATH)


def obter_chave_api() -> str:
    """
    Obtém a chave da Gemini a partir das variáveis de ambiente.

    O arquivo .env não é versionado no GitHub. Por isso, quem clonar o projeto
    precisa criar esse arquivo com base no .env.example.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not ENV_PATH.exists():
        raise RuntimeError(
            "Arquivo .env não encontrado. "
            "Crie um arquivo .env na raiz do projeto com base no .env.example."
        )

    if not api_key:
        raise RuntimeError(
            "A variável GEMINI_API_KEY está vazia ou não foi encontrada. "
            "Verifique se a chave foi preenchida corretamente no arquivo .env."
        )

    return api_key


def obter_cliente() -> genai.Client:
    """
    Cria o cliente da Gemini API.
    """
    api_key = obter_chave_api()

    return genai.Client(api_key=api_key)


def limpar_formatacao_resposta(resposta: str) -> str:
    """
    Limpa pequenas formatações que podem atrapalhar a exibição no Streamlit.

    O caractere $ é escapado porque o Streamlit pode interpretar valores como
    R$ como expressão matemática em Markdown.
    """
    resposta_limpa = resposta.replace("`", "")
    resposta_limpa = resposta_limpa.replace("$", r"\$")

    return resposta_limpa.strip()


def gerar_resposta_finantec(
    pergunta_usuario: str,
    contexto: str,
) -> str:
    """
    Envia a pergunta do usuário para a IA usando o contexto calculado pelo app.

    Os cálculos financeiros já chegam prontos no contexto. A IA deve apenas
    explicar os dados, respeitando as regras definidas no SYSTEM_PROMPT.
    """
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
                "thinking_level": "low",
            },
        )

        resposta = interacao.output_text

        if not resposta:
            return (
                "Não consegui gerar uma resposta com os dados disponíveis. "
                "Tente reformular sua pergunta."
            )

        return limpar_formatacao_resposta(resposta)

    except RuntimeError:
        # Mantém mensagens específicas, como .env ausente ou chave vazia.
        raise

    except Exception as erro:
        raise RuntimeError(
            "Não foi possível consultar a IA. "
            "Verifique sua conexão com a internet, sua chave da Gemini "
            "e se a API está disponível no momento."
        ) from erro