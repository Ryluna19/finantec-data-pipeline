"""Gerenciamento de transações já persistidas."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from analytics import (
    formatar_moeda as format_currency,
)
from components.data_management import (
    DATA_MODE_KEY,
)
from scripts.etl_transacoes import (
    run_etl_with_summary,
)
from src.transaction_editor import (
    ARQUIVO_TRANSACOES_MANUAIS,
    DATA_REFRESH_REQUESTED_KEY,
    MANUAL_DRAFT_KEY,
    MANUAL_EDIT_INDEX_KEY,
    MANUAL_FORM_VERSION_KEY,
)
from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
    is_valid_transaction_id,
)
from src.transaction_sources import (
    DuplicateTransactionIdError,
    TransactionNotFoundError,
    delete_transaction_from_source,
)
from ui_components import (
    TRANSACTION_TYPE_LABELS,
)


TRANSACTION_MANAGEMENT_FEEDBACK_KEY = (
    "transaction_management_feedback"
)

TRANSACTION_MANAGEMENT_VERSION_KEY = (
    "transaction_management_version"
)


def _set_management_feedback(
    message_type: str,
    message: str,
) -> None:
    """Guarda o resultado da última operação persistida."""
    st.session_state[
        TRANSACTION_MANAGEMENT_FEEDBACK_KEY
    ] = {
        "type": message_type,
        "message": message,
    }


def _show_management_feedback() -> None:
    """Exibe o resultado preservado após o rerun."""
    feedback = st.session_state.pop(
        TRANSACTION_MANAGEMENT_FEEDBACK_KEY,
        None,
    )

    if not feedback:
        return

    message_type = feedback[
        "type"
    ]

    message = feedback[
        "message"
    ]

    if message_type == "success":
        st.success(
            message
        )
        return

    if message_type == "warning":
        st.warning(
            message
        )
        return

    st.error(
        message
    )


def _get_management_version() -> int:
    """Retorna a versão dos controles de gerenciamento."""
    if (
        TRANSACTION_MANAGEMENT_VERSION_KEY
        not in st.session_state
    ):
        st.session_state[
            TRANSACTION_MANAGEMENT_VERSION_KEY
        ] = 0

    return int(
        st.session_state[
            TRANSACTION_MANAGEMENT_VERSION_KEY
        ]
    )


def _advance_management_version() -> None:
    """Recria os widgets após uma operação persistida."""
    current_version = (
        _get_management_version()
    )

    st.session_state[
        TRANSACTION_MANAGEMENT_VERSION_KEY
    ] = (
        current_version + 1
    )


def _format_date(
    value: object,
) -> str:
    """Formata uma data para identificar a transação."""
    parsed_date = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(
        parsed_date
    ):
        return "Data inválida"

    return parsed_date.strftime(
        "%d/%m/%Y"
    )


def _safe_text(
    value: object,
) -> str:
    """Transforma valores vazios em texto seguro."""
    if value is None:
        return ""

    try:
        if pd.isna(
            value
        ):
            return ""
    except (
        TypeError,
        ValueError,
    ):
        pass

    return str(
        value
    ).strip()


def _prepare_manageable_transactions(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Mantém somente transações com identificadores válidos."""
    if (
        transactions.empty
        or TRANSACTION_ID_COLUMN
        not in transactions.columns
    ):
        return transactions.iloc[
            0:0
        ].copy()

    manageable_transactions = (
        transactions.copy()
    )

    valid_id_rows = (
        manageable_transactions[
            TRANSACTION_ID_COLUMN
        ].map(
            is_valid_transaction_id
        )
    )

    manageable_transactions = (
        manageable_transactions.loc[
            valid_id_rows
        ].copy()
    )

    manageable_transactions[
        TRANSACTION_ID_COLUMN
    ] = (
        manageable_transactions[
            TRANSACTION_ID_COLUMN
        ]
        .astype(str)
        .str.strip()
    )

    manageable_transactions[
        "_sort_date"
    ] = pd.to_datetime(
        manageable_transactions["data"],
        errors="coerce",
    )

    return (
        manageable_transactions
        .sort_values(
            by="_sort_date",
            ascending=False,
            na_position="last",
        )
        .drop(
            columns=[
                "_sort_date",
            ]
        )
        .reset_index(
            drop=True
        )
    )


