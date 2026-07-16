"""Persistência de contas locais do FinanTec."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4


ACCOUNT_TABLE_NAME = "user_accounts"

PASSWORD_SCHEME = "scrypt"

PASSWORD_SALT_BYTES = 16

PASSWORD_HASH_BYTES = 64

SCRYPT_N = 2**14

SCRYPT_R = 8

SCRYPT_P = 1


class DuplicateUserAccountError(
    ValueError
):
    """Indica conflito com uma conta já existente."""


def _connect(
    database_path: Path,
) -> sqlite3.Connection:
    """Abre uma conexão SQLite."""
    database_path = Path(
        database_path
    )

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        database_path,
        timeout=5.0,
    )

    connection.row_factory = (
        sqlite3.Row
    )

    return connection


def _ensure_account_table(
    connection: sqlite3.Connection,
) -> None:
    """Cria a tabela de contas quando necessário."""
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {ACCOUNT_TABLE_NAME} (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            username_key TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            CHECK (
                length(username) BETWEEN 3 AND 50
            )
        )
        """
    )


def _normalize_user_id(
    user_id: object,
) -> str:
    """Valida o identificador interno da conta."""
    normalized_user_id = str(
        user_id
    ).strip()

    if not normalized_user_id:
        raise ValueError(
            "O identificador do usuário "
            "não pode ser vazio."
        )

    if len(normalized_user_id) > 120:
        raise ValueError(
            "O identificador do usuário deve possuir "
            "no máximo 120 caracteres."
        )

    return normalized_user_id


def _normalize_username(
    username: object,
) -> tuple[str, str]:
    """Normaliza o nome usado para entrar na conta."""
    normalized_username = str(
        username
        if username is not None
        else ""
    ).strip()

    if len(normalized_username) < 3:
        raise ValueError(
            "O nome de usuário deve possuir "
            "pelo menos 3 caracteres."
        )

    if len(normalized_username) > 50:
        raise ValueError(
            "O nome de usuário deve possuir "
            "no máximo 50 caracteres."
        )

    if any(
        character.isspace()
        for character in normalized_username
    ):
        raise ValueError(
            "O nome de usuário não pode conter espaços."
        )

    allowed_symbols = {
        ".",
        "_",
        "-",
    }

    if not all(
        character.isalnum()
        or character in allowed_symbols
        for character in normalized_username
    ):
        raise ValueError(
            "O nome de usuário pode conter somente "
            "letras, números, ponto, hífen e sublinhado."
        )

    username_key = (
        normalized_username.casefold()
    )

    return (
        normalized_username,
        username_key,
    )


def _validate_password(
    password: object,
) -> str:
    """Valida uma senha antes de gerar seu hash."""
    if not isinstance(
        password,
        str,
    ):
        raise ValueError(
            "A senha deve ser um texto válido."
        )

    if len(password) < 8:
        raise ValueError(
            "A senha deve possuir pelo menos "
            "8 caracteres."
        )

    if len(password) > 128:
        raise ValueError(
            "A senha deve possuir no máximo "
            "128 caracteres."
        )

    if not password.strip():
        raise ValueError(
            "A senha não pode conter apenas espaços."
        )

    return password


def hash_password(
    password: str,
) -> str:
    """Gera um hash seguro e aleatório para uma senha."""
    validated_password = (
        _validate_password(
            password
        )
    )

    salt = secrets.token_bytes(
        PASSWORD_SALT_BYTES
    )

    password_digest = hashlib.scrypt(
        validated_password.encode(
            "utf-8"
        ),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=PASSWORD_HASH_BYTES,
    )

    encoded_salt = (
        base64.urlsafe_b64encode(
            salt
        ).decode(
            "ascii"
        )
    )

    encoded_digest = (
        base64.urlsafe_b64encode(
            password_digest
        ).decode(
            "ascii"
        )
    )

    return "$".join(
        [
            PASSWORD_SCHEME,
            str(SCRYPT_N),
            str(SCRYPT_R),
            str(SCRYPT_P),
            encoded_salt,
            encoded_digest,
        ]
    )


