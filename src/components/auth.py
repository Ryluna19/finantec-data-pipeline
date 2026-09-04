"""Interface de autenticação do FinanTec."""

from __future__ import annotations

import hmac
import os

from datetime import timedelta
from math import ceil
from html import escape
from typing import Any

import streamlit as st

from data_loader import ARQUIVO_BANCO
from src.account_repository import (
    DuplicateUserAccountError,
    authenticate_user_account,
    create_user_account,
    has_user_accounts,
    is_user_account_expired,
    get_user_account_remaining_time,
)
from src.data_reset import (
    delete_expired_user_accounts,
)
from src.user_context import (
    LOCAL_USER_ID,
    get_current_account,
    set_current_account,
)
from ui_components import render_html

from components.header import (
    load_brand_mark_data_uri,
)

from components.appearance import (
    clear_session_preserving_visual_preferences,
    render_appearance_toolbar,
)

AUTH_FEEDBACK_KEY = "finantec_auth_feedback"

REGISTRATION_CODE_ENV = "FINANTEC_REGISTRATION_CODE"

TEMPORARY_ACCOUNT_OPTION = "Teste por 24 horas"

PERMANENT_ACCOUNT_OPTION = "Conta permanente"


def is_registration_code_valid(
    registration_code: str,
) -> bool:
    """Valida o código necessário para criar novas contas."""
    expected_code = os.environ.get(
        REGISTRATION_CODE_ENV,
        "",
    ).strip()

    provided_code = str(registration_code or "").strip()

    if not expected_code or not provided_code:
        return False

    return hmac.compare_digest(
        provided_code,
        expected_code,
    )


def is_registration_authorized(
    registration_code: str,
    *,
    temporary: bool,
) -> bool:
    """Autoriza teste público ou cadastro por convite."""
    if temporary:
        return True

    return is_registration_code_valid(registration_code)


def choose_registration_user_id(
    accounts_exist: bool,
    *,
    temporary: bool = False,
) -> str | None:
    """Preserva dados antigos somente na primeira conta permanente."""
    if accounts_exist or temporary:
        return None

    return LOCAL_USER_ID


def _start_authenticated_session(
    account: dict[str, Any],
) -> None:
    """Inicia uma sessão limpa para a conta informada."""
    clear_session_preserving_visual_preferences()
    set_current_account(account)

    st.cache_data.clear()
    st.rerun()


def _render_auth_brand_panel() -> None:
    """Exibe a identidade do produto na autenticação."""
    brand_mark_src = escape(
        load_brand_mark_data_uri(),
        quote=True,
    )

    render_html(f"""
        <section class="finantec-auth-brand">
            <div class="finantec-auth-brand-top">
                <div class="finantec-auth-logo">
                    <img
                        class="finantec-auth-brand-mark"
                        src="{brand_mark_src}"
                        alt=""
                    />
                </div>

                <span class="finantec-auth-product-name">
                    FinanTec
                </span>
            </div>

            <div class="finantec-auth-brand-copy">
                <span class="finantec-auth-eyebrow">
                    Organização financeira pessoal
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
                      <strong>Dados persistentes</strong>
                        <p>
                            Suas informações permanecem
                            vinculadas à sua conta.
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
                Projeto pessoal publicado para demonstração e testes.
            </p>
        </section>
        """)


def _render_auth_form_heading(
    *,
    accounts_exist: bool,
) -> None:
    """Exibe o título da área de acesso."""
    title = (
        "Bem-vindo de volta" if accounts_exist else "Comece a organizar suas finanças"
    )

    description = (
        "Entre na sua conta ou crie um novo espaço financeiro."
        if accounts_exist
        else ("Crie a primeira conta para iniciar " "seu espaço financeiro.")
    )

    render_html(f"""
        <header class="finantec-auth-form-heading">
            <span class="finantec-auth-form-eyebrow">
                Acesso seguro
            </span>

            <h2>{title}</h2>

            <p>{description}</p>
        </header>
        """)


