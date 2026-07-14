"""Regras compartilhadas de preparação e validação de transações."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_TRANSACTION_COLUMNS = [
    "data",
    "tipo",
    "descricao",
    "categoria",
    "valor",
]

VALID_TRANSACTION_TYPES = {
    "receita",
    "despesa",
}


def validate_required_columns(
    transactions: pd.DataFrame,
    source_file: Path,
) -> None:
    """Valida se a fonte possui todas as colunas obrigatórias."""
    missing_columns = [
        column
        for column in REQUIRED_TRANSACTION_COLUMNS
        if column not in transactions.columns
    ]

    if missing_columns:
        raise ValueError(
            f"O arquivo {source_file.name} não possui "
            f"as colunas obrigatórias: "
            f"{', '.join(missing_columns)}"
        )

def prepare_transactions(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Padroniza os valores antes da validação das transações."""
    prepared_transactions = transactions.copy()

    prepared_transactions["data"] = pd.to_datetime(
        prepared_transactions["data"],
        errors="coerce",
    )

    prepared_transactions["tipo"] = (
        prepared_transactions["tipo"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    prepared_transactions["descricao"] = (
        prepared_transactions["descricao"]
        .astype("string")
        .str.strip()
    )

    prepared_transactions["categoria"] = (
        prepared_transactions["categoria"]
        .astype("string")
        .str.strip()
    )

    prepared_transactions["valor"] = pd.to_numeric(
        prepared_transactions["valor"],
        errors="coerce",
    )

    return prepared_transactions

def add_rejection_reason(
    reasons: pd.Series,
    mask: pd.Series,
    reason: str,
) -> pd.Series:
    """Adiciona um motivo às linhas que atendem à condição informada."""
    safe_mask = pd.Series(
        mask,
        index=reasons.index,
    ).fillna(False)

    reasons.loc[safe_mask] = reasons.loc[safe_mask].apply(
        lambda current_reason: (
            reason
            if not current_reason
            else f"{current_reason}; {reason}"
        )
    )

    return reasons

def identify_rejection_reasons(
    transactions: pd.DataFrame,
) -> pd.Series:
    """Identifica todos os motivos de rejeição de cada transação."""
    reasons = pd.Series(
        "",
        index=transactions.index,
        dtype="object",
    )

    reasons = add_rejection_reason(
        reasons,
        transactions["data"].isna(),
        "data invalida ou vazia",
    )

    reasons = add_rejection_reason(
        reasons,
        transactions["tipo"].isna()
        | (transactions["tipo"] == ""),
        "tipo vazio",
    )

    reasons = add_rejection_reason(
        reasons,
        transactions["descricao"].isna()
        | (transactions["descricao"] == ""),
        "descricao vazia",
    )

    reasons = add_rejection_reason(
        reasons,
        transactions["categoria"].isna()
        | (transactions["categoria"] == ""),
        "categoria vazia",
    )

    reasons = add_rejection_reason(
        reasons,
        transactions["valor"].isna(),
        "valor invalido ou vazio",
    )

    type_is_filled = ~(
        transactions["tipo"].isna()
        | (transactions["tipo"] == "")
    )

    reasons = add_rejection_reason(
        reasons,
        type_is_filled
        & ~transactions["tipo"].isin(
            VALID_TRANSACTION_TYPES
        ),
        "tipo invalido",
    )

    value_is_filled = ~transactions["valor"].isna()

    reasons = add_rejection_reason(
        reasons,
        value_is_filled
        & (transactions["valor"] <= 0),
        "valor menor ou igual a zero",
    )

    return reasons

def split_transactions_by_validity(
    transactions: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa as transações entre válidas e rejeitadas."""
    prepared_transactions = prepare_transactions(
        transactions
    )

    rejection_reasons = identify_rejection_reasons(
        prepared_transactions
    )

    valid_rows = rejection_reasons == ""
    rejected_rows = ~valid_rows

    valid_transactions = prepared_transactions.loc[
        valid_rows
    ].copy()

    rejected_transactions = prepared_transactions.loc[
        rejected_rows
    ].copy()

    if not rejected_transactions.empty:
        rejected_transactions["motivo_rejeicao"] = (
            rejection_reasons.loc[rejected_rows]
        )

    return (
        valid_transactions,
        rejected_transactions,
    )

def finalize_valid_transactions(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona o período mensal e ordena as transações válidas."""
    finalized_transactions = transactions.copy()

    finalized_transactions["ano_mes"] = (
        finalized_transactions["data"]
        .dt.to_period("M")
        .astype(str)
    )

    return finalized_transactions.sort_values(
        by=[
            "data",
            "tipo",
            "categoria",
        ]
    ).reset_index(drop=True)

def build_rejection_message(
    rejected_transactions: pd.DataFrame,
    *,
    default_message: str,
) -> str:
    """Monta uma mensagem com os motivos de rejeição encontrados."""
    if (
        rejected_transactions.empty
        or "motivo_rejeicao"
        not in rejected_transactions.columns
    ):
        return default_message

    reasons = (
        rejected_transactions[
            "motivo_rejeicao"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if not reasons:
        return default_message

    return "; ".join(
        reasons
    )

def prepare_valid_transactions_for_database(
    transactions: pd.DataFrame,
    *,
    source: str,
) -> pd.DataFrame:
    """Finaliza transações já validadas para persistência."""
    prepared_transactions = (
        transactions.copy()
        .reset_index(
            drop=True
        )
    )

    if prepared_transactions.empty:
        return prepared_transactions

    prepared_transactions[
        "arquivo_origem"
    ] = str(
        source
    ).strip()

    prepared_transactions[
        "ano_mes"
    ] = (
        prepared_transactions["data"]
        .dt.to_period(
            "M"
        )
        .astype(str)
    )

    prepared_transactions["data"] = (
        prepared_transactions["data"]
        .dt.strftime(
            "%Y-%m-%d"
        )
    )

    return prepared_transactions