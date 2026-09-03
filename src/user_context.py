"""Contexto da conta autenticada no FinanTec."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

import streamlit as st

LOCAL_USER_ID = "local-user"

DATA_MODE_KEY = "finantec_data_mode"

AUTHENTICATED_ACCOUNT_KEY = "finantec_authenticated_account"


def _resolve_session_state(
    session_state: (
        MutableMapping[
            str,
            Any,
        ]
        | None
    ) = None,
):
    """Retorna o estado recebido ou a sessão do Streamlit."""
    if session_state is not None:
        return session_state

    return st.session_state


def get_current_account(
    session_state: (
        MutableMapping[
            str,
            Any,
        ]
        | None
    ) = None,
) -> dict[str, Any] | None:
    """Retorna a conta autenticada na sessão atual."""
    state = _resolve_session_state(session_state)

    raw_account = state.get(AUTHENTICATED_ACCOUNT_KEY)

    if not isinstance(
        raw_account,
        dict,
    ):
        return None

    user_id = str(
        raw_account.get(
            "user_id",
            "",
        )
    ).strip()

    username = str(
        raw_account.get(
            "username",
            "",
        )
    ).strip()

    raw_expires_at = raw_account.get("expires_at")

    expires_at = str(raw_expires_at).strip() if raw_expires_at is not None else None

    if not user_id or not username:
        return None

    return {
        "user_id": user_id,
        "username": username,
        "expires_at": expires_at,
    }


def set_current_account(
    account: dict[str, Any],
    session_state: (
        MutableMapping[
            str,
            Any,
        ]
        | None
    ) = None,
) -> dict[str, Any]:
    """Registra a conta autenticada na sessão."""
    if not isinstance(
        account,
        dict,
    ):
        raise ValueError("A conta autenticada deve ser " "um objeto válido.")

    user_id = str(
        account.get(
            "user_id",
            "",
        )
    ).strip()

    username = str(
        account.get(
            "username",
            "",
        )
    ).strip()

    raw_expires_at = account.get("expires_at")

    expires_at = str(raw_expires_at).strip() if raw_expires_at is not None else None

    if not user_id or not username:
        raise ValueError(
            "A conta autenticada deve possuir " "identificador e nome de usuário."
        )

    normalized_account = {
        "user_id": user_id,
        "username": username,
        "expires_at": expires_at,
    }

    state = _resolve_session_state(session_state)

    state[AUTHENTICATED_ACCOUNT_KEY] = normalized_account

    return normalized_account


def clear_current_account(
    session_state: (
        MutableMapping[
            str,
            Any,
        ]
        | None
    ) = None,
) -> None:
    """Remove a conta autenticada da sessão."""
    state = _resolve_session_state(session_state)

    state.pop(
        AUTHENTICATED_ACCOUNT_KEY,
        None,
    )


def get_current_user_id(
    session_state: (
        MutableMapping[
            str,
            Any,
        ]
        | None
    ) = None,
) -> str:
    """Retorna o identificador da conta autenticada."""
    account = get_current_account(session_state)

    if account is None:
        raise RuntimeError("Nenhum usuário está autenticado.")

    return account["user_id"]
