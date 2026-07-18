"""Testes das preferências visuais."""

from __future__ import annotations

from src.components.appearance import (
    ACCENT_PALETTE_KEY,
    APPEARANCE_KEY,
    build_visual_marker_classes,
    get_visual_preferences,
    clear_session_preserving_visual_preferences,
)


def test_visual_preferences_use_defaults():
    session_state: dict = {}

    preferences = get_visual_preferences(
        session_state
    )

    assert preferences == (
        "dark",
        "orange",
    )

    assert session_state == {
        APPEARANCE_KEY: "dark",
        ACCENT_PALETTE_KEY: "orange",
    }


def test_visual_preferences_preserve_valid_values():
    session_state = {
        APPEARANCE_KEY: "light",
        ACCENT_PALETTE_KEY: "blue",
    }

    assert get_visual_preferences(
        session_state
    ) == (
        "light",
        "blue",
    )


def test_visual_preferences_reject_invalid_values():
    session_state = {
        APPEARANCE_KEY: "unknown",
        ACCENT_PALETTE_KEY: "purple",
    }

    assert get_visual_preferences(
        session_state
    ) == (
        "dark",
        "orange",
    )


def test_builds_visual_marker_classes():
    classes = build_visual_marker_classes(
        "light",
        "green",
    )

    assert classes == (
        "finantec-visual-marker "
        "finantec-theme-light "
        "finantec-accent-green"
    )
    
def test_clears_session_preserving_visual_preferences():
    session_state = {
        APPEARANCE_KEY: "light",
        ACCENT_PALETTE_KEY: "blue",
        "authenticated_account": {
            "user_id": "user-1",
        },
        "temporary_value": True,
    }

    clear_session_preserving_visual_preferences(
        session_state
    )

    assert session_state == {
        APPEARANCE_KEY: "light",
        ACCENT_PALETTE_KEY: "blue",
    }