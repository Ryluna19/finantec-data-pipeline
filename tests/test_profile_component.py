"""Testes dos dados usados pelo componente de perfil."""

from __future__ import annotations

from contextlib import nullcontext

import pandas as pd
import pytest

import components.profile as profile_module

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


class ProfileRenderStreamlit:
    """Registra os controles dos estados resumidos do perfil."""

    def __init__(
        self,
    ) -> None:
        self.session_state: dict = {}
        self.markdowns: list[str] = []
        self.infos: list[str] = []
        self.buttons: list[str] = []

    def subheader(
        self,
        *_args,
        **_kwargs,
    ) -> None:
        return None

    def caption(
        self,
        *_args,
        **_kwargs,
    ) -> None:
        return None

    def info(
        self,
        message: str,
    ) -> None:
        self.infos.append(
            message
        )

    def markdown(
        self,
        text: str,
    ) -> None:
        self.markdowns.append(
            text
        )

    def container(
        self,
        **_kwargs,
    ):
        return nullcontext()

    def button(
        self,
        label: str,
        *_args,
        **_kwargs,
    ) -> bool:
        self.buttons.append(
            label
        )
        return False


def test_unconfigured_profile_has_dedicated_state_without_summary_metrics(
    monkeypatch,
) -> None:
    fake_streamlit = (
        ProfileRenderStreamlit()
    )
    rendered_summaries: list[dict] = []

    monkeypatch.setattr(
        profile_module,
        "st",
        fake_streamlit,
    )
    monkeypatch.setattr(
        profile_module,
        "_show_profile_feedback",
        lambda: None,
    )
    monkeypatch.setattr(
        profile_module,
        "_render_profile_summary",
        rendered_summaries.append,
    )

    profile_module.render_user_profile(
        {
            "user_id": "user-1",
            "objetivos_financeiros": [],
        },
        user_id="user-1",
        data_mode="user",
    )

    assert fake_streamlit.markdowns == [
        "### Perfil não configurado",
    ]
    assert fake_streamlit.buttons == [
        "Configurar perfil",
    ]
    assert rendered_summaries == []


def test_demo_profile_is_read_only_even_with_edit_mode_pending(
    monkeypatch,
) -> None:
    fake_streamlit = (
        ProfileRenderStreamlit()
    )
    fake_streamlit.session_state[
        profile_module.PROFILE_EDIT_MODE_KEY
    ] = True

    rendered_summaries: list[dict] = []

    monkeypatch.setattr(
        profile_module,
        "st",
        fake_streamlit,
    )
    monkeypatch.setattr(
        profile_module,
        "_show_profile_feedback",
        lambda: None,
    )
    monkeypatch.setattr(
        profile_module,
        "_render_profile_summary",
        rendered_summaries.append,
    )

    demo_profile = {
        "nome": "Marina Costa",
        "objetivos_financeiros": [],
    }

    profile_module.render_user_profile(
        demo_profile,
        user_id="user-1",
        data_mode="demo",
    )

    assert rendered_summaries == [
        demo_profile,
    ]
    assert fake_streamlit.buttons == []
    assert fake_streamlit.infos == [
        "Perfil de demonstração. "
        "Estas informações são fictícias e somente leitura.",
    ]
