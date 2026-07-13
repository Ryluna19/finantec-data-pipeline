"""Testes dos dados usados pelo componente de perfil."""

from __future__ import annotations

import pandas as pd
import pytest

from components.profile import (
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