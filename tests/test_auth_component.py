"""Testes das regras auxiliares da autenticação."""

from __future__ import annotations

from datetime import timedelta
import src.components.auth as auth_module

from src.components.auth import (
    REGISTRATION_CODE_ENV,
    choose_registration_user_id,
    is_registration_code_valid,
    is_registration_authorized,
)
from src.user_context import (
    LOCAL_USER_ID,
)


def test_first_account_preserves_local_user_id():
    assert choose_registration_user_id(accounts_exist=False) == LOCAL_USER_ID


def test_additional_accounts_receive_generated_id():
    assert choose_registration_user_id(accounts_exist=True) is None


def test_registration_code_accepts_matching_value(
    monkeypatch,
):
    monkeypatch.setenv(
        REGISTRATION_CODE_ENV,
        "finantec-test-code",
    )

    assert is_registration_code_valid("finantec-test-code")


def test_registration_code_rejects_wrong_value(
    monkeypatch,
):
    monkeypatch.setenv(
        REGISTRATION_CODE_ENV,
        "finantec-test-code",
    )

    assert not is_registration_code_valid("wrong-code")


def test_registration_code_rejects_when_not_configured(
    monkeypatch,
):
    monkeypatch.delenv(
        REGISTRATION_CODE_ENV,
        raising=False,
    )

    assert not is_registration_code_valid("any-code")


def test_expired_authenticated_session_is_ended(
    monkeypatch,
):
    account = {
        "user_id": "temporary-user",
        "username": "Visitante",
        "expires_at": ("2026-09-03T12:00:00+00:00"),
    }

    ended_sessions: list[str] = []

    monkeypatch.setattr(
        auth_module,
        "get_current_account",
        lambda: account,
    )

    monkeypatch.setattr(
        auth_module,
        "is_user_account_expired",
        lambda received_account: (received_account == account),
    )

    monkeypatch.setattr(
        auth_module,
        "_end_expired_account_session",
        lambda: ended_sessions.append(account["user_id"]),
    )

    result = auth_module.render_authentication_gate()

    assert result is None

    assert ended_sessions == ["temporary-user"]


def test_temporary_registration_does_not_require_code(
    monkeypatch,
):
    monkeypatch.delenv(
        REGISTRATION_CODE_ENV,
        raising=False,
    )

    assert is_registration_authorized(
        "",
        temporary=True,
    )

    assert not is_registration_authorized(
        "",
        temporary=False,
    )


def test_temporary_account_does_not_reuse_local_user_id():
    assert (
        choose_registration_user_id(
            accounts_exist=False,
            temporary=True,
        )
        is None
    )


def test_formats_temporary_account_remaining_time():
    assert (
        auth_module.format_temporary_account_time_remaining(
            timedelta(
                hours=2,
                minutes=5,
            )
        )
        == "2h 5min"
    )

    assert (
        auth_module.format_temporary_account_time_remaining(timedelta(hours=2)) == "2h"
    )

    assert (
        auth_module.format_temporary_account_time_remaining(timedelta(seconds=30))
        == "menos de 1 minuto"
    )
