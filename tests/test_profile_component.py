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
        self.captions: list[str] = []
        self.metrics: list[
            tuple[str, object]
        ] = []

    def subheader(
        self,
        *_args,
        **_kwargs,
    ) -> None:
        return None

    def caption(
        self,
        message: str,
        **_kwargs,
    ) -> None:
        self.captions.append(
            message
        )

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

    def metric(
        self,
        label: str,
        value: object,
        **_kwargs,
    ) -> None:
        self.metrics.append(
            (
                label,
                value,
            )
        )


class ProfileCacheData:
    """Registra a limpeza do cache após salvar o perfil."""

    def __init__(
        self,
    ) -> None:
        self.clear_calls = 0

    def clear(
        self,
    ) -> None:
        self.clear_calls += 1


class ProfileEditStreamlit(
    ProfileRenderStreamlit
):
    """Simula o formulário público reduzido do perfil."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.session_state[
            profile_module.PROFILE_EDIT_MODE_KEY
        ] = True
        self.cache_data = (
            ProfileCacheData()
        )
        self.text_inputs: list[str] = []
        self.text_input_limits: list[
            int | None
        ] = []
        self.legacy_controls: list[str] = []
        self.rerun_calls = 0
        self.errors: list[str] = []

    def form(
        self,
        *_args,
        **_kwargs,
    ):
        return nullcontext()

    def columns(
        self,
        specification,
        **_kwargs,
    ):
        column_count = (
            specification
            if isinstance(
                specification,
                int,
            )
            else len(
                specification
            )
        )

        return tuple(
            nullcontext()
            for _ in range(
                column_count
            )
        )

    def text_input(
        self,
        label: str,
        **_kwargs,
    ) -> str:
        self.text_inputs.append(
            label
        )
        self.text_input_limits.append(
            _kwargs.get(
                "max_chars"
            )
        )
        return "Ryan atualizado"

    def form_submit_button(
        self,
        label: str,
        **_kwargs,
    ) -> bool:
        return label == "Salvar alterações"

    def number_input(
        self,
        label: str,
        **_kwargs,
    ) -> int:
        self.legacy_controls.append(
            label
        )
        return 0

    def data_editor(
        self,
        *_args,
        **_kwargs,
    ):
        self.legacy_controls.append(
            "Fontes de renda"
        )
        return pd.DataFrame()

    def checkbox(
        self,
        label: str,
        **_kwargs,
    ) -> bool:
        self.legacy_controls.append(
            label
        )
        return False

    def text_area(
        self,
        label: str,
        **_kwargs,
    ) -> str:
        self.legacy_controls.append(
            label
        )
        return ""

    def error(
        self,
        message: str,
    ) -> None:
        self.errors.append(
            message
        )

    def rerun(
        self,
    ) -> None:
        self.rerun_calls += 1


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


def test_profile_summary_renders_only_display_name(
    monkeypatch,
) -> None:
    fake_streamlit = (
        ProfileRenderStreamlit()
    )

    monkeypatch.setattr(
        profile_module,
        "st",
        fake_streamlit,
    )

    profile_module._render_profile_summary(
        {
            "nome": "Ryan",
            "idade": 24,
            "ocupacao": "Desenvolvedor",
            "renda_mensal_principal": 2500.0,
            "situacao_atual": {
                "possui_dividas": True,
                "utiliza_cartao_de_credito": True,
                "observacao": "Texto legado",
            },
        }
    )

    assert fake_streamlit.markdowns == [
        "### Ryan",
    ]
    assert fake_streamlit.captions == []
    assert fake_streamlit.metrics == []
    assert fake_streamlit.infos == []


def test_profile_form_saves_only_display_name(
    monkeypatch,
) -> None:
    fake_streamlit = (
        ProfileEditStreamlit()
    )
    save_calls: list[dict] = []

    monkeypatch.setattr(
        profile_module,
        "st",
        fake_streamlit,
    )
    monkeypatch.setattr(
        profile_module,
        "save_user_profile",
        lambda **kwargs: save_calls.append(
            kwargs
        ),
    )

    profile_module.render_user_profile(
        {
            "user_id": "user-1",
            "nome": "Ryan",
            "idade": 24,
            "ocupacao": "Desenvolvedor",
            "fontes_de_renda": [
                {
                    "tipo": "Trabalho",
                    "valor_mensal": 2500.0,
                }
            ],
            "situacao_atual": {
                "possui_dividas": True,
                "utiliza_cartao_de_credito": True,
                "observacao": "Texto legado",
            },
            "objetivos_financeiros": [],
        },
        user_id="user-1",
        data_mode="user",
    )

    assert fake_streamlit.text_inputs == [
        "Como quer ser chamado?",
    ]
    assert fake_streamlit.text_input_limits == [
        120,
    ]
    assert fake_streamlit.legacy_controls == []
    assert save_calls == [
        {
            "database_path": (
                profile_module.ARQUIVO_BANCO
            ),
            "user_id": "user-1",
            "profile": {
                "nome": "Ryan atualizado",
            },
        }
    ]
    assert (
        fake_streamlit.cache_data.clear_calls
        == 1
    )
    assert fake_streamlit.rerun_calls == 1
    assert fake_streamlit.errors == []


def test_demo_profile_is_read_only_even_with_edit_mode_pending(
    monkeypatch,
) -> None:
    fake_streamlit = (
        ProfileRenderStreamlit()
    )
    fake_streamlit.session_state[
        profile_module.PROFILE_EDIT_MODE_KEY
    ] = True

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
    demo_profile = {
        "nome": "Marina Costa",
        "idade": 21,
        "ocupacao": "Estudante e estagiária",
        "renda_mensal_principal": 1600.0,
        "situacao_atual": {
            "possui_dividas": False,
            "utiliza_cartao_de_credito": True,
            "observacao": "Texto da persona",
        },
        "objetivos_financeiros": [],
    }

    profile_module.render_user_profile(
        demo_profile,
        user_id="user-1",
        data_mode="demo",
    )

    assert fake_streamlit.markdowns == [
        "### Marina Costa",
    ]
    assert fake_streamlit.metrics == []
    assert fake_streamlit.buttons == []
    assert fake_streamlit.captions == [
        "Consulte e atualize como você quer ser chamado.",
    ]
    assert fake_streamlit.infos == [
        "Perfil de demonstração. "
        "Estas informações são fictícias e somente leitura.",
    ]
