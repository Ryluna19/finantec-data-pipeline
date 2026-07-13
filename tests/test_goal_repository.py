"""Testes da persistência de metas financeiras."""

from __future__ import annotations

import pytest

from src.goal_repository import (
    DuplicateFinancialGoalError,
    FinancialGoalNotFoundError,
    create_financial_goal,
    delete_financial_goal,
    get_financial_goal,
    list_financial_goals,
    normalize_financial_goal,
    seed_financial_goals_if_needed,
    update_financial_goal,
)


def build_goal(
    name: str = "Comprar notebook",
) -> dict:
    """Cria uma meta válida para os testes."""
    return {
        "nome": name,
        "valor_meta": 3000.0,
        "valor_atual": 500.0,
        "prazo_meses": 10,
        "prioridade": "alta",
    }


def test_create_and_load_goal(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    created = create_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal=build_goal(),
    )

    loaded = get_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal_id=created["goal_id"],
    )

    assert loaded == created

    assert (
        loaded["nome"]
        == "Comprar notebook"
    )

    assert (
        loaded["status"]
        == "active"
    )


def test_update_goal(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    created = create_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal=build_goal(),
    )

    updated_payload = build_goal(
        "Notebook profissional"
    )

    updated_payload[
        "valor_atual"
    ] = 3000.0

    updated = update_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal_id=created["goal_id"],
        goal=updated_payload,
    )

    assert (
        updated["nome"]
        == "Notebook profissional"
    )

    assert (
        updated["status"]
        == "completed"
    )


def test_delete_goal(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    created = create_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal=build_goal(),
    )

    deleted = delete_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal_id=created["goal_id"],
    )

    assert deleted is True

    assert (
        get_financial_goal(
            database_path=database_path,
            user_id="user-1",
            goal_id=created["goal_id"],
        )
        is None
    )


def test_goals_are_isolated_by_user(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    create_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal=build_goal(
            "Meta do primeiro usuário"
        ),
    )

    create_financial_goal(
        database_path=database_path,
        user_id="user-2",
        goal=build_goal(
            "Meta do segundo usuário"
        ),
    )

    first_user_goals = (
        list_financial_goals(
            database_path=database_path,
            user_id="user-1",
        )
    )

    second_user_goals = (
        list_financial_goals(
            database_path=database_path,
            user_id="user-2",
        )
    )

    assert len(
        first_user_goals
    ) == 1

    assert (
        first_user_goals[0]["nome"]
        == "Meta do primeiro usuário"
    )

    assert (
        second_user_goals[0]["nome"]
        == "Meta do segundo usuário"
    )


def test_rejects_duplicate_goal_name(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    create_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal=build_goal(
            "Viagem"
        ),
    )

    with pytest.raises(
        DuplicateFinancialGoalError,
        match="Já existe",
    ):
        create_financial_goal(
            database_path=database_path,
            user_id="user-1",
            goal=build_goal(
                "  viagem  "
            ),
        )


def test_seed_goals_only_once(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    seeded_goals = (
        seed_financial_goals_if_needed(
            database_path=database_path,
            user_id="user-1",
            seed_goals=[
                build_goal(
                    "Reserva"
                ),
                build_goal(
                    "Notebook"
                ),
            ],
        )
    )

    assert len(
        seeded_goals
    ) == 2

    for goal in seeded_goals:
        delete_financial_goal(
            database_path=database_path,
            user_id="user-1",
            goal_id=goal["goal_id"],
        )

    second_seed = (
        seed_financial_goals_if_needed(
            database_path=database_path,
            user_id="user-1",
            seed_goals=[
                build_goal(
                    "Reserva"
                ),
                build_goal(
                    "Notebook"
                ),
            ],
        )
    )

    assert second_seed == []


def test_update_missing_goal_raises_error(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    with pytest.raises(
        FinancialGoalNotFoundError,
        match="não foi encontrada",
    ):
        update_financial_goal(
            database_path=database_path,
            user_id="user-1",
            goal_id="missing-goal",
            goal=build_goal(),
        )


def test_normalizes_medium_priority():
    normalized = (
        normalize_financial_goal(
            {
                "nome": "Viagem",
                "valor_meta": 2000.0,
                "valor_atual": 0.0,
                "prazo_meses": 12,
                "prioridade": "media",
            }
        )
    )

    assert (
        normalized["prioridade"]
        == "média"
    )


def test_rejects_invalid_values():
    goal = build_goal()

    goal["valor_meta"] = 0

    with pytest.raises(
        ValueError,
        match="maior que zero",
    ):
        normalize_financial_goal(
            goal
        )