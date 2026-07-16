"""Testes do contexto da conta autenticada."""

from __future__ import annotations

import pytest

from src.user_context import (
    AUTHENTICATED_ACCOUNT_KEY,
    clear_current_account,
    get_current_account,
    get_current_user_id,
    set_current_account,
)


def test_session_starts_without_authenticated_account():
    session_state: dict = {}

    assert (
        get_current_account(
            session_state
        )
        is None
    )

    with pytest.raises(
        RuntimeError,
        match="Nenhum usuário",
    ):
        get_current_user_id(
            session_state
        )


def test_sets_and_reads_authenticated_account():
    session_state: dict = {}

    account = set_current_account(
        {
            "user_id": "user-1",
            "username": "Ryan",
        },
        session_state,
    )

    assert account == {
        "user_id": "user-1",
        "username": "Ryan",
    }

    assert (
        get_current_account(
            session_state
        )
        == account
    )

    assert (
        get_current_user_id(
            session_state
        )
        == "user-1"
    )


def test_clears_authenticated_account():
    session_state = {
        AUTHENTICATED_ACCOUNT_KEY: {
            "user_id": "user-1",
            "username": "Ryan",
        },
        "another_key": "preserved",
    }

    clear_current_account(
        session_state
    )

    assert (
        get_current_account(
            session_state
        )
        is None
    )

    assert (
        session_state[
            "another_key"
        ]
        == "preserved"
    )


def test_rejects_invalid_authenticated_account():
    session_state: dict = {}

    with pytest.raises(
        ValueError,
        match="identificador",
    ):
        set_current_account(
            {
                "user_id": "",
                "username": "Ryan",
            },
            session_state,
        )