def _render_login_form() -> None:
    """Exibe o formulário de entrada."""
    st.markdown("### Entrar")

    st.caption("Use seu nome de usuário e sua senha para continuar.")

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
            width="stretch",
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
        st.error("Nome de usuário ou senha inválidos.")
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

    temporary = False

    if not accounts_exist:
        st.info(
            "A primeira conta deste ambiente será permanente "
            "e associada aos dados locais existentes."
        )

    else:
        account_type = st.radio(
            "Tipo de conta",
            options=(
                TEMPORARY_ACCOUNT_OPTION,
                PERMANENT_ACCOUNT_OPTION,
            ),
            horizontal=True,
            key="finantec-registration-account-type",
        )

        temporary = (
            account_type
            == TEMPORARY_ACCOUNT_OPTION
        )

        if temporary:
            st.info(
                "Acesso completo por 24 horas. Os dados "
                "permanecem entre acessos e são excluídos "
                "após o prazo. Use apenas dados fictícios."
            )

        else:
            st.caption(
                "A conta permanente requer o código de acesso "
                "fornecido pelo responsável pelo projeto."
            )

    registration_code = ""

    with st.form(
        "finantec-registration-form",
        border=False,
    ):
        if not temporary:
            registration_code = st.text_input(
                "Código de acesso",
                type="password",
                max_chars=128,
                autocomplete="off",
                placeholder="Digite o código de acesso",
                help=(
                    "O código é fornecido às pessoas "
                    "convidadas para usar o FinanTec."
                ),
            )

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

        submit_label = (
            "Criar conta de teste"
            if temporary
            else "Criar conta permanente"
        )

        submitted = st.form_submit_button(
            submit_label,
            type="primary",
            width="stretch",
        )

    if not submitted:
        return

    if not is_registration_authorized(
        registration_code,
        temporary=temporary,
    ):
        st.error(
            "Código de acesso inválido."
        )
        return

    if password != password_confirmation:
        st.error(
            "A confirmação da senha não corresponde."
        )
        return

    registration_user_id = (
        choose_registration_user_id(
            accounts_exist,
            temporary=temporary,
        )
    )

    try:
        account = create_user_account(
            database_path=ARQUIVO_BANCO,
            username=username,
            password=password,
            user_id=registration_user_id,
            temporary=temporary,
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

    message_type = feedback.get("type")

    if message_type == "success":
        st.success(message)
        return

    if message_type == "warning":
        st.warning(message)
        return

    st.error(message)

def format_temporary_account_time_remaining(
    remaining_time: timedelta,
) -> str:
    """Formata o prazo restante para exibição."""
    total_seconds = (
        remaining_time.total_seconds()
    )

    if total_seconds < 60:
        return "menos de 1 minuto"

    total_minutes = ceil(
        total_seconds / 60
    )

    hours, minutes = divmod(
        total_minutes,
        60,
    )

    if hours and minutes:
        return f"{hours}h {minutes}min"

    if hours:
        return f"{hours}h"

    return f"{minutes}min"


def render_temporary_account_notice(
    account: dict[str, Any],
) -> None:
    """Exibe a validade restante da conta temporária."""
    remaining_time = (
        get_user_account_remaining_time(
            account
        )
    )

    if remaining_time is None:
        return

    formatted_time = (
        format_temporary_account_time_remaining(
            remaining_time
        )
    )

    st.warning(
        "Conta temporária de teste — tempo restante: "
        f"{formatted_time}. Todos os dados desta conta "
        "serão excluídos ao final do prazo."
    )

def _end_expired_account_session() -> None:
    """Encerra a sessão e remove contas temporárias vencidas."""
    try:
        delete_expired_user_accounts(
            database_path=ARQUIVO_BANCO,
        )

    except RuntimeError as error:
        st.error(str(error))
        return

    clear_session_preserving_visual_preferences()

    st.session_state[AUTH_FEEDBACK_KEY] = {
        "type": "warning",
        "message": (
            "Sua conta temporária expirou. " "Os dados associados foram excluídos."
        ),
    }

    st.cache_data.clear()
    st.rerun()


def render_authentication_gate() -> dict[str, Any] | None:
    """Impede o acesso ao aplicativo sem autenticação."""
    current_account = get_current_account()

    if current_account is not None:
        if is_user_account_expired(current_account):
            _end_expired_account_session()
            return None

        return current_account

    try:
        delete_expired_user_accounts(
            database_path=ARQUIVO_BANCO,
        )

        accounts_exist = has_user_accounts(ARQUIVO_BANCO)
    except RuntimeError as error:
        st.error(str(error))
        return None

    render_html("""
        <div
            class="finantec-auth-page-marker"
            aria-hidden="true"
        ></div>
        """)

    render_appearance_toolbar(key="finantec-auth-toolbar")

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

            _render_auth_form_heading(accounts_exist=accounts_exist)

            _show_auth_feedback()

            if not accounts_exist:
                _render_registration_form(accounts_exist=False)

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
                    _render_registration_form(accounts_exist=True)

    return None


def _build_account_initials(
    username: str,
) -> str:
    """Cria iniciais curtas para a identidade da conta."""
    normalized_username = " ".join(
        str(username if username is not None else "").strip().split()
    )

    if not normalized_username:
        return "C"

    parts = [part for part in normalized_username.split() if part]

    if len(parts) == 1:
        return parts[0][0].upper()

    return (parts[0][0] + parts[-1][0]).upper()


def build_sidebar_account_html(
    username: str,
) -> str:
    """Monta a identidade compacta da conta na sidebar."""
    normalized_username = (
        " ".join(str(username if username is not None else "").strip().split())
        or "Conta FinanTec"
    )

    initials = _build_account_initials(normalized_username)

    return (
        '<div class="finantec-sidebar-account-identity">'
        '<span class="finantec-sidebar-account-avatar" '
        'aria-hidden="true">'
        f"{escape(initials)}"
        "</span>"
        '<div class="finantec-sidebar-account-copy">'
        '<span class="finantec-sidebar-account-eyebrow">'
        "Conta FinanTec"
        "</span>"
        f'<strong title="{escape(normalized_username)}">'
        f"{escape(normalized_username)}"
        "</strong>"
        "</div>"
        "</div>"
    )


def render_account_sidebar(
    account: dict[str, str],
) -> None:
    """Exibe a conta atual e a ação de encerramento da sessão."""
    username = str(
        account.get(
            "username",
            "Conta FinanTec",
        )
        or "Conta FinanTec"
    ).strip()

    with st.sidebar:
        with st.container(
            key="finantec-sidebar-account",
        ):
            (
                identity_column,
                action_column,
            ) = st.columns(
                [1.75, 0.75],
                gap="small",
            )

            with identity_column:
                render_html(build_sidebar_account_html(username))

            with action_column:
                logout_requested = st.button(
                    "Sair",
                    key="finantec-logout",
                    icon=":material/logout:",
                    type="secondary",
                    help="Encerrar a sessão atual",
                    width="stretch",
                )

            if logout_requested:
                clear_session_preserving_visual_preferences()
                st.cache_data.clear()
                st.rerun()
