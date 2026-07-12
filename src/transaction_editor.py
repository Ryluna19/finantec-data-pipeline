"""Entrada manual de transações financeiras.

O módulo mantém um rascunho na sessão do Streamlit para oferecer uma
experiência adequada tanto no celular quanto no desktop.

As transações continuam sendo salvas em data/raw/transacoes_manuais.csv
e processadas pelo pipeline ETL antes de entrarem no SQLite.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.etl_transacoes import run_etl_with_summary
from src.transaction_validation import (
    split_transactions_by_validity,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

ARQUIVO_TRANSACOES_MANUAIS = (
    RAW_DIR
    / "transacoes_manuais.csv"
)

COLUNAS_TRANSACOES = [
    "data",
    "tipo",
    "descricao",
    "categoria",
    "valor",
]

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


def criar_dataframe_vazio() -> pd.DataFrame:
    """Cria uma tabela vazia no formato do contrato."""
    return pd.DataFrame(
        columns=COLUNAS_TRANSACOES
    )


def carregar_transacoes_manuais() -> pd.DataFrame:
    """Carrega as transações manuais já salvas."""
    if not ARQUIVO_TRANSACOES_MANUAIS.exists():
        return criar_dataframe_vazio()

    transacoes = pd.read_csv(
        ARQUIVO_TRANSACOES_MANUAIS,
        encoding="utf-8-sig",
    )

    for coluna in COLUNAS_TRANSACOES:
        if coluna not in transacoes.columns:
            transacoes[coluna] = ""

    transacoes = transacoes[
        COLUNAS_TRANSACOES
    ].copy()

    transacoes["data"] = pd.to_datetime(
        transacoes["data"],
        errors="coerce",
    )

    return transacoes


def preparar_transacoes_para_salvar(
    transacoes: pd.DataFrame,
) -> pd.DataFrame:
    """Normaliza a tabela antes da persistência em CSV."""
    transacoes = transacoes[
        COLUNAS_TRANSACOES
    ].copy()

    transacoes = transacoes.dropna(
        how="all"
    )

    transacoes["data"] = (
        pd.to_datetime(
            transacoes["data"],
            errors="coerce",
        )
        .dt.strftime("%Y-%m-%d")
        .fillna("")
    )

    transacoes["tipo"] = (
        transacoes["tipo"]
        .astype("string")
        .fillna("")
        .str.strip()
        .str.lower()
    )

    transacoes["descricao"] = (
        transacoes["descricao"]
        .astype("string")
        .fillna("")
        .str.strip()
    )

    transacoes["categoria"] = (
        transacoes["categoria"]
        .astype("string")
        .fillna("")
        .str.strip()
    )

    transacoes["valor"] = pd.to_numeric(
        transacoes["valor"],
        errors="coerce",
    )

    return transacoes


def validar_transacoes_editadas(
    transacoes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reutiliza as regras de validação do pipeline ETL."""
    transacoes_preparadas = (
        preparar_transacoes_para_salvar(
            transacoes
        )
    )

    transacoes_preparadas = (
        transacoes_preparadas.dropna(
            how="all",
            subset=COLUNAS_TRANSACOES,
        )
    )

    if transacoes_preparadas.empty:
        return (
            transacoes_preparadas,
            pd.DataFrame(),
        )

    return split_transactions_by_validity(
        transacoes_preparadas
    )


def salvar_transacoes_manuais(
    transacoes: pd.DataFrame,
) -> None:
    """Salva as transações manuais em data/raw/."""
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    transacoes_para_salvar = (
        preparar_transacoes_para_salvar(
            transacoes
        )
    )

    transacoes_para_salvar.to_csv(
        ARQUIVO_TRANSACOES_MANUAIS,
        index=False,
        encoding="utf-8-sig",
    )


def limpar_transacoes_manuais() -> None:
    """Remove o arquivo local de transações manuais."""
    if ARQUIVO_TRANSACOES_MANUAIS.exists():
        ARQUIVO_TRANSACOES_MANUAIS.unlink()


def add_pending_transaction(
    transactions: pd.DataFrame,
    transaction: dict,
) -> pd.DataFrame:
    """Adiciona uma transação ao rascunho."""
    current_transactions = transactions[
        COLUNAS_TRANSACOES
    ].copy()

    new_transaction = pd.DataFrame(
        [transaction],
        columns=COLUNAS_TRANSACOES,
    )

    return pd.concat(
        [
            current_transactions,
            new_transaction,
        ],
        ignore_index=True,
    )


