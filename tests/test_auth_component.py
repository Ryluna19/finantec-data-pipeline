"""Testes das regras auxiliares da autenticação."""

from __future__ import annotations

from src.components.auth import (
    REGISTRATION_CODE_ENV,
    choose_registration_user_id,
    is_registration_code_valid,
)
from src.user_context import (
    LOCAL_USER_ID,
)


def test_first_account_preserves_local_user_id():
    assert (
        choose_registration_user_id(
            accounts_exist=False
        )
        == LOCAL_USER_ID
    )


def test_additional_accounts_receive_generated_id():
    assert (
        choose_registration_user_id(
            accounts_exist=True
        )
        is None
    )
def test_registration_code_accepts_matching_value(
    monkeypatch,
):
    monkeypatch.setenv(
        REGISTRATION_CODE_ENV,
        "finantec-test-code",
    )

    assert is_registration_code_valid(
        "finantec-test-code"
    )

def test_registration_code_rejects_wrong_value(
    monkeypatch,
):
    monkeypatch.setenv(
        REGISTRATION_CODE_ENV,
        "finantec-test-code",
    )

    assert not is_registration_code_valid(
        "wrong-code"
    )
def test_registration_code_rejects_when_not_configured(
    monkeypatch,
):
    monkeypatch.delenv(
        REGISTRATION_CODE_ENV,
        raising=False,
    )

    assert not is_registration_code_valid(
        "any-code"
    )