"""Interface para gerenciamento dos dados locais do FinanTec."""

from __future__ import annotations

import streamlit as st

from scripts.etl_transacoes import (
    run_etl_with_summary,
)
from src.data_reset import (
    reset_user_transaction_data,
    summarize_user_transaction_data,
)
from src.transaction_editor import (
    MANUAL_DRAFT_KEY,
    MANUAL_EDIT_INDEX_KEY,
    MANUAL_FEEDBACK_KEY,
    MANUAL_FORM_VERSION_KEY,
)
from src.user_context import (
    get_current_user_id,
)


DATA_MANAGEMENT_FEEDBACK_KEY = (
    "data_management_feedback"
)

DATA_MODE_KEY = (
    "finantec_data_mode"
)

RESET_CONFIRMATION_TEXT = "APAGAR"


def _set_feedback(
    message_type: str,
    message: str,
) -> None:
    """Guarda uma mensagem para exibição após o rerun."""
    st.session_state[
        DATA_MANAGEMENT_FEEDBACK_KEY
    ] = {
        "type": message_type,
        "message": message,
    }


def _show_feedback() -> None:
    """Exibe o resultado da última operação."""
    feedback = st.session_state.pop(
        DATA_MANAGEMENT_FEEDBACK_KEY,
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


def _clear_manual_session_state() -> None:
    """Remove rascunhos manuais mantidos na sessão."""
    state_keys = [
        MANUAL_DRAFT_KEY,
        MANUAL_EDIT_INDEX_KEY,
        MANUAL_FORM_VERSION_KEY,
        MANUAL_FEEDBACK_KEY,
        "resultado_etl",
        "messages_by_period",
    ]

    for state_key in state_keys:
        st.session_state.pop(
            state_key,
            None,
        )


def _refresh_application_data() -> None:
    """Limpa dados em cache antes de atualizar a interface."""
    st.cache_data.clear()


def _render_current_mode() -> None:
    """Exibe a fonte selecionada durante a sessão."""
    current_mode = st.session_state.get(
        DATA_MODE_KEY
    )

    mode_labels = {
        "user": "Meus dados",
        "demo": "Demonstração",
        "empty": "Sem transações",
    }

    if current_mode not in mode_labels:
        return

    st.info(
        "Exibindo no painel: "
        f"**{mode_labels[current_mode]}**"
    )


def _render_data_summary() -> dict[str, int | bool]:
    """Exibe um resumo dos dados transacionais locais."""
    current_user_id = (
        get_current_user_id()
    )

    summary = (
        summarize_user_transaction_data(
            user_id=current_user_id,
        )
    )

    source_files = int(
        summary["source_files"]
    )

    processed_files = int(
        summary["processed_files"]
    )

    transaction_rows = int(
        summary["transaction_rows"]
    )

    transaction_value_class = (
        "finantec-data-summary-value available"
        if transaction_rows > 0
        else "finantec-data-summary-value unavailable"
    )

    heading_html = (
        '<div class="finantec-section-heading">'
        "<h3>Resumo dos dados locais</h3>"
        "<p>"
        "Informações transacionais armazenadas "
        "neste dispositivo para o usuário atual."
        "</p>"
        "</div>"
    )

    summary_html = (
        '<div class="finantec-data-summary-grid">'

        '<div class="finantec-data-summary-card">'
        '<span class="finantec-data-summary-label">'
        "Arquivos importados"
        "</span>"
        '<strong class="finantec-data-summary-value">'
        f"{source_files}"
        "</strong>"
        '<span class="finantec-data-summary-description">'
        "Arquivos usados para adicionar transações."
        "</span>"
        "</div>"

        '<div class="finantec-data-summary-card">'
        '<span class="finantec-data-summary-label">'
        "Arquivos auxiliares"
        "</span>"
        '<strong class="finantec-data-summary-value">'
        f"{processed_files}"
        "</strong>"
        '<span class="finantec-data-summary-description">'
        "Arquivos locais gerados durante o processamento."
        "</span>"
        "</div>"

        '<div class="finantec-data-summary-card">'
        '<span class="finantec-data-summary-label">'
        "Transações salvas"
        "</span>"
        f'<strong class="{transaction_value_class}">'
        f"{transaction_rows}"
        "</strong>"
        '<span class="finantec-data-summary-description">'
        "Registros pessoais disponíveis no banco local."
        "</span>"
        "</div>"

        "</div>"
    )

    st.markdown(
        heading_html,
        unsafe_allow_html=True,
    )

    st.markdown(
        summary_html,
        unsafe_allow_html=True,
    )

    return summary


def _render_user_data_action(
    summary: dict[str, int | bool],
) -> None:
    """Permite voltar às transações pessoais do usuário."""
    with st.container(
        border=True,
        key="user-data-action-card",
    ):
        st.markdown(
            "#### Meus dados"
        )

        st.caption(
            "Mostra no painel as transações pessoais "
            "armazenadas no banco local."
        )

        has_user_transactions = (
            int(
                summary["transaction_rows"]
            )
            > 0
        )

        if not has_user_transactions:
            st.info(
                "Nenhuma transação pessoal foi encontrada."
            )

        if st.button(
            "Usar meus dados",
            key="use-user-data",
            disabled=not has_user_transactions,
        ):
            st.session_state[
                DATA_MODE_KEY
            ] = "user"

            _set_feedback(
                "success",
                (
                    "Dados pessoais carregados. "
                    f"{summary['transaction_rows']} "
                    "transação(ões) disponível(is)."
                ),
            )

            _refresh_application_data()
            st.rerun()


def _render_demo_action() -> None:
    """Permite carregar explicitamente a demonstração."""
    with st.container(
        border=True,
        key="demo-data-action-card",
    ):
        st.markdown(
            "#### Demonstração"
        )

        st.caption(
            "Exibe dados simulados para apresentar o projeto. "
            "Seus dados pessoais permanecem armazenados."
        )

        demo_confirmation = st.checkbox(
            (
                "Entendo que o painel mostrará "
                "temporariamente os dados simulados."
            ),
            key="confirm_demo_data",
        )

        if st.button(
            "Carregar demonstração",
            key="load-demo-data",
            disabled=not demo_confirmation,
        ):
            try:
                result = run_etl_with_summary(
                    use_demo_data=True
                )

                st.session_state[
                    DATA_MODE_KEY
                ] = "demo"

                _set_feedback(
                    "success",
                    (
                        "Demonstração carregada. "
                        f"{result['transacoes_processadas']} "
                        "transação(ões) simulada(s)."
                    ),
                )

                _refresh_application_data()
                st.rerun()

            except Exception as error:
                _set_feedback(
                    "error",
                    (
                        "Não foi possível carregar "
                        f"a demonstração: {error}"
                    ),
                )

                st.rerun()


def _render_reset_action(
    summary: dict[str, int | bool],
) -> None:
    """Exibe a exclusão das transações pessoais."""
    has_transaction_data = any(
        [
            int(
                summary["source_files"]
            )
            > 0,
            int(
                summary["processed_files"]
            )
            > 0,
            int(
                summary["transaction_rows"]
            )
            > 0,
            bool(
                summary["log_exists"]
            ),
        ]
    )

    with st.container(
        key="danger-zone-wrapper",
    ):
        with st.expander(
            "Zona de risco",
            expanded=False,
        ):
            st.error(
                "Será apagado permanentemente: suas transações "
                "pessoais, os arquivos usados para adicioná-las, "
                "as cópias locais geradas a partir delas e o "
                "registro técnico das importações. "
                "Será preservado: seu perfil, suas metas, o "
                "histórico de conversas, os dados de demonstração "
                "e o arquivo do banco local."
            )

            confirmation = st.text_input(
                "Digite APAGAR para confirmar",
                key="reset_data_confirmation",
                placeholder="APAGAR",
                help=(
                    "A exclusão só será liberada quando "
                    "o texto APAGAR for confirmado."
                ),
            )

            confirmed = (
                confirmation.strip().upper()
                == RESET_CONFIRMATION_TEXT
            )

            delete_enabled = (
                has_transaction_data
                and confirmed
            )

            if st.button(
                "Apagar minhas transações",
                key="delete-user-transactions",
                type="primary",
                disabled=not delete_enabled,
                use_container_width=True,
            ):
                try:
                    result = (
                        reset_user_transaction_data(
                            user_id=(
                                get_current_user_id()
                            ),
                        )
                    )

                    _clear_manual_session_state()

                    st.session_state[
                        DATA_MODE_KEY
                    ] = "empty"

                    _set_feedback(
                        "success",
                        (
                            "Transações pessoais apagadas. "
                            "Linhas removidas do banco: "
                            f"{result['transaction_rows_removed']} | "
                            "Arquivos importados removidos: "
                            f"{result['source_files_removed']} | "
                            "Arquivos auxiliares removidos: "
                            f"{result['processed_files_removed']}. "
                            "Perfil, metas e conversas foram preservados."
                        ),
                    )

                    _refresh_application_data()
                    st.rerun()

                except Exception as error:
                    _set_feedback(
                        "error",
                        (
                            "Não foi possível apagar "
                            f"as transações: {error}"
                        ),
                    )

                    st.rerun()


def render_data_management() -> None:
    """Exibe a área de gerenciamento dos dados."""
    st.subheader(
        "Dados e privacidade"
    )

    st.caption(
        "Escolha quais dados serão exibidos e controle "
        "as transações armazenadas localmente."
    )

    _show_feedback()
    _render_current_mode()

    summary = (
        _render_data_summary()
    )

    _render_user_data_action(
        summary
    )

    _render_demo_action()

    _render_reset_action(
        summary
    )
