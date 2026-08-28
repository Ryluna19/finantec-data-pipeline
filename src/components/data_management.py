"""Interface para gerenciamento dos dados locais do FinanTec."""

from __future__ import annotations

import logging
import streamlit as st

from scripts.etl_transacoes import (
    run_etl_with_summary,
)
from src.data_reset import (
    delete_user_financial_data,
    summarize_user_transaction_data,
    delete_user_account_and_data,
)
from src.transaction_editor import (
    MANUAL_DRAFT_KEY,
    MANUAL_EDIT_INDEX_KEY,
    MANUAL_FEEDBACK_KEY,
    MANUAL_FORM_VERSION_KEY,
)
from src.user_context import (
    get_current_account,
    get_current_user_id,
)

from components.navigation import (
    APP_SECTION_KEY,
    MAIN_SECTION,
)

from components.auth import (
    AUTH_FEEDBACK_KEY,
)
from data_loader import ARQUIVO_BANCO
from src.account_repository import (
    authenticate_user_account,
)

from components.appearance import (
    clear_session_preserving_visual_preferences,
)

from components.header import (
    build_page_header_html,
    build_section_header_html,
)
from ui_components import render_html

DATA_MANAGEMENT_FEEDBACK_KEY = (
    "data_management_feedback"
)

DATA_MODE_KEY = (
    "finantec_data_mode"
)

RESET_CONFIRMATION_TEXT = "APAGAR"


ACCOUNT_DELETION_CONFIRMATION_TEXT = (
    "EXCLUIR CONTA"
)


def build_data_mode_html(
    data_mode: str,
) -> str:
    """Monta o indicador do conjunto exibido no painel."""
    mode_content = {
        "user": {
            "label": "Meus dados",
            "description": (
                "O painel está usando os registros "
                "pessoais desta conta."
            ),
            "variant": "user",
        },
        "demo": {
            "label": "Demonstração",
            "description": (
                "O painel está exibindo temporariamente "
                "os dados simulados do projeto."
            ),
            "variant": "demo",
        },
        "empty": {
            "label": "Sem transações",
            "description": (
                "Nenhum conjunto de transações está "
                "disponível no painel."
            ),
            "variant": "empty",
        },
    }

    current_content = mode_content.get(
        data_mode
    )

    if current_content is None:
        return ""

    return (
        '<section class="finantec-data-mode-status '
        f'{current_content["variant"]}">'
        '<div class="finantec-data-mode-identity">'
        "<span>Fonte exibida no painel</span>"
        f'<strong>{current_content["label"]}</strong>'
        "</div>"
        f'<p>{current_content["description"]}</p>'
        "</section>"
    )

def build_data_summary_html(
    summary: dict[str, int | bool],
) -> str:
    """Monta os indicadores dos dados locais."""
    source_files = max(
        int(
            summary.get(
                "source_files",
                0,
            )
            or 0
        ),
        0,
    )

    processed_files = max(
        int(
            summary.get(
                "processed_files",
                0,
            )
            or 0
        ),
        0,
    )

    transaction_rows = max(
        int(
            summary.get(
                "transaction_rows",
                0,
            )
            or 0
        ),
        0,
    )

    transaction_value_class = (
        "finantec-data-summary-value available"
        if transaction_rows > 0
        else "finantec-data-summary-value unavailable"
    )

    return (
        '<div class="finantec-data-summary-grid">'

        '<article class="finantec-data-summary-card">'
        '<span class="finantec-data-summary-label">'
        "Arquivos importados"
        "</span>"
        '<strong class="finantec-data-summary-value">'
        f"{source_files}"
        "</strong>"
        '<span class="finantec-data-summary-description">'
        "Arquivos usados para adicionar transações."
        "</span>"
        "</article>"

        '<article class="finantec-data-summary-card">'
        '<span class="finantec-data-summary-label">'
        "Arquivos auxiliares"
        "</span>"
        '<strong class="finantec-data-summary-value">'
        f"{processed_files}"
        "</strong>"
        '<span class="finantec-data-summary-description">'
        "Arquivos locais gerados durante o processamento."
        "</span>"
        "</article>"

        '<article class="finantec-data-summary-card">'
        '<span class="finantec-data-summary-label">'
        "Transações salvas"
        "</span>"
        f'<strong class="{transaction_value_class}">'
        f"{transaction_rows}"
        "</strong>"
        '<span class="finantec-data-summary-description">'
        "Registros pessoais disponíveis no banco local."
        "</span>"
        "</article>"

        "</div>"
    )

