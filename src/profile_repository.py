"""Persistência do perfil financeiro do usuário."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


PROFILE_TABLE_NAME = "user_profiles"


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


def _ensure_profile_table(
    connection: sqlite3.Connection,
) -> None:
    """Cria a tabela de perfis quando necessário."""
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {PROFILE_TABLE_NAME} (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            occupation TEXT NOT NULL DEFAULT '',
            monthly_income REAL NOT NULL DEFAULT 0,
            profile_data TEXT NOT NULL,
            created_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            CHECK (
                monthly_income >= 0
            )
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


def _normalize_text(
    value: object,
    field_label: str,
    *,
    required: bool = False,
    maximum_length: int = 500,
) -> str:
    """Normaliza um campo textual."""
    text = (
        ""
        if value is None
        else str(value).strip()
    )

    if required and not text:
        raise ValueError(
            f"{field_label} não pode ser vazio."
        )

    if len(text) > maximum_length:
        raise ValueError(
            f"{field_label} deve possuir no máximo "
            f"{maximum_length} caracteres."
        )

    return text


def _normalize_age(
    value: object,
) -> int | None:
    """Normaliza uma idade opcional."""
    if (
        value is None
        or str(value).strip() == ""
    ):
        return None

    try:
        numeric_age = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "A idade deve ser um número inteiro."
        ) from error

    if not numeric_age.is_integer():
        raise ValueError(
            "A idade deve ser um número inteiro."
        )

    age = int(
        numeric_age
    )

    if (
        age < 0
        or age > 130
    ):
        raise ValueError(
            "A idade deve estar entre 0 e 130."
        )

    return age


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


def _normalize_boolean(
    value: object,
) -> bool:
    """Converte valores comuns para booleano."""
    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        return bool(
            value
        )

    normalized_value = str(
        value
    ).strip().lower()

    truthy_values = {
        "1",
        "true",
        "sim",
        "yes",
    }

    falsy_values = {
        "",
        "0",
        "false",
        "não",
        "nao",
        "no",
        "none",
    }

    if normalized_value in truthy_values:
        return True

    if normalized_value in falsy_values:
        return False

    raise ValueError(
        "O valor booleano informado é inválido."
    )


def _normalize_income_sources(
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Normaliza as fontes de renda do perfil."""
    raw_sources = profile.get(
        "fontes_de_renda",
        [],
    )

    if raw_sources is None:
        return []

    if not isinstance(
        raw_sources,
        list,
    ):
        raise ValueError(
            "As fontes de renda devem ser uma lista."
        )

    normalized_sources: list[
        dict[str, Any]
    ] = []

    for index, source in enumerate(
        raw_sources,
        start=1,
    ):
        if not isinstance(
            source,
            dict,
        ):
            raise ValueError(
                "Cada fonte de renda deve "
                "ser um objeto válido."
            )

        source_type = _normalize_text(
            source.get(
                "tipo"
            ),
            (
                "O tipo da fonte de renda "
                f"{index}"
            ),
            required=True,
            maximum_length=100,
        )

        monthly_value = (
            _normalize_non_negative_amount(
                source.get(
                    "valor_mensal",
                    0,
                ),
                (
                    "O valor mensal da fonte "
                    f"de renda {index}"
                ),
            )
        )

        normalized_sources.append(
            {
                "tipo": source_type,
                "valor_mensal": (
                    monthly_value
                ),
            }
        )

    return normalized_sources


