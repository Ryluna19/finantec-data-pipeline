"""Testes da persistência do perfil financeiro."""

from __future__ import annotations

import pytest

from src.profile_repository import (
    delete_user_profile,
    load_user_profile,
    normalize_user_profile,
    save_user_profile,
    seed_user_profile_if_missing,
)


def build_profile(
    name: str = "Ryan",
) -> dict:
    """Cria um perfil válido para os testes."""
    return {
        "nome": name,
        "idade": 24,
        "ocupacao": (
            "Desenvolvedor em formação"
        ),
        "renda_mensal_principal": 2500.0,
        "fontes_de_renda": [
            {
                "tipo": "Trabalho",
                "valor_mensal": 2500.0,
            }
        ],
        "objetivos_financeiros": [
            {
                "nome": "Notebook",
                "valor_meta": 3000.0,
            }
        ],
        "situacao_atual": {
            "possui_dividas": False,
            "utiliza_cartao_de_credito": True,
            "observacao": (
                "Deseja organizar melhor "
                "os gastos mensais."
            ),
        },
        "preferencias_de_comunicacao": {
            "tom": (
                "claro, direto e educativo"
            ),
            "nivel_de_conhecimento_financeiro": (
                "iniciante"
            ),
        },
    }


def test_save_and_load_user_profile(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    saved_profile = save_user_profile(
        database_path=database_path,
        user_id="user-1",
        profile=build_profile(),
    )

    loaded_profile = load_user_profile(
        database_path=database_path,
        user_id="user-1",
    )

    assert loaded_profile == saved_profile

    assert (
        loaded_profile[
            "nome"
        ]
        == "Ryan"
    )

    assert (
        loaded_profile[
            "renda_mensal_principal"
        ]
        == 2500.0
    )

    assert (
        loaded_profile[
            "situacao_atual"
        ][
            "utiliza_cartao_de_credito"
        ]
        is True
    )


def test_goals_are_not_stored_inside_profile(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    save_user_profile(
        database_path=database_path,
        user_id="user-1",
        profile=build_profile(),
    )

    loaded_profile = load_user_profile(
        database_path=database_path,
        user_id="user-1",
    )

    assert (
        "objetivos_financeiros"
        not in loaded_profile
    )


def test_update_existing_profile(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    save_user_profile(
        database_path=database_path,
        user_id="user-1",
        profile=build_profile(),
    )

    updated_profile = (
        build_profile(
            name="Ryan Santos"
        )
    )

    updated_profile[
        "renda_mensal_principal"
    ] = 3200.0

    save_user_profile(
        database_path=database_path,
        user_id="user-1",
        profile=updated_profile,
    )

    loaded_profile = load_user_profile(
        database_path=database_path,
        user_id="user-1",
    )

    assert (
        loaded_profile[
            "nome"
        ]
        == "Ryan Santos"
    )

    assert (
        loaded_profile[
            "renda_mensal_principal"
        ]
        == 3200.0
    )


def test_profiles_are_isolated_by_user(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    save_user_profile(
        database_path=database_path,
        user_id="user-1",
        profile=build_profile(
            name="Ryan"
        ),
    )

    save_user_profile(
        database_path=database_path,
        user_id="user-2",
        profile=build_profile(
            name="Marina"
        ),
    )

    first_profile = load_user_profile(
        database_path=database_path,
        user_id="user-1",
    )

    second_profile = load_user_profile(
        database_path=database_path,
        user_id="user-2",
    )

    assert (
        first_profile[
            "nome"
        ]
        == "Ryan"
    )

    assert (
        second_profile[
            "nome"
        ]
        == "Marina"
    )


def test_seed_does_not_replace_existing_profile(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    seed_user_profile_if_missing(
        database_path=database_path,
        user_id="user-1",
        seed_profile=build_profile(
            name="Primeiro perfil"
        ),
    )

    profile = (
        seed_user_profile_if_missing(
            database_path=database_path,
            user_id="user-1",
            seed_profile=build_profile(
                name="Novo perfil"
            ),
        )
    )

    assert (
        profile[
            "nome"
        ]
        == "Primeiro perfil"
    )


def test_delete_user_profile(
    tmp_path,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    save_user_profile(
        database_path=database_path,
        user_id="user-1",
        profile=build_profile(),
    )

    deleted = delete_user_profile(
        database_path=database_path,
        user_id="user-1",
    )

    assert deleted is True

    assert (
        load_user_profile(
            database_path=database_path,
            user_id="user-1",
        )
        is None
    )


def test_rejects_negative_monthly_income():
    profile = build_profile()

    profile[
        "renda_mensal_principal"
    ] = -100.0

    with pytest.raises(
        ValueError,
        match="não pode ser negativo",
    ):
        normalize_user_profile(
            profile
        )


def test_rejects_empty_name():
    profile = build_profile()

    profile[
        "nome"
    ] = "   "

    with pytest.raises(
        ValueError,
        match="nome não pode ser vazio",
    ):
        normalize_user_profile(
            profile
        )


def test_normalizes_text_and_boolean_values():
    profile = build_profile()

    profile["nome"] = "  Ryan  "

    profile[
        "situacao_atual"
    ][
        "possui_dividas"
    ] = "não"

    profile[
        "situacao_atual"
    ][
        "utiliza_cartao_de_credito"
    ] = "sim"

    normalized = normalize_user_profile(
        profile
    )

    assert (
        normalized[
            "nome"
        ]
        == "Ryan"
    )

    assert (
        normalized[
            "situacao_atual"
        ][
            "possui_dividas"
        ]
        is False
    )

    assert (
        normalized[
            "situacao_atual"
        ][
            "utiliza_cartao_de_credito"
        ]
        is True
    )