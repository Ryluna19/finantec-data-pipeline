"""Testes da integração das metas com o carregamento."""

from __future__ import annotations

import data_loader

from src.goal_repository import (
    delete_financial_goal,
)


def build_seed_profile() -> dict:
    """Cria um perfil inicial com metas antigas."""
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


def test_profile_loads_goals_from_database(
    tmp_path,
    monkeypatch,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    monkeypatch.setattr(
        data_loader,
        "ARQUIVO_BANCO",
        database_path,
    )

    monkeypatch.setattr(
        data_loader,
        "carregar_json",
        lambda _: build_seed_profile(),
    )

    profile = (
        data_loader
        .carregar_perfil_usuario()
    )

    goals = profile[
        "objetivos_financeiros"
    ]

    assert len(
        goals
    ) == 2

    assert all(
        "goal_id" in goal
        for goal in goals
    )


def test_deleted_goals_are_not_seeded_again(
    tmp_path,
    monkeypatch,
):
    database_path = (
        tmp_path
        / "finantec.db"
    )

    monkeypatch.setattr(
        data_loader,
        "ARQUIVO_BANCO",
        database_path,
    )

    monkeypatch.setattr(
        data_loader,
        "carregar_json",
        lambda _: build_seed_profile(),
    )

    first_profile = (
        data_loader
        .carregar_perfil_usuario()
    )

    for goal in first_profile[
        "objetivos_financeiros"
    ]:
        delete_financial_goal(
            database_path=database_path,
            user_id=(
                data_loader.LOCAL_USER_ID
            ),
            goal_id=goal["goal_id"],
        )

    second_profile = (
        data_loader
        .carregar_perfil_usuario()
    )

    assert (
        second_profile[
            "objetivos_financeiros"
        ]
        == []
    )


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