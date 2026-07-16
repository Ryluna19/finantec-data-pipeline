"""Testes das regras auxiliares da autenticação."""

from __future__ import annotations

from src.components.auth import (
    choose_registration_user_id,
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