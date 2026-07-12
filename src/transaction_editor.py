"""Entrada manual de transações financeiras.

O módulo mantém a interface do editor manual no Streamlit.
Persistência, regras do rascunho e controle da sessão ficam
centralizados em módulos especializados.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.etl_transacoes import (
    run_etl_with_summary,
)
from src.manual_transaction_service import (
    MANUAL_TRANSACTION_COLUMNS,
    STORED_TRANSACTION_COLUMNS,
    add_pending_transaction,
    build_manual_transaction_source_key,
    clear_manual_transactions,
    create_empty_manual_transactions,
    load_manual_transactions,
    prepare_manual_transactions_for_storage,
    remove_pending_transaction,
    save_manual_transactions,
    update_pending_transaction,
    validate_manual_transactions,
)
from src.manual_transaction_state import (
    MANUAL_DRAFT_KEY,
    MANUAL_EDIT_INDEX_KEY,
    MANUAL_FEEDBACK_KEY,
    MANUAL_FORM_VERSION_KEY,
    adjust_edit_index_after_removal,
    get_manual_draft,
    get_manual_edit_index,
    get_manual_form_version,
    initialize_manual_transaction_state as initialize_manual_state,
    pop_manual_feedback,
    reset_manual_form,
    set_manual_draft as set_manual_state_draft,
    set_manual_feedback,
    start_manual_edit,
)


DATA_REFRESH_REQUESTED_KEY = (
    "app_data_refresh_requested"
)

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
)

ARQUIVO_TRANSACOES_MANUAIS = (
    RAW_DIR
    / "transacoes_manuais.csv"
)

# Alias temporário para preservar testes e imports existentes.
COLUNAS_TRANSACOES = (
    MANUAL_TRANSACTION_COLUMNS
)

CATEGORIAS_SUGERIDAS = [
    "Trabalho",
    "Alimentação",
    "Transporte",
    "Serviços",
    "Assinaturas",
    "Educação",
    "Lazer",
    "Saúde",
    "Compras",
    "Reserva",
]


# -----------------------------------------------------------------------------
# Compatibilidade com chamadas e testes existentes
# -----------------------------------------------------------------------------


def get_manual_transaction_source_key() -> str:
    """Retorna a chave estável da fonte manual atual."""
    return (
        build_manual_transaction_source_key(
            source_file=(
                ARQUIVO_TRANSACOES_MANUAIS
            ),
            project_root=PROJECT_ROOT,
        )
    )


def criar_dataframe_vazio() -> pd.DataFrame:
    """Cria uma tabela manual vazia."""
    return (
        create_empty_manual_transactions()
    )


def carregar_transacoes_manuais() -> pd.DataFrame:
    """Carrega as transações da fonte manual atual."""
    return load_manual_transactions(
        source_file=(
            ARQUIVO_TRANSACOES_MANUAIS
        ),
        project_root=PROJECT_ROOT,
    )


def preparar_transacoes_para_salvar(
    transacoes: pd.DataFrame,
) -> pd.DataFrame:
    """Normaliza as transações antes da gravação."""
    return (
        prepare_manual_transactions_for_storage(
            transacoes
        )
    )


def validar_transacoes_editadas(
    transacoes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Valida as transações usando as regras do ETL."""
    return validate_manual_transactions(
        transacoes
    )


def salvar_transacoes_manuais(
    transacoes: pd.DataFrame,
) -> None:
    """Salva as transações na fonte manual atual."""
    save_manual_transactions(
        transactions=transacoes,
        source_file=(
            ARQUIVO_TRANSACOES_MANUAIS
        ),
        project_root=PROJECT_ROOT,
    )


def limpar_transacoes_manuais() -> None:
    """Remove a fonte manual atual."""
    clear_manual_transactions(
        ARQUIVO_TRANSACOES_MANUAIS
    )


def initialize_manual_transaction_state() -> None:
    """Inicializa o estado usando a fonte manual atual."""
    initialize_manual_state(
        source_file=(
            ARQUIVO_TRANSACOES_MANUAIS
        ),
        project_root=PROJECT_ROOT,
    )


def set_manual_draft(
    transactions: pd.DataFrame,
) -> None:
    """Atualiza o estado usando a fonte manual atual."""
    set_manual_state_draft(
        transactions=transactions,
        source_file=(
            ARQUIVO_TRANSACOES_MANUAIS
        ),
        project_root=PROJECT_ROOT,
    )


# -----------------------------------------------------------------------------
# Feedback e execução do ETL
# -----------------------------------------------------------------------------


def show_manual_feedback() -> None:
    """Exibe mensagens geradas antes de um rerun."""
    message = pop_manual_feedback()

    if message:
        st.success(
            message
        )


