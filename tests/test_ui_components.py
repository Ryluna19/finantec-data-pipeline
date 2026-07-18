"""Testes do carregamento dos estilos visuais."""

from __future__ import annotations

from src.ui_components import (
    STYLE_FILES,
    load_visual_styles,
)


def test_visual_style_files_exist():
    assert all(
        style_file.exists()
        for style_file in STYLE_FILES
    )


def test_visual_styles_are_loaded_in_expected_order():
    styles = load_visual_styles()

    section_titles = (
        "ESTRUTURA PRINCIPAL",
        "PAINÉIS FINANCEIROS",
        "RESPONSIVIDADE",
        "CARTÕES DO RASCUNHO",
        "AUTENTICAÇÃO",
        "APARÊNCIA E PALETAS",
    )

    positions = [
        styles.index(
            section_title
        )
        for section_title in section_titles
    ]

    assert positions == sorted(
        positions
    )


def test_visual_styles_do_not_duplicate_section_boundaries():
    styles = load_visual_styles()

    unique_sections = (
        "ESTRUTURA PRINCIPAL",
        "PAINÉIS FINANCEIROS",
        "CARTÕES DO RASCUNHO",
        "APARÊNCIA E PALETAS",
    )

    for section_title in unique_sections:
        assert (
            styles.count(
                section_title
            )
            == 1
        )