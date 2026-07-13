"""Persistência das metas financeiras do usuário."""

from __future__ import annotations

import sqlite3
import unicodedata
from pathlib import Path
from typing import Any
from uuid import uuid4


GOAL_TABLE_NAME = "financial_goals"
GOAL_SEED_TABLE_NAME = "financial_goal_seed_state"

VALID_PRIORITIES = {
    "baixa",
    "média",
    "alta",
}


class FinancialGoalNotFoundError(
    RuntimeError
):
    """Indica que uma meta não foi encontrada."""


class DuplicateFinancialGoalError(
    ValueError
):
    """Indica que já existe uma meta com o mesmo nome."""


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


def _ensure_goal_tables(
    connection: sqlite3.Connection,
) -> None:
    """Cria as estruturas necessárias para as metas."""
    connection.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS {GOAL_TABLE_NAME} (
            goal_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            name_key TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL NOT NULL DEFAULT 0,
            deadline_months INTEGER NOT NULL,
            priority TEXT NOT NULL DEFAULT 'média',
            status TEXT NOT NULL DEFAULT 'active',
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            CHECK (
                target_amount > 0
            ),

            CHECK (
                current_amount >= 0
            ),

            CHECK (
                deadline_months > 0
            ),

            CHECK (
                priority IN (
                    'baixa',
                    'média',
                    'alta'
                )
            ),

            CHECK (
                status IN (
                    'active',
                    'completed',
                    'archived'
                )
            ),

            UNIQUE (
                user_id,
                name_key
            )
        );

        CREATE INDEX IF NOT EXISTS
            idx_financial_goals_user
        ON {GOAL_TABLE_NAME} (
            user_id,
            status,
            sort_order
        );

        CREATE TABLE IF NOT EXISTS
            {GOAL_SEED_TABLE_NAME} (
                user_id TEXT PRIMARY KEY,
                seeded_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            );
        """
    )


def _normalize_user_id(
    user_id: str,
) -> str:
    """Valida o identificador do usuário."""
    normalized_user_id = str(
        user_id
    ).strip()

    if not normalized_user_id:
        raise ValueError(
            "O identificador do usuário "
            "não pode ser vazio."
        )

    return normalized_user_id


def _normalize_goal_id(
    goal_id: str,
) -> str:
    """Valida o identificador da meta."""
    normalized_goal_id = str(
        goal_id
    ).strip()

    if not normalized_goal_id:
        raise ValueError(
            "O identificador da meta "
            "não pode ser vazio."
        )

    return normalized_goal_id


def _normalize_name(
    value: object,
) -> str:
    """Normaliza o nome visível da meta."""
    name = str(
        value
        if value is not None
        else ""
    ).strip()

    if not name:
        raise ValueError(
            "O nome da meta não pode ser vazio."
        )

    if len(name) > 120:
        raise ValueError(
            "O nome da meta deve possuir "
            "no máximo 120 caracteres."
        )

    return name


def _build_name_key(
    name: str,
) -> str:
    """Cria uma chave comparável para impedir duplicidades."""
    normalized = unicodedata.normalize(
        "NFKD",
        name,
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    return " ".join(
        normalized
        .casefold()
        .split()
    )


def _normalize_positive_amount(
    value: object,
    field_label: str,
) -> float:
    """Normaliza um valor monetário maior que zero."""
    try:
        numeric_value = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            f"{field_label} deve ser um número válido."
        ) from error

    if numeric_value <= 0:
        raise ValueError(
            f"{field_label} deve ser maior que zero."
        )

    return numeric_value


def _normalize_non_negative_amount(
    value: object,
    field_label: str,
) -> float:
    """Normaliza um valor monetário não negativo."""
    try:
        numeric_value = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            f"{field_label} deve ser um número válido."
        ) from error

    if numeric_value < 0:
        raise ValueError(
            f"{field_label} não pode ser negativo."
        )

    return numeric_value


def _normalize_deadline_months(
    value: object,
) -> int:
    """Normaliza o prazo da meta em meses."""
    if isinstance(
        value,
        bool,
    ):
        raise ValueError(
            "O prazo da meta deve ser "
            "um número inteiro."
        )

    try:
        numeric_value = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "O prazo da meta deve ser "
            "um número inteiro."
        ) from error

    if not numeric_value.is_integer():
        raise ValueError(
            "O prazo da meta deve ser "
            "um número inteiro."
        )

    deadline_months = int(
        numeric_value
    )

    if (
        deadline_months < 1
        or deadline_months > 600
    ):
        raise ValueError(
            "O prazo da meta deve estar "
            "entre 1 e 600 meses."
        )

    return deadline_months


def _normalize_priority(
    value: object,
) -> str:
    """Normaliza a prioridade da meta."""
    priority = str(
        value
        if value is not None
        else "média"
    ).strip().casefold()

    priority_aliases = {
        "baixa": "baixa",
        "media": "média",
        "média": "média",
        "alta": "alta",
    }

    normalized_priority = (
        priority_aliases.get(
            priority
        )
    )

    if (
        normalized_priority
        not in VALID_PRIORITIES
    ):
        raise ValueError(
            "A prioridade deve ser "
            "baixa, média ou alta."
        )

    return normalized_priority


def normalize_financial_goal(
    goal: dict[str, Any],
) -> dict[str, Any]:
    """Valida e normaliza uma meta financeira."""
    if not isinstance(
        goal,
        dict,
    ):
        raise ValueError(
            "A meta deve ser um objeto válido."
        )

    name = _normalize_name(
        goal.get(
            "nome"
        )
    )

    target_amount = (
        _normalize_positive_amount(
            goal.get(
                "valor_meta"
            ),
            "O valor da meta",
        )
    )

    current_amount = (
        _normalize_non_negative_amount(
            goal.get(
                "valor_atual",
                0,
            ),
            "O valor atual",
        )
    )

    deadline_months = (
        _normalize_deadline_months(
            goal.get(
                "prazo_meses"
            )
        )
    )

    priority = _normalize_priority(
        goal.get(
            "prioridade",
            "média",
        )
    )

    status = (
        "completed"
        if current_amount >= target_amount
        else "active"
    )

    return {
        "nome": name,
        "name_key": _build_name_key(
            name
        ),
        "valor_meta": target_amount,
        "valor_atual": current_amount,
        "prazo_meses": deadline_months,
        "prioridade": priority,
        "status": status,
    }


def _row_to_goal(
    row: sqlite3.Row,
) -> dict[str, Any]:
    """Converte uma linha do banco para o formato da aplicação."""
    return {
        "goal_id": str(
            row["goal_id"]
        ),
        "nome": str(
            row["name"]
        ),
        "valor_meta": float(
            row["target_amount"]
        ),
        "valor_atual": float(
            row["current_amount"]
        ),
        "prazo_meses": int(
            row["deadline_months"]
        ),
        "prioridade": str(
            row["priority"]
        ),
        "status": str(
            row["status"]
        ),
    }


def _get_next_sort_order(
    connection: sqlite3.Connection,
    user_id: str,
) -> int:
    """Obtém a próxima posição da lista de metas."""
    row = connection.execute(
        f"""
        SELECT
            COALESCE(
                MAX(sort_order),
                -1
            ) + 1 AS next_order
        FROM {GOAL_TABLE_NAME}
        WHERE user_id = ?
        """,
        (
            user_id,
        ),
    ).fetchone()

    return int(
        row["next_order"]
    )


def list_financial_goals(
    database_path: Path,
    user_id: str,
    *,
    include_archived: bool = False,
) -> list[dict[str, Any]]:
    """Lista as metas do usuário."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    where_status = (
        ""
        if include_archived
        else "AND status != 'archived'"
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_goal_tables(
                connection
            )

            rows = connection.execute(
                f"""
                SELECT
                    goal_id,
                    name,
                    target_amount,
                    current_amount,
                    deadline_months,
                    priority,
                    status
                FROM {GOAL_TABLE_NAME}
                WHERE
                    user_id = ?
                    {where_status}
                ORDER BY
                    sort_order ASC,
                    created_at ASC,
                    name ASC
                """,
                (
                    normalized_user_id,
                ),
            ).fetchall()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "as metas financeiras."
        ) from error

    return [
        _row_to_goal(
            row
        )
        for row in rows
    ]


