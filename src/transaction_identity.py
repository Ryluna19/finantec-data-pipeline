"""Identidade estável das transações do FinanTec."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from uuid import (
    NAMESPACE_URL,
    UUID,
    uuid4,
    uuid5,
)

import pandas as pd


TRANSACTION_ID_COLUMN = "transaction_id"


def create_transaction_id() -> str:
    """Cria um identificador aleatório para uma nova transação."""
    return str(
        uuid4()
    )


def is_valid_transaction_id(
    value: object,
) -> bool:
    """Verifica se o valor representa um UUID válido."""
    if value is None:
        return False

    try:
        if pd.isna(value):
            return False
    except (
        TypeError,
        ValueError,
    ):
        return False

    text_value = str(
        value
    ).strip()

    if not text_value:
        return False

    try:
        UUID(text_value)
    except (
        TypeError,
        ValueError,
        AttributeError,
    ):
        return False

    return True


def normalize_transaction_id(
    value: object,
) -> str:
    """Normaliza um UUID existente para sua representação textual."""
    if not is_valid_transaction_id(
        value
    ):
        raise ValueError(
            "O identificador informado não é um UUID válido."
        )

    return str(
        UUID(
            str(value).strip()
        )
    )


def _normalize_text(
    value: object,
) -> str:
    """Normaliza um valor textual usado na identidade."""
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (
        TypeError,
        ValueError,
    ):
        pass

    return str(
        value
    ).strip()


def _normalize_date(
    value: object,
) -> str:
    """Normaliza uma data para gerar uma identidade determinística."""
    parsed_date = pd.to_datetime(
        value,
        errors="coerce",
    )

    if not pd.isna(
        parsed_date
    ):
        return parsed_date.strftime(
            "%Y-%m-%d"
        )

    return _normalize_text(
        value
    )


def _normalize_amount(
    value: object,
) -> str:
    """Normaliza um valor monetário para duas casas decimais."""
    parsed_amount = pd.to_numeric(
        pd.Series(
            [value]
        ),
        errors="coerce",
    ).iloc[0]

    if pd.isna(
        parsed_amount
    ):
        return _normalize_text(
            value
        )

    return f"{float(parsed_amount):.2f}"


def _normalize_identity_value(
    column: str,
    value: object,
) -> str:
    """Normaliza um campo conforme seu significado financeiro."""
    if column == "data":
        return _normalize_date(
            value
        )

    if column == "valor":
        return _normalize_amount(
            value
        )

    normalized_text = _normalize_text(
        value
    )

    if column == "tipo":
        return normalized_text.lower()

    return normalized_text


def build_transaction_signature(
    row: pd.Series,
    identity_columns: Sequence[str],
) -> str:
    """Cria a assinatura canônica dos campos financeiros."""
    payload = {
        column: _normalize_identity_value(
            column,
            row.get(
                column
            ),
        )
        for column in identity_columns
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    )


def ensure_transaction_ids(
    transactions: pd.DataFrame,
    source_key: str,
    identity_columns: Sequence[str],
) -> pd.DataFrame:
    """Preserva IDs válidos e gera IDs estáveis para linhas antigas."""
    missing_columns = [
        column
        for column in identity_columns
        if column not in transactions.columns
    ]

    if missing_columns:
        raise ValueError(
            "Não foi possível gerar os identificadores. "
            "Colunas ausentes: "
            f"{', '.join(missing_columns)}"
        )

    identified_transactions = (
        transactions.copy()
    )

    if (
        TRANSACTION_ID_COLUMN
        not in identified_transactions.columns
    ):
        identified_transactions[
            TRANSACTION_ID_COLUMN
        ] = ""

    signature_occurrences: Counter[str] = (
        Counter()
    )

    transaction_ids: list[str] = []

    for _, row in (
        identified_transactions.iterrows()
    ):
        signature = (
            build_transaction_signature(
                row,
                identity_columns,
            )
        )

        occurrence = (
            signature_occurrences[
                signature
            ]
        )

        signature_occurrences[
            signature
        ] += 1

        current_id = row.get(
            TRANSACTION_ID_COLUMN
        )

        if is_valid_transaction_id(
            current_id
        ):
            transaction_ids.append(
                normalize_transaction_id(
                    current_id
                )
            )
            continue

        identity_seed = (
            "finantec:"
            f"{source_key}:"
            f"{signature}:"
            f"{occurrence}"
        )

        transaction_ids.append(
            str(
                uuid5(
                    NAMESPACE_URL,
                    identity_seed,
                )
            )
        )

    identified_transactions[
        TRANSACTION_ID_COLUMN
    ] = pd.Series(
        transaction_ids,
        index=identified_transactions.index,
        dtype="string",
    )

    return identified_transactions