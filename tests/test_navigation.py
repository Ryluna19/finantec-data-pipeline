"""Testes da identidade exibida na navegação local."""

from __future__ import annotations

import components.navigation as navigation_module


class SidebarContext:
    """Simula o contexto da barra lateral."""

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exception_type,
        exception_value,
        traceback,
    ) -> bool:
        return False

class DummyContext:
    """Simula um container do Streamlit."""

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exception_type,
        exception_value,
        traceback,
    ) -> bool:
        return False

class NavigationStreamlit:
    """Registra a identidade e os avisos da navegação."""

    def __init__(
        self,
    ) -> None:
        self.session_state: dict = {}
        self.sidebar = SidebarContext()
        self.menu_labels: list[str] = []
        self.captions: list[str] = []

    def menu_button(
        self,
        *,
        label: str,
        **_kwargs,
    ) -> None:
        self.menu_labels.append(
            label
        )
        return None

    def caption(
        self,
        text: str,
    ) -> None:
        self.captions.append(
            text
        )

    def divider(
        self,
    ) -> None:
        return None

    def container(
        self,
        **_kwargs,
    ) -> DummyContext:
        return DummyContext()

def test_demo_keeps_personal_identity_and_shows_mode(
    monkeypatch,
) -> None:
    fake_streamlit = (
        NavigationStreamlit()
    )

    monkeypatch.setattr(
        navigation_module,
        "st",
        fake_streamlit,
    )

    navigation_module.render_user_navigation(
        {
            "nome": "Ryan",
        },
        data_mode="demo",
    )

    assert fake_streamlit.menu_labels == [
    "Painel",
    ]
    assert fake_streamlit.captions == [
    "Navegação principal",
    "Perfil ativo: Ryan",
    "Modo demonstração ativo",
    ]


def test_unconfigured_profile_uses_navigation_fallback(
    monkeypatch,
) -> None:
    fake_streamlit = (
        NavigationStreamlit()
    )

    monkeypatch.setattr(
        navigation_module,
        "st",
        fake_streamlit,
    )

    navigation_module.render_user_navigation(
        {
            "objetivos_financeiros": [],
        },
        data_mode="user",
    )

    assert fake_streamlit.menu_labels == [
    "Painel",
    ]
    assert fake_streamlit.captions == [
    "Navegação principal",
    "Perfil ativo: Perfil local",
    ]
