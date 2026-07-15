"""Interface de visualização e edição do perfil financeiro."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from analytics import (
    formatar_moeda as format_currency,
)
from data_loader import ARQUIVO_BANCO
from src.profile_repository import (
    save_user_profile,
)


PROFILE_FEEDBACK_KEY = (
    "profile_feedback"
)

PROFILE_EDIT_MODE_KEY = (
    "profile_edit_mode"
)


def _show_profile_feedback() -> None:
    """Exibe o resultado preservado após a atualização."""
    feedback = st.session_state.pop(
        PROFILE_FEEDBACK_KEY,
        None,
    )

    if not feedback:
        return

    message_type = feedback.get(
        "type",
        "success",
    )

    message = feedback.get(
        "message",
        "",
    )

    if message_type == "success":
        st.success(
            message
        )
        return

    st.error(
        message
    )


def _set_profile_feedback(
    message_type: str,
    message: str,
) -> None:
    """Guarda uma mensagem para o próximo rerun."""
    st.session_state[
        PROFILE_FEEDBACK_KEY
    ] = {
        "type": message_type,
        "message": message,
    }


def _set_profile_edit_mode(
    is_editing: bool,
) -> None:
    """Ativa ou encerra a edição do perfil."""
    st.session_state[
        PROFILE_EDIT_MODE_KEY
    ] = is_editing


def income_sources_to_dataframe(
    profile: dict[str, Any],
) -> pd.DataFrame:
    """Converte as fontes de renda para edição em tabela."""
    sources = profile.get(
        "fontes_de_renda",
        [],
    )

    if not isinstance(
        sources,
        list,
    ):
        sources = []

    rows = []

    for source in sources:
        if not isinstance(
            source,
            dict,
        ):
            continue

        rows.append(
            {
                "Tipo": str(
                    source.get(
                        "tipo",
                        "",
                    )
                ).strip(),
                "Valor mensal": (
                    pd.to_numeric(
                        source.get(
                            "valor_mensal",
                            0,
                        ),
                        errors="coerce",
                    )
                ),
            }
        )

    if not rows:
        saved_income = pd.to_numeric(
            profile.get(
                "renda_mensal_principal",
                0,
            ),
            errors="coerce",
        )

        if (
            not pd.isna(
                saved_income
            )
            and float(
                saved_income
            ) > 0
        ):
            rows.append(
                {
                    "Tipo": "Renda principal",
                    "Valor mensal": float(
                        saved_income
                    ),
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "Tipo",
            "Valor mensal",
        ],
    )


def prepare_income_sources(
    table: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Normaliza as fontes de renda editadas."""
    if table is None or table.empty:
        return []

    sources: list[
        dict[str, Any]
    ] = []

    for _, row in table.iterrows():
        source_type = str(
            row.get(
                "Tipo",
                "",
            )
            or ""
        ).strip()

        monthly_value = pd.to_numeric(
            row.get(
                "Valor mensal",
                None,
            ),
            errors="coerce",
        )

        value_is_empty = pd.isna(
            monthly_value
        )

        if (
            not source_type
            and value_is_empty
        ):
            continue

        if not source_type:
            raise ValueError(
                "Informe o tipo de todas "
                "as fontes de renda preenchidas."
            )

        if value_is_empty:
            monthly_value = 0.0

        if float(
            monthly_value
        ) < 0:
            raise ValueError(
                "O valor de uma fonte de renda "
                "não pode ser negativo."
            )

        sources.append(
            {
                "tipo": source_type,
                "valor_mensal": float(
                    monthly_value
                ),
            }
        )

    return sources


def calculate_monthly_income(
    table: pd.DataFrame,
) -> float:
    """Soma os valores mensais das fontes de renda."""
    sources = prepare_income_sources(
        table
    )

    return round(
        sum(
            float(
                source[
                    "valor_mensal"
                ]
            )
            for source in sources
        ),
        2,
    )


