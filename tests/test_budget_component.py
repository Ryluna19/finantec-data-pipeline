"""Testes do componente de orçamento mensal."""

from __future__ import annotations

import pandas as pd

from src.components.budget import (
    _find_budget,
    build_budget_dashboard_summary,
    build_budget_payload,
    build_budget_period_options,
    format_budget_period,
    get_budget_status_label,
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


def test_budget_period_options_work_without_transactions():
    periods = (
        build_budget_period_options(
            pd.DataFrame(),
            reference_period="2026-07",
        )
    )

    assert periods == [
        "2026-07",
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