"""Respostas determinísticas para perguntas financeiras simples.

Os valores são recebidos dos cálculos já realizados pela aplicação.
Perguntas mais complexas continuam sendo encaminhadas ao modelo generativo.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from analytics import (
    formatar_moeda as format_currency,
)
from src.financial_intents import (
    FinancialIntent,
    classify_financial_intent,
)


LOCAL_RESPONSE_INTENTS = {
    FinancialIntent.BALANCE,
    FinancialIntent.INCOME,
    FinancialIntent.EXPENSES,
    FinancialIntent.RESERVE,
    FinancialIntent.TOP_CATEGORY,
    FinancialIntent.PERIOD_SUMMARY,
    FinancialIntent.HELP,
}


def _format_currency_for_markdown(
    value: float,
) -> str:
    """Formata moeda sem ativar expressões matemáticas no Streamlit."""
    return (
        format_currency(
            value
        )
        .replace(
            "$",
            r"\$",
        )
    )


def _get_summary_amount(
    summary: dict[str, Any],
    key: str,
) -> float | None:
    """Obtém um valor numérico seguro do resumo financeiro."""
    numeric_value = pd.to_numeric(
        summary.get(
            key
        ),
        errors="coerce",
    )

    if pd.isna(
        numeric_value
    ):
        return None

    return float(
        numeric_value
    )


def _build_missing_value_response(
    label: str,
) -> str:
    """Informa que o indicador solicitado não está disponível."""
    return (
        f"Não há dados suficientes para informar {label} "
        "no período analisado."
    )


def _build_balance_response(
    summary: dict[str, Any],
) -> str:
    """Responde perguntas sobre saldo disponível."""
    balance = _get_summary_amount(
        summary,
        "saldo_disponivel",
    )

    if balance is None:
        return _build_missing_value_response(
            "o saldo disponível"
        )

    formatted_balance = (
        _format_currency_for_markdown(
            balance
        )
    )

    if balance > 0:
        situation = (
            "O valor está positivo e representa o que permaneceu "
            "disponível depois das despesas e do valor reservado."
        )

    elif balance < 0:
        situation = (
            "O valor está negativo, indicando que as saídas "
            "superaram os recursos disponíveis no período."
        )

    else:
        situation = (
            "O saldo ficou zerado após considerar as movimentações "
            "registradas no período."
        )

    return (
        f"Seu saldo disponível é de **{formatted_balance}**.\n\n"
        f"{situation}"
    )


def _build_income_response(
    summary: dict[str, Any],
) -> str:
    """Responde perguntas sobre receitas."""
    income = _get_summary_amount(
        summary,
        "receitas_totais",
    )

    if income is None:
        return _build_missing_value_response(
            "as receitas totais"
        )

    formatted_income = (
        _format_currency_for_markdown(
            income
        )
    )

    return (
        "As receitas registradas no período totalizam "
        f"**{formatted_income}**."
    )


def _build_expenses_response(
    summary: dict[str, Any],
) -> str:
    """Responde perguntas sobre despesas."""
    expenses = _get_summary_amount(
        summary,
        "despesas_do_mes",
    )

    if expenses is None:
        return _build_missing_value_response(
            "as despesas"
        )

    formatted_expenses = (
        _format_currency_for_markdown(
            expenses
        )
    )

    return (
        "As despesas registradas no período totalizam "
        f"**{formatted_expenses}**."
    )


def _build_reserve_response(
    summary: dict[str, Any],
) -> str:
    """Responde perguntas sobre valor destinado à reserva."""
    reserve = _get_summary_amount(
        summary,
        "valor_guardado_reserva",
    )

    if reserve is None:
        return _build_missing_value_response(
            "o valor reservado"
        )

    formatted_reserve = (
        _format_currency_for_markdown(
            reserve
        )
    )

    return (
        "O valor destinado à reserva no período foi de "
        f"**{formatted_reserve}**.\n\n"
        "Esse valor é separado do saldo disponível."
    )


def _prepare_category_expenses(
    expenses_by_category: pd.Series,
) -> pd.Series:
    """Mantém apenas categorias com valores numéricos válidos."""
    if expenses_by_category.empty:
        return pd.Series(
            dtype="float64"
        )

    numeric_expenses = pd.to_numeric(
        expenses_by_category,
        errors="coerce",
    ).dropna()

    return numeric_expenses.loc[
        numeric_expenses >= 0
    ]


def _build_top_category_response(
    expenses_by_category: pd.Series,
) -> str:
    """Responde qual categoria possui o maior gasto."""
    numeric_expenses = (
        _prepare_category_expenses(
            expenses_by_category
        )
    )

    if numeric_expenses.empty:
        return (
            "Não há gastos por categoria suficientes "
            "para identificar o maior consumo do período."
        )

    highest_value = float(
        numeric_expenses.max()
    )

    top_categories = [
        str(
            category
        )
        for category in (
            numeric_expenses.loc[
                numeric_expenses
                == highest_value
            ]
            .index
            .tolist()
        )
    ]

    formatted_value = (
        _format_currency_for_markdown(
            highest_value
        )
    )

    if len(top_categories) == 1:
        return (
            "A categoria com o maior gasto foi "
            f"**{top_categories[0]}**, com "
            f"**{formatted_value}**."
        )

    categories_text = ", ".join(
        top_categories
    )

    return (
        "Houve empate entre as categorias "
        f"**{categories_text}**, cada uma com "
        f"**{formatted_value}**."
    )


def _build_period_summary_response(
    summary: dict[str, Any],
    expenses_by_category: pd.Series,
) -> str:
    """Apresenta os principais indicadores do período."""
    income = _get_summary_amount(
        summary,
        "receitas_totais",
    )

    expenses = _get_summary_amount(
        summary,
        "despesas_do_mes",
    )

    reserve = _get_summary_amount(
        summary,
        "valor_guardado_reserva",
    )

    balance = _get_summary_amount(
        summary,
        "saldo_disponivel",
    )

    if all(
        value is None
        for value in (
            income,
            expenses,
            reserve,
            balance,
        )
    ):
        return (
            "Não há indicadores financeiros suficientes "
            "para montar o resumo deste período."
        )

    summary_lines: list[str] = []

    if income is not None:
        summary_lines.append(
            "- Receitas: "
            f"**{_format_currency_for_markdown(income)}**"
        )

    if expenses is not None:
        summary_lines.append(
            "- Despesas: "
            f"**{_format_currency_for_markdown(expenses)}**"
        )

    if reserve is not None:
        summary_lines.append(
            "- Reserva: "
            f"**{_format_currency_for_markdown(reserve)}**"
        )

    if balance is not None:
        summary_lines.append(
            "- Saldo disponível: "
            f"**{_format_currency_for_markdown(balance)}**"
        )

    numeric_expenses = (
        _prepare_category_expenses(
            expenses_by_category
        )
    )

    if not numeric_expenses.empty:
        highest_value = float(
            numeric_expenses.max()
        )

        top_categories = [
            str(
                category
            )
            for category in (
                numeric_expenses.loc[
                    numeric_expenses
                    == highest_value
                ]
                .index
                .tolist()
            )
        ]

        category_text = ", ".join(
            top_categories
        )

        summary_lines.append(
            "- Maior categoria de gastos: "
            f"**{category_text}** "
            f"({_format_currency_for_markdown(highest_value)})"
        )

    return (
        "Resumo do período:\n\n"
        + "\n".join(
            summary_lines
        )
    )


def _build_help_response() -> str:
    """Apresenta exemplos de perguntas aceitas."""
    return (
        "Posso ajudar você a consultar os dados financeiros "
        "do período e entender conceitos básicos.\n\n"
        "Alguns exemplos:\n"
        "- Quanto ainda tenho?\n"
        "- Quanto entrou e quanto eu gastei?\n"
        "- Onde estou gastando mais?\n"
        "- Quanto preciso guardar para uma meta?"
    )


def build_local_financial_response(
    question: str,
    summary: dict[str, Any],
    expenses_by_category: pd.Series,
) -> str | None:
    """Cria uma resposta local quando a intenção for simples."""
    classification = (
        classify_financial_intent(
            question
        )
    )

    intent = classification.intent

    if intent not in LOCAL_RESPONSE_INTENTS:
        return None

    if intent == FinancialIntent.BALANCE:
        return _build_balance_response(
            summary
        )

    if intent == FinancialIntent.INCOME:
        return _build_income_response(
            summary
        )

    if intent == FinancialIntent.EXPENSES:
        return _build_expenses_response(
            summary
        )

    if intent == FinancialIntent.RESERVE:
        return _build_reserve_response(
            summary
        )

    if intent == FinancialIntent.TOP_CATEGORY:
        return _build_top_category_response(
            expenses_by_category
        )

    if intent == FinancialIntent.PERIOD_SUMMARY:
        return _build_period_summary_response(
            summary=summary,
            expenses_by_category=(
                expenses_by_category
            ),
        )

    if intent == FinancialIntent.HELP:
        return _build_help_response()

    return None