def get_financial_goal(
    database_path: Path,
    user_id: str,
    goal_id: str,
) -> dict[str, Any] | None:
    """Carrega uma meta específica."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    normalized_goal_id = (
        _normalize_goal_id(
            goal_id
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_goal_tables(
                connection
            )

            row = connection.execute(
                f"""
                SELECT
                    goal_id,
                    name,
                    target_amount,
                    current_amount,
                    deadline_months,
                    priority,
                    status
                FROM {GOAL_TABLE_NAME}
                WHERE
                    user_id = ?
                    AND goal_id = ?
                """,
                (
                    normalized_user_id,
                    normalized_goal_id,
                ),
            ).fetchone()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "a meta financeira."
        ) from error

    if row is None:
        return None

    return _row_to_goal(
        row
    )


def create_financial_goal(
    database_path: Path,
    user_id: str,
    goal: dict[str, Any],
) -> dict[str, Any]:
    """Cria uma nova meta financeira."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    normalized_goal = (
        normalize_financial_goal(
            goal
        )
    )

    goal_id = str(
        uuid4()
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_goal_tables(
                connection
            )

            sort_order = (
                _get_next_sort_order(
                    connection,
                    normalized_user_id,
                )
            )

            try:
                connection.execute(
                    f"""
                    INSERT INTO {GOAL_TABLE_NAME} (
                        goal_id,
                        user_id,
                        name,
                        name_key,
                        target_amount,
                        current_amount,
                        deadline_months,
                        priority,
                        status,
                        sort_order
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?
                    )
                    """,
                    (
                        goal_id,
                        normalized_user_id,
                        normalized_goal[
                            "nome"
                        ],
                        normalized_goal[
                            "name_key"
                        ],
                        normalized_goal[
                            "valor_meta"
                        ],
                        normalized_goal[
                            "valor_atual"
                        ],
                        normalized_goal[
                            "prazo_meses"
                        ],
                        normalized_goal[
                            "prioridade"
                        ],
                        normalized_goal[
                            "status"
                        ],
                        sort_order,
                    ),
                )

            except sqlite3.IntegrityError as error:
                raise DuplicateFinancialGoalError(
                    "Já existe uma meta "
                    "com esse nome."
                ) from error

    except DuplicateFinancialGoalError:
        raise

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível criar "
            "a meta financeira."
        ) from error

    created_goal = get_financial_goal(
        database_path=database_path,
        user_id=normalized_user_id,
        goal_id=goal_id,
    )

    if created_goal is None:
        raise RuntimeError(
            "A meta foi criada, mas não "
            "pôde ser carregada novamente."
        )

    return created_goal


