"""Testes da montagem de contexto para a IA."""

from __future__ import annotations

import pandas as pd

from prompts import (
    montar_contexto,
    montar_mensagem_usuario,
    resumir_gastos_por_categoria,
    resumir_conversa_recente,
)


def test_category_summary_identifies_top_category():
    summary = (
        resumir_gastos_por_categoria(
            {
                "Alimentação": 350.0,
                "Transporte": 120.0,
                "Lazer": 80.0,
            }
        )
    )

    assert (
        summary[
            "categorias_com_maior_gasto"
        ]
        == [
            "Alimentação",
        ]
    )

    assert (
        summary["maior_valor"]
        == 350.0
    )

    assert not summary[
        "ha_empate"
    ]


def test_category_summary_identifies_tie():
    summary = (
        resumir_gastos_por_categoria(
            {
                "Alimentação": 200.0,
                "Transporte": 200.0,
            }
        )
    )

    assert set(
        summary[
            "categorias_com_maior_gasto"
        ]
    ) == {
        "Alimentação",
        "Transporte",
    }

    assert summary[
        "ha_empate"
    ]


def test_context_contains_precalculated_category_summary():
    context = montar_contexto(
        perfil_usuario={},
        resumo_financeiro={
            "saldo_disponivel": 500.0,
        },
        gastos_por_categoria=pd.Series(
            {
                "Alimentação": 300.0,
                "Transporte": 100.0,
            }
        ),
        simulacoes_metas=[],
        historico_atendimento=(
            pd.DataFrame()
        ),
        conceitos_financeiros={},
        produtos_financeiros={},
    )

    assert (
        "RESUMO DE CATEGORIAS "
        "CALCULADO PELO PYTHON"
        in context
    )

    assert (
        '"Alimentação"'
        in context
    )

    assert (
        '"maior_valor": 300.0'
        in context
    )


def test_user_message_contains_intent_and_conversation():
    message = montar_mensagem_usuario(
        pergunta_usuario=(
            "E quanto falta para a minha?"
        ),
        contexto=(
            "RESUMO FINANCEIRO"
        ),
        contexto_intencao=(
            "INTENÇÃO: meta_financeira"
        ),
        historico_conversa=[
            {
                "role": "user",
                "content": (
                    "O que é uma reserva?"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "É um valor para imprevistos."
                ),
                "source": "ai",
            },
        ],
    )

    assert (
        "RESUMO FINANCEIRO"
        in message
    )

    assert (
        "CONVERSA RECENTE"
        in message
    )

    assert (
        "O que é uma reserva?"
        in message
    )

    assert (
        "INTENÇÃO: meta_financeira"
        in message
    )

    assert (
        "E quanto falta para a minha?"
        in message
    )
    
def test_recent_conversation_ignores_initial_message():
    messages = [
        {
            "role": "assistant",
            "content": "Mensagem inicial",
            "source": "system",
        },
        {
            "role": "user",
            "content": "O que é reserva?",
            "source": "",
        },
        {
            "role": "assistant",
            "content": "É um valor para imprevistos.",
            "source": "ai",
        },
    ]

    conversation = (
        resumir_conversa_recente(
            messages
        )
    )

    assert conversation == [
        {
            "papel": "pessoa_usuaria",
            "conteudo": (
                "O que é reserva?"
            ),
        },
        {
            "papel": "finantec",
            "conteudo": (
                "É um valor para imprevistos."
            ),
        },
    ]


def test_recent_conversation_keeps_only_latest_messages():
    messages = [
        {
            "role": "user",
            "content": (
                f"Pergunta {index}"
            ),
        }
        for index in range(
            5
        )
    ]

    conversation = (
        resumir_conversa_recente(
            mensagens=messages,
            limite=2,
        )
    )

    assert conversation == [
        {
            "papel": "pessoa_usuaria",
            "conteudo": "Pergunta 3",
        },
        {
            "papel": "pessoa_usuaria",
            "conteudo": "Pergunta 4",
        },
    ]


def test_recent_conversation_truncates_long_content():
    long_content = (
        "a"
        * 900
    )

    conversation = (
        resumir_conversa_recente(
            [
                {
                    "role": "user",
                    "content": long_content,
                }
            ]
        )
    )

    content = conversation[
        0
    ][
        "conteudo"
    ]

    assert content.endswith(
        "…"
    )

    assert len(
        content
    ) == 801