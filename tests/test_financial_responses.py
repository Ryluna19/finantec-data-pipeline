"""Testes das respostas financeiras determinísticas."""

from __future__ import annotations

import pandas as pd

from src.financial_responses import (
    build_local_financial_response,
)


def build_summary() -> dict:
    """Cria um resumo financeiro básico para os testes."""
    return {
        "receitas_totais": 10200.0,
        "despesas_do_mes": 2775.30,
        "valor_guardado_reserva": 520.0,
        "saldo_disponivel": 7424.70,
    }


def build_expenses() -> pd.Series:
    """Cria gastos por categoria para os testes."""
    return pd.Series(
        {
            "Serviços": 695.0,
            "Alimentação": 450.0,
            "Transporte": 300.0,
        }
    )


def test_balance_question_uses_local_summary():
    response = (
        build_local_financial_response(
            question=(
                "Quanto ainda tenho?"
            ),
            summary=build_summary(),
            expenses_by_category=(
                build_expenses()
            ),
        )
    )

    assert (
        "7.424,70"
        in response
    )

    assert (
        "saldo disponível"
        in response.lower()
    )


def test_income_question_uses_local_summary():
    response = (
        build_local_financial_response(
            question=(
                "Quanto entrou?"
            ),
            summary=build_summary(),
            expenses_by_category=(
                build_expenses()
            ),
        )
    )

    assert (
        "10.200,00"
        in response
    )


def test_expenses_question_uses_local_summary():
    response = (
        build_local_financial_response(
            question=(
                "Quanto eu gastei?"
            ),
            summary=build_summary(),
            expenses_by_category=(
                build_expenses()
            ),
        )
    )

    assert (
        "2.775,30"
        in response
    )


def test_reserve_question_uses_local_summary():
    response = (
        build_local_financial_response(
            question=(
                "Quanto eu poupei?"
            ),
            summary=build_summary(),
            expenses_by_category=(
                build_expenses()
            ),
        )
    )

    assert (
        "520,00"
        in response
    )

    assert (
        "saldo disponível"
        in response.lower()
    )


def test_top_category_response():
    response = (
        build_local_financial_response(
            question=(
                "Onde estou gastando mais?"
            ),
            summary=build_summary(),
            expenses_by_category=(
                build_expenses()
            ),
        )
    )

    assert (
        "Serviços"
        in response
    )

    assert (
        "695,00"
        in response
    )


def test_top_category_response_handles_tie():
    expenses = pd.Series(
        {
            "Alimentação": 500.0,
            "Serviços": 500.0,
            "Transporte": 200.0,
        }
    )

    response = (
        build_local_financial_response(
            question=(
                "Qual categoria pesa mais?"
            ),
            summary=build_summary(),
            expenses_by_category=(
                expenses
            ),
        )
    )

    assert (
        "empate"
        in response.lower()
    )

    assert (
        "Alimentação"
        in response
    )

    assert (
        "Serviços"
        in response
    )


def test_period_summary_contains_main_values():
    response = (
        build_local_financial_response(
            question=(
                "Me dê um resumo financeiro."
            ),
            summary=build_summary(),
            expenses_by_category=(
                build_expenses()
            ),
        )
    )

    assert (
        "10.200,00"
        in response
    )

    assert (
        "2.775,30"
        in response
    )

    assert (
        "520,00"
        in response
    )

    assert (
        "7.424,70"
        in response
    )

    assert (
        "Serviços"
        in response
    )


def test_unknown_question_returns_safe_local_response():
    response = (
        build_local_financial_response(
            question=(
                "Qual é a previsão do tempo?"
            ),
            summary=build_summary(),
            expenses_by_category=(
                build_expenses()
            ),
        )
    )

    assert (
        "ainda não é atendida"
        in response.lower()
    )

    assert (
        "não será enviada"
        in response.lower()
    )


def test_concept_question_returns_safe_local_response():
    response = (
        build_local_financial_response(
            question=(
                "O que é reserva de emergência?"
            ),
            summary=build_summary(),
            expenses_by_category=(
                build_expenses()
            ),
        )
    )

    assert (
        "cálculos locais"
        in response.lower()
    )

    assert (
        "serviço externo"
        in response.lower()
    )


def test_product_question_returns_safe_local_response():
    response = (
        build_local_financial_response(
            question=(
                "Qual CDB é o melhor hoje?"
            ),
            summary=build_summary(),
            expenses_by_category=(
                build_expenses()
            ),
        )
    )

    assert (
        "não será enviada"
        in response.lower()
    )