def verify_password(
    password: object,
    stored_password_hash: object,
) -> bool:
    """Compara uma senha com o hash persistido."""
    if not isinstance(
        password,
        str,
    ):
        return False

    if not isinstance(
        stored_password_hash,
        str,
    ):
        return False

    try:
        (
            scheme,
            n_text,
            r_text,
            p_text,
            encoded_salt,
            encoded_digest,
        ) = stored_password_hash.split(
            "$",
            maxsplit=5,
        )

        if scheme != PASSWORD_SCHEME:
            return False

        scrypt_n = int(
            n_text
        )

        scrypt_r = int(
            r_text
        )

        scrypt_p = int(
            p_text
        )

        if (
            scrypt_n <= 1
            or scrypt_n > 2**20
            or scrypt_r <= 0
            or scrypt_r > 32
            or scrypt_p <= 0
            or scrypt_p > 16
        ):
            return False

        salt = (
            base64.urlsafe_b64decode(
                encoded_salt.encode(
                    "ascii"
                )
            )
        )

        expected_digest = (
            base64.urlsafe_b64decode(
                encoded_digest.encode(
                    "ascii"
                )
            )
        )

        candidate_digest = (
            hashlib.scrypt(
                password.encode(
                    "utf-8"
                ),
                salt=salt,
                n=scrypt_n,
                r=scrypt_r,
                p=scrypt_p,
                dklen=len(
                    expected_digest
                ),
            )
        )

    except (
        TypeError,
        ValueError,
        UnicodeError,
    ):
        return False

    return hmac.compare_digest(
        candidate_digest,
        expected_digest,
    )


def _row_to_account(
    row: sqlite3.Row,
) -> dict[str, Any]:
    """Converte uma linha SQLite em conta pública."""
    return {
        "user_id": str(
            row[
                "user_id"
            ]
        ),
        "username": str(
            row[
                "username"
            ]
        ),
        "created_at": str(
            row[
                "created_at"
            ]
        ),
        "updated_at": str(
            row[
                "updated_at"
            ]
        ),
    }


def create_user_account(
    database_path: Path,
    username: str,
    password: str,
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Cria uma conta local com senha protegida."""
    (
        normalized_username,
        username_key,
    ) = _normalize_username(
        username
    )

    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
        if user_id is not None
        else str(
            uuid4()
        )
    )

    password_hash = hash_password(
        password
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_account_table(
                connection
            )

            connection.execute(
                f"""
                INSERT INTO {ACCOUNT_TABLE_NAME} (
                    user_id,
                    username,
                    username_key,
                    password_hash
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    normalized_user_id,
                    normalized_username,
                    username_key,
                    password_hash,
                ),
            )

            row = connection.execute(
                f"""
                SELECT
                    user_id,
                    username,
                    created_at,
                    updated_at
                FROM {ACCOUNT_TABLE_NAME}
                WHERE user_id = ?
                """,
                (
                    normalized_user_id,
                ),
            ).fetchone()

    except sqlite3.IntegrityError as error:
        raise DuplicateUserAccountError(
            "Já existe uma conta com esse "
            "nome de usuário ou identificador."
        ) from error

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível criar "
            "a conta do usuário."
        ) from error

    if row is None:
        raise RuntimeError(
            "A conta foi criada, mas não pôde "
            "ser carregada novamente."
        )

    return _row_to_account(
        row
    )


def get_user_account_by_username(
    database_path: Path,
    username: str,
) -> dict[str, Any] | None:
    """Carrega uma conta pelo nome de usuário."""
    (
        _,
        username_key,
    ) = _normalize_username(
        username
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_account_table(
                connection
            )

            row = connection.execute(
                f"""
                SELECT
                    user_id,
                    username,
                    created_at,
                    updated_at
                FROM {ACCOUNT_TABLE_NAME}
                WHERE username_key = ?
                """,
                (
                    username_key,
                ),
            ).fetchone()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "a conta do usuário."
        ) from error

    if row is None:
        return None

    return _row_to_account(
        row
    )


def get_user_account_by_id(
    database_path: Path,
    user_id: str,
) -> dict[str, Any] | None:
    """Carrega uma conta pelo identificador interno."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_account_table(
                connection
            )

            row = connection.execute(
                f"""
                SELECT
                    user_id,
                    username,
                    created_at,
                    updated_at
                FROM {ACCOUNT_TABLE_NAME}
                WHERE user_id = ?
                """,
                (
                    normalized_user_id,
                ),
            ).fetchone()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "a conta do usuário."
        ) from error

    if row is None:
        return None

    return _row_to_account(
        row
    )


def authenticate_user_account(
    database_path: Path,
    username: str,
    password: str,
) -> dict[str, Any] | None:
    """Valida as credenciais e retorna a conta autenticada."""
    try:
        (
            _,
            username_key,
        ) = _normalize_username(
            username
        )

    except ValueError:
        return None

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_account_table(
                connection
            )

            row = connection.execute(
                f"""
                SELECT
                    user_id,
                    username,
                    password_hash,
                    created_at,
                    updated_at
                FROM {ACCOUNT_TABLE_NAME}
                WHERE username_key = ?
                """,
                (
                    username_key,
                ),
            ).fetchone()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível autenticar "
            "a conta do usuário."
        ) from error

    if row is None:
        return None

    if not verify_password(
        password,
        row[
            "password_hash"
        ],
    ):
        return None

    return _row_to_account(
        row
    )