def _save_manual_draft_callback() -> None:
    """Salva o rascunho sem executar o ETL."""
    transactions = get_manual_draft()

    salvar_transacoes_manuais(
        transactions
    )

    set_manual_feedback(
        "Rascunho salvo em "
        "data/raw/transacoes_manuais.csv."
    )


def _process_manual_etl_callback() -> None:
    """Salva o rascunho, executa o ETL e atualiza os dados."""
    transactions = get_manual_draft()

    salvar_transacoes_manuais(
        transactions
    )

    try:
        resultado = (
            run_etl_with_summary()
        )

    except Exception as erro:
        st.session_state[
            "resultado_etl"
        ] = {
            "sucesso": False,
            "mensagem": (
                "Erro ao executar ETL: "
                f"{erro}"
            ),
        }

        return

    st.session_state[
        "resultado_etl"
    ] = {
        **resultado,
        "mensagem": (
            "Transações salvas e ETL "
            "executado com sucesso."
        ),
    }

    st.session_state[
        DATA_REFRESH_REQUESTED_KEY
    ] = True


def _clear_manual_transactions_callback() -> None:
    """Remove as transações manuais e reexecuta o ETL."""
    limpar_transacoes_manuais()

    set_manual_draft(
        criar_dataframe_vazio()
    )

    reset_manual_form()

    try:
        resultado = (
            run_etl_with_summary()
        )

    except Exception as erro:
        st.session_state[
            "resultado_etl"
        ] = {
            "sucesso": False,
            "mensagem": (
                "Erro ao executar ETL: "
                f"{erro}"
            ),
        }

        return

    st.session_state[
        "resultado_etl"
    ] = {
        **resultado,
        "mensagem": (
            "Transações manuais removidas "
            "e ETL executado novamente."
        ),
    }

    st.session_state[
        DATA_REFRESH_REQUESTED_KEY
    ] = True


def exibir_resultado_etl_salvo() -> None:
    """Exibe o resultado do ETL guardado na sessão."""
    resultado = st.session_state.pop(
        "resultado_etl",
        None,
    )

    if not resultado:
        return

    if resultado["sucesso"]:
        st.success(
            f"{resultado['mensagem']}\n\n"
            "Transações processadas: "
            f"{resultado['transacoes_processadas']} | "
            "Transações rejeitadas: "
            f"{resultado['transacoes_rejeitadas']}"
        )

        return

    st.error(
        resultado["mensagem"]
    )


# -----------------------------------------------------------------------------
# Valores e opções do formulário
# -----------------------------------------------------------------------------


def _safe_text(
    value: object,
) -> str:
    """Converte valores vazios em texto seguro."""
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


def _get_form_defaults(
    transactions: pd.DataFrame,
) -> dict[str, object]:
    """Retorna valores iniciais para inclusão ou edição."""
    edit_index = (
        get_manual_edit_index()
    )

    if (
        edit_index is None
        or edit_index < 0
        or edit_index >= len(transactions)
    ):
        return {
            "data": date.today(),
            "tipo": "despesa",
            "descricao": "",
            "categoria": "Alimentação",
            "valor": 0.01,
        }

    transaction = transactions.iloc[
        edit_index
    ]

    transaction_date = pd.to_datetime(
        transaction["data"],
        errors="coerce",
    )

    if pd.isna(
        transaction_date
    ):
        date_value = date.today()

    else:
        date_value = (
            transaction_date.date()
        )

    amount = pd.to_numeric(
        transaction["valor"],
        errors="coerce",
    )

    if (
        pd.isna(amount)
        or amount <= 0
    ):
        amount = 0.01

    return {
        "data": date_value,
        "tipo": _safe_text(
            transaction["tipo"]
        ).lower(),
        "descricao": _safe_text(
            transaction["descricao"]
        ),
        "categoria": _safe_text(
            transaction["categoria"]
        ),
        "valor": float(
            amount
        ),
    }


def _get_category_options(
    current_category: str,
) -> list[str]:
    """Inclui categorias que não estejam nas sugestões."""
    options = (
        CATEGORIAS_SUGERIDAS.copy()
    )

    if (
        current_category
        and current_category not in options
    ):
        options.insert(
            0,
            current_category,
        )

    return options


