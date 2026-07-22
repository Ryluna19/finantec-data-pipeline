"""Testes do componente de orçamento mensal."""

from __future__ import annotations

import pandas as pd
import pytest

from src.components.budget import (
    CATEGORY_PLACEHOLDER,
    DEFAULT_BUDGET_CATEGORIES,
    _find_budget,
    build_budget_card_html,
    build_budget_summary_html,
    build_budget_category_options,
    build_budget_dashboard_summary,
    build_budget_end_period_options,
    build_budget_payload,
    build_budget_removal_dialog_copy,
    build_budget_period_options,
    format_budget_period,
    format_budget_validity,
    get_budget_status_label,
    is_budget_inherited_period,
    resolve_budget_category,
)


def test_budget_period_options_include_future_and_existing_months():
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

    periods = build_budget_period_options(
        transactions,
        budget_periods=[
            "2025-10",
            "2027-09",
        ],
        reference_period="2026-07",
        future_months=2,
    )

    assert periods == [
        "2026-07",
        "2026-08",
        "2026-09",
        "2027-09",
        "2026-06",
        "2026-05",
        "2025-10",
    ]


def test_budget_period_options_work_without_transactions_or_budgets():
    periods = build_budget_period_options(
        pd.DataFrame(),
        reference_period="2026-12",
        future_months=2,
    )

    assert periods == [
        "2026-12",
        "2027-01",
        "2027-02",
    ]


def test_budget_period_options_reject_negative_future_horizon():
    with pytest.raises(
        ValueError,
        match="não pode ser negativa",
    ):
        build_budget_period_options(
            pd.DataFrame(),
            reference_period="2026-07",
            future_months=-1,
        )


def test_budget_end_period_options_include_start_and_future_months():
    periods = build_budget_end_period_options(
        "2026-11",
        future_months=3,
    )

    assert periods == [
        "2026-11",
        "2026-12",
        "2027-01",
        "2027-02",
    ]


def test_budget_end_period_options_keep_existing_end_outside_horizon():
    periods = build_budget_end_period_options(
        "2026-07",
        current_end_period="2027-12",
        future_months=2,
    )

    assert periods == [
        "2026-07",
        "2026-08",
        "2026-09",
        "2027-12",
    ]


def test_budget_end_period_options_reject_negative_future_horizon():
    with pytest.raises(
        ValueError,
        match="não pode ser negativa",
    ):
        build_budget_end_period_options(
            "2026-07",
            future_months=-1,
        )


def test_build_budget_payload_defaults_to_continuous():
    payload = build_budget_payload(
        period="2026-07",
        category="Alimentação",
        planned_amount=800.0,
    )

    assert payload == {
        "period": "2026-07",
        "end_period": None,
        "category": "Alimentação",
        "planned_amount": 800.0,
    }


def test_build_budget_payload_accepts_temporary_end_period():
    payload = build_budget_payload(
        period="2026-07",
        end_period="2026-12",
        category="Alimentação",
        planned_amount=800.0,
    )

    assert payload == {
        "period": "2026-07",
        "end_period": "2026-12",
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


def test_formats_continuous_budget_validity():
    validity = format_budget_validity(
        start_period="2026-07",
        end_period=None,
    )

    assert validity == (
        "Contínuo desde Julho/2026"
    )


def test_formats_single_month_budget_validity():
    validity = format_budget_validity(
        start_period="2026-07",
        end_period="2026-07",
    )

    assert validity == (
        "Temporário · somente Julho/2026"
    )


def test_formats_temporary_budget_validity():
    validity = format_budget_validity(
        start_period="2026-07",
        end_period="2026-12",
    )

    assert validity == (
        "Temporário · Julho/2026 até Dezembro/2026"
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


def test_build_budget_card_html_uses_compact_financial_summary():
    html = build_budget_card_html(
        category="Educação",
        validity_label=(
            "Contínuo desde Julho/2026"
        ),
        status="within_limit",
        planned_amount=400.0,
        spent_amount=0.0,
        remaining_amount=400.0,
        usage_percentage=0.0,
    )

    assert "Educação" in html
    assert "Contínuo desde Julho/2026" in html
    assert "Dentro do limite" in html
    assert "R$ 0,00" in html
    assert "R$ 400,00" in html
    assert "Disponível" in html
    assert "0.0%" in html
    assert "finantec-budget-card-body" in html


def test_build_budget_card_html_escapes_category_text():
    html = build_budget_card_html(
        category="<script>alert('x')</script>",
        validity_label="Contínuo",
        status="within_limit",
        planned_amount=100.0,
        spent_amount=20.0,
        remaining_amount=80.0,
        usage_percentage=20.0,
    )

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_build_budget_summary_html_uses_single_compact_panel():
    html = build_budget_summary_html(
        {
            "total_planned": 1100.0,
            "total_spent": 130.0,
            "total_remaining": 970.0,
            "categories_over_limit": 1,
        }
    )

    assert html.count(
        "finantec-budget-summary-item"
    ) == 4
    assert "finantec-budget-summary-panel" in html
    assert "Planejado" in html
    assert "Gasto" in html
    assert "Disponível" in html
    assert "Acima do limite" in html
    assert "R$ 1.100,00" in html
    assert "R$ 130,00" in html
    assert "R$ 970,00" in html
    assert 'class="finantec-budget-summary-item danger"' in html


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
            "end_period": None,
            "category": "Alimentação",
            "planned_amount": 300.0,
        },
        {
            "budget_id": "budget-2",
            "period": "2026-07",
            "end_period": "2026-07",
            "category": "Transporte",
            "planned_amount": 200.0,
        },
    ]

    summary = build_budget_dashboard_summary(
        transactions=transactions,
        budgets=budgets,
    )

    assert summary["remaining_amount"] == 50.0
    assert summary["planned_categories"] == 2
    assert summary["over_limit_categories"] == [
        "Alimentação",
    ]


def test_build_budget_dashboard_summary_without_limits():
    summary = build_budget_dashboard_summary(
        transactions=pd.DataFrame(),
        budgets=[],
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
    assert categories.count("Alimentação") == 1


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
    )

    assert category == "Alimentação"


def test_resolve_budget_category_rejects_empty_selection():
    category = resolve_budget_category(
        selected_category=(
            CATEGORY_PLACEHOLDER
        ),
    )

    assert category == ""


def test_build_budget_removal_dialog_copy_for_delete():
    copy = build_budget_removal_dialog_copy(
        category="Compras",
        is_inherited_period=False,
        selected_period="2026-07",
    )

    assert copy == {
        "title": "Excluir limite",
        "question": (
            "Deseja excluir o limite de “Compras”?"
        ),
        "description": (
            "Essa ação não pode ser desfeita."
        ),
        "confirm_label": "Sim, excluir",
    }


def test_build_budget_removal_dialog_copy_for_end():
    copy = build_budget_removal_dialog_copy(
        category="Educação",
        is_inherited_period=True,
        selected_period="2026-09",
    )

    assert copy == {
        "title": "Encerrar limite",
        "question": (
            "Deseja encerrar o limite de “Educação” "
            "a partir de Setembro/2026?"
        ),
        "description": (
            "Os meses anteriores serão preservados."
        ),
        "confirm_label": "Sim, encerrar",
    }


def test_budget_period_is_inherited_when_started_before_selected_month():
    assert is_budget_inherited_period(
        start_period="2026-07",
        selected_period="2026-09",
    ) is True


def test_budget_period_is_not_inherited_in_start_month():
    assert is_budget_inherited_period(
        start_period="2026-07",
        selected_period="2026-07",
    ) is False