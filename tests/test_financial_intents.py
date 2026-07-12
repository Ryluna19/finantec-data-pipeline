"""Testes da classificação local de intenções financeiras."""

from __future__ import annotations

import pytest

from src.financial_intents import (
    FinancialIntent,
    build_intent_prompt_context,
    classify_financial_intent,
    normalize_question,
)


@pytest.mark.parametrize(
    (
        "question",
        "expected_intent",
    ),
    [
        (
            "Qual é meu saldo?",
            FinancialIntent.BALANCE,
        ),
        (
            "Quanto ainda tenho?",
            FinancialIntent.BALANCE,
        ),
        (
            "Sobrou dinheiro este mês?",
            FinancialIntent.BALANCE,
        ),
        (
            "Posso gastar quanto?",
            FinancialIntent.BALANCE,
        ),
        (
            "Estou no vermelho?",
            FinancialIntent.BALANCE,
        ),
        (
            "Quanto eu recebi?",
            FinancialIntent.INCOME,
        ),
        (
            "Quanto entrou este mês?",
            FinancialIntent.INCOME,
        ),
        (
            "Qual foi minha renda?",
            FinancialIntent.INCOME,
        ),
        (
            "Quanto eu gastei?",
            FinancialIntent.EXPENSES,
        ),
        (
            "Qual o total de despesas?",
            FinancialIntent.EXPENSES,
        ),
        (
            "Quanto saiu da conta?",
            FinancialIntent.EXPENSES,
        ),
        (
            "Quanto eu separei para reserva?",
            FinancialIntent.RESERVE,
        ),
        (
            "Quanto guardei?",
            FinancialIntent.RESERVE,
        ),
        (
            "Quanto poupei neste mês?",
            FinancialIntent.RESERVE,
        ),
        (
            "Onde estou gastando mais?",
            FinancialIntent.TOP_CATEGORY,
        ),
        (
            "Com o que mais gastei?",
            FinancialIntent.TOP_CATEGORY,
        ),
        (
            "Qual categoria pesa mais?",
            FinancialIntent.TOP_CATEGORY,
        ),
        (
            "Qual categoria teve o maior gasto?",
            FinancialIntent.TOP_CATEGORY,
        ),
        (
            "Me dê um resumo financeiro.",
            FinancialIntent.PERIOD_SUMMARY,
        ),
        (
            "Como estou financeiramente?",
            FinancialIntent.PERIOD_SUMMARY,
        ),
        (
            "Quanto preciso guardar por mês para o notebook?",
            FinancialIntent.GOAL,
        ),
        (
            "Tenho uma meta para uma viagem.",
            FinancialIntent.GOAL,
        ),
        (
            "O que é uma reserva de emergência?",
            FinancialIntent.FINANCIAL_CONCEPT,
        ),
        (
            "Me explique juros compostos.",
            FinancialIntent.FINANCIAL_CONCEPT,
        ),
        (
            "Qual investimento é melhor hoje?",
            FinancialIntent.FINANCIAL_PRODUCT,
        ),
        (
            "Como funciona um CDB?",
            FinancialIntent.FINANCIAL_CONCEPT,
        ),
        (
            "Como você pode me ajudar?",
            FinancialIntent.HELP,
        ),
        (
            "Me dê exemplos de perguntas.",
            FinancialIntent.HELP,
        ),
    ],
)
def test_classify_financial_intent(
    question,
    expected_intent,
):
    classification = (
        classify_financial_intent(
            question
        )
    )

    assert (
        classification.intent
        == expected_intent
    )

    assert classification.is_known


def test_concept_has_priority_over_reserve():
    classification = (
        classify_financial_intent(
            "O que é uma reserva de emergência?"
        )
    )

    assert (
        classification.intent
        == FinancialIntent.FINANCIAL_CONCEPT
    )


def test_goal_has_priority_over_reserve():
    classification = (
        classify_financial_intent(
            "Quanto preciso guardar para minha reserva?"
        )
    )

    assert (
        classification.intent
        == FinancialIntent.GOAL
    )


def test_unknown_intent():
    classification = (
        classify_financial_intent(
            "Qual é a previsão do tempo?"
        )
    )

    assert (
        classification.intent
        == FinancialIntent.UNKNOWN
    )

    assert not classification.is_known


def test_normalize_question_removes_accents():
    assert (
        normalize_question(
            "Qual é a minha SITUAÇÃO financeira?"
        )
        == "qual e a minha situacao financeira"
    )


def test_build_intent_prompt_context():
    classification = (
        classify_financial_intent(
            "Quanto ainda tenho?"
        )
    )

    context = (
        build_intent_prompt_context(
            classification
        )
    )

    assert (
        "intenção: saldo"
        in context
    )

    assert (
        "saldo_disponivel"
        in context
    )