def is_account_deletion_confirmed(
    confirmation: str,
) -> bool:
    """Valida a confirmação textual da exclusão da conta."""
    normalized_confirmation = " ".join(
        str(confirmation)
        .strip()
        .upper()
        .split()
    )

    return (
        normalized_confirmation
        == ACCOUNT_DELETION_CONFIRMATION_TEXT
    )

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
    current_mode = str(
        st.session_state.get(
            DATA_MODE_KEY,
            "user",
        )
    )

    if current_mode not in {
        "user",
        "demo",
        "empty",
    }:
        current_mode = "user"

    st.session_state[
        DATA_MODE_KEY
    ] = current_mode

    render_html(
        build_data_mode_html(
            current_mode
        )
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

    render_html(
        build_section_header_html(
            title="Resumo dos dados locais",
            description=(
                "Informações transacionais armazenadas "
                "neste dispositivo para o usuário atual."
            ),
            compact=True,
        )
    )

    render_html(
        build_data_summary_html(
            summary
        )
    )

    return summary


def _render_user_data_action(
    summary: dict[str, int | bool],
) -> None:
    """Permite voltar às transações pessoais do usuário."""
    is_active = (
            str(
                st.session_state.get(
                    DATA_MODE_KEY,
                    "user",
                )
            )
            == "user"
        )
    
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
            (
                "Meus dados em uso"
                if is_active
                else "Usar meus dados"
            ),
            key="use-user-data",
            disabled=is_active,
        ):
                st.session_state[
                    DATA_MODE_KEY
                ] = "user"

                st.session_state[
                    APP_SECTION_KEY
                ] = MAIN_SECTION

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
    
    is_active = (
        str(
            st.session_state.get(
                DATA_MODE_KEY,
                "user",
            )
        )
        == "demo"
    )
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
            (
                "Demonstração em uso"
                if is_active
                else "Carregar demonstração"
            ),
            key="load-demo-data",
            disabled=(
                is_active
                or not demo_confirmation
            ),
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

            except Exception:
                logging.exception(
                    "Falha inesperada ao carregar "
                    "os dados de demonstração."
                )

                _set_feedback(
                    "error",
                    (
                        "Não foi possível carregar "
                        "a demonstração."
                    ),
                )

                st.rerun()