def _normalize_current_situation(
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Normaliza informações complementares do perfil."""
    raw_situation = profile.get(
        "situacao_atual",
        {},
    )

    if raw_situation is None:
        raw_situation = {}

    if not isinstance(
        raw_situation,
        dict,
    ):
        raise ValueError(
            "A situação atual deve ser "
            "um objeto válido."
        )

    normalized_situation: dict[
        str,
        Any,
    ] = {
        "possui_dividas": (
            _normalize_boolean(
                raw_situation.get(
                    "possui_dividas",
                    False,
                )
            )
        ),
        "utiliza_cartao_de_credito": (
            _normalize_boolean(
                raw_situation.get(
                    "utiliza_cartao_de_credito",
                    False,
                )
            )
        ),
        "observacao": _normalize_text(
            raw_situation.get(
                "observacao",
                "",
            ),
            "A observação",
            maximum_length=1000,
        ),
    }

    optional_amount_fields = (
        "reserva_antes_do_mes",
        "valor_separado_no_mes",
        "reserva_atual",
    )

    for field_name in optional_amount_fields:
        if field_name not in raw_situation:
            continue

        normalized_situation[
            field_name
        ] = _normalize_non_negative_amount(
            raw_situation[
                field_name
            ],
            field_name,
        )

    return normalized_situation


def _normalize_preferences(
    profile: dict[str, Any],
) -> dict[str, str]:
    """Normaliza preferências de comunicação."""
    raw_preferences = profile.get(
        "preferencias_de_comunicacao",
        {},
    )

    if raw_preferences is None:
        raw_preferences = {}

    if not isinstance(
        raw_preferences,
        dict,
    ):
        raise ValueError(
            "As preferências de comunicação "
            "devem ser um objeto válido."
        )

    return {
        "tom": _normalize_text(
            raw_preferences.get(
                "tom",
                "claro, direto e educativo",
            ),
            "O tom de comunicação",
            required=True,
            maximum_length=100,
        ),
        "nivel_de_conhecimento_financeiro": (
            _normalize_text(
                raw_preferences.get(
                    "nivel_de_conhecimento_financeiro",
                    "iniciante",
                ),
                (
                    "O nível de conhecimento "
                    "financeiro"
                ),
                required=True,
                maximum_length=50,
            )
        ),
    }


def normalize_user_profile(
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Valida e normaliza os dados do perfil."""
    if not isinstance(
        profile,
        dict,
    ):
        raise ValueError(
            "O perfil deve ser um objeto válido."
        )

    name = _normalize_text(
        profile.get(
            "nome"
        ),
        "O nome",
        required=True,
        maximum_length=120,
    )

    normalized_profile: dict[
        str,
        Any,
    ] = {
        "nome": name,
    }

    if "idade" in profile:
        normalized_profile[
            "idade"
        ] = _normalize_age(
            profile[
                "idade"
            ]
        )

    if "ocupacao" in profile:
        normalized_profile[
            "ocupacao"
        ] = _normalize_text(
            profile[
                "ocupacao"
            ],
            "A ocupação",
            maximum_length=150,
        )

    if "renda_mensal_principal" in profile:
        normalized_profile[
            "renda_mensal_principal"
        ] = _normalize_non_negative_amount(
            profile[
                "renda_mensal_principal"
            ],
            "A renda mensal principal",
        )

    if "fontes_de_renda" in profile:
        normalized_profile[
            "fontes_de_renda"
        ] = _normalize_income_sources(
            profile
        )

    if "situacao_atual" in profile:
        normalized_profile[
            "situacao_atual"
        ] = _normalize_current_situation(
            profile
        )

    if (
        "preferencias_de_comunicacao"
        in profile
    ):
        normalized_profile[
            "preferencias_de_comunicacao"
        ] = _normalize_preferences(
            profile
        )

    return normalized_profile


def load_user_profile(
    database_path: Path,
    user_id: str,
) -> dict[str, Any] | None:
    """Carrega o perfil de um usuário."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_profile_table(
                connection
            )

            row = connection.execute(
                f"""
                SELECT
                    user_id,
                    profile_data
                FROM {PROFILE_TABLE_NAME}
                WHERE user_id = ?
                """,
                (
                    normalized_user_id,
                ),
            ).fetchone()

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível carregar "
            "o perfil do usuário."
        ) from error

    if row is None:
        return None

    try:
        profile_data = json.loads(
            row[
                "profile_data"
            ]
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ) as error:
        raise RuntimeError(
            "O perfil armazenado possui "
            "um formato inválido."
        ) from error

    return {
        "user_id": str(
            row[
                "user_id"
            ]
        ),
        **profile_data,
    }


def save_user_profile(
    database_path: Path,
    user_id: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Cria ou atualiza o perfil de um usuário."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    normalized_profile = (
        normalize_user_profile(
            profile
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_profile_table(
                connection
            )

            existing_row = connection.execute(
                f"""
                SELECT
                    occupation,
                    monthly_income,
                    profile_data
                FROM {PROFILE_TABLE_NAME}
                WHERE user_id = ?
                """,
                (
                    normalized_user_id,
                ),
            ).fetchone()

            if existing_row is None:
                stored_profile = dict(
                    normalized_profile
                )
                stored_occupation = (
                    normalized_profile.get(
                        "ocupacao",
                        "",
                    )
                )
                stored_monthly_income = (
                    normalized_profile.get(
                        "renda_mensal_principal",
                        0,
                    )
                )

            else:
                try:
                    existing_profile = json.loads(
                        existing_row[
                            "profile_data"
                        ]
                    )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ) as error:
                    raise RuntimeError(
                        "O perfil armazenado possui "
                        "um formato inválido."
                    ) from error

                if not isinstance(
                    existing_profile,
                    dict,
                ):
                    raise RuntimeError(
                        "O perfil armazenado possui "
                        "um formato inválido."
                    )

                stored_profile = {
                    **existing_profile,
                    **normalized_profile,
                }
                stored_occupation = (
                    normalized_profile.get(
                        "ocupacao",
                        existing_row[
                            "occupation"
                        ],
                    )
                )
                stored_monthly_income = (
                    normalized_profile.get(
                        "renda_mensal_principal",
                        existing_row[
                            "monthly_income"
                        ],
                    )
                )

            serialized_profile = json.dumps(
                stored_profile,
                ensure_ascii=False,
                separators=(
                    ",",
                    ":",
                ),
            )

            connection.execute(
                f"""
                INSERT INTO {PROFILE_TABLE_NAME} (
                    user_id,
                    name,
                    occupation,
                    monthly_income,
                    profile_data
                )
                VALUES (?, ?, ?, ?, ?)

                ON CONFLICT(user_id)
                DO UPDATE SET
                    name = excluded.name,
                    occupation = excluded.occupation,
                    monthly_income = excluded.monthly_income,
                    profile_data = excluded.profile_data,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    normalized_user_id,
                    stored_profile[
                        "nome"
                    ],
                    stored_occupation,
                    stored_monthly_income,
                    serialized_profile,
                ),
            )

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível salvar "
            "o perfil do usuário."
        ) from error

    return {
        "user_id": normalized_user_id,
        **stored_profile,
    }


def seed_user_profile_if_missing(
    database_path: Path,
    user_id: str,
    seed_profile: dict[str, Any],
) -> dict[str, Any]:
    """Cria o perfil inicial somente quando ele não existir."""
    existing_profile = (
        load_user_profile(
            database_path=database_path,
            user_id=user_id,
        )
    )

    if existing_profile is not None:
        return existing_profile

    return save_user_profile(
        database_path=database_path,
        user_id=user_id,
        profile=seed_profile,
    )


def delete_user_profile(
    database_path: Path,
    user_id: str,
) -> bool:
    """Exclui o perfil informado."""
    normalized_user_id = (
        _normalize_user_id(
            user_id
        )
    )

    try:
        with _connect(
            database_path
        ) as connection:
            _ensure_profile_table(
                connection
            )

            cursor = connection.execute(
                f"""
                DELETE FROM {PROFILE_TABLE_NAME}
                WHERE user_id = ?
                """,
                (
                    normalized_user_id,
                ),
            )

    except sqlite3.Error as error:
        raise RuntimeError(
            "Não foi possível excluir "
            "o perfil do usuário."
        ) from error

    return (
        cursor.rowcount > 0
    )
