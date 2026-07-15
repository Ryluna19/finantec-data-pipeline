"""Persistência dos orçamentos mensais por categoria."""

from __future__ import annotations

import math
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any
from uuid import uuid4


BUDGET_TABLE_NAME = "monthly_budgets"

_PERIOD_PATTERN = re.compile(
    r"^\d{4}-(0[1-9]|1[0-2])$"
)


class MonthlyBudgetNotFoundError(
    RuntimeError
):
    """Indica que um orçamento mensal não foi encontrado."""


class DuplicateMonthlyBudgetError(
    ValueError
):
    """Indica orçamento duplicado para categoria e período."""


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


def _ensure_budget_table(
    connection: sqlite3.Connection,
) -> None:
    """Cria a estrutura necessária para os orçamentos."""
    connection.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS {BUDGET_TABLE_NAME} (
            budget_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            period TEXT NOT NULL,
            category TEXT NOT NULL,
            category_key TEXT NOT NULL,
            planned_amount REAL NOT NULL,
            created_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            CHECK (
                planned_amount > 0
            ),

            UNIQUE (
                user_id,
                period,
                category_key
            )
        );

        CREATE INDEX IF NOT EXISTS
            idx_monthly_budgets_user_period
        ON {BUDGET_TABLE_NAME} (
            user_id,
            period,
            category_key
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


def _normalize_budget_id(
    budget_id: str,
) -> str:
    """Valida o identificador do orçamento."""
    normalized_budget_id = str(
        budget_id
    ).strip()

    if not normalized_budget_id:
        raise ValueError(
            "O identificador do orçamento "
            "não pode ser vazio."
        )

    return normalized_budget_id


def _normalize_period(
    value: object,
) -> str:
    """Valida o período mensal no formato AAAA-MM."""
    period = str(
        value
        if value is not None
        else ""
    ).strip()

    if not _PERIOD_PATTERN.fullmatch(
        period
    ):
        raise ValueError(
            "O período deve estar no formato AAAA-MM."
        )

    return period


def _build_category_key(
    category: str,
) -> str:
    """Cria uma chave comparável para a categoria."""
    normalized = unicodedata.normalize(
        "NFKD",
        category,
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


def _normalize_category(
    value: object,
) -> tuple[str, str]:
    """Valida a categoria e cria sua chave normalizada."""
    category = " ".join(
        str(
            value
            if value is not None
            else ""
        )
        .strip()
        .split()
    )

    if not category:
        raise ValueError(
            "A categoria do orçamento "
            "não pode ser vazia."
        )

    if len(category) > 100:
        raise ValueError(
            "A categoria do orçamento deve possuir "
            "no máximo 100 caracteres."
        )

    category_key = _build_category_key(
        category
    )

    if category_key == "reserva":
        raise ValueError(
            "A categoria Reserva não entra "
            "no orçamento de consumo."
        )

    return (
        category,
        category_key,
    )


def _normalize_planned_amount(
    value: object,
) -> float:
    """Valida o valor planejado."""
    try:
        planned_amount = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "O valor planejado deve ser "
            "um número válido."
        ) from error

    if (
        not math.isfinite(
            planned_amount
        )
        or planned_amount <= 0
    ):
        raise ValueError(
            "O valor planejado deve ser "
            "maior que zero."
        )

    return planned_amount


def normalize_monthly_budget(
    budget: dict[str, Any],
) -> dict[str, Any]:
    """Valida e normaliza um orçamento mensal."""
    if not isinstance(
        budget,
        dict,
    ):
        raise ValueError(
            "O orçamento deve ser um objeto válido."
        )

    period = _normalize_period(
        budget.get(
            "period"
        )
    )

    (
        category,
        category_key,
    ) = _normalize_category(
        budget.get(
            "category"
        )
    )

    planned_amount = (
        _normalize_planned_amount(
            budget.get(
                "planned_amount"
            )
        )
    )

    return {
        "period": period,
        "category": category,
        "category_key": category_key,
        "planned_amount": planned_amount,
    }


def _row_to_budget(
    row: sqlite3.Row,
) -> dict[str, Any]:
    """Converte uma linha do banco para a aplicação."""
    return {
        "budget_id": str(
            row["budget_id"]
        ),
        "period": str(
            row["period"]
        ),
        "category": str(
            row["category"]
        ),
        "planned_amount": float(
            row["planned_amount"]
        ),
    }


def list_monthly_budgets(
    database_path: Path,
    user_id: str,
    period: str,
) -> list[dict[str, Any]]:
    """Lista os orçamentos do usuário em um período."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    normalized_period = (
        _normalize_period(
            period
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_budget_table(
                connection
            )

            rows = connection.execute(
                f"""
                SELECT
                    budget_id,
                    period,
                    category,
                    planned_amount
                FROM {BUDGET_TABLE_NAME}
                WHERE
                    user_id = ?
                    AND period = ?
                ORDER BY
                    category_key ASC,
                    category ASC
                """,
                (
                    normalized_user_id,
                    normalized_period,
                ),
            ).fetchall()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "os orçamentos mensais."
        ) from error

    return [
        _row_to_budget(
            row
        )
        for row in rows
    ]


def get_monthly_budget(
    database_path: Path,
    user_id: str,
    budget_id: str,
) -> dict[str, Any] | None:
    """Carrega um orçamento mensal específico."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    normalized_budget_id = (
        _normalize_budget_id(
            budget_id
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_budget_table(
                connection
            )

            row = connection.execute(
                f"""
                SELECT
                    budget_id,
                    period,
                    category,
                    planned_amount
                FROM {BUDGET_TABLE_NAME}
                WHERE
                    user_id = ?
                    AND budget_id = ?
                """,
                (
                    normalized_user_id,
                    normalized_budget_id,
                ),
            ).fetchone()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "o orçamento mensal."
        ) from error

    if row is None:
        return None

    return _row_to_budget(
        row
    )


def create_monthly_budget(
    database_path: Path,
    user_id: str,
    budget: dict[str, Any],
) -> dict[str, Any]:
    """Cria um orçamento mensal por categoria."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    normalized_budget = (
        normalize_monthly_budget(
            budget
        )
    )

    budget_id = str(
        uuid4()
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_budget_table(
                connection
            )

            try:
                connection.execute(
                    f"""
                    INSERT INTO {BUDGET_TABLE_NAME} (
                        budget_id,
                        user_id,
                        period,
                        category,
                        category_key,
                        planned_amount
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        budget_id,
                        normalized_user_id,
                        normalized_budget[
                            "period"
                        ],
                        normalized_budget[
                            "category"
                        ],
                        normalized_budget[
                            "category_key"
                        ],
                        normalized_budget[
                            "planned_amount"
                        ],
                    ),
                )

            except sqlite3.IntegrityError as error:
                raise DuplicateMonthlyBudgetError(
                    "Já existe um orçamento para "
                    "essa categoria no período."
                ) from error

    except DuplicateMonthlyBudgetError:
        raise

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível criar "
            "o orçamento mensal."
        ) from error

    created_budget = get_monthly_budget(
        database_path=database_path,
        user_id=normalized_user_id,
        budget_id=budget_id,
    )

    if created_budget is None:
        raise RuntimeError(
            "O orçamento foi criado, mas não "
            "pôde ser carregado novamente."
        )

    return created_budget


