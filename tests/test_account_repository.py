"""Testes do repositório de contas locais."""

from __future__ import annotations

import sqlite3
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest
import src.account_repository as account_repository
from src.account_repository import (
    ACCOUNT_TABLE_NAME,
    LOGIN_ATTEMPT_TABLE_NAME,
    LOGIN_MAX_FAILED_ATTEMPTS,
    DuplicateUserAccountError,
    ExpiredUserAccountError,
    LoginTemporarilyLockedError,
    authenticate_user_account,
    create_user_account,
    get_user_account_by_id,
    get_user_account_by_username,
    hash_password,
    verify_password,
    get_user_account_remaining_time,
)


def test_password_hash_is_not_plain_text():
    password = "senha-segura-123"

    password_hash = hash_password(
        password
    )

    assert password_hash != password

    assert verify_password(
        password,
        password_hash,
    )

    assert not verify_password(
        "senha-incorreta",
        password_hash,
    )

def test_new_password_hash_uses_current_scrypt_parameters():
    password_hash = hash_password(
        "senha-segura-123"
    )

    (
        scheme,
        n_text,
        r_text,
        p_text,
        _,
        _,
    ) = password_hash.split(
        "$",
        maxsplit=5,
    )

    assert (
        scheme
        == account_repository.PASSWORD_SCHEME
    )

    assert (
        int(n_text)
        == account_repository.SCRYPT_N
    )

    assert (
        int(r_text)
        == account_repository.SCRYPT_R
    )

    assert (
        int(p_text)
        == account_repository.SCRYPT_P
    )

def test_password_hash_with_previous_cost_remains_valid(
    monkeypatch,
):
    password = "senha-segura-123"

    with monkeypatch.context() as patch:
        patch.setattr(
            account_repository,
            "SCRYPT_P",
            1,
        )

        previous_password_hash = (
            account_repository.hash_password(
                password
            )
        )

    assert verify_password(
        password,
        previous_password_hash,
    )

    assert not verify_password(
        "senha-incorreta",
        previous_password_hash,
    )

