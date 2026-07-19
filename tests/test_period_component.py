"""Testes do componente compartilhado de períodos."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from src.components.period import (
    ALL_MONTHS,
    build_period_month_options,
    build_period_year_options,
    filter_transactions_by_period,
    format_period_label,
)


REFERENCE_DATE = date(
    2026,
    7,
    19,
)


def test_period_year_options_include_current_and_transaction_years():
    transactions = pd.DataFrame(
        {
            "data": [
                "2024-05-10",
                "2025-12-20",
                "data inválida",
            ],
        }
    )

    years = build_period_year_options(
        transactions,
        reference_date=REFERENCE_DATE,
    )

    assert years == [
        2026,
        2025,
        2024,
    ]


def test_period_year_options_work_without_transactions():
    years = build_period_year_options(
        pd.DataFrame(),
        reference_date=REFERENCE_DATE,
    )

    assert years == [
        2026,
    ]


def test_period_month_options_include_full_year_and_calendar():
    months = build_period_month_options()

    assert months == [
        ALL_MONTHS,
        *range(
            1,
            13,
        ),
    ]


def test_period_month_options_can_hide_full_year():
    months = build_period_month_options(
        include_full_year=False,
    )

    assert months == list(
        range(
            1,
            13,
        )
    )


def test_format_period_label():
    assert (
        format_period_label(
            2026,
            ALL_MONTHS,
        )
        == "2026"
    )

    assert (
        format_period_label(
            2026,
            7,
        )
        == "Julho/2026"
    )


def test_format_period_label_rejects_invalid_month():
    with pytest.raises(
        ValueError,
    ):
        format_period_label(
            2026,
            13,
        )


def test_filter_transactions_by_month():
    transactions = pd.DataFrame(
        {
            "data": [
                "2026-06-01",
                "2026-07-01",
                "2025-07-01",
            ],
            "descricao": [
                "Junho",
                "Julho",
                "Ano anterior",
            ],
        }
    )

    result = filter_transactions_by_period(
        transactions,
        year=2026,
        month=7,
    )

    assert result[
        "descricao"
    ].tolist() == [
        "Julho",
    ]


def test_filter_transactions_by_full_year():
    transactions = pd.DataFrame(
        {
            "data": [
                "2026-01-01",
                "2026-07-01",
                "2025-07-01",
            ],
            "descricao": [
                "Janeiro",
                "Julho",
                "Ano anterior",
            ],
        }
    )

    result = filter_transactions_by_period(
        transactions,
        year=2026,
        month=ALL_MONTHS,
    )

    assert result[
        "descricao"
    ].tolist() == [
        "Janeiro",
        "Julho",
    ]


def test_filter_transactions_without_date_column_returns_empty():
    transactions = pd.DataFrame(
        {
            "descricao": [
                "Sem data",
            ],
        }
    )

    result = filter_transactions_by_period(
        transactions,
        year=2026,
        month=7,
    )

    assert result.empty
    assert list(
        result.columns
    ) == [
        "descricao",
    ]


def test_filter_transactions_rejects_invalid_month():
    with pytest.raises(
        ValueError,
    ):
        filter_transactions_by_period(
            pd.DataFrame(),
            year=2026,
            month=13,
        )