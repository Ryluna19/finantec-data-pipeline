"""Testes das ações de seleção do contexto de dados."""

from __future__ import annotations

import components.data_management as data_management_module


class DummyContext:
    """Simula um container do Streamlit."""

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exception_type,
        exception_value,
        traceback,
    ) -> bool:
        return False


class FakeCacheData:
    """Registra a limpeza do cache da aplicação."""

    def __init__(
        self,
    ) -> None:
        self.clear_calls = 0

    def clear(
        self,
    ) -> None:
        self.clear_calls += 1


class FakeStreamlit:
    """Simula os controles usados para selecionar dados pessoais."""

    def __init__(
        self,
        *,
        click_user_data: bool,
    ) -> None:
        self.click_user_data = (
            click_user_data
        )
        self.session_state: dict = {
            data_management_module.DATA_MODE_KEY: (
                "demo"
            ),
        }
        self.cache_data = FakeCacheData()
        self.button_disabled: bool | None = None
        self.info_messages: list[str] = []
        self.rerun_requested = False

    def container(
        self,
        **_kwargs,
    ) -> DummyContext:
        return DummyContext()

    def markdown(
        self,
        *_args,
        **_kwargs,
    ) -> None:
        return None

    def caption(
        self,
        *_args,
        **_kwargs,
    ) -> None:
        return None

    def info(
        self,
        message: str,
    ) -> None:
        self.info_messages.append(
            message
        )

    def button(
        self,
        label: str,
        *_args,
        **kwargs,
    ) -> bool:
        if label != "Usar meus dados":
            return False

        self.button_disabled = bool(
            kwargs.get(
                "disabled",
                False,
            )
        )

        return (
            self.click_user_data
            and not self.button_disabled
        )

    def rerun(
        self,
    ) -> None:
        self.rerun_requested = True


def render_user_data_action(
    monkeypatch,
    *,
    transaction_rows: int,
) -> FakeStreamlit:
    """Executa a ação isolada com o resumo informado."""
    fake_streamlit = FakeStreamlit(
        click_user_data=True,
    )

    monkeypatch.setattr(
        data_management_module,
        "st",
        fake_streamlit,
    )

    data_management_module._render_user_data_action(
        {
            "transaction_rows": transaction_rows,
        }
    )

    return fake_streamlit


def test_user_data_action_returns_to_personal_context_without_transactions(
    monkeypatch,
) -> None:
    fake_streamlit = render_user_data_action(
        monkeypatch,
        transaction_rows=0,
    )

    assert fake_streamlit.button_disabled is False
    assert fake_streamlit.session_state[
        data_management_module.DATA_MODE_KEY
    ] == "user"

    assert fake_streamlit.session_state[
        data_management_module.DATA_MANAGEMENT_FEEDBACK_KEY
    ] == {
        "type": "success",
        "message": (
            "Dados pessoais carregados. "
            "0 transação(ões) disponível(is)."
        ),
    }

    assert fake_streamlit.info_messages == [
        "Nenhuma transação pessoal foi encontrada.",
    ]
    assert (
        fake_streamlit.cache_data.clear_calls
        == 1
    )
    assert fake_streamlit.rerun_requested is True


def test_user_data_action_keeps_personal_context_with_transactions(
    monkeypatch,
) -> None:
    fake_streamlit = render_user_data_action(
        monkeypatch,
        transaction_rows=3,
    )

    assert fake_streamlit.button_disabled is False
    assert fake_streamlit.session_state[
        data_management_module.DATA_MODE_KEY
    ] == "user"

    assert fake_streamlit.session_state[
        data_management_module.DATA_MANAGEMENT_FEEDBACK_KEY
    ]["message"] == (
        "Dados pessoais carregados. "
        "3 transação(ões) disponível(is)."
    )

    assert fake_streamlit.info_messages == []
    assert (
        fake_streamlit.cache_data.clear_calls
        == 1
    )
    assert fake_streamlit.rerun_requested is True
