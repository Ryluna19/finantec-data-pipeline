"""Testes da persistência dos orçamentos mensais."""

from __future__ import annotations

import sqlite3

import pytest

import src.budget_repository as budget_repository
from src.budget_repository import (
    DuplicateMonthlyBudgetError,
    MonthlyBudgetNotFoundError,
    create_monthly_budget,
    delete_monthly_budget,
    get_monthly_budget,
    list_monthly_budget_periods,
    list_monthly_budgets,
    list_active_monthly_budgets,
    normalize_monthly_budget,
    split_monthly_budget_from_period,
    update_monthly_budget,
)


END_PERIOD_UNSET = object()


def build_budget(
    category: str = "Alimentação",
    period: str = "2026-07",
    planned_amount: float = 800.0,
    end_period: str | None | object = END_PERIOD_UNSET,
) -> dict:
    """Cria um orçamento válido para os testes."""
    budget = {
        "period": period,
        "category": category,
        "planned_amount": planned_amount,
    }

    if end_period is not END_PERIOD_UNSET:
        budget[
            "end_period"
        ] = end_period

    return budget


def test_create_and_load_budget(tmp_path):
    database_path = tmp_path / "finantec.db"

    created = create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(),
    )


    loaded = get_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget_id=created["budget_id"],
    )

    assert loaded == created
    assert loaded["category"] == "Alimentação"
    assert loaded["planned_amount"] == 800.0
    assert (
        loaded["end_period"]
        is None
    )


def test_lists_only_requested_period(tmp_path):
    database_path = tmp_path / "finantec.db"

    create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            category="Alimentação",
            period="2026-07",
        ),
    )

    create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            category="Transporte",
            period="2026-08",
        ),
    )

    july_budgets = list_monthly_budgets(
        database_path=database_path,
        user_id="user-1",
        period="2026-07",
    )

    assert len(july_budgets) == 1
    assert july_budgets[0]["category"] == "Alimentação"


def test_lists_distinct_budget_periods_for_user(tmp_path):
    database_path = tmp_path / "finantec.db"

    create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            category="Alimentação",
            period="2026-07",
        ),
    )

    create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            category="Transporte",
            period="2026-07",
        ),
    )

    create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            category="Moradia",
            period="2027-03",
        ),
    )

    create_monthly_budget(
        database_path=database_path,
        user_id="user-2",
        budget=build_budget(
            category="Lazer",
            period="2028-01",
        ),
    )

    periods = list_monthly_budget_periods(
        database_path=database_path,
        user_id="user-1",
    )

    assert periods == [
        "2027-03",
        "2026-07",
    ]


def test_update_budget(tmp_path):
    database_path = tmp_path / "finantec.db"

    created = create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(),
    )

    updated = update_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget_id=created["budget_id"],
        budget=build_budget(
            category="Mercado",
            planned_amount=950.0,
        ),
    )

    assert updated["category"] == "Mercado"
    assert updated["planned_amount"] == 950.0


def test_delete_budget(tmp_path):
    database_path = tmp_path / "finantec.db"

    created = create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(),
    )

    deleted = delete_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget_id=created["budget_id"],
    )

    assert deleted is True
    assert (
        get_monthly_budget(
            database_path=database_path,
            user_id="user-1",
            budget_id=created["budget_id"],
        )
        is None
    )


def test_budgets_are_isolated_by_user(tmp_path):
    database_path = tmp_path / "finantec.db"

    create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            category="Alimentação",
        ),
    )

    create_monthly_budget(
        database_path=database_path,
        user_id="user-2",
        budget=build_budget(
            category="Transporte",
        ),
    )

    first_user_budgets = list_monthly_budgets(
        database_path=database_path,
        user_id="user-1",
        period="2026-07",
    )

    second_user_budgets = list_monthly_budgets(
        database_path=database_path,
        user_id="user-2",
        period="2026-07",
    )

    assert len(first_user_budgets) == 1
    assert first_user_budgets[0]["category"] == "Alimentação"
    assert second_user_budgets[0]["category"] == "Transporte"


def test_rejects_duplicate_category_in_period(tmp_path):
    database_path = tmp_path / "finantec.db"

    create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            category="Alimentação",
        ),
    )

    with pytest.raises(
        DuplicateMonthlyBudgetError,
        match="Já existe",
    ):
        create_monthly_budget(
            database_path=database_path,
            user_id="user-1",
            budget=build_budget(
                category="  ALIMENTACAO  ",
            ),
        )