def _render_profile_summary(
    profile: dict[str, Any],
) -> None:
    """Exibe um resumo do perfil atual."""
    situation = profile.get(
        "situacao_atual",
        {},
    )

    name = str(
        profile.get(
            "nome",
            "Perfil não configurado",
        )
    )

    occupation = str(
        profile.get(
            "ocupacao",
            "",
        )
        or "Ocupação não informada"
    )

    age = profile.get(
        "idade"
    )

    monthly_income = float(
        profile.get(
            "renda_mensal_principal",
            0,
        )
        or 0
    )

    profile_details = [
        occupation,
    ]

    if age:
        profile_details.append(
            f"{int(age)} anos"
        )

    st.markdown(
        f"### {name}"
    )

    st.caption(
        " • ".join(
            profile_details
        )
    )

    (
        income_column,
        debt_column,
        card_column,
    ) = st.columns(
        3,
        gap="small",
    )

    with income_column:
        st.metric(
            "Renda mensal total",
            format_currency(
                monthly_income
            ),
        )

    with debt_column:
        st.metric(
            "Possui dívidas",
            (
                "Sim"
                if situation.get(
                    "possui_dividas",
                    False,
                )
                else "Não"
            ),
        )

    with card_column:
        st.metric(
            "Usa cartão de crédito",
            (
                "Sim"
                if situation.get(
                    "utiliza_cartao_de_credito",
                    False,
                )
                else "Não"
            ),
        )

    observation = str(
        situation.get(
            "observacao",
            "",
        )
    ).strip()

    if observation:
        st.info(
            observation
        )


def _build_profile_payload(
    *,
    name: str,
    age: int,
    occupation: str,
    income_sources: pd.DataFrame,
    has_debts: bool,
    uses_credit_card: bool,
    observation: str,
    existing_preferences: dict[str, Any],
) -> dict[str, Any]:
    """Monta o perfil recebido pelo repositório."""
    normalized_income_sources = (
        prepare_income_sources(
            income_sources
        )
    )

    monthly_income = round(
        sum(
            float(
                source[
                    "valor_mensal"
                ]
            )
            for source in (
                normalized_income_sources
            )
        ),
        2,
    )

    return {
        "nome": name,
        "idade": (
            None
            if age <= 0
            else age
        ),
        "ocupacao": occupation,
        "renda_mensal_principal": (
            monthly_income
        ),
        "fontes_de_renda": (
            normalized_income_sources
        ),
        "situacao_atual": {
            "possui_dividas": has_debts,
            "utiliza_cartao_de_credito": (
                uses_credit_card
            ),
            "observacao": observation,
        },
        "preferencias_de_comunicacao": (
            dict(
                existing_preferences
            )
        ),
    }