def update_pending_transaction(
    transactions: pd.DataFrame,
    index: int,
    transaction: dict,
) -> pd.DataFrame:
    """Atualiza uma transação existente no rascunho."""
    if index < 0 or index >= len(transactions):
        raise IndexError(
            "Índice de transação inválido."
        )

    updated_transactions = transactions[
        COLUNAS_TRANSACOES
    ].copy()

    for column in COLUNAS_TRANSACOES:
        updated_transactions.loc[
            index,
            column,
        ] = transaction[column]

    return updated_transactions.reset_index(
        drop=True
    )


def remove_pending_transaction(
    transactions: pd.DataFrame,
    index: int,
) -> pd.DataFrame:
    """Remove uma transação do rascunho."""
    if index < 0 or index >= len(transactions):
        raise IndexError(
            "Índice de transação inválido."
        )

    return (
        transactions
        .drop(index=index)
        .reset_index(drop=True)
    )


def initialize_manual_transaction_state() -> None:
    """Inicializa o rascunho e os controles da interface."""
    if MANUAL_DRAFT_KEY not in st.session_state:
        st.session_state[
            MANUAL_DRAFT_KEY
        ] = (
            carregar_transacoes_manuais()
            .reset_index(drop=True)
        )

    if MANUAL_EDIT_INDEX_KEY not in st.session_state:
        st.session_state[
            MANUAL_EDIT_INDEX_KEY
        ] = None

    if MANUAL_FORM_VERSION_KEY not in st.session_state:
        st.session_state[
            MANUAL_FORM_VERSION_KEY
        ] = 0


def get_manual_draft() -> pd.DataFrame:
    """Retorna uma cópia do rascunho atual."""
    return st.session_state[
        MANUAL_DRAFT_KEY
    ].copy()


def set_manual_draft(
    transactions: pd.DataFrame,
) -> None:
    """Atualiza o rascunho mantido na sessão."""
    st.session_state[
        MANUAL_DRAFT_KEY
    ] = (
        transactions[
            COLUNAS_TRANSACOES
        ]
        .copy()
        .reset_index(drop=True)
    )


def reset_manual_form() -> None:
    """Retorna o formulário ao modo de inclusão."""
    st.session_state[
        MANUAL_EDIT_INDEX_KEY
    ] = None

    st.session_state[
        MANUAL_FORM_VERSION_KEY
    ] += 1


def set_manual_feedback(
    message: str,
) -> None:
    """Armazena uma mensagem para o próximo rerun."""
    st.session_state[
        MANUAL_FEEDBACK_KEY
    ] = message


def show_manual_feedback() -> None:
    """Exibe mensagens geradas antes de um rerun."""
    message = st.session_state.pop(
        MANUAL_FEEDBACK_KEY,
        None,
    )

    if message:
        st.success(message)


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


def _safe_text(value) -> str:
    """Converte valores vazios em texto seguro."""
    if pd.isna(value):
        return ""

    return str(value)


def _get_form_defaults(
    transactions: pd.DataFrame,
) -> dict:
    """Retorna valores iniciais para inclusão ou edição."""
    edit_index = st.session_state[
        MANUAL_EDIT_INDEX_KEY
    ]

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

    if pd.isna(transaction_date):
        date_value = date.today()
    else:
        date_value = transaction_date.date()

    amount = pd.to_numeric(
        transaction["valor"],
        errors="coerce",
    )

    if pd.isna(amount) or amount <= 0:
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
        "valor": float(amount),
    }


def _get_category_options(
    current_category: str,
) -> list[str]:
    """Inclui categorias existentes que não estejam nas sugestões."""
    options = CATEGORIAS_SUGERIDAS.copy()

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
    """Monta uma mensagem curta com os problemas encontrados."""
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

    return "; ".join(reasons)


def render_manual_transaction_form(
    transactions: pd.DataFrame,
) -> None:
    """Exibe o formulário vertical de inclusão ou edição."""
    edit_index = st.session_state[
        MANUAL_EDIT_INDEX_KEY
    ]

    editing = edit_index is not None

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

    category_options = (
        _get_category_options(
            defaults["categoria"]
        )
    )

    type_options = [
        "receita",
        "despesa",
    ]

    type_index = (
        type_options.index(
            defaults["tipo"]
        )
        if defaults["tipo"] in type_options
        else 1
    )

    category_index = (
        category_options.index(
            defaults["categoria"]
        )
        if defaults["categoria"]
        in category_options
        else 0
    )

    form_version = st.session_state[
        MANUAL_FORM_VERSION_KEY
    ]

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
            help="Data em que a transação aconteceu.",
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
            value=defaults["descricao"],
            placeholder="Ex.: Compra no mercado",
            help="Descrição curta da transação.",
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
            value=defaults["valor"],
            step=1.00,
            format="%.2f",
            help="Informe um valor maior que zero.",
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