def test_allows_same_category_after_previous_budget_ends(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    first = create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            period="2026-07",
            end_period="2026-07",
        ),
    )

    second = create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            period="2026-08",
        ),
    )

    assert (
        first["end_period"]
        == "2026-07"
    )

    assert (
        second["period"]
        == "2026-08"
    )

    assert (
        second["end_period"]
        is None
    )

def test_lists_continuous_budget_in_future_periods(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            period="2026-07",
        ),
    )

    september_budgets = (
        list_active_monthly_budgets(
            database_path=database_path,
            user_id="user-1",
            period="2026-09",
        )
    )

    assert len(
        september_budgets
    ) == 1

    assert (
        september_budgets[0]["category"]
        == "Alimentação"
    )

    assert (
        september_budgets[0]["end_period"]
        is None
    )


def test_temporary_budget_stops_after_end_period(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            period="2026-07",
            end_period="2026-08",
        ),
    )

    august_budgets = (
        list_active_monthly_budgets(
            database_path=database_path,
            user_id="user-1",
            period="2026-08",
        )
    )

    september_budgets = (
        list_active_monthly_budgets(
            database_path=database_path,
            user_id="user-1",
            period="2026-09",
        )
    )

    assert len(
        august_budgets
    ) == 1

    assert september_budgets == []


def test_rejects_overlapping_budget_for_same_category(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            period="2026-07",
        ),
    )

    with pytest.raises(
        DuplicateMonthlyBudgetError,
        match="sobreposta",
    ):
        create_monthly_budget(
            database_path=database_path,
            user_id="user-1",
            budget=build_budget(
                period="2026-08",
            ),
        )


def test_rejects_end_period_before_start_period():
    with pytest.raises(
        ValueError,
        match="anterior",
    ):
        normalize_monthly_budget(
            build_budget(
                period="2026-07",
                end_period="2026-06",
            )
        )


def test_update_preserves_end_period_when_not_provided(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    created = create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            period="2026-07",
            end_period="2026-09",
        ),
    )

    updated = update_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget_id=created["budget_id"],
        budget=build_budget(
            period="2026-07",
            planned_amount=950.0,
        ),
    )

    assert (
        updated["end_period"]
        == "2026-09"
    )

    assert (
        updated["planned_amount"]
        == 950.0
    )


def test_migrates_existing_budget_as_single_month(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            """
            CREATE TABLE monthly_budgets (
                budget_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                period TEXT NOT NULL,
                category TEXT NOT NULL,
                category_key TEXT NOT NULL,
                planned_amount REAL NOT NULL,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (
                    user_id,
                    period,
                    category_key
                )
            )
            """
        )

        connection.execute(
            """
            INSERT INTO monthly_budgets (
                budget_id,
                user_id,
                period,
                category,
                category_key,
                planned_amount
            )
            VALUES (
                ?, ?, ?, ?, ?, ?
            )
            """,
            (
                "legacy-budget",
                "user-1",
                "2026-07",
                "Alimentação",
                "alimentacao",
                800.0,
            ),
        )

    july_budgets = (
        list_active_monthly_budgets(
            database_path=database_path,
            user_id="user-1",
            period="2026-07",
        )
    )

    august_budgets = (
        list_active_monthly_budgets(
            database_path=database_path,
            user_id="user-1",
            period="2026-08",
        )
    )

    assert len(
        july_budgets
    ) == 1

    assert (
        july_budgets[0]["end_period"]
        == "2026-07"
    )

    assert august_budgets == []

@pytest.mark.parametrize(
    "period",
    [
        "",
        "2026",
        "2026-7",
        "2026-00",
        "2026-13",
        "julho-2026",
    ],
)
def test_rejects_invalid_period(
    period,
):
    with pytest.raises(
        ValueError,
        match="AAAA-MM",
    ):
        normalize_monthly_budget(
            build_budget(
                period=period,
            )
        )


@pytest.mark.parametrize(
    "planned_amount",
    [
        0,
        -1,
        "invalid",
        float("nan"),
        float("inf"),
    ],
)
def test_rejects_invalid_planned_amount(planned_amount):
    with pytest.raises(ValueError):
        normalize_monthly_budget(
            build_budget(
                planned_amount=planned_amount,
            )
        )


def test_rejects_reserve_category():
    with pytest.raises(
        ValueError,
        match="Reserva",
    ):
        normalize_monthly_budget(
            build_budget(
                category="reserva",
            )
        )


