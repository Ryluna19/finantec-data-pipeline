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
    """Cria e atualiza a estrutura dos orçamentos."""
    connection.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS {BUDGET_TABLE_NAME} (
            budget_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            period TEXT NOT NULL,
            end_period TEXT,
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

            CHECK (
                end_period IS NULL
                OR end_period >= period
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

    columns = {
        str(
            row["name"]
        )
        for row in connection.execute(
            f"""
            PRAGMA table_info(
                {BUDGET_TABLE_NAME}
            )
            """
        ).fetchall()
    }

    if "end_period" not in columns:
        connection.execute(
            f"""
            ALTER TABLE {BUDGET_TABLE_NAME}
            ADD COLUMN end_period TEXT
            """
        )

        # Limites antigos eram válidos apenas no mês cadastrado.
        connection.execute(
            f"""
            UPDATE {BUDGET_TABLE_NAME}
            SET end_period = period
            WHERE end_period IS NULL
            """
        )

    connection.execute(
        f"""
        CREATE INDEX IF NOT EXISTS
            idx_monthly_budgets_user_active_period
        ON {BUDGET_TABLE_NAME} (
            user_id,
            category_key,
            period,
            end_period
        )
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

def _normalize_end_period(
    value: object,
    *,
    start_period: str,
) -> str | None:
    """Valida o último mês de vigência do limite."""
    if value is None:
        return None

    end_period_text = str(
        value
    ).strip()

    if not end_period_text:
        return None

    end_period = _normalize_period(
        end_period_text
    )

    if end_period < start_period:
        raise ValueError(
            "O fim da vigência do orçamento "
            "não pode ser anterior ao mês inicial."
        )

    return end_period

def _get_previous_period(
    period: str,
) -> str:
    """Retorna o mês imediatamente anterior ao período informado."""
    normalized_period = _normalize_period(
        period
    )

    year_text, month_text = (
        normalized_period.split(
            "-",
            maxsplit=1,
        )
    )

    year = int(
        year_text
    )

    month = int(
        month_text
    )

    if month == 1:
        return (
            f"{year - 1:04d}-12"
        )

    return (
        f"{year:04d}-"
        f"{month - 1:02d}"
    )


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

    end_period = _normalize_end_period(
        budget.get(
            "end_period"
        ),
        start_period=period,
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
        "end_period": end_period,
        "category": category,
        "category_key": category_key,
        "planned_amount": planned_amount,
    }


def _row_to_budget(
    row: sqlite3.Row,
) -> dict[str, Any]:
    """Converte uma linha do banco para a aplicação."""
    end_period = row[
        "end_period"
    ]

    return {
        "budget_id": str(
            row["budget_id"]
        ),
        "period": str(
            row["period"]
        ),
        "end_period": (
            str(
                end_period
            )
            if end_period is not None
            else None
        ),
        "category": str(
            row["category"]
        ),
        "planned_amount": float(
            row["planned_amount"]
        ),
    }

def _has_overlapping_budget(
    connection: sqlite3.Connection,
    *,
    user_id: str,
    category_key: str,
    start_period: str,
    end_period: str | None,
    excluded_budget_id: str | None = None,
) -> bool:
    """Verifica se uma categoria já possui vigência sobreposta."""
    query = f"""
        SELECT
            budget_id
        FROM {BUDGET_TABLE_NAME}
        WHERE
            user_id = ?
            AND category_key = ?
            AND (
                end_period IS NULL
                OR end_period >= ?
            )
            AND (
                ? IS NULL
                OR period <= ?
            )
    """

    parameters: list[object] = [
        user_id,
        category_key,
        start_period,
        end_period,
        end_period,
    ]

    if excluded_budget_id is not None:
        query += """
            AND budget_id <> ?
        """

        parameters.append(
            excluded_budget_id
        )

    query += """
        LIMIT 1
    """

    row = connection.execute(
        query,
        parameters,
    ).fetchone()

    return row is not None

def list_monthly_budget_periods(
    database_path: Path,
    user_id: str,
) -> list[str]:
    """Lista os períodos que possuem orçamento salvo para o usuário."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
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
                SELECT DISTINCT
                    period
                FROM {BUDGET_TABLE_NAME}
                WHERE
                    user_id = ?
                ORDER BY
                    period DESC
                """,
                (
                    normalized_user_id,
                ),
            ).fetchall()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "os períodos dos orçamentos mensais."
        ) from error

    return [
        str(
            row[
                "period"
            ]
        )
        for row in rows
    ]


def list_monthly_budgets(
    database_path: Path,
    user_id: str,
    period: str,
) -> list[dict[str, Any]]:
    """Lista os orçamentos iniciados em um período."""
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
                    end_period,
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

def list_active_monthly_budgets(
    database_path: Path,
    user_id: str,
    period: str,
) -> list[dict[str, Any]]:
    """Lista os limites vigentes em determinado mês."""
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
                    end_period,
                    category,
                    planned_amount
                FROM {BUDGET_TABLE_NAME}
                WHERE
                    user_id = ?
                    AND period <= ?
                    AND (
                        end_period IS NULL
                        OR end_period >= ?
                    )
                ORDER BY
                    category_key ASC,
                    category ASC
                """,
                (
                    normalized_user_id,
                    normalized_period,
                    normalized_period,
                ),
            ).fetchall()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "os orçamentos vigentes."
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
                    end_period,
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
    """Cria uma regra de orçamento por categoria."""
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

            if _has_overlapping_budget(
                connection,
                user_id=normalized_user_id,
                category_key=normalized_budget[
                    "category_key"
                ],
                start_period=normalized_budget[
                    "period"
                ],
                end_period=normalized_budget[
                    "end_period"
                ],
            ):
                raise DuplicateMonthlyBudgetError(
                    "Já existe um orçamento para "
                    "essa categoria com vigência sobreposta."
                )

            try:
                connection.execute(
                    f"""
                    INSERT INTO {BUDGET_TABLE_NAME} (
                        budget_id,
                        user_id,
                        period,
                        end_period,
                        category,
                        category_key,
                        planned_amount
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        budget_id,
                        normalized_user_id,
                        normalized_budget[
                            "period"
                        ],
                        normalized_budget[
                            "end_period"
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
    """Atualiza uma regra de orçamento existente."""
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

    if not isinstance(
        budget,
        dict,
    ):
        raise ValueError(
            "O orçamento deve ser um objeto válido."
        )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_budget_table(
                connection
            )

            existing_row = connection.execute(
                f"""
                SELECT
                    budget_id,
                    period,
                    end_period,
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

            if existing_row is None:
                raise MonthlyBudgetNotFoundError(
                    "O orçamento informado "
                    "não foi encontrado."
                )

            budget_to_normalize = dict(
                budget
            )

            # Enquanto a interface antiga não envia vigência,
            # preserva o valor já salvo durante uma edição.
            if "end_period" not in budget_to_normalize:
                budget_to_normalize[
                    "end_period"
                ] = existing_row[
                    "end_period"
                ]

            normalized_budget = (
                normalize_monthly_budget(
                    budget_to_normalize
                )
            )

            if _has_overlapping_budget(
                connection,
                user_id=normalized_user_id,
                category_key=normalized_budget[
                    "category_key"
                ],
                start_period=normalized_budget[
                    "period"
                ],
                end_period=normalized_budget[
                    "end_period"
                ],
                excluded_budget_id=normalized_budget_id,
            ):
                raise DuplicateMonthlyBudgetError(
                    "Já existe um orçamento para "
                    "essa categoria com vigência sobreposta."
                )

            try:
                cursor = connection.execute(
                    f"""
                    UPDATE {BUDGET_TABLE_NAME}
                    SET
                        period = ?,
                        end_period = ?,
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
                            "end_period"
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


def split_monthly_budget_from_period(
    database_path: Path,
    user_id: str,
    budget_id: str,
    split_period: str,
    budget: dict[str, Any],
) -> dict[str, Any]:
    """Cria uma nova regra preservando os meses anteriores."""
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

    normalized_split_period = (
        _normalize_period(
            split_period
        )
    )

    if not isinstance(
        budget,
        dict,
    ):
        raise ValueError(
            "O orçamento deve ser um objeto válido."
        )

    new_budget_id = str(
        uuid4()
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_budget_table(
                connection
            )

            existing_row = connection.execute(
                f"""
                SELECT
                    budget_id,
                    period,
                    end_period,
                    category,
                    category_key,
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

            if existing_row is None:
                raise MonthlyBudgetNotFoundError(
                    "O orçamento informado "
                    "não foi encontrado."
                )

            start_period = str(
                existing_row[
                    "period"
                ]
            )

            existing_end_period_value = (
                existing_row[
                    "end_period"
                ]
            )

            existing_end_period = (
                str(
                    existing_end_period_value
                )
                if existing_end_period_value is not None
                else None
            )

            if normalized_split_period <= start_period:
                raise ValueError(
                    "O mês da alteração deve ser posterior "
                    "ao início do limite."
                )

            if (
                existing_end_period is not None
                and normalized_split_period > existing_end_period
            ):
                raise ValueError(
                    "O mês da alteração está fora "
                    "da vigência do limite."
                )

            budget_to_normalize = dict(
                budget
            )

            budget_to_normalize[
                "period"
            ] = normalized_split_period

            if "end_period" not in budget_to_normalize:
                budget_to_normalize[
                    "end_period"
                ] = existing_end_period

            normalized_budget = (
                normalize_monthly_budget(
                    budget_to_normalize
                )
            )

            if _has_overlapping_budget(
                connection,
                user_id=normalized_user_id,
                category_key=normalized_budget[
                    "category_key"
                ],
                start_period=normalized_budget[
                    "period"
                ],
                end_period=normalized_budget[
                    "end_period"
                ],
                excluded_budget_id=normalized_budget_id,
            ):
                raise DuplicateMonthlyBudgetError(
                    "Já existe um orçamento para "
                    "essa categoria com vigência sobreposta."
                )

            previous_period = (
                _get_previous_period(
                    normalized_split_period
                )
            )

            try:
                connection.execute(
                    f"""
                    UPDATE {BUDGET_TABLE_NAME}
                    SET
                        end_period = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE
                        user_id = ?
                        AND budget_id = ?
                    """,
                    (
                        previous_period,
                        normalized_user_id,
                        normalized_budget_id,
                    ),
                )

                connection.execute(
                    f"""
                    INSERT INTO {BUDGET_TABLE_NAME} (
                        budget_id,
                        user_id,
                        period,
                        end_period,
                        category,
                        category_key,
                        planned_amount
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        new_budget_id,
                        normalized_user_id,
                        normalized_budget[
                            "period"
                        ],
                        normalized_budget[
                            "end_period"
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
                    "Não foi possível criar a nova vigência "
                    "porque ela entra em conflito com "
                    "outro orçamento."
                ) from error

            created_row = connection.execute(
                f"""
                SELECT
                    budget_id,
                    period,
                    end_period,
                    category,
                    planned_amount
                FROM {BUDGET_TABLE_NAME}
                WHERE
                    user_id = ?
                    AND budget_id = ?
                """,
                (
                    normalized_user_id,
                    new_budget_id,
                ),
            ).fetchone()

            if created_row is None:
                raise RuntimeError(
                    "A nova vigência foi criada, mas não "
                    "pôde ser carregada novamente."
                )

            created_budget = (
                _row_to_budget(
                    created_row
                )
            )

    except (
        DuplicateMonthlyBudgetError,
        MonthlyBudgetNotFoundError,
        ValueError,
        RuntimeError,
    ):
        raise

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível alterar o orçamento "
            "a partir do período informado."
        ) from error

    return created_budget


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