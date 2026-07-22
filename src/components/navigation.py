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

SECTION_LABELS = {
    section: label
    for label, section in SECTION_OPTIONS.items()
}

SECTION_TRIGGER_LABELS = {
    MAIN_SECTION: "Painel",
    PROFILE_SECTION: "Perfil",
    DATA_SECTION: "Dados",
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


def get_section_label(
    section: str,
) -> str:
    """Retorna o rótulo visível da seção informada."""
    normalized_section = str(
        section
    ).strip()

    return SECTION_LABELS.get(
        normalized_section,
        SECTION_LABELS[
            MAIN_SECTION
        ],
    )


def get_section_trigger_label(
    section: str,
) -> str:
    """Retorna o rótulo compacto exibido no botão da sidebar."""
    normalized_section = str(
        section
    ).strip()

    return SECTION_TRIGGER_LABELS.get(
        normalized_section,
        SECTION_TRIGGER_LABELS[
            MAIN_SECTION
        ],
    )


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
    data_mode: str,
) -> str:
    """Exibe a navegação principal dentro da sidebar."""
    active_section = (
        get_active_section()
    )

    name = str(
        profile.get(
            "nome",
            "Perfil local",
        )
        or "Perfil local"
    ).strip()

    active_label = get_section_trigger_label(
        active_section
    )

    with st.sidebar:
        with st.container(
            key="finantec-sidebar-navigation",
        ):
            st.caption(
                "Navegação principal"
            )

            selected_option = st.menu_button(
                label=active_label,
                options=list(
                    SECTION_OPTIONS
                ),
                key="finantec-user-menu",
                icon=(
                    ":material/"
                    "space_dashboard:"
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

            st.caption(
                f"Perfil ativo: {name}"
            )

            if data_mode == "demo":
                st.caption(
                    "Modo demonstração ativo"
                )

    return active_section