def update_monthly_budget(
    database_path: Path,
    user_id: str,
    budget_id: str,
    budget: dict[str, Any],
) -> dict[str, Any]:
    """Atualiza um orçamento mensal existente."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    normalized_budget_id = (
        _normalize_budget_id(
            budget_id
        )
    )

    normalized_budget = (
        normalize_monthly_budget(
            budget
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_budget_table(
                connection
            )

            try:
                cursor = connection.execute(
                    f"""
                    UPDATE {BUDGET_TABLE_NAME}
                    SET
                        period = ?,
                        category = ?,
                        category_key = ?,
                        planned_amount = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE
                        user_id = ?
                        AND budget_id = ?
                    """,
                    (
                        normalized_budget[
                            "period"
                        ],
                        normalized_budget[
                            "category"
                        ],
                        normalized_budget[
                            "category_key"
                        ],
                        normalized_budget[
                            "planned_amount"
                        ],
                        normalized_user_id,
                        normalized_budget_id,
                    ),
                )

            except sqlite3.IntegrityError as error:
                raise DuplicateMonthlyBudgetError(
                    "Já existe um orçamento para "
                    "essa categoria no período."
                ) from error

            if cursor.rowcount == 0:
                raise MonthlyBudgetNotFoundError(
                    "O orçamento informado "
                    "não foi encontrado."
                )

    except (
        DuplicateMonthlyBudgetError,
        MonthlyBudgetNotFoundError,
    ):
        raise

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível atualizar "
            "o orçamento mensal."
        ) from error

    updated_budget = get_monthly_budget(
        database_path=database_path,
        user_id=normalized_user_id,
        budget_id=normalized_budget_id,
    )

    if updated_budget is None:
        raise RuntimeError(
            "O orçamento foi atualizado, mas não "
            "pôde ser carregado novamente."
        )

    return updated_budget


def delete_monthly_budget(
    database_path: Path,
    user_id: str,
    budget_id: str,
) -> bool:
    """Exclui um orçamento mensal."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    normalized_budget_id = (
        _normalize_budget_id(
            budget_id
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_budget_table(
                connection
            )

            cursor = connection.execute(
                f"""
                DELETE FROM {BUDGET_TABLE_NAME}
                WHERE
                    user_id = ?
                    AND budget_id = ?
                """,
                (
                    normalized_user_id,
                    normalized_budget_id,
                ),
            )

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível excluir "
            "o orçamento mensal."
        ) from error

    return cursor.rowcount > 0