def format_currency_brl(value) -> str:
    """Formata um número como moeda brasileira."""
    numeric_value = pd.to_numeric(
        value,
        errors="coerce",
    )

    if pd.isna(numeric_value):
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


def format_date_brl(value) -> str:
    """Formata uma data no padrão brasileiro."""
    transaction_date = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(transaction_date):
        return "Data inválida"

    return transaction_date.strftime(
        "%d/%m/%Y"
    )


def render_pending_transactions(
    transactions: pd.DataFrame,
) -> None:
    """Exibe as transações pendentes em cartões responsivos."""
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
        .reset_index(drop=True)
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
                [3.2, 1.4, 2.4],
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
                        st.session_state[
                            MANUAL_EDIT_INDEX_KEY
                        ] = index

                        st.session_state[
                            MANUAL_FORM_VERSION_KEY
                        ] += 1

                        st.rerun()

                with delete_column:
                    if st.button(
                        "Excluir",
                        key=(
                            "delete_manual_"
                            f"{index}"
                        ),
                        use_container_width=True,
                    ):
                        updated_transactions = (
                            remove_pending_transaction(
                                transactions,
                                index,
                            )
                        )

                        current_edit_index = (
                            st.session_state[
                                MANUAL_EDIT_INDEX_KEY
                            ]
                        )

                        if current_edit_index == index:
                            st.session_state[
                                MANUAL_EDIT_INDEX_KEY
                            ] = None

                        elif (
                            current_edit_index is not None
                            and current_edit_index > index
                        ):
                            st.session_state[
                                MANUAL_EDIT_INDEX_KEY
                            ] = (
                                current_edit_index - 1
                            )

                        set_manual_draft(
                            updated_transactions
                        )

                        st.session_state[
                            MANUAL_FORM_VERSION_KEY
                        ] += 1

                        set_manual_feedback(
                            "Transação removida do rascunho."
                        )

                        st.rerun()


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

    render_manual_transaction_form(
        transactions
    )

    st.divider()

    transactions = get_manual_draft()

    render_pending_transactions(
        transactions
    )

    valid_transactions, rejected_transactions = (
        validar_transacoes_editadas(
            transactions
        )
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

    has_transactions = not transactions.empty
    has_rejections = not rejected_transactions.empty

    # Evita retornar no meio da renderização e deixar
    # elementos antigos acumulados na interface.
    should_refresh_app = False

    st.markdown(
        "### Ações"
    )

    with st.container(
        key="manual-actions",
    ):
        save_column, process_column = st.columns(
            2,
            gap="small",
        )

        with save_column:
            save_clicked = st.button(
                "Salvar sem processar",
                key="manual-save-draft",
                disabled=(
                    not has_transactions
                    or has_rejections
                ),
                use_container_width=True,
            )

            if save_clicked:
                salvar_transacoes_manuais(
                    transactions
                )

                st.success(
                    "Rascunho salvo em "
                    "data/raw/transacoes_manuais.csv."
                )

        with process_column:
            process_clicked = st.button(
                "Salvar e processar ETL",
                key="manual-process-etl",
                type="primary",
                disabled=(
                    not has_transactions
                    or has_rejections
                ),
                use_container_width=True,
            )

            if process_clicked:
                salvar_transacoes_manuais(
                    transactions
                )

                try:
                    resultado = (
                        run_etl_with_summary()
                    )

                    st.session_state[
                        "resultado_etl"
                    ] = {
                        **resultado,
                        "mensagem": (
                            "Transações salvas e ETL "
                            "executado com sucesso."
                        ),
                    }

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

                should_refresh_app = True

        clear_clicked = st.button(
            "Limpar transações manuais",
            key="manual-clear-all",
            disabled=not has_transactions,
            use_container_width=True,
        )

        if clear_clicked:
            limpar_transacoes_manuais()

            set_manual_draft(
                criar_dataframe_vazio()
            )

            reset_manual_form()

            try:
                resultado = (
                    run_etl_with_summary()
                )

                st.session_state[
                    "resultado_etl"
                ] = {
                    **resultado,
                    "mensagem": (
                        "Transações manuais removidas "
                        "e ETL executado novamente."
                    ),
                }

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

            should_refresh_app = True

    st.info(
        "As transações entram no SQLite somente "
        "depois que o pipeline ETL é executado."
    )

    return should_refresh_app