def _render_reset_action() -> None:
    """Exibe a exclusão completa dos dados financeiros."""
    with st.container(
        key="danger-zone-wrapper",
    ):
        with st.expander(
            "Zona de risco",
            expanded=False,
        ):
            st.error(
                "Esta ação apaga permanentemente suas transações, "
                "perfil financeiro, metas, orçamentos e histórico "
                "pessoal. Sua conta, senha, sessão e os dados de "
                "demonstração serão preservados."
            )

            with st.form(
                "delete-user-financial-data-form",
                border=False,
            ):
                confirmation = st.text_input(
                    "Digite APAGAR para confirmar",
                    key="reset_data_confirmation",
                    placeholder="APAGAR",
                    help=(
                        "Digite APAGAR e confirme a ação "
                        "para excluir seus dados financeiros."
                    ),
                )

                submitted = st.form_submit_button(
                    "Apagar meus dados",
                    type="primary",
                    width="stretch",
                )

            if not submitted:
                return

            confirmed = (
                confirmation.strip().upper()
                == RESET_CONFIRMATION_TEXT
            )

            if not confirmed:
                st.error(
                    "Digite APAGAR corretamente "
                    "para confirmar a exclusão."
                )
                return

            try:
                result = delete_user_financial_data(
                    database_path=ARQUIVO_BANCO,
                    user_id=get_current_user_id(),
                )

                _clear_manual_session_state()

                st.session_state[
                    DATA_MODE_KEY
                ] = "empty"

                st.session_state[
                    APP_SECTION_KEY
                ] = MAIN_SECTION

                removed_rows = sum(
                    int(value)
                    for key, value in result.items()
                    if key.endswith(
                        "_rows_removed"
                    )
                )

                _set_feedback(
                    "success",
                    (
                        "Seus dados financeiros foram apagados. "
                        f"Registros removidos: {removed_rows}. "
                        "Sua conta e senha foram preservadas."
                    ),
                )

                _refresh_application_data()
                st.rerun()

            except ValueError as error:
                _set_feedback(
                    "error",
                    (
                        "Não foi possível apagar "
                        f"seus dados: {error}"
                    ),
                )

                st.rerun()

            except RuntimeError:
                logging.exception(
                    "Falha ao apagar os dados "
                    "financeiros do usuário."
                )

                _set_feedback(
                    "error",
                    (
                        "Não foi possível apagar "
                        "seus dados."
                    ),
                )

                st.rerun()

def _render_account_deletion_action() -> None:
    """Exibe a exclusão definitiva da conta autenticada."""
    current_account = get_current_account()

    if current_account is None:
        return

    with st.container(
        key="account-deletion-wrapper",
    ):
        with st.expander(
            "Excluir conta",
            expanded=False,
        ):
            st.error(
                "Esta ação exclui permanentemente sua conta, "
                "credenciais, transações, perfil, metas, "
                "orçamentos e histórico. Ela não pode ser desfeita."
            )

            with st.form(
                "delete-current-account-form",
                border=False,
            ):
                password = st.text_input(
                    "Confirme sua senha",
                    type="password",
                    max_chars=128,
                    autocomplete="current-password",
                )

                confirmation = st.text_input(
                    "Digite EXCLUIR CONTA para confirmar",
                    placeholder="EXCLUIR CONTA",
                )

                submitted = st.form_submit_button(
                    "Excluir minha conta",
                    type="primary",
                    width="stretch",
                )

            if not submitted:
                return

            if not password:
                st.error(
                    "Informe sua senha para continuar."
                )
                return

            if not is_account_deletion_confirmed(
                confirmation
            ):
                st.error(
                    "Digite EXCLUIR CONTA corretamente "
                    "para confirmar a exclusão."
                )
                return

            try:
                authenticated_account = (
                    authenticate_user_account(
                        database_path=ARQUIVO_BANCO,
                        username=current_account["username"],
                        password=password,
                    )
                )

                if (
                    authenticated_account is None
                    or authenticated_account["user_id"]
                    != current_account["user_id"]
                ):
                    st.error(
                        "A senha informada está incorreta."
                    )
                    return

                delete_user_account_and_data(
                    database_path=ARQUIVO_BANCO,
                    user_id=current_account["user_id"],
                )

                clear_session_preserving_visual_preferences()

                st.session_state[
                    AUTH_FEEDBACK_KEY
                ] = {
                    "type": "success",
                    "message": (
                        "Sua conta e os dados associados "
                        "foram excluídos."
                    ),
                }

                st.cache_data.clear()
                st.rerun()

            except (
                ValueError,
                RuntimeError,
            ) as error:
                st.error(
                    str(error)
                )
                

def render_data_management() -> None:
    """Exibe a área de gerenciamento dos dados."""
    render_html(
        build_page_header_html(
            title="Dados e privacidade",
            description=(
                "Escolha quais dados serão exibidos "
                "e controle as informações associadas "
                "à sua conta."
            ),
        )
    )

    _show_feedback()
    _render_current_mode()

    summary = _render_data_summary()

    _render_user_data_action(summary)
    _render_demo_action()
    _render_reset_action()
    _render_account_deletion_action()
