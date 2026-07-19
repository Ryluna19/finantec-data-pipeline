"""Entrada rápida de uma única transação financeira."""

from __future__ import annotations

from datetime import date
from typing import Literal

import pandas as pd
import streamlit as st

from scripts.etl_transacoes import (
    ARQUIVO_BANCO,
    TABELA_TRANSACOES,
)
from src.manual_transaction_database_service import (
    save_manual_transactions_to_database,
)
from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
    create_transaction_id,
)
from src.user_context import (
    get_current_user_id,
)


QUICK_TRANSACTION_CANCELLED = "cancelled"
QUICK_TRANSACTION_SAVED = "saved"

QuickTransactionResult = Literal[
    "cancelled",
    "saved",
] | None

TRANSACTION_TYPE_OPTIONS = [
    "despesa",
    "receita",
]

TRANSACTION_CATEGORY_OPTIONS = [
    "Alimentação",
    "Transporte",
    "Serviços",
    "Assinaturas",
    "Educação",
    "Lazer",
    "Saúde",
    "Compras",
    "Trabalho",
    "Reserva",
]


def build_quick_transaction(
    *,
    transaction_date: date,
    transaction_type: str,
    description: str,
    category: str,
    amount: float,
) -> pd.DataFrame:
    """Monta uma transação única com identificador próprio."""
    return pd.DataFrame(
        [
            {
                TRANSACTION_ID_COLUMN: (
                    create_transaction_id()
                ),
                "data": transaction_date,
                "tipo": str(
                    transaction_type
                ).strip().lower(),
                "descricao": str(
                    description
                ).strip(),
                "categoria": str(
                    category
                ).strip(),
                "valor": float(
                    amount
                ),
            }
        ]
    )


def save_quick_transaction(
    transaction: pd.DataFrame,
) -> dict[str, int]:
    """Salva uma transação diretamente no SQLite do usuário."""
    return save_manual_transactions_to_database(
        transactions=transaction,
        database_path=ARQUIVO_BANCO,
        table_name=TABELA_TRANSACOES,
        user_id=get_current_user_id(),
    )


def render_quick_transaction_form() -> QuickTransactionResult:
    """Exibe um formulário compacto para um único lançamento."""
    with st.form(
        key="quick-transaction-form",
        border=False,
    ):
        date_column, type_column = st.columns(
            2,
            gap="small",
            vertical_alignment="bottom",
        )

        with date_column:
            transaction_date = st.date_input(
                "Data",
                value=date.today(),
                format="DD/MM/YYYY",
            )

        with type_column:
            transaction_type = st.selectbox(
                "Tipo",
                options=(
                    TRANSACTION_TYPE_OPTIONS
                ),
                index=0,
            )

        description = st.text_input(
            "Descrição",
            placeholder="Ex.: Compra no mercado",
        )

        category_column, amount_column = (
            st.columns(
                2,
                gap="small",
                vertical_alignment="bottom",
            )
        )

        with category_column:
            category = st.selectbox(
                "Categoria",
                options=(
                    TRANSACTION_CATEGORY_OPTIONS
                ),
                index=0,
            )

        with amount_column:
            amount = st.number_input(
                "Valor",
                min_value=0.01,
                value=0.01,
                step=1.00,
                format="%.2f",
            )

        with st.container(
            key="quick-transaction-actions",
        ):
            cancel_column, save_column = st.columns(
                2,
                gap="small",
            )

        with cancel_column:
                cancelled = st.form_submit_button(
                    "Cancelar",
                    key="quick-transaction-cancel",
                    use_container_width=True,
                )

        with save_column:
                submitted = st.form_submit_button(
                    "Salvar transação",
                    key="quick-transaction-save",
                    type="primary",
                    use_container_width=True,
                )

    if cancelled:
        return QUICK_TRANSACTION_CANCELLED

    if not submitted:
        return None

    transaction = build_quick_transaction(
        transaction_date=transaction_date,
        transaction_type=str(
            transaction_type
        ),
        description=description,
        category=str(
            category
        ),
        amount=float(
            amount
        ),
    )

    try:
        result = save_quick_transaction(
            transaction
        )

    except ValueError as error:
        st.error(
            str(
                error
            )
        )
        return None

    except Exception as error:
        st.error(
            "Não foi possível salvar a transação: "
            f"{error}"
        )
        return None

    if int(
        result.get(
            "inserted",
            0,
        )
    ) != 1:
        st.error(
            "A transação não foi inserida no banco local."
        )
        return None

    return QUICK_TRANSACTION_SAVED