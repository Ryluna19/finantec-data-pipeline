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
from src.user_context import (
    LOCAL_USER_ID,
)


PROFILE_FEEDBACK_KEY = (
    "profile_feedback"
)

KNOWLEDGE_LEVEL_OPTIONS = [
    "iniciante",
    "intermediário",
    "avançado",
]

COMMUNICATION_TONE_OPTIONS = [
    "claro, direto e educativo",
    "resumido e objetivo",
    "detalhado e educativo",
]


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


def _get_option_index(
    options: list[str],
    current_value: object,
) -> int:
    """Obtém o índice seguro de uma opção atual."""
    normalized_value = str(
        current_value
        or ""
    ).strip()

    if normalized_value in options:
        return options.index(
            normalized_value
        )

    return 0


def income_sources_to_dataframe(
    profile: dict[str, Any],
) -> pd.DataFrame:
    """Converte as fontes de renda para edição em tabela."""
    sources = profile.get(
        "fontes_de_renda",
        [],
    )

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

    for index, row in table.iterrows():
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


def _render_profile_summary(
    profile: dict[str, Any],
) -> None:
    """Exibe um resumo do perfil atual."""
    situation = profile.get(
        "situacao_atual",
        {},
    )

    preferences = profile.get(
        "preferencias_de_comunicacao",
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

    monthly_income = float(
        profile.get(
            "renda_mensal_principal",
            0,
        )
        or 0
    )

    knowledge_level = str(
        preferences.get(
            "nivel_de_conhecimento_financeiro",
            "iniciante",
        )
    ).capitalize()

    st.markdown(
        f"### {name}"
    )

    st.caption(
        occupation
    )

    (
        income_column,
        knowledge_column,
        debt_column,
        card_column,
    ) = st.columns(
        4,
        gap="small",
    )

    with income_column:
        st.metric(
            "Renda principal",
            format_currency(
                monthly_income
            ),
        )

    with knowledge_column:
        st.metric(
            "Conhecimento financeiro",
            knowledge_level,
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
    monthly_income: float,
    income_sources: pd.DataFrame,
    has_debts: bool,
    uses_credit_card: bool,
    observation: str,
    communication_tone: str,
    knowledge_level: str,
) -> dict[str, Any]:
    """Monta o perfil recebido pelo repositório."""
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
            prepare_income_sources(
                income_sources
            )
        ),
        "situacao_atual": {
            "possui_dividas": has_debts,
            "utiliza_cartao_de_credito": (
                uses_credit_card
            ),
            "observacao": observation,
        },
        "preferencias_de_comunicacao": {
            "tom": communication_tone,
            "nivel_de_conhecimento_financeiro": (
                knowledge_level
            ),
        },
    }


def render_user_profile(
    profile: dict[str, Any],
) -> None:
    """Exibe e permite editar o perfil financeiro."""
    st.subheader(
        "Meu perfil"
    )

    st.caption(
        "Estas informações personalizam as metas "
        "e o contexto utilizado pelo assistente."
    )

    _show_profile_feedback()

    with st.container(
        border=True,
        key="profile-summary-card",
    ):
        _render_profile_summary(
            profile
        )

    st.markdown(
        "### Editar perfil"
    )

    situation = profile.get(
        "situacao_atual",
        {},
    )

    preferences = profile.get(
        "preferencias_de_comunicacao",
        {},
    )

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

    current_tone = preferences.get(
        "tom",
        COMMUNICATION_TONE_OPTIONS[0],
    )

    tone_options = (
        COMMUNICATION_TONE_OPTIONS.copy()
    )

    if current_tone not in tone_options:
        tone_options.append(
            str(
                current_tone
            )
        )

    current_knowledge = preferences.get(
        "nivel_de_conhecimento_financeiro",
        KNOWLEDGE_LEVEL_OPTIONS[0],
    )

    knowledge_options = (
        KNOWLEDGE_LEVEL_OPTIONS.copy()
    )

    if (
        current_knowledge
        not in knowledge_options
    ):
        knowledge_options.append(
            str(
                current_knowledge
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

        monthly_income = st.number_input(
            "Renda mensal principal",
            min_value=0.0,
            value=float(
                profile.get(
                    "renda_mensal_principal",
                    0,
                )
                or 0
            ),
            step=100.0,
            format="%.2f",
        )

        st.markdown(
            "#### Fontes de renda"
        )

        st.caption(
            "Detalhe a composição da renda. "
            "Adicione ou remova linhas conforme necessário."
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

        st.markdown(
            "#### Preferências do assistente"
        )

        (
            knowledge_column,
            tone_column,
        ) = st.columns(
            2,
            gap="medium",
        )

        with knowledge_column:
            knowledge_level = st.selectbox(
                "Conhecimento financeiro",
                options=knowledge_options,
                index=_get_option_index(
                    knowledge_options,
                    current_knowledge,
                ),
                format_func=lambda value: (
                    value.capitalize()
                ),
            )

        with tone_column:
            communication_tone = st.selectbox(
                "Estilo das explicações",
                options=tone_options,
                index=_get_option_index(
                    tone_options,
                    current_tone,
                ),
            )

        submitted = st.form_submit_button(
            "Salvar perfil",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    try:
        profile_payload = (
            _build_profile_payload(
                name=name,
                age=int(age),
                occupation=occupation,
                monthly_income=float(
                    monthly_income
                ),
                income_sources=(
                    income_sources
                ),
                has_debts=has_debts,
                uses_credit_card=(
                    uses_credit_card
                ),
                observation=observation,
                communication_tone=(
                    communication_tone
                ),
                knowledge_level=(
                    knowledge_level
                ),
            )
        )

        save_user_profile(
            database_path=(
                ARQUIVO_BANCO
            ),
            user_id=LOCAL_USER_ID,
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

    _set_profile_feedback(
        "success",
        "Perfil atualizado com sucesso.",
    )

    st.cache_data.clear()
    st.rerun()