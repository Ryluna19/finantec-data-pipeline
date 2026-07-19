"""Testes do componente de orçamento mensal."""

from __future__ import annotations

import pandas as pd

from src.components.budget import (
    CATEGORY_PLACEHOLDER,
    DEFAULT_BUDGET_CATEGORIES,
    _find_budget,
    build_budget_category_options,
    build_budget_dashboard_summary,
    build_budget_payload,
    build_budget_period_options,
    format_budget_period,
    get_budget_status_label,
    resolve_budget_category,
)


def test_budget_period_options_include_current_and_existing_months():
    transactions = pd.DataFrame(
        {
            "data": pd.to_datetime(
                [
                    "2026-05-01",
                    "2026-06-01",
                ]
            ),
            "ano_mes": [
                "2026-05",
                "2026-06",
            ],
        }
    )

    periods = (
        build_budget_period_options(
            transactions,
            reference_period="2026-07",
        )
    )

    assert periods == [
        "2026-07",
        "2026-06",
        "2026-05",
    ]

def test_build_budget_payload():
    payload = build_budget_payload(
        period="2026-07",
        category="Alimentação",
        planned_amount=800.0,
    )

    assert payload == {
        "period": "2026-07",
        "category": "Alimentação",
        "planned_amount": 800.0,
    }


def test_formats_budget_period():
    assert (
        format_budget_period(
            "2026-07"
        )
        == "Julho/2026"
    )


def test_budget_status_labels():
    assert (
        get_budget_status_label(
            "within_limit",
            50.0,
        )
        == "Dentro do limite"
    )

    assert (
        get_budget_status_label(
            "near_limit",
            85.0,
        )
        == "Próximo do limite"
    )

    assert (
        get_budget_status_label(
            "near_limit",
            100.0,
        )
        == "Limite atingido"
    )

    assert (
        get_budget_status_label(
            "over_limit",
            120.0,
        )
        == "Limite ultrapassado"
    )
    
def test_build_budget_dashboard_summary():
    transactions = pd.DataFrame(
        {
            "tipo": [
                "despesa",
                "despesa",
            ],
            "categoria": [
                "Alimentação",
                "Transporte",
            ],
            "valor": [
                350.0,
                100.0,
            ],
        }
    )

    budgets = [
        {
            "budget_id": "budget-1",
            "period": "2026-07",
            "category": "Alimentação",
            "planned_amount": 300.0,
        },
        {
            "budget_id": "budget-2",
            "period": "2026-07",
            "category": "Transporte",
            "planned_amount": 200.0,
        },
    ]

    summary = (
        build_budget_dashboard_summary(
            transactions=transactions,
            budgets=budgets,
        )
    )

    assert (
        summary["remaining_amount"]
        == 50.0
    )

    assert (
        summary["planned_categories"]
        == 2
    )

    assert (
        summary[
            "over_limit_categories"
        ]
        == [
            "Alimentação",
        ]
    )


def test_build_budget_dashboard_summary_without_limits():
    summary = (
        build_budget_dashboard_summary(
            transactions=pd.DataFrame(),
            budgets=[],
        )
    )

    assert summary == {
        "remaining_amount": 0.0,
        "over_limit_categories": [],
        "planned_categories": 0,
    }
    
def test_budget_category_options_combine_defaults_and_expenses():
    transactions = pd.DataFrame(
        {
            "tipo": [
                "despesa",
                "despesa",
                "despesa",
                "receita",
                "despesa",
            ],
            "categoria": [
                " Alimentação ",
                "Mercado",
                "Transporte",
                "Trabalho",
                "Reserva",
            ],
        }
    )

    categories = build_budget_category_options(
        transactions
    )

    assert "Alimentação" in categories
    assert "Mercado" in categories
    assert "Transporte" in categories
    assert "Moradia" in categories
    assert "Reserva" not in categories
    assert "Trabalho" not in categories

    assert categories.count(
        "Alimentação"
    ) == 1


def test_budget_category_options_use_defaults_without_transactions():
    categories = build_budget_category_options(
        pd.DataFrame()
    )

    assert categories == list(
        DEFAULT_BUDGET_CATEGORIES
    )


def test_resolve_budget_category_uses_selected_option():
    category = resolve_budget_category(
        selected_category=(
            "Alimentação"
        ),
        custom_category="",
    )

    assert category == "Alimentação"


def test_resolve_budget_category_prefers_custom_value():
    category = resolve_budget_category(
        selected_category=(
            "Alimentação"
        ),
        custom_category=(
            "  Saúde   Mental  "
        ),
    )

    assert category == "Saúde Mental"


def test_resolve_budget_category_rejects_empty_selection():
    category = resolve_budget_category(
        selected_category=(
            CATEGORY_PLACEHOLDER
        ),
        custom_category="",
    )

    assert category == ""