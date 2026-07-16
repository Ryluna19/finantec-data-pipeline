"""Testes dos subtitulos das telas secundarias."""

from __future__ import annotations

from contextlib import nullcontext

import components.data_management as data_management_module
import components.profile as profile_module


class FakeStreamlit:
    """Registra os subtitulos exibidos sem renderizar a interface."""

    def __init__(
        self,
    ) -> None:
        self.session_state: dict = {}
        self.subheaders: list[tuple[str, str | None]] = []

    def subheader(
        self,
        text: str,
        *,
        anchor: str | None = None,
    ) -> None:
        self.subheaders.append(
            (
                text,
                anchor,
            )
        )

    def caption(
        self,
        *_args,
        **_kwargs,
    ) -> None:
        return None

    def markdown(
        self,
        *_args,
        **_kwargs,
    ) -> None:
        return None

    def container(
        self,
        **_kwargs,
    ):
        return nullcontext()

    def button(
        self,
        *_args,
        **_kwargs,
    ) -> bool:
        return False


def test_profile_heading_uses_a_stable_anchor(
    monkeypatch,
) -> None:
    fake_streamlit = FakeStreamlit()

    monkeypatch.setattr(
        profile_module,
        "st",
        fake_streamlit,
    )
    monkeypatch.setattr(
        profile_module,
        "_show_profile_feedback",
        lambda: None,
    )
    monkeypatch.setattr(
        profile_module,
        "_render_profile_summary",
        lambda _profile: None,
    )

    profile_module.render_user_profile(
        {},
        user_id="user-1",
        data_mode="user",
    )

    assert fake_streamlit.subheaders == [
        (
            "Meu perfil",
            "meu-perfil",
        )
    ]


def test_data_management_heading_uses_a_stable_anchor(
    monkeypatch,
) -> None:
    fake_streamlit = FakeStreamlit()
    summary: dict[str, int | bool] = {}

    monkeypatch.setattr(
        data_management_module,
        "st",
        fake_streamlit,
    )
    monkeypatch.setattr(
        data_management_module,
        "_show_feedback",
        lambda: None,
    )
    monkeypatch.setattr(
        data_management_module,
        "_render_current_mode",
        lambda: None,
    )
    monkeypatch.setattr(
        data_management_module,
        "_render_data_summary",
        lambda: summary,
    )
    monkeypatch.setattr(
        data_management_module,
        "_render_user_data_action",
        lambda _summary: None,
    )
    monkeypatch.setattr(
        data_management_module,
        "_render_demo_action",
        lambda: None,
    )
    monkeypatch.setattr(
        data_management_module,
        "_render_reset_action",
        lambda: None,
    )
    monkeypatch.setattr(
        data_management_module,
        "_render_account_deletion_action",
        lambda: None,
    )

    data_management_module.render_data_management()

    assert fake_streamlit.subheaders == [
        (
            "Dados e privacidade",
            "dados-e-privacidade",
        )
    ]
