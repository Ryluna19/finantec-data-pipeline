"""Persistência local do histórico de conversa do FinanTec."""

from __future__ import annotations

import sqlite3
from pathlib import Path


CHAT_TABLE_NAME = (
    "chat_messages"
)

VALID_CHAT_ROLES = {
    "user",
    "assistant",
}

VALID_RESPONSE_SOURCES = {
    "",
    "local",
    "ai",
    "error",
}


def _connect(
    database_path: Path,
) -> sqlite3.Connection:
    """Abre uma conexão SQLite para o histórico."""
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


def _ensure_chat_table(
    connection: sqlite3.Connection,
) -> None:
    """Cria a estrutura do histórico quando necessário."""
    connection.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS {CHAT_TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            data_mode TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            response_source TEXT,
            created_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            CHECK (
                role IN (
                    'user',
                    'assistant'
                )
            )
        );

        CREATE INDEX IF NOT EXISTS
            idx_chat_messages_context
        ON {CHAT_TABLE_NAME} (
            data_mode,
            period,
            id
        );
        """
    )


def _validate_context(
    period: str,
    data_mode: str,
) -> tuple[str, str]:
    """Valida o contexto usado para separar conversas."""
    normalized_period = (
        period.strip()
    )

    normalized_mode = (
        data_mode.strip()
    )

    if not normalized_period:
        raise ValueError(
            "O período da conversa não pode ser vazio."
        )

    if not normalized_mode:
        raise ValueError(
            "O modo dos dados não pode ser vazio."
        )

    return (
        normalized_period,
        normalized_mode,
    )


def _validate_message(
    role: str,
    content: str,
    response_source: str = "",
) -> tuple[str, str, str]:
    """Valida uma mensagem antes da persistência."""
    normalized_role = (
        role.strip().lower()
    )

    normalized_content = (
        content.strip()
    )

    normalized_source = (
        response_source
        .strip()
        .lower()
    )

    if (
        normalized_role
        not in VALID_CHAT_ROLES
    ):
        raise ValueError(
            "Papel de mensagem inválido."
        )

    if not normalized_content:
        raise ValueError(
            "O conteúdo da mensagem não pode ser vazio."
        )

    if (
        normalized_source
        not in VALID_RESPONSE_SOURCES
    ):
        raise ValueError(
            "Origem de resposta inválida."
        )

    return (
        normalized_role,
        normalized_content,
        normalized_source,
    )


def load_chat_messages(
    database_path: Path,
    period: str,
    data_mode: str,
    limit: int = 100,
) -> list[dict[str, str]]:
    """Carrega as mensagens mais recentes de um contexto."""
    normalized_period, normalized_mode = (
        _validate_context(
            period=period,
            data_mode=data_mode,
        )
    )

    if limit <= 0:
        raise ValueError(
            "O limite de mensagens deve ser maior que zero."
        )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_chat_table(
                connection
            )

            rows = connection.execute(
                f"""
                SELECT
                    role,
                    content,
                    COALESCE(
                        response_source,
                        ''
                    ) AS response_source
                FROM (
                    SELECT
                        id,
                        role,
                        content,
                        response_source
                    FROM {CHAT_TABLE_NAME}
                    WHERE
                        period = ?
                        AND data_mode = ?
                    ORDER BY id DESC
                    LIMIT ?
                )
                ORDER BY id ASC
                """,
                (
                    normalized_period,
                    normalized_mode,
                    limit,
                ),
            ).fetchall()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "o histórico da conversa."
        ) from error

    return [
        {
            "role": str(
                row["role"]
            ),
            "content": str(
                row["content"]
            ),
            "source": str(
                row["response_source"]
            ),
        }
        for row in rows
    ]


def save_chat_exchange(
    database_path: Path,
    period: str,
    data_mode: str,
    question: str,
    response: str,
    response_source: str,
) -> None:
    """Salva uma pergunta e sua resposta na mesma transação."""
    normalized_period, normalized_mode = (
        _validate_context(
            period=period,
            data_mode=data_mode,
        )
    )

    (
        user_role,
        normalized_question,
        _,
    ) = _validate_message(
        role="user",
        content=question,
    )

    (
        assistant_role,
        normalized_response,
        normalized_source,
    ) = _validate_message(
        role="assistant",
        content=response,
        response_source=(
            response_source
        ),
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_chat_table(
                connection
            )

            connection.executemany(
                f"""
                INSERT INTO {CHAT_TABLE_NAME} (
                    period,
                    data_mode,
                    role,
                    content,
                    response_source
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        normalized_period,
                        normalized_mode,
                        user_role,
                        normalized_question,
                        None,
                    ),
                    (
                        normalized_period,
                        normalized_mode,
                        assistant_role,
                        normalized_response,
                        normalized_source,
                    ),
                ],
            )

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível salvar "
            "o histórico da conversa."
        ) from error


def clear_chat_messages(
    database_path: Path,
    period: str,
    data_mode: str,
) -> int:
    """Remove somente a conversa do contexto informado."""
    normalized_period, normalized_mode = (
        _validate_context(
            period=period,
            data_mode=data_mode,
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_chat_table(
                connection
            )

            cursor = connection.execute(
                f"""
                DELETE FROM {CHAT_TABLE_NAME}
                WHERE
                    period = ?
                    AND data_mode = ?
                """,
                (
                    normalized_period,
                    normalized_mode,
                ),
            )

            deleted_count = (
                cursor.rowcount
            )

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível limpar "
            "o histórico da conversa."
        ) from error

    return int(
        deleted_count
    )