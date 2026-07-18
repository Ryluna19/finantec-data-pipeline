"""Controles de aparência do FinanTec."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

import streamlit as st


APPEARANCE_KEY = "finantec_appearance"
ACCENT_PALETTE_KEY = "finantec_accent_palette"

APPEARANCE_WIDGET_KEY = "finantec_appearance_selector"
ACCENT_WIDGET_KEY = "finantec_accent_selector"

DEFAULT_APPEARANCE = "dark"
DEFAULT_ACCENT_PALETTE = "orange"

APPEARANCE_OPTIONS = {
    "Escuro": "dark",
    "Claro": "light",
}

ACCENT_PALETTE_OPTIONS = {
    "Laranja": "orange",
    "Azul": "blue",
    "Verde": "green",
}


def get_visual_preferences(
    session_state: MutableMapping[str, Any] | None = None,
) -> tuple[str, str]:
    """Obtém e normaliza as preferências visuais da sessão."""
    state = st.session_state if session_state is None else session_state

    appearance = str(
        state.get(APPEARANCE_KEY, DEFAULT_APPEARANCE)
    ).strip()

    accent_palette = str(
        state.get(ACCENT_PALETTE_KEY, DEFAULT_ACCENT_PALETTE)
    ).strip()

    if appearance not in APPEARANCE_OPTIONS.values():
        appearance = DEFAULT_APPEARANCE

    if accent_palette not in ACCENT_PALETTE_OPTIONS.values():
        accent_palette = DEFAULT_ACCENT_PALETTE

    state[APPEARANCE_KEY] = appearance
    state[ACCENT_PALETTE_KEY] = accent_palette

    return appearance, accent_palette

def clear_session_preserving_visual_preferences(
    session_state: MutableMapping[str, Any] | None = None,
) -> None:
    """Limpa a sessão sem perder as preferências visuais."""
    state = (
        st.session_state
        if session_state is None
        else session_state
    )

    appearance, accent_palette = get_visual_preferences(
        state
    )

    state.clear()

    state[APPEARANCE_KEY] = appearance
    state[ACCENT_PALETTE_KEY] = accent_palette


def build_visual_marker_classes(
    appearance: str,
    accent_palette: str,
) -> str:
    """Monta as classes usadas pelo CSS dinâmico."""
    normalized_appearance = (
        appearance
        if appearance in APPEARANCE_OPTIONS.values()
        else DEFAULT_APPEARANCE
    )

    normalized_palette = (
        accent_palette
        if accent_palette in ACCENT_PALETTE_OPTIONS.values()
        else DEFAULT_ACCENT_PALETTE
    )

    return (
        "finantec-visual-marker "
        f"finantec-theme-{normalized_appearance} "
        f"finantec-accent-{normalized_palette}"
    )


def _find_label(
    options: dict[str, str],
    selected_value: str,
) -> str:
    """Localiza o rótulo associado ao valor interno."""
    return next(
        label
        for label, value in options.items()
        if value == selected_value
    )


def _render_visual_preference_fields(
    *,
    show_caption: bool,
) -> None:
    """Renderiza os campos compartilhados de aparência."""
    appearance, accent_palette = get_visual_preferences()

    appearance_labels = list(
        APPEARANCE_OPTIONS
    )

    accent_labels = list(
        ACCENT_PALETTE_OPTIONS
    )

    appearance_label = st.selectbox(
        "Tema",
        options=appearance_labels,
        index=appearance_labels.index(
            _find_label(
                APPEARANCE_OPTIONS,
                appearance,
            )
        ),
        key=APPEARANCE_WIDGET_KEY,
    )

    accent_label = st.selectbox(
        "Cor de destaque",
        options=accent_labels,
        index=accent_labels.index(
            _find_label(
                ACCENT_PALETTE_OPTIONS,
                accent_palette,
            )
        ),
        key=ACCENT_WIDGET_KEY,
    )

    selected_appearance = APPEARANCE_OPTIONS[
        appearance_label
    ]

    selected_palette = ACCENT_PALETTE_OPTIONS[
        accent_label
    ]

    if (
        selected_appearance != appearance
        or selected_palette != accent_palette
    ):
        st.session_state[
            APPEARANCE_KEY
        ] = selected_appearance

        st.session_state[
            ACCENT_PALETTE_KEY
        ] = selected_palette

        st.rerun()

    if show_caption:
        st.caption(
            "A preferência permanece ativa neste navegador "
            "enquanto a aplicação estiver aberta."
        )


def render_appearance_controls(
    *,
    compact: bool = False,
) -> None:
    """Exibe os controles de tema e cor de destaque."""
    if compact:
        appearance, accent_palette = (
            get_visual_preferences()
        )

        appearance_label = _find_label(
            APPEARANCE_OPTIONS,
            appearance,
        )

        accent_label = _find_label(
            ACCENT_PALETTE_OPTIONS,
            accent_palette,
        )

        trigger_label = (
            f"{appearance_label} · "
            f"{accent_label}"
        )

        with st.container(
            key="finantec-appearance-popover",
        ):
            with st.popover(
                trigger_label,
                icon=":material/palette:",
            ):
                st.markdown(
                    "**Aparência**"
                )

                _render_visual_preference_fields(
                    show_caption=False
                )

        return

    with st.expander(
        "Aparência",
        expanded=False,
    ):
        _render_visual_preference_fields(
            show_caption=True
        )
        
def render_appearance_toolbar(
    *,
    key: str,
) -> None:
    """Exibe o controle compacto alinhado ao topo da página."""
    with st.container(
        key=key,
    ):
        render_appearance_controls(
            compact=True
        )