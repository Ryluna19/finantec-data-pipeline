"""Seleção e filtragem contextual de períodos."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from ui_components import MONTH_NAMES_PT_BR


ALL_MONTHS = 0


def _get_reference_date(
    reference_date: date | None = None,
) -> date:
    """Retorna a data usada como referência para os seletores."""
    return reference_date or date.today()


def _normalize_transaction_dates(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Converte datas válidas sem alterar o DataFrame recebido."""
    if transactions.empty:
        return transactions.copy()

    if "data" not in transactions.columns:
        return transactions.iloc[0:0].copy()

    normalized = transactions.copy()

    normalized["data"] = pd.to_datetime(
        normalized["data"],
        errors="coerce",
    )

    return normalized.dropna(
        subset=["data"],
    ).copy()


def build_period_year_options(
    transactions: pd.DataFrame,
    reference_date: date | None = None,
) -> list[int]:
    """Monta os anos disponíveis incluindo sempre o ano atual."""
    reference = _get_reference_date(
        reference_date
    )

    years = {
        reference.year,
    }

    normalized = _normalize_transaction_dates(
        transactions
    )

    if not normalized.empty:
        years.update(
            normalized["data"]
            .dt.year
            .astype(int)
            .tolist()
        )

    return sorted(
        years,
        reverse=True,
    )


def build_period_month_options(
    *,
    include_full_year: bool = True,
) -> list[int]:
    """Monta os meses do calendário, com opção de ano inteiro."""
    months = list(
        range(
            1,
            13,
        )
    )

    if include_full_year:
        return [
            ALL_MONTHS,
            *months,
        ]

    return months


def format_period_label(
    year: int,
    month: int,
) -> str:
    """Formata o período selecionado para exibição."""
    if month == ALL_MONTHS:
        return str(
            year
        )

    if month not in MONTH_NAMES_PT_BR:
        raise ValueError(
            "O mês informado deve estar entre 1 e 12."
        )

    return (
        f"{MONTH_NAMES_PT_BR[month]}"
        f"/{year}"
    )


def filter_transactions_by_period(
    transactions: pd.DataFrame,
    *,
    year: int,
    month: int,
) -> pd.DataFrame:
    """Filtra transações por ano e, opcionalmente, por mês."""
    if month not in {
        ALL_MONTHS,
        *range(
            1,
            13,
        ),
    }:
        raise ValueError(
            "O mês informado deve estar entre 0 e 12."
        )

    normalized = _normalize_transaction_dates(
        transactions
    )

    if normalized.empty:
        return normalized

    year_filter = (
        normalized["data"]
        .dt.year
        .eq(
            int(
                year
            )
        )
    )

    if month == ALL_MONTHS:
        return normalized.loc[
            year_filter
        ].copy()

    month_filter = (
        normalized["data"]
        .dt.month
        .eq(
            int(
                month
            )
        )
    )

    return normalized.loc[
        year_filter
        & month_filter
    ].copy()


def render_period_selector(
    transactions: pd.DataFrame,
    *,
    key_prefix: str,
    reference_date: date | None = None,
    include_full_year: bool = True,
) -> tuple[int, str, pd.DataFrame]:
    """Exibe um seletor local e retorna as transações do período."""
    reference = _get_reference_date(
        reference_date
    )

    years = build_period_year_options(
        transactions,
        reference_date=reference,
    )

    year_column, month_column = st.columns(
        2,
        gap="small",
    )

    selected_year = year_column.selectbox(
        "Ano",
        options=years,
        index=years.index(
            reference.year
        ),
        key=(
            f"{key_prefix}_year_filter"
        ),
    )

    months = build_period_month_options(
        include_full_year=include_full_year,
    )

    default_month = (
        reference.month
        if selected_year == reference.year
        else ALL_MONTHS
    )

    selected_month = month_column.selectbox(
        "Mês",
        options=months,
        index=months.index(
            default_month
        ),
        format_func=lambda value: (
            "Ano inteiro"
            if value == ALL_MONTHS
            else MONTH_NAMES_PT_BR[value]
        ),
        key=(
            f"{key_prefix}_month_filter"
        ),
    )

    period_label = format_period_label(
        int(
            selected_year
        ),
        int(
            selected_month
        ),
    )

    filtered_transactions = (
        filter_transactions_by_period(
            transactions,
            year=int(
                selected_year
            ),
            month=int(
                selected_month
            ),
        )
    )

    return (
        int(
            selected_month
        ),
        period_label,
        filtered_transactions,
    )