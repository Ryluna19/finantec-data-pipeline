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
from ui_components import render_html


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
    set_current_account(account)

    st.cache_data.clear()
    st.rerun()


def _render_auth_brand_panel() -> None:
    """Exibe a identidade do produto na autenticação."""
    render_html(
        """
        <section class="finantec-auth-brand">
            <div class="finantec-auth-brand-top">
                <div class="finantec-auth-logo">
                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                        aria-hidden="true"
                    >
                        <path
                            d="M4 7.5H18C19.1 7.5 20 8.4 20 9.5V17.5C20 18.6 19.1 19.5 18 19.5H5C3.9 19.5 3 18.6 3 17.5V6.5C3 5.4 3.9 4.5 5 4.5H16"
                        />
                        <path d="M3 8H18" />
                        <path
                            d="M15.5 12H20V16H15.5C14.4 16 13.5 15.1 13.5 14C13.5 12.9 14.4 12 15.5 12Z"
                        />
                        <circle
                            cx="16.5"
                            cy="14"
                            r="0.5"
                            fill="currentColor"
                            stroke="none"
                        />
                    </svg>
                </div>

                <span class="finantec-auth-product-name">
                    FinanTec
                </span>
            </div>

            <div class="finantec-auth-brand-copy">
                <span class="finantec-auth-eyebrow">
                    Organização financeira local
                </span>

                <h1>
                    Controle seu dinheiro sem complicação.
                </h1>

                <p>
                    Registre transações, acompanhe seus gastos,
                    planeje limites mensais e organize suas metas
                    em um único lugar.
                </p>
            </div>

            <div class="finantec-auth-benefits">
                <div class="finantec-auth-benefit">
                    <span class="finantec-auth-benefit-icon">
                        01
                    </span>

                    <div>
                        <strong>Dados separados</strong>
                        <p>
                            Cada conta mantém suas próprias
                            informações financeiras.
                        </p>
                    </div>
                </div>

                <div class="finantec-auth-benefit">
                    <span class="finantec-auth-benefit-icon">
                        02
                    </span>

                    <div>
                        <strong>Uso local</strong>
                        <p>
                            Seus dados permanecem armazenados
                            no banco local do FinanTec.
                        </p>
                    </div>
                </div>

                <div class="finantec-auth-benefit">
                    <span class="finantec-auth-benefit-icon">
                        03
                    </span>

                    <div>
                        <strong>Visão completa</strong>
                        <p>
                            Dashboard, metas e orçamento integrados
                            às suas transações.
                        </p>
                    </div>
                </div>
            </div>

            <p class="finantec-auth-local-note">
                Projeto educativo de uso local e privado.
            </p>
        </section>
        """
    )


def _render_auth_form_heading(
    *,
    accounts_exist: bool,
) -> None:
    """Exibe o título da área de acesso."""
    title = (
        "Bem-vindo de volta"
        if accounts_exist
        else "Comece a organizar suas finanças"
    )

    description = (
        "Entre na sua conta ou crie um novo espaço financeiro."
        if accounts_exist
        else (
            "Crie a primeira conta para associar os dados "
            "já existentes neste dispositivo."
        )
    )

    render_html(
        f"""
        <header class="finantec-auth-form-heading">
            <span class="finantec-auth-form-eyebrow">
                Acesso seguro
            </span>

            <h2>{title}</h2>

            <p>{description}</p>
        </header>
        """
    )


def _render_login_form() -> None:
    """Exibe o formulário de entrada."""
    st.markdown("### Entrar")

    st.caption(
        "Use seu nome de usuário e sua senha para continuar."
    )

    with st.form(
        "finantec-login-form",
        border=False,
    ):
        username = st.text_input(
            "Nome de usuário",
            max_chars=50,
            autocomplete="username",
            placeholder="Digite seu nome de usuário",
        )

        password = st.text_input(
            "Senha",
            type="password",
            max_chars=128,
            autocomplete="current-password",
            placeholder="Digite sua senha",
        )

        submitted = st.form_submit_button(
            "Entrar no FinanTec",
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
        st.error(str(error))
        return

    if account is None:
        st.error(
            "Nome de usuário ou senha inválidos."
        )
        return

    _start_authenticated_session(account)


def _render_registration_form(
    *,
    accounts_exist: bool,
) -> None:
    """Exibe o formulário de criação de conta."""
    title = (
        "Criar conta"
        if accounts_exist
        else "Criar primeira conta"
    )

    st.markdown(f"### {title}")

    if not accounts_exist:
        st.info(
            "Esta conta será associada aos dados pessoais "
            "já existentes neste dispositivo."
        )
    else:
        st.caption(
            "A nova conta começará sem transações, "
            "perfil, metas ou orçamento."
        )

    with st.form(
        "finantec-registration-form",
        border=False,
    ):
        username = st.text_input(
            "Nome de usuário",
            max_chars=50,
            autocomplete="username",
            placeholder="Escolha um nome de usuário",
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
            placeholder="Crie uma senha",
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
            placeholder="Digite a senha novamente",
        )

        submitted = st.form_submit_button(
            "Criar minha conta",
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

    registration_user_id = choose_registration_user_id(
        accounts_exist
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
        st.error(str(error))
        return

    _start_authenticated_session(account)


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

    message_type = feedback.get(
        "type"
    )

    if message_type == "success":
        st.success(message)
        return

    if message_type == "warning":
        st.warning(message)
        return

    st.error(message)


def render_authentication_gate() -> dict[str, str] | None:
    """Impede o acesso ao aplicativo sem autenticação."""
    current_account = get_current_account()

    if current_account is not None:
        return current_account

    try:
        accounts_exist = has_user_accounts(
            ARQUIVO_BANCO
        )

    except RuntimeError as error:
        st.error(str(error))
        return None

    render_html(
        """
        <div
            class="finantec-auth-page-marker"
            aria-hidden="true"
        ></div>
        """
    )

    with st.container(
        border=True,
        key="finantec-auth-shell",
    ):
        brand_column, form_column = st.columns(
            [1.05, 1],
            gap="small",
        )

        with brand_column:
            _render_auth_brand_panel()

        with form_column:
            _render_auth_form_heading(
                accounts_exist=accounts_exist
            )

            _show_auth_feedback()

            if not accounts_exist:
                _render_registration_form(
                    accounts_exist=False
                )

            else:
                login_tab, registration_tab = st.tabs(
                    (
                        "Entrar",
                        "Criar conta",
                    )
                )

                with login_tab:
                    _render_login_form()

                with registration_tab:
                    _render_registration_form(
                        accounts_exist=True
                    )

    return None


def render_account_sidebar(
    account: dict[str, str],
) -> None:
    """Exibe a conta atual e a ação de saída."""
    with st.sidebar:
        st.caption("Conta atual")

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