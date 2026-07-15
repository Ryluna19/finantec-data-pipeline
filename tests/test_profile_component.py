"""Testes dos dados usados pelo componente de perfil."""

from __future__ import annotations

import pandas as pd
import pytest

from components.profile import (
    calculate_monthly_income,
    income_sources_to_dataframe,
    prepare_income_sources,
)


def test_income_sources_to_dataframe():
    profile = {
        "fontes_de_renda": [
            {
                "tipo": "Estágio",
                "valor_mensal": 1600.0,
            },
            {
                "tipo": "Freelance",
                "valor_mensal": 400.0,
            },
        ]
    }

    result = (
        income_sources_to_dataframe(
            profile
        )
    )

    assert result.to_dict(
        orient="records"
    ) == [
        {
            "Tipo": "Estágio",
            "Valor mensal": 1600.0,
        },
        {
            "Tipo": "Freelance",
            "Valor mensal": 400.0,
        },
    ]


def test_income_sources_to_dataframe_uses_saved_income_as_fallback():
    profile = {
        "renda_mensal_principal": 1800.0,
        "fontes_de_renda": [],
    }

    result = (
        income_sources_to_dataframe(
            profile
        )
    )

    assert result.to_dict(
        orient="records"
    ) == [
        {
            "Tipo": "Renda principal",
            "Valor mensal": 1800.0,
        }
    ]


def test_prepare_income_sources_ignores_empty_rows():
    table = pd.DataFrame(
        [
            {
                "Tipo": "Trabalho",
                "Valor mensal": 2500.0,
            },
            {
                "Tipo": "",
                "Valor mensal": None,
            },
        ]
    )

    result = prepare_income_sources(
        table
    )

    assert result == [
        {
            "tipo": "Trabalho",
            "valor_mensal": 2500.0,
        }
    ]


def test_prepare_income_sources_rejects_missing_type():
    table = pd.DataFrame(
        [
            {
                "Tipo": "",
                "Valor mensal": 500.0,
            }
        ]
    )

    with pytest.raises(
        ValueError,
        match="Informe o tipo",
    ):
        prepare_income_sources(
            table
        )


def test_prepare_income_sources_rejects_negative_value():
    table = pd.DataFrame(
        [
            {
                "Tipo": "Freelance",
                "Valor mensal": -100.0,
            }
        ]
    )

    with pytest.raises(
        ValueError,
        match="não pode ser negativo",
    ):
        prepare_income_sources(
            table
        )


def test_calculate_monthly_income_sums_sources():
    table = pd.DataFrame(
        [
            {
                "Tipo": "Estágio",
                "Valor mensal": 1600.0,
            },
            {
                "Tipo": "Freelance",
                "Valor mensal": 400.0,
            },
        ]
    )

    result = calculate_monthly_income(
        table
    )

    assert result == 2000.0


def test_calculate_monthly_income_returns_zero_for_empty_table():
    table = pd.DataFrame(
        columns=[
            "Tipo",
            "Valor mensal",
        ]
    )

    result = calculate_monthly_income(
        table
    )

    assert result == 0.0