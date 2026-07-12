"""Testes da montagem de contexto para a IA."""

from __future__ import annotations

import pandas as pd

from prompts import (
    montar_contexto,
    montar_mensagem_usuario,
    resumir_gastos_por_categoria,
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


def test_user_message_contains_intent_context():
    message = montar_mensagem_usuario(
        pergunta_usuario=(
            "Quanto ainda tenho?"
        ),
        contexto=(
            "RESUMO FINANCEIRO"
        ),
        contexto_intencao=(
            "INTENÇÃO: saldo"
        ),
    )

    assert (
        "RESUMO FINANCEIRO"
        in message
    )

    assert (
        "INTENÇÃO: saldo"
        in message
    )

    assert (
        "Quanto ainda tenho?"
        in message
    )