def _build_transaction_labels(
    transactions: pd.DataFrame,
) -> dict[str, str]:
    """Cria rótulos legíveis mantendo o ID como valor real."""
    labels: dict[
        str,
        str,
    ] = {}

    for _, transaction in (
        transactions.iterrows()
    ):
        transaction_id = _safe_text(
            transaction[
                TRANSACTION_ID_COLUMN
            ]
        )

        transaction_type = (
            _safe_text(
                transaction.get(
                    "tipo"
                )
            )
            .lower()
        )

        type_label = (
            TRANSACTION_TYPE_LABELS.get(
                transaction_type,
                transaction_type.title(),
            )
        )

        description = (
            _safe_text(
                transaction.get(
                    "descricao"
                )
            )
            or "Sem descrição"
        )

        date_label = _format_date(
            transaction.get(
                "data"
            )
        )

        amount_label = format_currency(
            transaction.get(
                "valor",
                0,
            )
        )

        labels[
            transaction_id
        ] = (
            f"{date_label} · "
            f"{type_label} · "
            f"{description} · "
            f"{amount_label}"
        )

    return labels


def _update_manual_draft_after_deletion(
    transaction_id: str,
    source_file: Path,
) -> None:
    """Remove do rascunho uma transação manual já excluída."""
    if (
        source_file.resolve()
        != ARQUIVO_TRANSACOES_MANUAIS.resolve()
    ):
        return

    draft = st.session_state.get(
        MANUAL_DRAFT_KEY
    )

    if (
        not isinstance(
            draft,
            pd.DataFrame,
        )
        or TRANSACTION_ID_COLUMN
        not in draft.columns
    ):
        return

    matching_indexes = (
        draft.index[
            draft[
                TRANSACTION_ID_COLUMN
            ]
            .astype(str)
            .str.strip()
            == transaction_id
        ]
        .tolist()
    )

    if not matching_indexes:
        return

    deleted_index = int(
        matching_indexes[0]
    )

    st.session_state[
        MANUAL_DRAFT_KEY
    ] = (
        draft.drop(
            index=matching_indexes
        )
        .reset_index(
            drop=True
        )
    )

    current_edit_index = (
        st.session_state.get(
            MANUAL_EDIT_INDEX_KEY
        )
    )

    if current_edit_index == deleted_index:
        st.session_state[
            MANUAL_EDIT_INDEX_KEY
        ] = None

        st.session_state[
            MANUAL_FORM_VERSION_KEY
        ] = (
            st.session_state.get(
                MANUAL_FORM_VERSION_KEY,
                0,
            )
            + 1
        )

    elif (
        current_edit_index is not None
        and current_edit_index > deleted_index
    ):
        st.session_state[
            MANUAL_EDIT_INDEX_KEY
        ] = (
            current_edit_index - 1
        )


def _delete_persisted_transaction(
    transaction_id: str,
) -> None:
    """Exclui a fonte, reexecuta o ETL e prepara o refresh."""
    source_file: Path | None = None

    try:
        source_file = (
            delete_transaction_from_source(
                transaction_id
            )
        )

        result = run_etl_with_summary(
            use_demo_data=False
        )

        _update_manual_draft_after_deletion(
            transaction_id=transaction_id,
            source_file=source_file,
        )

        st.session_state[
            DATA_MODE_KEY
        ] = "user"

        st.session_state[
            DATA_REFRESH_REQUESTED_KEY
        ] = True

        _set_management_feedback(
            "success",
            (
                "Transação excluída permanentemente. "
                f"Fonte atualizada: {source_file.name}. "
                "Transações processadas após a exclusão: "
                f"{result['transacoes_processadas']}."
            ),
        )

    except TransactionNotFoundError:
        _set_management_feedback(
            "error",
            (
                "A transação não foi encontrada nos arquivos "
                "do usuário. Ela pode pertencer aos dados "
                "de demonstração ou já ter sido removida."
            ),
        )

    except DuplicateTransactionIdError:
        _set_management_feedback(
            "error",
            (
                "A exclusão foi bloqueada porque o mesmo ID "
                "aparece em mais de uma fonte."
            ),
        )

    except (
        ValueError,
        OSError,
    ) as error:
        _set_management_feedback(
            "error",
            (
                "Não foi possível excluir a transação: "
                f"{error}"
            ),
        )

    except Exception as error:
        logging.exception(
            "Falha inesperada ao excluir uma transação persistida."
        )

        if source_file is None:
            message = (
                "Não foi possível excluir a transação: "
                f"{error}"
            )

        else:
            message = (
                "A fonte foi alterada, mas não foi possível "
                "concluir o reprocessamento do ETL. "
                "Execute o ETL novamente. "
                f"Detalhes: {error}"
            )

        _set_management_feedback(
            "error",
            message,
        )

    _advance_management_version()
    st.rerun()


