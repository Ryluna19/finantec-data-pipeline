"""Testes da integração do agente sem chamadas externas."""

from __future__ import annotations

from types import SimpleNamespace

import agent


class FakeInteractions:
    """Simula o recurso de interações da Gemini."""

    def __init__(self):
        self.last_call = None

    def create(
        self,
        **kwargs,
    ):
        self.last_call = kwargs

        return SimpleNamespace(
            output_text=(
                "Resposta baseada no contexto."
            )
        )


class FakeClient:
    """Simula o cliente necessário pelo agente."""

    def __init__(self):
        self.interactions = (
            FakeInteractions()
        )


def test_agent_sends_classified_intent(
    monkeypatch,
):
    fake_client = FakeClient()

    monkeypatch.setattr(
        agent,
        "obter_cliente",
        lambda: fake_client,
    )

    response = (
        agent.gerar_resposta_finantec(
            pergunta_usuario=(
                "Quanto ainda tenho?"
            ),
            contexto=(
                "RESUMO FINANCEIRO: "
                "saldo_disponivel = 500"
            ),
        )
    )

    request = (
        fake_client
        .interactions
        .last_call
    )

    assert (
        response
        == "Resposta baseada no contexto."
    )

    assert request is not None

    assert (
        "INTENÇÃO IDENTIFICADA "
        "PELA APLICAÇÃO"
        in request["input"]
    )

    assert (
        "intenção: saldo"
        in request["input"]
    )

    assert (
        "Quanto ainda tenho?"
        in request["input"]
    )


def test_empty_question_does_not_create_client(
    monkeypatch,
):
    def fail_if_called():
        raise AssertionError(
            "O cliente não deveria ser criado."
        )

    monkeypatch.setattr(
        agent,
        "obter_cliente",
        fail_if_called,
    )

    response = (
        agent.gerar_resposta_finantec(
            pergunta_usuario="   ",
            contexto="contexto",
        )
    )

    assert response == (
        "Digite uma pergunta "
        "para que eu possa ajudar."
    )


def test_clean_response_formatting():
    response = (
        agent.limpar_formatacao_resposta(
            "`Saldo:` R$ 100,00"
        )
    )

    assert response == (
        r"Saldo: R\$ 100,00"
    )