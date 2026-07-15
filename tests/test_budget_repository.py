"""Testes da persistência dos orçamentos mensais."""

from __future__ import annotations

import pytest

from src.budget_repository import (
    DuplicateMonthlyBudgetError,
    MonthlyBudgetNotFoundError,
    create_monthly_budget,
    delete_monthly_budget,
    get_monthly_budget,
    list_monthly_budgets,
    normalize_monthly_budget,
    update_monthly_budget,
)


def build_budget(
    category: str = "Alimentação",
    period: str = "2026-07",
    planned_amount: float = 800.0,
) -> dict:
    """Cria um orçamento válido para os testes."""
    return {
        "period": period,
        "category": category,
        "planned_amount": planned_amount,
    }


def test_create_and_load_budget(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

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

    assert (
        loaded["category"]
        == "Alimentação"
    )

    assert (
        loaded["planned_amount"]
        == 800.0
    )


def test_lists_only_requested_period(
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

    assert len(
        july_budgets
    ) == 1

    assert (
        july_budgets[0]["category"]
        == "Alimentação"
    )


def test_update_budget(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

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

    assert (
        updated["category"]
        == "Mercado"
    )

    assert (
        updated["planned_amount"]
        == 950.0
    )


def test_delete_budget(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

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


def test_budgets_are_isolated_by_user(
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

    first_user_budgets = (
        list_monthly_budgets(
            database_path=database_path,
            user_id="user-1",
            period="2026-07",
        )
    )

    second_user_budgets = (
        list_monthly_budgets(
            database_path=database_path,
            user_id="user-2",
            period="2026-07",
        )
    )

    assert len(
        first_user_budgets
    ) == 1

    assert (
        first_user_budgets[0]["category"]
        == "Alimentação"
    )

    assert (
        second_user_budgets[0]["category"]
        == "Transporte"
    )


def test_rejects_duplicate_category_in_period(
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


def test_allows_same_category_in_different_period(
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
        first["period"]
        == "2026-07"
    )

    assert (
        second["period"]
        == "2026-08"
    )


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
def test_rejects_invalid_planned_amount(
    planned_amount,
):
    with pytest.raises(
        ValueError,
    ):
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


def test_update_missing_budget_raises_error(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

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