"""Testes dos componentes visuais da sidebar."""

from components.auth import (
    build_sidebar_account_html,
)
from components.navigation import (
    DATA_SECTION,
    MAIN_SECTION,
    PROFILE_SECTION,
    get_section_label,
    get_section_trigger_label,
)


def test_sidebar_account_html_normalizes_username():
    html = build_sidebar_account_html(
        "  Ryan   Santos  "
    )

    assert "Ryan Santos" in html
    assert ">RS<" in html
    assert "Conta local" in html


def test_sidebar_account_html_escapes_username():
    html = build_sidebar_account_html(
        "<script>alert('x')</script>"
    )

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_section_labels_match_navigation_destinations():
    assert (
        get_section_label(
            MAIN_SECTION
        )
        == "Painel financeiro"
    )

    assert (
        get_section_label(
            PROFILE_SECTION
        )
        == "Meu perfil"
    )

    assert (
        get_section_label(
            DATA_SECTION
        )
        == "Dados e privacidade"
    )


def test_invalid_section_label_falls_back_to_main():
    assert (
        get_section_label(
            "unknown"
        )
        == "Painel financeiro"
    )


def test_section_trigger_labels_are_compact():
    assert (
        get_section_trigger_label(
            MAIN_SECTION
        )
        == "Painel"
    )

    assert (
        get_section_trigger_label(
            PROFILE_SECTION
        )
        == "Perfil"
    )

    assert (
        get_section_trigger_label(
            DATA_SECTION
        )
        == "Dados"
    )

    assert (
        get_section_trigger_label(
            "unknown"
        )
        == "Painel"
    )