def render_persisted_transaction_management(
    transactions: pd.DataFrame,
) -> None:
    """Exibe seleção e confirmação de exclusão persistida."""
    _show_management_feedback()

    should_expand = (
        TRANSACTION_MANAGEMENT_FEEDBACK_KEY
        in st.session_state
    )

    with st.container(
        key="persisted-transaction-management",
    ):
        with st.expander(
            "Gerenciar transação persistida",
            expanded=should_expand,
        ):
            st.caption(
                "Selecione uma movimentação já processada. "
                "A exclusão altera o arquivo de origem, "
                "reexecuta o ETL e atualiza o SQLite."
            )

            if (
                st.session_state.get(
                    DATA_MODE_KEY
                )
                == "demo"
            ):
                st.info(
                    "Os dados de demonstração são somente leitura. "
                    "Carregue os dados do usuário para editar "
                    "ou excluir movimentações."
                )
                return

            if transactions.empty:
                st.info(
                    "Não há transações no resultado atual "
                    "para gerenciar."
                )
                return

            if (
                TRANSACTION_ID_COLUMN
                not in transactions.columns
            ):
                st.warning(
                    "As transações atuais ainda não possuem "
                    "identificadores persistentes."
                )
                return

            manageable_transactions = (
                _prepare_manageable_transactions(
                    transactions
                )
            )

            if manageable_transactions.empty:
                st.warning(
                    "Nenhuma transação com ID válido "
                    "está disponível neste resultado."
                )
                return

            if (
                manageable_transactions[
                    TRANSACTION_ID_COLUMN
                ].duplicated().any()
            ):
                st.error(
                    "Existem IDs duplicados no resultado atual. "
                    "A exclusão foi bloqueada por segurança."
                )
                return

            labels = (
                _build_transaction_labels(
                    manageable_transactions
                )
            )

            transaction_ids = (
                manageable_transactions[
                    TRANSACTION_ID_COLUMN
                ].tolist()
            )

            widget_version = (
                _get_management_version()
            )

            selected_id = st.selectbox(
                "Transação",
                options=transaction_ids,
                format_func=lambda transaction_id: (
                    labels.get(
                        transaction_id,
                        transaction_id,
                    )
                ),
                key=(
                    "persisted-transaction-selection-"
                    f"{widget_version}"
                ),
            )

            selected_transaction = (
                manageable_transactions.loc[
                    manageable_transactions[
                        TRANSACTION_ID_COLUMN
                    ]
                    == selected_id
                ]
                .iloc[0]
            )

            source_name = _safe_text(
                selected_transaction.get(
                    "arquivo_origem"
                )
            )

            category = (
                _safe_text(
                    selected_transaction.get(
                        "categoria"
                    )
                )
                or "Sem categoria"
            )

            if source_name:
                st.caption(
                    f"Categoria: {category} · "
                    f"Origem: {source_name}"
                )
            else:
                st.caption(
                    f"Categoria: {category}"
                )

            confirmed = st.checkbox(
                (
                    "Confirmo que desejo excluir permanentemente "
                    "a transação selecionada."
                ),
                key=(
                    "persisted-transaction-confirmation-"
                    f"{widget_version}"
                ),
            )

            if st.button(
                "Excluir transação",
                key=(
                    "delete-persisted-transaction-"
                    f"{widget_version}"
                ),
                type="primary",
                disabled=not confirmed,
            ):
                _delete_persisted_transaction(
                    selected_id
                )