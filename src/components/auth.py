"""Interface de autenticação local do FinanTec."""

from __future__ import annotations

from typing import Any

import streamlit as st

from data_loader import ARQUIVO_BANCO
from src.account_repository import (
    DuplicateUserAccountError,
    authenticate_user_account,
    create_user_account,
    has_user_accounts,
)
from src.user_context import (
    LOCAL_USER_ID,
    get_current_account,
    set_current_account,
)


AUTH_FEEDBACK_KEY = "finantec_auth_feedback"

def choose_registration_user_id(
    accounts_exist: bool,
) -> str | None:
    """Preserva os dados antigos na primeira conta criada."""
    if accounts_exist:
        return None

    return LOCAL_USER_ID


def _start_authenticated_session(
    account: dict[str, Any],
) -> None:
    """Inicia uma sessão limpa para a conta informada."""
    st.session_state.clear()

    set_current_account(
        account
    )

    st.cache_data.clear()
    st.rerun()


def _render_login_form() -> None:
    """Exibe o formulário de entrada."""
    st.markdown(
        "### Entrar"
    )

    st.caption(
        "Acesse seus dados financeiros locais."
    )

    with st.form(
        "finantec-login-form",
        border=True,
    ):
        username = st.text_input(
            "Nome de usuário",
            max_chars=50,
            autocomplete="username",
        )

        password = st.text_input(
            "Senha",
            type="password",
            max_chars=128,
            autocomplete="current-password",
        )

        submitted = st.form_submit_button(
            "Entrar",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    try:
        account = authenticate_user_account(
            database_path=ARQUIVO_BANCO,
            username=username,
            password=password,
        )

    except RuntimeError as error:
        st.error(
            str(error)
        )
        return

    if account is None:
        st.error(
            "Nome de usuário ou senha inválidos."
        )
        return

    _start_authenticated_session(
        account
    )


def _render_registration_form(
    *,
    accounts_exist: bool,
) -> None:
    """Exibe o formulário de criação de conta."""
    st.markdown(
        "### Criar conta"
    )

    if not accounts_exist:
        st.info(
            "A primeira conta será associada aos "
            "dados pessoais já existentes neste dispositivo."
        )

    st.caption(
        "Cada conta mantém transações, perfil, "
        "metas e orçamento separados."
    )

    with st.form(
        "finantec-registration-form",
        border=True,
    ):
        username = st.text_input(
            "Nome de usuário",
            max_chars=50,
            autocomplete="username",
            help=(
                "Use letras, números, ponto, "
                "hífen ou sublinhado."
            ),
        )

        password = st.text_input(
            "Senha",
            type="password",
            max_chars=128,
            autocomplete="new-password",
            help=(
                "A senha deve possuir pelo menos "
                "8 caracteres."
            ),
        )

        password_confirmation = st.text_input(
            "Confirmar senha",
            type="password",
            max_chars=128,
            autocomplete="new-password",
        )

        submitted = st.form_submit_button(
            "Criar conta",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if password != password_confirmation:
        st.error(
            "A confirmação da senha não corresponde."
        )
        return

    registration_user_id = (
        choose_registration_user_id(
            accounts_exist
        )
    )

    try:
        account = create_user_account(
            database_path=ARQUIVO_BANCO,
            username=username,
            password=password,
            user_id=registration_user_id,
        )

    except (
        DuplicateUserAccountError,
        ValueError,
        RuntimeError,
    ) as error:
        st.error(
            str(error)
        )
        return

    _start_authenticated_session(
        account
    )

def _show_auth_feedback() -> None:
    """Exibe mensagens deixadas por uma sessão encerrada."""
    feedback = st.session_state.pop(
        AUTH_FEEDBACK_KEY,
        None,
    )

    if not feedback:
        return

    message = str(
        feedback.get(
            "message",
            "",
        )
    )

    if feedback.get("type") == "success":
        st.success(message)
        return

    if feedback.get("type") == "warning":
        st.warning(message)
        return

    st.error(message)

def render_authentication_gate(
) -> dict[str, str] | None:
    """Impede o acesso ao aplicativo sem uma conta autenticada."""
    current_account = (
        get_current_account()
    )

    if current_account is not None:
        return current_account

    st.title(
        "FinanTec"
    )

    st.caption(
        "Organização financeira local e privada."
    )
    
    _show_auth_feedback()

    try:
        accounts_exist = (
            has_user_accounts(
                ARQUIVO_BANCO
            )
        )

    except RuntimeError as error:
        st.error(
            str(error)
        )
        return None

    if not accounts_exist:
        st.markdown(
            "Crie sua primeira conta para continuar."
        )

        _render_registration_form(
            accounts_exist=False,
        )

        return None

    login_tab, registration_tab = (
        st.tabs(
            (
                "Entrar",
                "Criar conta",
            )
        )
    )

    with login_tab:
        _render_login_form()

    with registration_tab:
        _render_registration_form(
            accounts_exist=True,
        )

    return None


def render_account_sidebar(
    account: dict[str, str],
) -> None:
    """Exibe a conta atual e a ação de saída."""
    with st.sidebar:
        st.caption(
            "Conta atual"
        )

        st.markdown(
            f"**{account['username']}**"
        )

        if st.button(
            "Sair",
            key="finantec-logout",
            use_container_width=True,
        ):
            st.session_state.clear()
            st.cache_data.clear()
            st.rerun()

        st.divider()