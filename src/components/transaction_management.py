"""Gerenciamento de transações já persistidas."""

from __future__ import annotations

import logging
from datetime import date
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
    ARQUIVO_BANCO,
    TABELA_TRANSACOES,
)
from src.manual_transaction_state import (
    invalidate_manual_draft,
)
from src.transaction_editor import (
    ARQUIVO_TRANSACOES_MANUAIS,
    CATEGORIAS_SUGERIDAS,
    DATA_REFRESH_REQUESTED_KEY,
)
from src.transaction_identity import (
    TRANSACTION_ID_COLUMN,
    is_valid_transaction_id,
)
from src.transaction_sources import (
    DuplicateTransactionIdError,
    TransactionNotFoundError,
)
from src.transaction_sync_service import (
    PartialTransactionSyncError,
    delete_persisted_transaction,
    update_persisted_transaction,
)
from src.user_context import (
    get_current_user_id,
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
    labels: dict[str, str] = {}

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


def _invalidate_manual_draft(
    source_file: Path,
) -> None:
    """Descarta o rascunho quando a fonte manual é alterada."""
    if (
        source_file.resolve()
        != ARQUIVO_TRANSACOES_MANUAIS.resolve()
    ):
        return

    invalidate_manual_draft()


def _complete_persisted_operation(
    source_file: Path | None,
) -> None:
    """Atualiza o estado depois da operação persistida."""
    if source_file is not None:
        _invalidate_manual_draft(
            source_file
        )

    st.session_state[
        DATA_MODE_KEY
    ] = "user"

    st.session_state[
        DATA_REFRESH_REQUESTED_KEY
    ] = True


def _build_location_message(
    source_file: Path | None,
    *,
    operation: str,
) -> str:
    """Informa onde a operação foi aplicada."""
    if source_file is None:
        if operation == "updated":
            return (
                "Registro atualizado diretamente "
                "no banco local."
            )

        return (
            "Registro removido diretamente "
            "do banco local."
        )

    return (
        f"Fonte sincronizada: {source_file.name}."
    )


def _update_persisted_transaction(
    transaction_id: str,
    updates: dict[str, object],
) -> None:
    """Atualiza a transação persistida."""
    try:
        source_file = (
            update_persisted_transaction(
                transaction_id=transaction_id,
                updates=updates,
                database_path=ARQUIVO_BANCO,
                table_name=TABELA_TRANSACOES,
                user_id=(
                    get_current_user_id()
                ),
                data_mode="user",
            )
        )

        _complete_persisted_operation(
            source_file
        )

        location_message = (
            _build_location_message(
                source_file,
                operation="updated",
            )
        )

        _set_management_feedback(
            "success",
            (
                "Transação atualizada com sucesso. "
                f"{location_message}"
            ),
        )

    except TransactionNotFoundError:
        _set_management_feedback(
            "error",
            (
                "A transação não foi encontrada "
                "nos dados do usuário."
            ),
        )

    except DuplicateTransactionIdError:
        _set_management_feedback(
            "error",
            (
                "A edição foi bloqueada porque "
                "o mesmo ID aparece em mais de uma fonte."
            ),
        )

    except PartialTransactionSyncError as error:
        _set_management_feedback(
            "error",
            str(
                error
            ),
        )

    except ValueError as error:
        _set_management_feedback(
            "error",
            (
                "Os dados informados não são válidos: "
                f"{error}"
            ),
        )

    except (
        OSError,
        RuntimeError,
    ) as error:
        _set_management_feedback(
            "error",
            (
                "Não foi possível atualizar "
                f"a transação: {error}"
            ),
        )

    except Exception as error:
        logging.exception(
            "Falha inesperada ao atualizar "
            "uma transação persistida."
        )

        _set_management_feedback(
            "error",
            (
                "Ocorreu uma falha inesperada "
                f"durante a atualização: {error}"
            ),
        )

    _advance_management_version()
    st.rerun()


def _delete_persisted_transaction(
    transaction_id: str,
) -> None:
    """Exclui a transação persistida."""
    try:
        source_file = (
            delete_persisted_transaction(
                transaction_id=transaction_id,
                database_path=ARQUIVO_BANCO,
                table_name=TABELA_TRANSACOES,
                user_id=(
                    get_current_user_id()
                ),
                data_mode="user",
            )
        )

        _complete_persisted_operation(
            source_file
        )

        location_message = (
            _build_location_message(
                source_file,
                operation="deleted",
            )
        )

        _set_management_feedback(
            "success",
            (
                "Transação excluída permanentemente. "
                f"{location_message}"
            ),
        )

    except TransactionNotFoundError:
        _set_management_feedback(
            "error",
            (
                "A transação não foi encontrada "
                "nos dados do usuário."
            ),
        )

    except DuplicateTransactionIdError:
        _set_management_feedback(
            "error",
            (
                "A exclusão foi bloqueada porque "
                "o mesmo ID aparece em mais de uma fonte."
            ),
        )

    except PartialTransactionSyncError as error:
        _set_management_feedback(
            "error",
            str(
                error
            ),
        )

    except (
        ValueError,
        OSError,
        RuntimeError,
    ) as error:
        _set_management_feedback(
            "error",
            (
                "Não foi possível excluir "
                f"a transação: {error}"
            ),
        )

    except Exception as error:
        logging.exception(
            "Falha inesperada ao excluir "
            "uma transação persistida."
        )

        _set_management_feedback(
            "error",
            (
                "Ocorreu uma falha inesperada "
                f"durante a exclusão: {error}"
            ),
        )

    _advance_management_version()
    st.rerun()


def _get_date_default(
    transaction: pd.Series,
) -> date:
    """Retorna uma data segura para o formulário de edição."""
    parsed_date = pd.to_datetime(
        transaction.get(
            "data"
        ),
        errors="coerce",
    )

    if pd.isna(
        parsed_date
    ):
        return date.today()

    return parsed_date.date()


def _get_amount_default(
    transaction: pd.Series,
) -> float:
    """Retorna um valor monetário válido para o formulário."""
    amount = pd.to_numeric(
        transaction.get(
            "valor"
        ),
        errors="coerce",
    )

    if (
        pd.isna(
            amount
        )
        or amount <= 0
    ):
        return 0.01

    return float(
        amount
    )


def _get_type_options(
    current_type: str,
) -> list[str]:
    """Monta as opções de tipo mantendo o valor atual."""
    options = [
        "receita",
        "despesa",
    ]

    if (
        current_type
        and current_type not in options
    ):
        options.insert(
            0,
            current_type,
        )

    return options


def _get_category_options(
    transactions: pd.DataFrame,
    current_category: str,
) -> list[str]:
    """Combina categorias sugeridas, existentes e a atual."""
    options: list[str] = []

    existing_categories = (
        transactions[
            "categoria"
        ]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    candidates = [
        *CATEGORIAS_SUGERIDAS,
        *existing_categories,
        current_category,
    ]

    for category in candidates:
        normalized_category = (
            _safe_text(
                category
            )
        )

        if (
            normalized_category
            and normalized_category not in options
        ):
            options.append(
                normalized_category
            )

    return options


def _render_edit_form(
    selected_transaction: pd.Series,
    selected_id: str,
    transactions: pd.DataFrame,
    widget_version: int,
) -> None:
    """Exibe o formulário de edição da transação selecionada."""
    current_type = (
        _safe_text(
            selected_transaction.get(
                "tipo"
            )
        )
        .lower()
    )

    current_description = (
        _safe_text(
            selected_transaction.get(
                "descricao"
            )
        )
    )

    current_category = (
        _safe_text(
            selected_transaction.get(
                "categoria"
            )
        )
    )

    type_options = (
        _get_type_options(
            current_type
        )
    )

    category_options = (
        _get_category_options(
            transactions=transactions,
            current_category=current_category,
        )
    )

    type_index = (
        type_options.index(
            current_type
        )
        if current_type in type_options
        else 0
    )

    category_index = (
        category_options.index(
            current_category
        )
        if current_category in category_options
        else 0
    )

    widget_token = (
        selected_id
        .replace(
            "-",
            "",
        )[
            :12
        ]
    )

    with st.container(
        key="persisted-edit-form-card",
    ):
        with st.form(
            key=(
                "persisted-transaction-edit-form-"
                f"{widget_version}-"
                f"{widget_token}"
            ),
            border=False,
        ):
            with st.container(
                key="persisted-edit-primary-row",
            ):
                (
                    date_column,
                    type_column,
                ) = st.columns(
                    2,
                    gap="medium",
                    vertical_alignment="bottom",
                )

                with date_column:
                    transaction_date = st.date_input(
                        "Data",
                        value=(
                            _get_date_default(
                                selected_transaction
                            )
                        ),
                        format="DD/MM/YYYY",
                        key=(
                            "persisted-edit-date-"
                            f"{widget_version}-"
                            f"{widget_token}"
                        ),
                    )

                with type_column:
                    transaction_type = st.selectbox(
                        "Tipo",
                        options=type_options,
                        index=type_index,
                        format_func=lambda value: (
                            TRANSACTION_TYPE_LABELS.get(
                                value,
                                value.title(),
                            )
                        ),
                        key=(
                            "persisted-edit-type-"
                            f"{widget_version}-"
                            f"{widget_token}"
                        ),
                    )

            description = st.text_input(
                "Descrição",
                value=current_description,
                key=(
                    "persisted-edit-description-"
                    f"{widget_version}-"
                    f"{widget_token}"
                ),
            )

            with st.container(
                key="persisted-edit-secondary-row",
            ):
                (
                    category_column,
                    amount_column,
                ) = st.columns(
                    2,
                    gap="medium",
                    vertical_alignment="bottom",
                )

                with category_column:
                    category = st.selectbox(
                        "Categoria",
                        options=category_options,
                        index=category_index,
                        key=(
                            "persisted-edit-category-"
                            f"{widget_version}-"
                            f"{widget_token}"
                        ),
                    )

                with amount_column:
                    amount = st.number_input(
                        "Valor",
                        min_value=0.01,
                        value=(
                            _get_amount_default(
                                selected_transaction
                            )
                        ),
                        step=1.00,
                        format="%.2f",
                        key=(
                            "persisted-edit-amount-"
                            f"{widget_version}-"
                            f"{widget_token}"
                        ),
                    )

            submitted = st.form_submit_button(
                "Salvar alterações",
                type="primary",
            )

    if not submitted:
        return

    _update_persisted_transaction(
        transaction_id=selected_id,
        updates={
            "data": transaction_date,
            "tipo": transaction_type,
            "descricao": description,
            "categoria": category,
            "valor": amount,
        },
    )


def _render_delete_confirmation(
    selected_id: str,
    widget_version: int,
) -> None:
    """Exibe a confirmação da exclusão permanente."""
    st.warning(
        "A exclusão remove a transação do banco local "
        "e também do arquivo de origem quando ele existir. "
        "Essa ação não pode ser desfeita pela interface."
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


def render_persisted_transaction_management(
    transactions: pd.DataFrame,
) -> None:
    """Exibe edição e exclusão de transações persistidas."""
    should_expand = (
        TRANSACTION_MANAGEMENT_FEEDBACK_KEY
        in st.session_state
    )

    _show_management_feedback()

    with st.container(
        key="persisted-transaction-management",
    ):
        with st.expander(
            "Gerenciar transação persistida",
            expanded=should_expand,
        ):
            st.caption(
                "Selecione uma movimentação já persistida. "
                "As alterações são aplicadas ao banco local "
                "e ao arquivo de origem quando ele ainda existir."
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
                    "A edição e a exclusão foram bloqueadas."
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

            source_label = (
                "Banco local"
                if source_name.startswith(
                    "database:"
                )
                else source_name
            )

            category = (
                _safe_text(
                    selected_transaction.get(
                        "categoria"
                    )
                )
                or "Sem categoria"
            )

            if source_label:
                st.caption(
                    f"Categoria: {category} · "
                    f"Origem: {source_label}"
                )

            else:
                st.caption(
                    f"Categoria: {category}"
                )

            edit_tab, delete_tab = st.tabs(
                [
                    "Editar",
                    "Excluir",
                ]
            )

            with edit_tab:
                _render_edit_form(
                    selected_transaction=(
                        selected_transaction
                    ),
                    selected_id=selected_id,
                    transactions=(
                        manageable_transactions
                    ),
                    widget_version=widget_version,
                )

            with delete_tab:
                _render_delete_confirmation(
                    selected_id=selected_id,
                    widget_version=widget_version,
                )