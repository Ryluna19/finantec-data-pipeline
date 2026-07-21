"""Testes da persistência de metas financeiras."""

from __future__ import annotations

import calendar
import sqlite3
from datetime import date

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


def add_months(
    base_date: date,
    months: int,
) -> date:
    """Adiciona meses para montar datas estáveis nos testes."""
    month_index = (
        base_date.month
        - 1
        + months
    )

    target_year = (
        base_date.year
        + month_index // 12
    )

    target_month = (
        month_index % 12
        + 1
    )

    target_day = min(
        base_date.day,
        calendar.monthrange(
            target_year,
            target_month,
        )[1],
    )

    return date(
        target_year,
        target_month,
        target_day,
    )


def build_goal(
    name: str = "Comprar notebook",
) -> dict:
    """Cria uma meta válida para os testes."""
    return {
        "nome": name,
        "valor_meta": 3000.0,
        "valor_atual": 500.0,
        "data_limite": add_months(
            date.today(),
            10,
        ).isoformat(),
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

    assert (
        loaded["data_limite"]
        == add_months(
            date.today(),
            10,
        ).isoformat()
    )

    assert (
        loaded["prazo_meses"]
        == 10
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

    updated_payload[
        "data_limite"
    ] = add_months(
        date.today(),
        14,
    ).isoformat()

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

    assert (
        updated["data_limite"]
        == updated_payload[
            "data_limite"
        ]
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
                "data_limite": add_months(
                    date.today(),
                    12,
                ),
                "prioridade": "media",
            }
        )
    )

    assert (
        normalized["prioridade"]
        == "média"
    )

    assert (
        normalized["prazo_meses"]
        == 12
    )


def test_accepts_legacy_deadline_months():
    normalized = (
        normalize_financial_goal(
            {
                "nome": "Viagem",
                "valor_meta": 2000.0,
                "valor_atual": 0.0,
                "prazo_meses": 12,
                "prioridade": "média",
            }
        )
    )

    assert (
        normalized["data_limite"]
        == add_months(
            date.today(),
            12,
        ).isoformat()
    )

    assert (
        normalized["prazo_meses"]
        == 12
    )


def test_rejects_past_deadline():
    with pytest.raises(
        ValueError,
        match="não pode estar no passado",
    ):
        normalize_financial_goal(
            {
                "nome": "Viagem",
                "valor_meta": 2000.0,
                "valor_atual": 0.0,
                "data_limite": "2020-01-01",
                "prioridade": "média",
            }
        )


def test_migrates_legacy_goal_deadline(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.executescript(
            """
            CREATE TABLE financial_goals (
                goal_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                name_key TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL NOT NULL DEFAULT 0,
                deadline_months INTEGER NOT NULL,
                priority TEXT NOT NULL DEFAULT 'média',
                status TEXT NOT NULL DEFAULT 'active',
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (
                    user_id,
                    name_key
                )
            );

            CREATE TABLE financial_goal_seed_state (
                user_id TEXT PRIMARY KEY,
                seeded_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            );

            INSERT INTO financial_goals (
                goal_id,
                user_id,
                name,
                name_key,
                target_amount,
                current_amount,
                deadline_months,
                priority,
                status,
                sort_order,
                created_at
            )
            VALUES (
                'legacy-goal',
                'user-1',
                'Meta antiga',
                'meta antiga',
                3000,
                500,
                3,
                'média',
                'active',
                0,
                '2026-01-15 10:00:00'
            );
            """
        )

    loaded = list_financial_goals(
        database_path=database_path,
        user_id="user-1",
    )

    assert len(
        loaded
    ) == 1

    assert (
        loaded[0]["data_limite"]
        == "2026-04-15"
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(financial_goals)"
            ).fetchall()
        }

    assert "deadline_date" in columns


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