def test_update_missing_budget_raises_error(tmp_path):
    database_path = tmp_path / "finantec.db"

    with pytest.raises(
        MonthlyBudgetNotFoundError,
        match="não foi encontrado",
    ):
        update_monthly_budget(
            database_path=database_path,
            user_id="user-1",
            budget_id="missing-budget",
            budget=build_budget(),
        )

def test_split_continuous_budget_preserves_previous_months(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    created = create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            period="2026-07",
        ),
    )

    new_budget = (
        split_monthly_budget_from_period(
            database_path=database_path,
            user_id="user-1",
            budget_id=created["budget_id"],
            split_period="2026-09",
            budget=build_budget(
                period="2026-09",
                planned_amount=950.0,
            ),
        )
    )

    previous_budget = get_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget_id=created["budget_id"],
    )

    assert previous_budget is not None
    assert (
        previous_budget["period"]
        == "2026-07"
    )
    assert (
        previous_budget["end_period"]
        == "2026-08"
    )

    assert (
        new_budget["period"]
        == "2026-09"
    )
    assert (
        new_budget["end_period"]
        is None
    )
    assert (
        new_budget["planned_amount"]
        == 950.0
    )

    august_budgets = (
        list_active_monthly_budgets(
            database_path=database_path,
            user_id="user-1",
            period="2026-08",
        )
    )

    september_budgets = (
        list_active_monthly_budgets(
            database_path=database_path,
            user_id="user-1",
            period="2026-09",
        )
    )

    assert (
        august_budgets[0]["budget_id"]
        == created["budget_id"]
    )
    assert (
        september_budgets[0]["budget_id"]
        == new_budget["budget_id"]
    )


def test_split_temporary_budget_preserves_original_end_when_omitted(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    created = create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            period="2026-07",
            end_period="2026-12",
        ),
    )

    new_budget = (
        split_monthly_budget_from_period(
            database_path=database_path,
            user_id="user-1",
            budget_id=created["budget_id"],
            split_period="2026-10",
            budget=build_budget(
                period="2026-10",
                planned_amount=900.0,
            ),
        )
    )

    previous_budget = get_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget_id=created["budget_id"],
    )

    assert previous_budget is not None
    assert (
        previous_budget["end_period"]
        == "2026-09"
    )
    assert (
        new_budget["end_period"]
        == "2026-12"
    )


@pytest.mark.parametrize(
    "split_period",
    [
        "2026-06",
        "2026-07",
    ],
)
def test_split_rejects_period_before_or_equal_to_start(
    tmp_path,
    split_period,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    created = create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            period="2026-07",
        ),
    )

    with pytest.raises(
        ValueError,
        match="posterior",
    ):
        split_monthly_budget_from_period(
            database_path=database_path,
            user_id="user-1",
            budget_id=created["budget_id"],
            split_period=split_period,
            budget=build_budget(
                period=split_period,
            ),
        )


def test_split_rejects_period_after_temporary_budget_ends(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    created = create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            period="2026-07",
            end_period="2026-09",
        ),
    )

    with pytest.raises(
        ValueError,
        match="fora da vigência",
    ):
        split_monthly_budget_from_period(
            database_path=database_path,
            user_id="user-1",
            budget_id=created["budget_id"],
            split_period="2026-10",
            budget=build_budget(
                period="2026-10",
            ),
        )


def test_split_rolls_back_when_new_rule_cannot_be_created(
    tmp_path,
    monkeypatch,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    created = create_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget=build_budget(
            period="2026-07",
        ),
    )

    monkeypatch.setattr(
        budget_repository,
        "uuid4",
        lambda: created["budget_id"],
    )

    with pytest.raises(
        DuplicateMonthlyBudgetError,
        match="conflito",
    ):
        split_monthly_budget_from_period(
            database_path=database_path,
            user_id="user-1",
            budget_id=created["budget_id"],
            split_period="2026-09",
            budget=build_budget(
                period="2026-09",
                planned_amount=950.0,
            ),
        )

    unchanged_budget = get_monthly_budget(
        database_path=database_path,
        user_id="user-1",
        budget_id=created["budget_id"],
    )

    assert unchanged_budget is not None
    assert (
        unchanged_budget["end_period"]
        is None
    )

    september_budgets = (
        list_active_monthly_budgets(
            database_path=database_path,
            user_id="user-1",
            period="2026-09",
        )
    )

    assert len(
        september_budgets
    ) == 1
    assert (
        september_budgets[0]["budget_id"]
        == created["budget_id"]
    )