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
        st.success(message)
        return

    if message_type == "warning":
        st.warning(message)
        return

    st.error(message)


def _clear_manual_session_state() -> None:
    """Remove rascunhos manuais mantidos na sessão."""
    state_keys = [
        MANUAL_DRAFT_KEY,
        MANUAL_EDIT_INDEX_KEY,
        MANUAL_FORM_VERSION_KEY,
        MANUAL_FEEDBACK_KEY,
        "resultado_etl",
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
    """Exibe o modo escolhido durante a sessão atual."""
    current_mode = st.session_state.get(
        DATA_MODE_KEY
    )

    mode_labels = {
        "user": "Dados do usuário",
        "demo": "Dados de demonstração",
        "empty": "Dashboard vazio",
    }

    if current_mode not in mode_labels:
        return

    st.info(
        "Modo atual desta sessão: "
        f"**{mode_labels[current_mode]}**"
    )


def _render_data_summary() -> dict[str, int | bool]:
    """Exibe um resumo visual dos dados locais encontrados."""
    summary = summarize_user_transaction_data()

    database_available = bool(
        summary["database_exists"]
    )

    database_label = (
        "Disponível"
        if database_available
        else "Não criado"
    )

    database_value_class = (
        "finantec-data-summary-value available"
        if database_available
        else "finantec-data-summary-value unavailable"
    )

    heading_html = (
        '<div class="finantec-section-heading">'
        "<h3>Resumo local</h3>"
        "<p>"
        "Situação dos arquivos e do banco usados pelo dashboard."
        "</p>"
        "</div>"
    )

    summary_html = (
        '<div class="finantec-data-summary-grid">'

        '<div class="finantec-data-summary-card">'
        '<span class="finantec-data-summary-label">'
        "Fontes do usuário"
        "</span>"
        '<strong class="finantec-data-summary-value">'
        f'{summary["source_files"]}'
        "</strong>"
        '<span class="finantec-data-summary-description">'
        "Arquivos encontrados em data/raw."
        "</span>"
        "</div>"

        '<div class="finantec-data-summary-card">'
        '<span class="finantec-data-summary-label">'
        "Arquivos processados"
        "</span>"
        '<strong class="finantec-data-summary-value">'
        f'{summary["processed_files"]}'
        "</strong>"
        '<span class="finantec-data-summary-description">'
        "Saídas geradas pelo pipeline ETL."
        "</span>"
        "</div>"

        '<div class="finantec-data-summary-card">'
        '<span class="finantec-data-summary-label">'
        "Banco SQLite"
        "</span>"
        f'<strong class="{database_value_class}">'
        f"{database_label}"
        "</strong>"
        '<span class="finantec-data-summary-description">'
        "Base atualmente usada pelo dashboard."
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
    """Permite processar somente os dados reais do usuário."""
    with st.container(
        border=True
    ):
        st.markdown(
            "#### Meus dados"
        )

        st.caption(
            "Processa somente os arquivos existentes "
            "em data/raw/, incluindo transações manuais "
            "e lotes importados."
        )

        has_user_sources = (
            summary["source_files"] > 0
        )

        if not has_user_sources:
            st.info(
                "Nenhuma fonte de dados do usuário "
                "foi encontrada."
            )

        if st.button(
            "Usar meus dados",
            type="primary",
            disabled=not has_user_sources,
            use_container_width=True,
        ):
            try:
                result = run_etl_with_summary(
                    use_demo_data=False
                )

                st.session_state[
                    DATA_MODE_KEY
                ] = "user"

                _set_feedback(
                    "success",
                    (
                        "Dados do usuário processados. "
                        f"{result['transacoes_processadas']} "
                        "transação(ões) carregada(s)."
                    ),
                )

                _refresh_application_data()
                st.rerun()

            except Exception as error:
                _set_feedback(
                    "error",
                    (
                        "Não foi possível processar "
                        f"os dados do usuário: {error}"
                    ),
                )

                st.rerun()


def _render_demo_action() -> None:
    """Permite carregar explicitamente a demonstração."""
    with st.container(
        border=True
    ):
        st.markdown(
            "#### Dados de demonstração"
        )

        st.caption(
            "Preenche o dashboard com dados simulados. "
            "Os arquivos pessoais não são apagados."
        )

        demo_confirmation = st.checkbox(
            (
                "Entendo que o dashboard atual será "
                "temporariamente substituído pela demonstração."
            ),
            key="confirm_demo_data",
        )

        if st.button(
            "Carregar demonstração",
            disabled=not demo_confirmation,
            use_container_width=True,
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
    """Exibe a ação destrutiva de limpeza dos dados."""
    has_local_data = any(
        [
            summary["source_files"] > 0,
            summary["processed_files"] > 0,
            summary["database_exists"],
            summary["log_exists"],
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
                "Exclusão permanente: esta ação remove "
                "transações manuais, lotes importados, "
                "arquivos processados e o banco local. "
                "Essa operação não pode ser desfeita. "
                "Os dados de demonstração serão preservados."
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
                has_local_data
                and confirmed
            )

            if st.button(
                "Apagar todos os dados do usuário",
                key="delete-all-user-data",
                type="primary",
                disabled=not delete_enabled,
                use_container_width=True,
            ):
                try:
                    result = (
                        reset_user_transaction_data()
                    )

                    _clear_manual_session_state()

                    st.session_state[
                        DATA_MODE_KEY
                    ] = "empty"

                    _set_feedback(
                        "success",
                        (
                            "Dados locais apagados. "
                            "Fontes removidas: "
                            f"{result['source_files_removed']} | "
                            "Arquivos processados removidos: "
                            f"{result['processed_files_removed']}."
                        ),
                    )

                    _refresh_application_data()
                    st.rerun()

                except Exception as error:
                    _set_feedback(
                        "error",
                        (
                            "Não foi possível apagar "
                            f"os dados locais: {error}"
                        ),
                    )

                    st.rerun()


def render_data_management() -> None:
    """Exibe a área de gerenciamento dos dados."""
    st.subheader(
        "Gerenciar dados"
    )

    st.caption(
        "Escolha entre seus dados reais e a base "
        "simulada usada para demonstração do projeto."
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