def render_user_profile(
    profile: dict[str, Any],
    user_id: str,
    data_mode: str,
) -> None:
    """Exibe e permite editar o perfil financeiro."""
    st.subheader(
        "Meu perfil",
        anchor="meu-perfil",
    )

    st.caption(
        "Consulte e atualize suas informações "
        "financeiras pessoais."
    )

    _show_profile_feedback()

    is_demo = data_mode == "demo"
    is_configured = bool(
        str(
            profile.get(
                "nome",
                "",
            )
            or ""
        ).strip()
    )

    if is_demo:
        st.info(
            "Perfil de demonstração. "
            "Estas informações são fictícias e somente leitura."
        )

        with st.container(
            border=True,
            key="profile-summary-card",
        ):
            _render_profile_summary(
                profile
            )

        return

    is_editing = bool(
        st.session_state.get(
            PROFILE_EDIT_MODE_KEY,
            False,
        )
    )

    if not is_editing:
        if is_configured:
            with st.container(
                border=True,
                key="profile-summary-card",
            ):
                _render_profile_summary(
                    profile
                )

        else:
            with st.container(
                border=True,
                key="profile-empty-card",
            ):
                st.markdown(
                    "### Perfil não configurado"
                )

                st.caption(
                    "Preencha suas informações para "
                    "configurar o perfil financeiro."
                )

        if st.button(
            (
                "Editar perfil"
                if is_configured
                else "Configurar perfil"
            ),
            key="start-profile-edit",
            type="primary",
        ):
            _set_profile_edit_mode(
                True
            )

            st.rerun()

        return

    st.markdown(
        (
            "### Editar perfil"
            if is_configured
            else "### Configurar perfil"
        )
    )

    situation = profile.get(
        "situacao_atual",
        {},
    )

    existing_preferences = profile.get(
        "preferencias_de_comunicacao",
        {},
    )

    if not isinstance(
        existing_preferences,
        dict,
    ):
        existing_preferences = {}

    current_age = profile.get(
        "idade"
    )

    age_value = (
        int(current_age)
        if current_age is not None
        else 0
    )

    current_income_sources = (
        income_sources_to_dataframe(
            profile
        )
    )

    with st.form(
        "user-profile-form",
        border=True,
    ):
        (
            name_column,
            age_column,
        ) = st.columns(
            [
                3,
                1,
            ],
            gap="medium",
        )

        with name_column:
            name = st.text_input(
                "Nome",
                value=str(
                    profile.get(
                        "nome",
                        "",
                    )
                ),
                max_chars=120,
            )

        with age_column:
            age = st.number_input(
                "Idade",
                min_value=0,
                max_value=130,
                value=age_value,
                step=1,
                help=(
                    "Use 0 para deixar "
                    "a idade não informada."
                ),
            )

        occupation = st.text_input(
            "Ocupação",
            value=str(
                profile.get(
                    "ocupacao",
                    "",
                )
            ),
            max_chars=150,
            placeholder=(
                "Ex.: estudante, estagiário, desenvolvedor"
            ),
        )

        st.markdown(
            "#### Fontes de renda"
        )

        st.caption(
            "A renda mensal total será calculada "
            "automaticamente pela soma das fontes "
            "informadas."
        )

        income_sources = st.data_editor(
            current_income_sources,
            key="profile-income-sources",
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            column_config={
                "Tipo": (
                    st.column_config.TextColumn(
                        "Tipo",
                        required=True,
                        width="large",
                        help=(
                            "Ex.: salário, estágio, "
                            "freelance ou benefício."
                        ),
                    )
                ),
                "Valor mensal": (
                    st.column_config.NumberColumn(
                        "Valor mensal",
                        min_value=0.0,
                        step=50.0,
                        format="R$ %.2f",
                        width="medium",
                    )
                ),
            },
        )

        st.markdown(
            "#### Situação financeira"
        )

        (
            debt_column,
            card_column,
        ) = st.columns(
            2,
            gap="medium",
        )

        with debt_column:
            has_debts = st.checkbox(
                "Possuo dívidas atualmente",
                value=bool(
                    situation.get(
                        "possui_dividas",
                        False,
                    )
                ),
            )

        with card_column:
            uses_credit_card = st.checkbox(
                "Utilizo cartão de crédito",
                value=bool(
                    situation.get(
                        "utiliza_cartao_de_credito",
                        False,
                    )
                ),
            )

        observation = st.text_area(
            "Observação pessoal",
            value=str(
                situation.get(
                    "observacao",
                    "",
                )
            ),
            max_chars=1000,
            placeholder=(
                "Ex.: quero reduzir gastos por impulso "
                "e guardar dinheiro todos os meses."
            ),
        )

        (
            save_column,
            cancel_column,
        ) = st.columns(
            2,
            gap="medium",
        )

        with save_column:
            submitted = (
                st.form_submit_button(
                    "Salvar alterações",
                    type="primary",
                    use_container_width=True,
                )
            )

        with cancel_column:
            cancelled = (
                st.form_submit_button(
                    "Cancelar",
                    use_container_width=True,
                )
            )

    if cancelled:
        _set_profile_edit_mode(
            False
        )

        st.rerun()

    if not submitted:
        return

    try:
        profile_payload = (
            _build_profile_payload(
                name=name,
                age=int(
                    age
                ),
                occupation=occupation,
                income_sources=(
                    income_sources
                ),
                has_debts=has_debts,
                uses_credit_card=(
                    uses_credit_card
                ),
                observation=observation,
                existing_preferences=(
                    existing_preferences
                ),
            )
        )

        save_user_profile(
            database_path=(
                ARQUIVO_BANCO
            ),
            user_id=user_id,
            profile=profile_payload,
        )

    except (
        ValueError,
        RuntimeError,
    ) as error:
        st.error(
            str(
                error
            )
        )

        return

    _set_profile_edit_mode(
        False
    )

    _set_profile_feedback(
        "success",
        (
            "Perfil atualizado com sucesso."
            if is_configured
            else "Perfil configurado com sucesso."
        ),
    )

    st.cache_data.clear()
    st.rerun()