def _get_validation_message(
    rejected_transactions: pd.DataFrame,
) -> str:
    """Monta uma mensagem curta com os erros encontrados."""
    if (
        rejected_transactions.empty
        or "motivo_rejeicao"
        not in rejected_transactions.columns
    ):
        return (
            "A transação possui dados inválidos."
        )

    reasons = (
        rejected_transactions[
            "motivo_rejeicao"
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

    if not reasons:
        return (
            "A transação possui dados inválidos."
        )

    return "; ".join(
        reasons
    )


# -----------------------------------------------------------------------------
# Formulário
# -----------------------------------------------------------------------------


def render_manual_transaction_form(
    transactions: pd.DataFrame,
) -> None:
    """Exibe o formulário de inclusão ou edição."""
    edit_index = (
        get_manual_edit_index()
    )

    editing = (
        edit_index is not None
    )

    if editing:
        st.markdown(
            "### Editar transação"
        )

        if st.button(
            "Cancelar edição",
            key="cancel_manual_edit",
        ):
            reset_manual_form()
            st.rerun()

    else:
        st.markdown(
            "### Nova transação"
        )

    defaults = _get_form_defaults(
        transactions
    )

    default_type = str(
        defaults["tipo"]
    )

    default_category = str(
        defaults["categoria"]
    )

    category_options = (
        _get_category_options(
            default_category
        )
    )

    type_options = [
        "receita",
        "despesa",
    ]

    type_index = (
        type_options.index(
            default_type
        )
        if default_type in type_options
        else 1
    )

    category_index = (
        category_options.index(
            default_category
        )
        if default_category in category_options
        else 0
    )

    form_version = (
        get_manual_form_version()
    )

    with st.form(
        key=(
            "manual_transaction_form_"
            f"{form_version}"
        ),
        border=False,
    ):
        transaction_date = st.date_input(
            "Data",
            value=defaults["data"],
            format="DD/MM/YYYY",
            help=(
                "Data em que a transação aconteceu."
            ),
        )

        transaction_type = st.selectbox(
            "Tipo",
            options=type_options,
            index=type_index,
            help=(
                "Receita representa uma entrada; "
                "despesa representa uma saída."
            ),
        )

        description = st.text_input(
            "Descrição",
            value=str(
                defaults["descricao"]
            ),
            placeholder="Ex.: Compra no mercado",
            help=(
                "Descrição curta da transação."
            ),
        )

        category = st.selectbox(
            "Categoria",
            options=category_options,
            index=category_index,
            help=(
                "Categoria usada nos indicadores "
                "e gráficos financeiros."
            ),
        )

        amount = st.number_input(
            "Valor",
            min_value=0.01,
            value=float(
                defaults["valor"]
            ),
            step=1.00,
            format="%.2f",
            help=(
                "Informe um valor maior que zero."
            ),
        )

        submit_label = (
            "Salvar alteração"
            if editing
            else "Adicionar transação"
        )

        submitted = st.form_submit_button(
            submit_label,
            type="primary",
        )

    if not submitted:
        return

    candidate = pd.DataFrame(
        [
            {
                "data": transaction_date,
                "tipo": transaction_type,
                "descricao": description,
                "categoria": category,
                "valor": amount,
            }
        ]
    )

    _, rejected_transactions = (
        validar_transacoes_editadas(
            candidate
        )
    )

    if not rejected_transactions.empty:
        st.error(
            _get_validation_message(
                rejected_transactions
            )
        )

        return

    prepared_transaction = (
        preparar_transacoes_para_salvar(
            candidate
        )
        .iloc[0]
        .to_dict()
    )

    if editing:
        updated_transactions = (
            update_pending_transaction(
                transactions=transactions,
                index=edit_index,
                transaction=prepared_transaction,
            )
        )

        feedback = (
            "Transação atualizada no rascunho."
        )

    else:
        updated_transactions = (
            add_pending_transaction(
                transactions=transactions,
                transaction=prepared_transaction,
            )
        )

        feedback = (
            "Transação adicionada ao rascunho."
        )

    set_manual_draft(
        updated_transactions
    )

    set_manual_feedback(
        feedback
    )

    reset_manual_form()
    st.rerun()


# -----------------------------------------------------------------------------
# Formatação
# -----------------------------------------------------------------------------


def format_currency_brl(
    value: object,
) -> str:
    """Formata um número como moeda brasileira."""
    numeric_value = pd.to_numeric(
        value,
        errors="coerce",
    )

    if pd.isna(
        numeric_value
    ):
        numeric_value = 0.0

    formatted = (
        f"{float(numeric_value):,.2f}"
    )

    formatted = (
        formatted
        .replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )

    return f"R$ {formatted}"


def format_date_brl(
    value: object,
) -> str:
    """Formata uma data no padrão brasileiro."""
    transaction_date = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(
        transaction_date
    ):
        return "Data inválida"

    return transaction_date.strftime(
        "%d/%m/%Y"
    )


# -----------------------------------------------------------------------------
# Ações do rascunho
# -----------------------------------------------------------------------------


def _start_manual_edit(
    index: int,
) -> None:
    """Ativa a edição de uma linha do rascunho."""
    start_manual_edit(
        index
    )

    st.rerun()


def _remove_manual_draft_item(
    transactions: pd.DataFrame,
    index: int,
) -> None:
    """Remove uma linha e atualiza o estado do editor."""
    updated_transactions = (
        remove_pending_transaction(
            transactions,
            index,
        )
    )

    set_manual_draft(
        updated_transactions
    )

    adjust_edit_index_after_removal(
        index
    )

    set_manual_feedback(
        "Transação removida do rascunho."
    )

    st.rerun()


def render_pending_transactions(
    transactions: pd.DataFrame,
) -> None:
    """Exibe as transações pendentes em cartões."""
    st.markdown(
        "### Transações no rascunho"
    )

    if transactions.empty:
        st.info(
            "Nenhuma transação adicionada. "
            "Preencha o formulário acima para começar."
        )

        return

    for index, transaction in (
        transactions
        .reset_index(
            drop=True
        )
        .iterrows()
    ):
        description = _safe_text(
            transaction["descricao"]
        )

        category = _safe_text(
            transaction["categoria"]
        )

        transaction_type = _safe_text(
            transaction["tipo"]
        ).capitalize()

        date_label = format_date_brl(
            transaction["data"]
        )

        amount_label = format_currency_brl(
            transaction["valor"]
        )

        with st.container(
            border=True,
            key=(
                "manual-transaction-card-"
                f"{index}"
            ),
        ):
            (
                details_column,
                amount_column,
                actions_column,
            ) = st.columns(
                [
                    3.2,
                    1.4,
                    2.4,
                ],
                gap="medium",
            )

            with details_column:
                st.markdown(
                    f"**{description or 'Sem descrição'}**"
                )

                st.caption(
                    f"{date_label} · "
                    f"{transaction_type} · "
                    f"{category or 'Sem categoria'}"
                )

            with amount_column:
                st.caption(
                    "Valor"
                )

                st.markdown(
                    f"### {amount_label}"
                )

            with actions_column:
                st.caption(
                    "Ações"
                )

                (
                    edit_column,
                    delete_column,
                ) = st.columns(
                    2,
                    gap="small",
                )

                with edit_column:
                    if st.button(
                        "Editar",
                        key=(
                            "edit_manual_"
                            f"{index}"
                        ),
                        use_container_width=True,
                    ):
                        _start_manual_edit(
                            index
                        )

                with delete_column:
                    if st.button(
                        "Excluir",
                        key=(
                            "delete_manual_"
                            f"{index}"
                        ),
                        use_container_width=True,
                    ):
                        _remove_manual_draft_item(
                            transactions=transactions,
                            index=index,
                        )


# -----------------------------------------------------------------------------
# Composição
# -----------------------------------------------------------------------------


def exibir_editor_transacoes_manuais() -> bool:
    """Exibe a entrada manual adaptada ao celular."""
    initialize_manual_transaction_state()

    st.subheader(
        "Entrada manual de transações"
    )

    exibir_resultado_etl_salvo()
    show_manual_feedback()

    st.caption(
        "Adicione as transações pelo formulário, "
        "revise os cartões e processe o lote quando terminar."
    )

    transactions = get_manual_draft()

    with st.container(
        border=True,
        key="manual-entry-card",
    ):
        render_manual_transaction_form(
            transactions
        )

    st.divider()

    transactions = get_manual_draft()

    render_pending_transactions(
        transactions
    )

    (
        valid_transactions,
        rejected_transactions,
    ) = validar_transacoes_editadas(
        transactions
    )

    st.caption(
        "Prévia da validação: "
        f"{len(valid_transactions)} linha(s) válida(s) "
        "e "
        f"{len(rejected_transactions)} linha(s) com erro."
    )

    if not rejected_transactions.empty:
        st.warning(
            "Corrija as transações com erro "
            "antes de salvar e processar."
        )

        with st.expander(
            "Ver problemas encontrados"
        ):
            st.dataframe(
                rejected_transactions,
                use_container_width=True,
                hide_index=True,
            )

    has_transactions = (
        not transactions.empty
    )

    has_rejections = (
        not rejected_transactions.empty
    )

    actions_disabled = (
        not has_transactions
        or has_rejections
    )

    st.markdown(
        "### Ações"
    )

    with st.container(
        key="manual-actions",
    ):
        (
            save_column,
            process_column,
        ) = st.columns(
            2,
            gap="small",
        )

        with save_column:
            st.button(
                "Salvar sem processar",
                key="manual-save-draft",
                disabled=actions_disabled,
                use_container_width=True,
                on_click=(
                    _save_manual_draft_callback
                ),
            )

        with process_column:
            st.button(
                "Salvar e processar ETL",
                key="manual-process-etl",
                type="primary",
                disabled=actions_disabled,
                use_container_width=True,
                on_click=(
                    _process_manual_etl_callback
                ),
            )

        st.button(
            "Limpar transações manuais",
            key="manual-clear-all",
            disabled=not has_transactions,
            use_container_width=True,
            on_click=(
                _clear_manual_transactions_callback
            ),
        )

    st.info(
        "As transações entram no SQLite somente "
        "depois que o pipeline ETL é executado."
    )

    return False