def update_financial_goal(
    database_path: Path,
    user_id: str,
    goal_id: str,
    goal: dict[str, Any],
) -> dict[str, Any]:
    """Atualiza uma meta financeira existente."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    normalized_goal_id = (
        _normalize_goal_id(
            goal_id
        )
    )

    normalized_goal = (
        normalize_financial_goal(
            goal
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_goal_tables(
                connection
            )

            try:
                cursor = connection.execute(
                    f"""
                    UPDATE {GOAL_TABLE_NAME}
                    SET
                        name = ?,
                        name_key = ?,
                        target_amount = ?,
                        current_amount = ?,
                        deadline_months = ?,
                        priority = ?,
                        status = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE
                        user_id = ?
                        AND goal_id = ?
                    """,
                    (
                        normalized_goal[
                            "nome"
                        ],
                        normalized_goal[
                            "name_key"
                        ],
                        normalized_goal[
                            "valor_meta"
                        ],
                        normalized_goal[
                            "valor_atual"
                        ],
                        normalized_goal[
                            "prazo_meses"
                        ],
                        normalized_goal[
                            "prioridade"
                        ],
                        normalized_goal[
                            "status"
                        ],
                        normalized_user_id,
                        normalized_goal_id,
                    ),
                )

            except sqlite3.IntegrityError as error:
                raise DuplicateFinancialGoalError(
                    "Já existe uma meta "
                    "com esse nome."
                ) from error

            if cursor.rowcount == 0:
                raise FinancialGoalNotFoundError(
                    "A meta informada não foi encontrada."
                )

    except (
        DuplicateFinancialGoalError,
        FinancialGoalNotFoundError,
    ):
        raise

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível atualizar "
            "a meta financeira."
        ) from error

    updated_goal = get_financial_goal(
        database_path=database_path,
        user_id=normalized_user_id,
        goal_id=normalized_goal_id,
    )

    if updated_goal is None:
        raise RuntimeError(
            "A meta foi atualizada, mas não "
            "pôde ser carregada novamente."
        )

    return updated_goal


def delete_financial_goal(
    database_path: Path,
    user_id: str,
    goal_id: str,
) -> bool:
    """Exclui uma meta financeira."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    normalized_goal_id = (
        _normalize_goal_id(
            goal_id
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_goal_tables(
                connection
            )

            cursor = connection.execute(
                f"""
                DELETE FROM {GOAL_TABLE_NAME}
                WHERE
                    user_id = ?
                    AND goal_id = ?
                """,
                (
                    normalized_user_id,
                    normalized_goal_id,
                ),
            )

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível excluir "
            "a meta financeira."
        ) from error

    return cursor.rowcount > 0