def test_authentication_rehashes_previous_password_cost(
    tmp_path,
    monkeypatch,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    password = "senha-segura-123"

    with monkeypatch.context() as patch:
        patch.setattr(
            account_repository,
            "SCRYPT_P",
            1,
        )

        create_user_account(
            database_path=database_path,
            username="ryan",
            password=password,
        )

    authenticated_account = (
        authenticate_user_account(
            database_path=database_path,
            username="ryan",
            password=password,
        )
    )

    assert authenticated_account is not None

    with sqlite3.connect(
        database_path
    ) as connection:
        row = connection.execute(
            f"""
            SELECT password_hash
            FROM {ACCOUNT_TABLE_NAME}
            WHERE username_key = ?
            """,
            (
                "ryan",
            ),
        ).fetchone()

    assert row is not None

    updated_password_hash = str(
        row[
            0
        ]
    )

    assert not (
        account_repository
        .password_hash_needs_rehash(
            updated_password_hash
        )
    )

    assert verify_password(
        password,
        updated_password_hash,
    )

def test_failed_authentication_does_not_rehash_password(
    tmp_path,
    monkeypatch,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    with monkeypatch.context() as patch:
        patch.setattr(
            account_repository,
            "SCRYPT_P",
            1,
        )

        create_user_account(
            database_path=database_path,
            username="ryan",
            password="senha-segura-123",
        )

    with sqlite3.connect(
        database_path
    ) as connection:
        previous_row = connection.execute(
            f"""
            SELECT password_hash
            FROM {ACCOUNT_TABLE_NAME}
            WHERE username_key = ?
            """,
            (
                "ryan",
            ),
        ).fetchone()

    assert previous_row is not None

    previous_password_hash = str(
        previous_row[
            0
        ]
    )

    authenticated_account = (
        authenticate_user_account(
            database_path=database_path,
            username="ryan",
            password="senha-incorreta",
        )
    )

    assert authenticated_account is None

    with sqlite3.connect(
        database_path
    ) as connection:
        current_row = connection.execute(
            f"""
            SELECT password_hash
            FROM {ACCOUNT_TABLE_NAME}
            WHERE username_key = ?
            """,
            (
                "ryan",
            ),
        ).fetchone()

    assert current_row is not None

    assert (
        str(
            current_row[
                0
            ]
        )
        == previous_password_hash
    )

def test_same_password_generates_different_hashes():
    password = "senha-segura-123"

    first_hash = hash_password(
        password
    )

    second_hash = hash_password(
        password
    )

    assert first_hash != second_hash

    assert verify_password(
        password,
        first_hash,
    )

    assert verify_password(
        password,
        second_hash,
    )

def test_existing_account_table_receives_expiration_column(
    tmp_path,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            f"""
            CREATE TABLE {ACCOUNT_TABLE_NAME} (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                username_key TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    assert not (
        account_repository.has_user_accounts(
            database_path
        )
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        account_columns = {
            str(
                row[
                    1
                ]
            )
            for row in connection.execute(
                f"""
                PRAGMA table_info(
                    {ACCOUNT_TABLE_NAME}
                )
                """
            ).fetchall()
        }

    assert "expires_at" in account_columns


def test_temporary_account_expires_after_24_hours(
    tmp_path,
    monkeypatch,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    current_time = datetime(
        2026,
        9,
        2,
        12,
        0,
        tzinfo=timezone.utc,
    )

    monkeypatch.setattr(
        account_repository,
        "_utc_now",
        lambda: current_time,
    )

    account = create_user_account(
        database_path=database_path,
        username="visitante",
        password="senha-temporaria-123",
        temporary=True,
    )

    expected_expiration = (
        current_time
        + timedelta(
            hours=24
        )
    ).isoformat()

    assert account[
        "expires_at"
    ] == expected_expiration

    loaded_account = (
        get_user_account_by_username(
            database_path=database_path,
            username="visitante",
        )
    )

    assert loaded_account == account

def test_reports_temporary_account_remaining_time(
    monkeypatch,
):
    current_time = datetime(
        2026,
        9,
        3,
        12,
        0,
        tzinfo=timezone.utc,
    )

    monkeypatch.setattr(
        account_repository,
        "_utc_now",
        lambda: current_time,
    )

    remaining_time = get_user_account_remaining_time(
        {
            "expires_at": (
                current_time
                + timedelta(
                    hours=2,
                    minutes=15,
                )
            ).isoformat(),
        }
    )

    assert remaining_time == timedelta(
        hours=2,
        minutes=15,
    )

    assert (
        get_user_account_remaining_time(
            {
                "expires_at": None,
            }
        )
        is None
    )


def test_expired_temporary_account_cannot_authenticate(
    tmp_path,
    monkeypatch,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    creation_time = datetime(
        2026,
        9,
        2,
        12,
        0,
        tzinfo=timezone.utc,
    )

    monkeypatch.setattr(
        account_repository,
        "_utc_now",
        lambda: creation_time,
    )

    account = create_user_account(
        database_path=database_path,
        username="visitante",
        password="senha-temporaria-123",
        temporary=True,
    )

    monkeypatch.setattr(
        account_repository,
        "_utc_now",
        lambda: (
            creation_time
            + timedelta(
                hours=24
            )
        ),
    )

    with pytest.raises(
        ExpiredUserAccountError
    ):
        authenticate_user_account(
            database_path=database_path,
            username="visitante",
            password="senha-temporaria-123",
        )

    with sqlite3.connect(
        database_path
    ) as connection:
        failed_attempt = connection.execute(
            f"""
            SELECT failed_attempts
            FROM {LOGIN_ATTEMPT_TABLE_NAME}
            WHERE user_id = ?
            """,
            (
                account[
                    "user_id"
                ],
            ),
        ).fetchone()

    assert failed_attempt is None

def test_create_and_load_account(
    tmp_path,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    account = create_user_account(
        database_path=database_path,
        username="Ryan.Santos",
        password="senha-segura-123",
    )

    loaded_account = (
        get_user_account_by_username(
            database_path=database_path,
            username="ryan.santos",
        )
    )

    assert loaded_account is not None

    assert loaded_account == account

    assert loaded_account[
        "expires_at"
    ] is None
    
    assert (
        loaded_account[
            "username"
        ]
        == "Ryan.Santos"
    )

def test_create_account_with_existing_user_id(
    tmp_path,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    account = create_user_account(
        database_path=database_path,
        username="ryan",
        password="senha-segura-123",
        user_id="local-user",
    )

    loaded_account = (
        get_user_account_by_id(
            database_path=database_path,
            user_id="local-user",
        )
    )

    assert account[
        "user_id"
    ] == "local-user"

    assert loaded_account == account


def test_password_is_stored_only_as_hash(
    tmp_path,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    password = "senha-segura-123"

    create_user_account(
        database_path=database_path,
        username="ryan",
        password=password,
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        row = connection.execute(
            f"""
            SELECT password_hash
            FROM {ACCOUNT_TABLE_NAME}
            WHERE username_key = ?
            """,
            (
                "ryan",
            ),
        ).fetchone()

    assert row is not None

    stored_password_hash = str(
        row[
            0
        ]
    )

    assert stored_password_hash != password

    assert verify_password(
        password,
        stored_password_hash,
    )


def test_authenticate_account(
    tmp_path,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    created_account = (
        create_user_account(
            database_path=database_path,
            username="Ryan",
            password="senha-segura-123",
        )
    )

    authenticated_account = (
        authenticate_user_account(
            database_path=database_path,
            username="RYAN",
            password="senha-segura-123",
        )
    )

    assert (
        authenticated_account
        == created_account
    )

    assert (
        authenticate_user_account(
            database_path=database_path,
            username="Ryan",
            password="senha-incorreta",
        )
        is None
    )

    assert (
        authenticate_user_account(
            database_path=database_path,
            username="inexistente",
            password="senha-segura-123",
        )
        is None
    )

def test_failed_logins_are_persisted(
    tmp_path,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    account = create_user_account(
        database_path=database_path,
        username="ryan",
        password="senha-segura-123",
    )

    authenticate_user_account(
        database_path=database_path,
        username="ryan",
        password="senha-incorreta",
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        row = connection.execute(
            f"""
            SELECT failed_attempts
            FROM {LOGIN_ATTEMPT_TABLE_NAME}
            WHERE user_id = ?
            """,
            (
                account[
                    "user_id"
                ],
            ),
        ).fetchone()

    assert row is not None

    assert row[
        0
    ] == 1


def test_successful_login_clears_failed_attempts(
    tmp_path,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    account = create_user_account(
        database_path=database_path,
        username="ryan",
        password="senha-segura-123",
    )

    authenticate_user_account(
        database_path=database_path,
        username="ryan",
        password="senha-incorreta",
    )

    authenticated_account = (
        authenticate_user_account(
            database_path=database_path,
            username="ryan",
            password="senha-segura-123",
        )
    )

    assert authenticated_account == account

    with sqlite3.connect(
        database_path
    ) as connection:
        row = connection.execute(
            f"""
            SELECT 1
            FROM {LOGIN_ATTEMPT_TABLE_NAME}
            WHERE user_id = ?
            """,
            (
                account[
                    "user_id"
                ],
            ),
        ).fetchone()

    assert row is None


def test_login_is_locked_after_maximum_failed_attempts(
    tmp_path,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    create_user_account(
        database_path=database_path,
        username="ryan",
        password="senha-segura-123",
    )

    for _ in range(
        LOGIN_MAX_FAILED_ATTEMPTS - 1
    ):
        assert (
            authenticate_user_account(
                database_path=database_path,
                username="ryan",
                password="senha-incorreta",
            )
            is None
        )

    with pytest.raises(
        LoginTemporarilyLockedError,
        match="Muitas tentativas",
    ):
        authenticate_user_account(
            database_path=database_path,
            username="ryan",
            password="senha-incorreta",
        )


def test_correct_password_is_rejected_during_lockout(
    tmp_path,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    create_user_account(
        database_path=database_path,
        username="ryan",
        password="senha-segura-123",
    )

    for _ in range(
        LOGIN_MAX_FAILED_ATTEMPTS
    ):
        try:
            authenticate_user_account(
                database_path=database_path,
                username="ryan",
                password="senha-incorreta",
            )

        except LoginTemporarilyLockedError:
            pass

    with pytest.raises(
        LoginTemporarilyLockedError,
        match="Muitas tentativas",
    ):
        authenticate_user_account(
            database_path=database_path,
            username="ryan",
            password="senha-segura-123",
        )


def test_duplicate_username_is_case_insensitive(
    tmp_path,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    create_user_account(
        database_path=database_path,
        username="Ryan",
        password="senha-segura-123",
    )

    with pytest.raises(
        DuplicateUserAccountError,
        match="Já existe uma conta",
    ):
        create_user_account(
            database_path=database_path,
            username="RYAN",
            password="outra-senha-123",
        )


@pytest.mark.parametrize(
    "username",
    [
        "",
        "ab",
        "nome com espaco",
        "nome@email",
    ],
)
def test_rejects_invalid_username(
    tmp_path,
    username,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    with pytest.raises(
        ValueError
    ):
        create_user_account(
            database_path=database_path,
            username=username,
            password="senha-segura-123",
        )


@pytest.mark.parametrize(
    "password",
    [
        "",
        "1234567",
        "        ",
    ],
)
def test_rejects_invalid_password(
    tmp_path,
    password,
):
    database_path = (
        tmp_path
        / "accounts.db"
    )

    with pytest.raises(
        ValueError
    ):
        create_user_account(
            database_path=database_path,
            username="ryan",
            password=password,
        )


def test_verify_password_rejects_invalid_hash():
    assert not verify_password(
        "senha-segura-123",
        "",
    )

    assert not verify_password(
        "senha-segura-123",
        "hash-invalido",
    )