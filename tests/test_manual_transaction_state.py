"""Testes do estado da entrada manual de transações."""

from __future__ import annotations

import pandas as pd
import pytest
import streamlit as st

from src.manual_transaction_state import (
    MANUAL_DRAFT_KEY,
    MANUAL_EDIT_INDEX_KEY,
    MANUAL_FEEDBACK_KEY,
    MANUAL_FORM_VERSION_KEY,
    adjust_edit_index_after_removal,
    get_manual_draft,
    get_manual_edit_index,
    get_manual_form_version,
    invalidate_manual_draft,
    pop_manual_feedback,
    reset_manual_form,
    set_manual_feedback,
    start_manual_edit,
)


STATE_KEYS = [
    MANUAL_DRAFT_KEY,
    MANUAL_EDIT_INDEX_KEY,
    MANUAL_FORM_VERSION_KEY,
    MANUAL_FEEDBACK_KEY,
]


@pytest.fixture(autouse=True)
def clear_manual_state():
    """Limpa as chaves do editor antes e depois de cada teste."""
    for key in STATE_KEYS:
        st.session_state.pop(
            key,
            None,
        )

    yield

    for key in STATE_KEYS:
        st.session_state.pop(
            key,
            None,
        )


def test_get_manual_draft_returns_copy():
    original = pd.DataFrame(
        [
            {
                "descricao": "Mercado",
            }
        ]
    )

    st.session_state[
        MANUAL_DRAFT_KEY
    ] = original

    result = get_manual_draft()

    result.loc[
        0,
        "descricao",
    ] = "Alterada"

    assert (
        st.session_state[
            MANUAL_DRAFT_KEY
        ].loc[
            0,
            "descricao",
        ]
        == "Mercado"
    )


def test_get_manual_draft_requires_initialization():
    with pytest.raises(
        RuntimeError,
        match="ainda não foi inicializado",
    ):
        get_manual_draft()


def test_reset_manual_form_finishes_editing():
    st.session_state[
        MANUAL_EDIT_INDEX_KEY
    ] = 3

    st.session_state[
        MANUAL_FORM_VERSION_KEY
    ] = 4

    reset_manual_form()

    assert (
        get_manual_edit_index()
        is None
    )

    assert (
        get_manual_form_version()
        == 5
    )


def test_start_manual_edit_stores_index():
    st.session_state[
        MANUAL_FORM_VERSION_KEY
    ] = 2

    start_manual_edit(
        4
    )

    assert (
        get_manual_edit_index()
        == 4
    )

    assert (
        get_manual_form_version()
        == 3
    )


def test_removing_current_edit_finishes_editing():
    st.session_state[
        MANUAL_EDIT_INDEX_KEY
    ] = 2

    st.session_state[
        MANUAL_FORM_VERSION_KEY
    ] = 5

    adjust_edit_index_after_removal(
        2
    )

    assert (
        get_manual_edit_index()
        is None
    )

    assert (
        get_manual_form_version()
        == 6
    )


def test_removing_previous_row_decrements_edit_index():
    st.session_state[
        MANUAL_EDIT_INDEX_KEY
    ] = 4

    st.session_state[
        MANUAL_FORM_VERSION_KEY
    ] = 1

    adjust_edit_index_after_removal(
        2
    )

    assert (
        get_manual_edit_index()
        == 3
    )

    assert (
        get_manual_form_version()
        == 2
    )


def test_removing_later_row_preserves_edit_index():
    st.session_state[
        MANUAL_EDIT_INDEX_KEY
    ] = 1

    st.session_state[
        MANUAL_FORM_VERSION_KEY
    ] = 7

    adjust_edit_index_after_removal(
        3
    )

    assert (
        get_manual_edit_index()
        == 1
    )

    assert (
        get_manual_form_version()
        == 8
    )


def test_feedback_is_consumed_once():
    set_manual_feedback(
        "Transação salva."
    )

    assert (
        pop_manual_feedback()
        == "Transação salva."
    )

    assert (
        pop_manual_feedback()
        is None
    )


def test_invalidate_manual_draft_clears_state():
    st.session_state[
        MANUAL_DRAFT_KEY
    ] = pd.DataFrame(
        [
            {
                "descricao": "Mercado",
            }
        ]
    )

    st.session_state[
        MANUAL_EDIT_INDEX_KEY
    ] = 0

    st.session_state[
        MANUAL_FORM_VERSION_KEY
    ] = 3

    invalidate_manual_draft()

    assert (
        MANUAL_DRAFT_KEY
        not in st.session_state
    )

    assert (
        get_manual_edit_index()
        is None
    )

    assert (
        get_manual_form_version()
        == 4
    )