def seed_financial_goals_if_needed(
    database_path: Path,
    user_id: str,
    seed_goals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Copia as metas iniciais apenas uma vez."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    if not isinstance(
        seed_goals,
        list,
    ):
        raise ValueError(
            "As metas iniciais devem ser uma lista."
        )

    normalized_goals = [
        normalize_financial_goal(
            goal
        )
        for goal in seed_goals
    ]

    name_keys = [
        goal["name_key"]
        for goal in normalized_goals
    ]

    if (
        len(name_keys)
        != len(set(name_keys))
    ):
        raise DuplicateFinancialGoalError(
            "As metas iniciais possuem "
            "nomes duplicados."
        )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_goal_tables(
                connection
            )

            seed_row = connection.execute(
                f"""
                SELECT 1
                FROM {GOAL_SEED_TABLE_NAME}
                WHERE user_id = ?
                """,
                (
                    normalized_user_id,
                ),
            ).fetchone()

            if seed_row is not None:
                return list_financial_goals(
                    database_path=database_path,
                    user_id=normalized_user_id,
                )

            existing_row = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM {GOAL_TABLE_NAME}
                WHERE user_id = ?
                """,
                (
                    normalized_user_id,
                ),
            ).fetchone()

            existing_count = int(
                existing_row["total"]
            )

            if existing_count == 0:
                for (
                    sort_order,
                    normalized_goal,
                ) in enumerate(
                    normalized_goals
                ):
                    connection.execute(
                        f"""
                        INSERT INTO {GOAL_TABLE_NAME} (
                            goal_id,
                            user_id,
                            name,
                            name_key,
                            target_amount,
                            current_amount,
                            deadline_months,
                            priority,
                            status,
                            sort_order
                        )
                        VALUES (
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?
                        )
                        """,
                        (
                            str(
                                uuid4()
                            ),
                            normalized_user_id,
                            normalized_goal[
                                "nome"
                            ],
                            normalized_goal[
                                "name_key"
                            ],
                            normalized_goal[
                                "valor_meta"
                            ],
                            normalized_goal[
                                "valor_atual"
                            ],
                            normalized_goal[
                                "prazo_meses"
                            ],
                            normalized_goal[
                                "prioridade"
                            ],
                            normalized_goal[
                                "status"
                            ],
                            sort_order,
                        ),
                    )

            connection.execute(
                f"""
                INSERT INTO {GOAL_SEED_TABLE_NAME} (
                    user_id
                )
                VALUES (?)
                """,
                (
                    normalized_user_id,
                ),
            )

    except sqlite3.IntegrityError as error:
        raise DuplicateFinancialGoalError(
            "Não foi possível importar as metas "
            "iniciais por causa de nomes duplicados."
        ) from error

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível importar "
            "as metas financeiras iniciais."
        ) from error

    return list_financial_goals(
        database_path=database_path,
        user_id=normalized_user_id,
    )