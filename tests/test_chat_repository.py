"""Testes da persistência local do histórico de conversa."""

from __future__ import annotations

from src.chat_repository import (
    clear_chat_messages,
    load_chat_messages,
    save_chat_exchange,
)


def test_save_and_load_chat_exchange(
    tmp_path,
):
    database_path = (
        tmp_path
        / "chat.db"
    )

    save_chat_exchange(
        database_path=database_path,
        period="Julho/2026",
        data_mode="user",
        question="Quanto ainda tenho?",
        response="Seu saldo é de R$ 500,00.",
        response_source="local",
    )

    messages = load_chat_messages(
        database_path=database_path,
        period="Julho/2026",
        data_mode="user",
    )

    assert messages == [
        {
            "role": "user",
            "content": (
                "Quanto ainda tenho?"
            ),
            "source": "",
        },
        {
            "role": "assistant",
            "content": (
                "Seu saldo é de R$ 500,00."
            ),
            "source": "local",
        },
    ]


def test_chat_history_isolated_by_period(
    tmp_path,
):
    database_path = (
        tmp_path
        / "chat.db"
    )

    save_chat_exchange(
        database_path=database_path,
        period="Junho/2026",
        data_mode="user",
        question="Pergunta de junho",
        response="Resposta de junho",
        response_source="ai",
    )

    save_chat_exchange(
        database_path=database_path,
        period="Julho/2026",
        data_mode="user",
        question="Pergunta de julho",
        response="Resposta de julho",
        response_source="local",
    )

    june_messages = (
        load_chat_messages(
            database_path=database_path,
            period="Junho/2026",
            data_mode="user",
        )
    )

    july_messages = (
        load_chat_messages(
            database_path=database_path,
            period="Julho/2026",
            data_mode="user",
        )
    )

    assert len(
        june_messages
    ) == 2

    assert (
        june_messages[0]["content"]
        == "Pergunta de junho"
    )

    assert len(
        july_messages
    ) == 2

    assert (
        july_messages[0]["content"]
        == "Pergunta de julho"
    )


def test_chat_history_isolated_by_data_mode(
    tmp_path,
):
    database_path = (
        tmp_path
        / "chat.db"
    )

    save_chat_exchange(
        database_path=database_path,
        period="2026",
        data_mode="user",
        question="Pergunta real",
        response="Resposta real",
        response_source="local",
    )

    save_chat_exchange(
        database_path=database_path,
        period="2026",
        data_mode="demo",
        question="Pergunta demo",
        response="Resposta demo",
        response_source="ai",
    )

    user_messages = (
        load_chat_messages(
            database_path=database_path,
            period="2026",
            data_mode="user",
        )
    )

    demo_messages = (
        load_chat_messages(
            database_path=database_path,
            period="2026",
            data_mode="demo",
        )
    )

    assert (
        user_messages[0]["content"]
        == "Pergunta real"
    )

    assert (
        demo_messages[0]["content"]
        == "Pergunta demo"
    )


def test_clear_chat_removes_only_selected_context(
    tmp_path,
):
    database_path = (
        tmp_path
        / "chat.db"
    )

    save_chat_exchange(
        database_path=database_path,
        period="Junho/2026",
        data_mode="user",
        question="Pergunta de junho",
        response="Resposta de junho",
        response_source="local",
    )

    save_chat_exchange(
        database_path=database_path,
        period="Julho/2026",
        data_mode="user",
        question="Pergunta de julho",
        response="Resposta de julho",
        response_source="local",
    )

    deleted_count = (
        clear_chat_messages(
            database_path=database_path,
            period="Junho/2026",
            data_mode="user",
        )
    )

    assert deleted_count == 2

    assert (
        load_chat_messages(
            database_path=database_path,
            period="Junho/2026",
            data_mode="user",
        )
        == []
    )

    assert len(
        load_chat_messages(
            database_path=database_path,
            period="Julho/2026",
            data_mode="user",
        )
    ) == 2


def test_load_chat_respects_limit(
    tmp_path,
):
    database_path = (
        tmp_path
        / "chat.db"
    )

    for index in range(
        4
    ):
        save_chat_exchange(
            database_path=database_path,
            period="2026",
            data_mode="user",
            question=(
                f"Pergunta {index}"
            ),
            response=(
                f"Resposta {index}"
            ),
            response_source="local",
        )

    messages = load_chat_messages(
        database_path=database_path,
        period="2026",
        data_mode="user",
        limit=4,
    )

    assert len(
        messages
    ) == 4

    assert (
        messages[0]["content"]
        == "Pergunta 2"
    )

    assert (
        messages[-1]["content"]
        == "Resposta 3"
    )