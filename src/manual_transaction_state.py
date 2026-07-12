"""Estado da entrada manual de transações."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.manual_transaction_service import (
    identify_manual_transactions,
    load_manual_transactions,
)


MANUAL_DRAFT_KEY = (
    "manual_transactions_draft"
)

MANUAL_EDIT_INDEX_KEY = (
    "manual_transaction_edit_index"
)

MANUAL_FORM_VERSION_KEY = (
    "manual_transaction_form_version"
)

MANUAL_FEEDBACK_KEY = (
    "manual_transaction_feedback"
)


def initialize_manual_transaction_state(
    source_file: Path,
    project_root: Path,
) -> None:
    """Inicializa o rascunho e os controles do editor."""
    if (
        MANUAL_DRAFT_KEY
        not in st.session_state
    ):
        st.session_state[
            MANUAL_DRAFT_KEY
        ] = (
            load_manual_transactions(
                source_file=source_file,
                project_root=project_root,
            )
            .reset_index(
                drop=True
            )
        )

    if (
        MANUAL_EDIT_INDEX_KEY
        not in st.session_state
    ):
        st.session_state[
            MANUAL_EDIT_INDEX_KEY
        ] = None

    if (
        MANUAL_FORM_VERSION_KEY
        not in st.session_state
    ):
        st.session_state[
            MANUAL_FORM_VERSION_KEY
        ] = 0


def get_manual_draft() -> pd.DataFrame:
    """Retorna uma cópia do rascunho atual."""
    draft = st.session_state.get(
        MANUAL_DRAFT_KEY
    )

    if not isinstance(
        draft,
        pd.DataFrame,
    ):
        raise RuntimeError(
            "O estado das transações manuais "
            "ainda não foi inicializado."
        )

    return draft.copy()


def set_manual_draft(
    transactions: pd.DataFrame,
    source_file: Path,
    project_root: Path,
) -> None:
    """Atualiza o rascunho preservando IDs estáveis."""
    identified_transactions = (
        identify_manual_transactions(
            transactions=transactions,
            source_file=source_file,
            project_root=project_root,
        )
    )

    st.session_state[
        MANUAL_DRAFT_KEY
    ] = (
        identified_transactions
        .copy()
        .reset_index(
            drop=True
        )
    )


def get_manual_edit_index() -> int | None:
    """Retorna o índice atualmente em edição."""
    edit_index = st.session_state.get(
        MANUAL_EDIT_INDEX_KEY
    )

    if edit_index is None:
        return None

    return int(
        edit_index
    )


def get_manual_form_version() -> int:
    """Retorna a versão atual do formulário."""
    return int(
        st.session_state.get(
            MANUAL_FORM_VERSION_KEY,
            0,
        )
    )


def _advance_manual_form_version() -> None:
    """Incrementa a versão usada nas chaves dos widgets."""
    st.session_state[
        MANUAL_FORM_VERSION_KEY
    ] = (
        get_manual_form_version()
        + 1
    )


def reset_manual_form() -> None:
    """Retorna o formulário ao modo de inclusão."""
    st.session_state[
        MANUAL_EDIT_INDEX_KEY
    ] = None

    _advance_manual_form_version()


def start_manual_edit(
    index: int,
) -> None:
    """Ativa a edição de uma linha do rascunho."""
    if index < 0:
        raise ValueError(
            "O índice de edição não pode ser negativo."
        )

    st.session_state[
        MANUAL_EDIT_INDEX_KEY
    ] = index

    _advance_manual_form_version()


def adjust_edit_index_after_removal(
    removed_index: int,
) -> None:
    """Ajusta a edição depois da remoção de uma linha."""
    current_edit_index = (
        get_manual_edit_index()
    )

    if current_edit_index == removed_index:
        st.session_state[
            MANUAL_EDIT_INDEX_KEY
        ] = None

    elif (
        current_edit_index is not None
        and current_edit_index > removed_index
    ):
        st.session_state[
            MANUAL_EDIT_INDEX_KEY
        ] = (
            current_edit_index - 1
        )

    _advance_manual_form_version()


def set_manual_feedback(
    message: str,
) -> None:
    """Guarda uma mensagem para o próximo ciclo."""
    st.session_state[
        MANUAL_FEEDBACK_KEY
    ] = message


def pop_manual_feedback() -> str | None:
    """Consome a mensagem de feedback existente."""
    feedback = st.session_state.pop(
        MANUAL_FEEDBACK_KEY,
        None,
    )

    if feedback is None:
        return None

    return str(
        feedback
    )


def invalidate_manual_draft() -> None:
    """Descarta o rascunho e encerra a edição atual."""
    st.session_state.pop(
        MANUAL_DRAFT_KEY,
        None,
    )

    st.session_state[
        MANUAL_EDIT_INDEX_KEY
    ] = None

    _advance_manual_form_version()