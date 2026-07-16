"""Testes do repositório de contas locais."""

from __future__ import annotations

import sqlite3

import pytest

from src.account_repository import (
    ACCOUNT_TABLE_NAME,
    DuplicateUserAccountError,
    authenticate_user_account,
    create_user_account,
    get_user_account_by_id,
    get_user_account_by_username,
    hash_password,
    verify_password,
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