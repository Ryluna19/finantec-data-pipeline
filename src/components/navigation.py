"""Navegação principal e menu local do usuário."""

from __future__ import annotations

from typing import Any

import streamlit as st


APP_SECTION_KEY = (
    "finantec_app_section"
)

MAIN_SECTION = "main"
PROFILE_SECTION = "profile"
DATA_SECTION = "data"

VALID_SECTIONS = {
    MAIN_SECTION,
    PROFILE_SECTION,
    DATA_SECTION,
}

SECTION_OPTIONS = {
    "Painel financeiro": MAIN_SECTION,
    "Meu perfil": PROFILE_SECTION,
    "Dados e privacidade": DATA_SECTION,
}


def get_active_section() -> str:
    """Obtém a seção externa atualmente aberta."""
    active_section = str(
        st.session_state.get(
            APP_SECTION_KEY,
            MAIN_SECTION,
        )
    ).strip()

    if active_section not in VALID_SECTIONS:
        active_section = MAIN_SECTION

        st.session_state[
            APP_SECTION_KEY
        ] = active_section

    return active_section


def _open_section(
    section: str,
) -> None:
    """Troca a seção ativa e atualiza a interface."""
    if section not in VALID_SECTIONS:
        section = MAIN_SECTION

    if (
        st.session_state.get(
            APP_SECTION_KEY
        )
        == section
    ):
        return

    st.session_state[
        APP_SECTION_KEY
    ] = section

    st.rerun()


def render_user_navigation(
    profile: dict[str, Any],
) -> str:
    """Exibe o menu compacto do usuário na sidebar."""
    active_section = (
        get_active_section()
    )

    name = str(
        profile.get(
            "nome",
            "Meu perfil",
        )
        or "Meu perfil"
    ).strip()

    with st.sidebar:
        selected_option = st.menu_button(
            label=name,
            options=list(
                SECTION_OPTIONS
            ),
            key="finantec-user-menu",
            icon=(
                ":material/"
                "account_circle:"
            ),
            type="secondary",
            width="stretch",
        )

        if selected_option:
            selected_section = (
                SECTION_OPTIONS[
                    selected_option
                ]
            )

            _open_section(
                selected_section
            )
            
        st.divider()

    return active_section