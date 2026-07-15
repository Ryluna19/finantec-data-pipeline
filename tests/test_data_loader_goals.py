"""Testes da integração do perfil e das metas com o carregamento."""

from __future__ import annotations

import sqlite3

import data_loader

from src.goal_repository import (
    GOAL_SEED_TABLE_NAME,
    GOAL_TABLE_NAME,
    create_financial_goal,
)
from src.profile_repository import (
    PROFILE_TABLE_NAME,
    save_user_profile,
)


def build_demo_profile() -> dict:
    """Cria a persona fictícia usada nos testes de demonstração."""
    return {
        "nome": "Marina",
        "objetivos_financeiros": [
            {
                "nome": "Reserva",
                "valor_meta": 1500.0,
                "valor_atual": 500.0,
                "prazo_meses": 10,
                "prioridade": "alta",
            },
            {
                "nome": "Notebook",
                "valor_meta": 2800.0,
                "valor_atual": 0.0,
                "prazo_meses": 14,
                "prioridade": "média",
            },
        ],
    }


def configure_database(
    tmp_path,
    monkeypatch,
):
    """Direciona o carregador para um banco temporário."""
    database_path = (
        tmp_path
        / "finantec.db"
    )

    monkeypatch.setattr(
        data_loader,
        "ARQUIVO_BANCO",
        database_path,
    )

    return database_path


def build_goal(
    name: str,
) -> dict:
    """Cria uma meta válida para persistência."""
    return {
        "nome": name,
        "valor_meta": 3000.0,
        "valor_atual": 500.0,
        "prazo_meses": 10,
        "prioridade": "média",
    }


def count_user_rows(
    database_path,
    table_name: str,
    user_id: str,
) -> int:
    """Conta registros de um usuário em uma tabela já criada."""
    with sqlite3.connect(
        database_path
    ) as connection:
        row = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE user_id = ?
            """,
            (
                user_id,
            ),
        ).fetchone()

    return int(
        row[0]
    )


def test_new_personal_user_starts_without_profile_goals_or_seed_marker(
    tmp_path,
    monkeypatch,
) -> None:
    database_path = configure_database(
        tmp_path,
        monkeypatch,
    )

    profile = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-1",
            data_mode="user",
        )
    )

    assert profile == {
        "user_id": "user-1",
        "objetivos_financeiros": [],
    }

    assert count_user_rows(
        database_path,
        PROFILE_TABLE_NAME,
        "user-1",
    ) == 0

    assert count_user_rows(
        database_path,
        GOAL_TABLE_NAME,
        "user-1",
    ) == 0

    assert count_user_rows(
        database_path,
        GOAL_SEED_TABLE_NAME,
        "user-1",
    ) == 0


def test_profile_and_first_goal_can_be_created_independently(
    tmp_path,
    monkeypatch,
) -> None:
    database_path = configure_database(
        tmp_path,
        monkeypatch,
    )

    empty_profile = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-1",
        )
    )

    assert empty_profile[
        "objetivos_financeiros"
    ] == []

    create_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal=build_goal(
            "Notebook"
        ),
    )

    goals_without_profile = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-1",
        )
    )

    assert "nome" not in goals_without_profile
    assert len(
        goals_without_profile[
            "objetivos_financeiros"
        ]
    ) == 1

    save_user_profile(
        database_path=database_path,
        user_id="user-1",
        profile={
            "nome": "Ryan",
        },
    )

    configured_profile = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-1",
        )
    )

    assert configured_profile[
        "nome"
    ] == "Ryan"

    assert len(
        configured_profile[
            "objetivos_financeiros"
        ]
    ) == 1


def test_empty_mode_uses_existing_personal_profile_and_goals(
    tmp_path,
    monkeypatch,
) -> None:
    database_path = configure_database(
        tmp_path,
        monkeypatch,
    )

    save_user_profile(
        database_path=database_path,
        user_id="user-1",
        profile={
            "nome": "Ryan",
        },
    )

    create_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal=build_goal(
            "Reserva"
        ),
    )

    profile = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-1",
            data_mode="empty",
        )
    )

    assert profile[
        "nome"
    ] == "Ryan"

    assert [
        goal["nome"]
        for goal in profile[
            "objetivos_financeiros"
        ]
    ] == [
        "Reserva",
    ]


def test_demo_profile_is_stable_and_does_not_create_database(
    tmp_path,
    monkeypatch,
) -> None:
    database_path = configure_database(
        tmp_path,
        monkeypatch,
    )

    monkeypatch.setattr(
        data_loader,
        "carregar_json",
        lambda _: build_demo_profile(),
    )

    first_demo = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-1",
            data_mode="demo",
        )
    )

    second_demo = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-2",
            data_mode="demo",
        )
    )

    assert first_demo[
        "nome"
    ] == "Marina"

    assert [
        goal["goal_id"]
        for goal in first_demo[
            "objetivos_financeiros"
        ]
    ] == [
        goal["goal_id"]
        for goal in second_demo[
            "objetivos_financeiros"
        ]
    ]

    assert not database_path.exists()


def test_demo_does_not_mix_or_modify_personal_data(
    tmp_path,
    monkeypatch,
) -> None:
    database_path = configure_database(
        tmp_path,
        monkeypatch,
    )

    monkeypatch.setattr(
        data_loader,
        "carregar_json",
        lambda _: build_demo_profile(),
    )

    save_user_profile(
        database_path=database_path,
        user_id="user-1",
        profile={
            "nome": "Ryan",
        },
    )

    create_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal=build_goal(
            "Viagem"
        ),
    )

    personal_before = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-1",
            data_mode="user",
        )
    )

    demo_profile = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-1",
            data_mode="demo",
        )
    )

    personal_after = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-1",
            data_mode="user",
        )
    )

    assert demo_profile[
        "nome"
    ] == "Marina"

    assert [
        goal["nome"]
        for goal in demo_profile[
            "objetivos_financeiros"
        ]
    ] == [
        "Reserva",
        "Notebook",
    ]

    assert personal_after == personal_before

    assert count_user_rows(
        database_path,
        GOAL_SEED_TABLE_NAME,
        "user-1",
    ) == 0


def test_profiles_and_goals_remain_isolated_by_user(
    tmp_path,
    monkeypatch,
) -> None:
    database_path = configure_database(
        tmp_path,
        monkeypatch,
    )

    save_user_profile(
        database_path=database_path,
        user_id="user-1",
        profile={
            "nome": "Perfil 1",
        },
    )

    create_financial_goal(
        database_path=database_path,
        user_id="user-1",
        goal=build_goal(
            "Viagem"
        ),
    )

    first_user = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-1",
        )
    )

    second_user = (
        data_loader
        .carregar_perfil_usuario(
            user_id="user-2",
        )
    )

    assert first_user[
        "nome"
    ] == "Perfil 1"

    assert len(
        first_user[
            "objetivos_financeiros"
        ]
    ) == 1

    assert second_user == {
        "user_id": "user-2",
        "objetivos_financeiros": [],
    }


def test_merge_profile_with_goals_does_not_mutate_profile():
    profile = {
        "nome": "Ryan",
    }

    goals = [
        {
            "goal_id": "goal-1",
            "nome": "Viagem",
        }
    ]

    result = (
        data_loader
        .merge_profile_with_goals(
            profile=profile,
            goals=goals,
        )
    )

    assert (
        result[
            "objetivos_financeiros"
        ]
        == goals
    )

    assert (
        "objetivos_financeiros"
        not in profile
    )
