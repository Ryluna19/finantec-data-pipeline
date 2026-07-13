"""Testes dos cálculos usados pelo componente de metas."""

from __future__ import annotations

from components.goals import (
    build_goal_payload,
    calculate_estimated_months,
    calculate_goal_progress,
)


def test_calculate_goal_progress():
    assert (
        calculate_goal_progress(
            current_value=500.0,
            goal_value=2000.0,
        )
        == 25.0
    )


def test_goal_progress_is_limited_to_one_hundred():
    assert (
        calculate_goal_progress(
            current_value=3000.0,
            goal_value=2000.0,
        )
        == 100.0
    )


def test_goal_progress_handles_invalid_target():
    assert (
        calculate_goal_progress(
            current_value=500.0,
            goal_value=0.0,
        )
        == 0.0
    )


def test_calculate_estimated_months():
    assert (
        calculate_estimated_months(
            remaining_value=1000.0,
            monthly_amount=300.0,
        )
        == 4
    )


def test_estimated_months_for_completed_goal():
    assert (
        calculate_estimated_months(
            remaining_value=0.0,
            monthly_amount=300.0,
        )
        == 0
    )


def test_estimated_months_rejects_zero_monthly_amount():
    assert (
        calculate_estimated_months(
            remaining_value=1000.0,
            monthly_amount=0.0,
        )
        is None
    )


def test_build_goal_payload():
    payload = build_goal_payload(
        name="Viagem",
        target_amount=5000.0,
        current_amount=500.0,
        deadline_months=18,
        priority="alta",
    )

    assert payload == {
        "nome": "Viagem",
        "valor_meta": 5000.0,
        "valor_atual": 500.0,
        "prazo_meses": 18,
        "prioridade": "alta",
    }