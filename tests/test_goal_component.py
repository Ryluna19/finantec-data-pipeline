"""Testes dos cálculos usados pelo componente de metas."""

from __future__ import annotations

import components.goals as goals_module

from components.goals import (
    build_goal_payload,
    calculate_estimated_months,
    calculate_goal_overview,
    calculate_goal_progress,
)


class DummyContext:
    """Simula colunas do Streamlit."""

    def __enter__(self):
        return self

    def __exit__(
        self,
        exception_type,
        exception_value,
        traceback,
    ) -> bool:
        return False


class FakeStreamlit:
    """Simula os controles usados para alternar as visualizações."""

    def __init__(
        self,
        *,
        clicked_label: str | None = None,
    ) -> None:
        self.clicked_label = clicked_label
        self.session_state: dict = {}
        self.buttons: list[tuple[str, str]] = []

    def subheader(
        self,
        *args,
        **kwargs,
    ) -> None:
        return None

    def caption(
        self,
        *args,
        **kwargs,
    ) -> None:
        return None

    def info(
        self,
        *args,
        **kwargs,
    ) -> None:
        return None

    def columns(
        self,
        count,
        *args,
        **kwargs,
    ):
        column_count = (
            len(
                count
            )
            if isinstance(
                count,
                list,
            )
            else int(
                count
            )
        )

        return tuple(
            DummyContext()
            for _ in range(
                column_count
            )
        )

    def container(
        self,
        *args,
        **kwargs,
    ):
        return DummyContext()

    def markdown(
        self,
        *args,
        **kwargs,
    ) -> None:
        return None

    def metric(
        self,
        *args,
        **kwargs,
    ) -> None:
        return None

    def success(
        self,
        *args,
        **kwargs,
    ) -> None:
        return None

    def button(
        self,
        label,
        *args,
        on_click=None,
        **kwargs,
    ) -> bool:
        self.buttons.append(
            (
                str(label),
                str(kwargs.get("type")),
            )
        )

        clicked = label == self.clicked_label

        if clicked and on_click:
            on_click(
                *kwargs.get(
                    "args",
                    (),
                )
            )

        return clicked


def configure_goal_views(
    monkeypatch,
    *,
    clicked_label: str | None = None,
) -> tuple[FakeStreamlit, list[str]]:
    """Substitui as visualizações por registros de chamadas."""
    fake_streamlit = FakeStreamlit(
        clicked_label=clicked_label,
    )

    events: list[str] = []

    monkeypatch.setattr(
        goals_module,
        "st",
        fake_streamlit,
    )

    monkeypatch.setattr(
        goals_module,
        "_render_goal_management_view",
        lambda goals, user_id, read_only=False: events.append(
            f"management:{user_id}:{read_only}"
        ),
    )

    monkeypatch.setattr(
        goals_module,
        "_render_goal_simulator_view",
        lambda goals, summary: events.append("simulator"),
    )

    return fake_streamlit, events


def test_calculate_goal_progress():
    assert (
        calculate_goal_progress(
            current_value=500.0,
            goal_value=2000.0,
        )
        == 25.0
    )


def test_goal_progress_is_limited_to_one_hundred():
    assert (
        calculate_goal_progress(
            current_value=3000.0,
            goal_value=2000.0,
        )
        == 100.0
    )


def test_goal_progress_handles_invalid_target():
    assert (
        calculate_goal_progress(
            current_value=500.0,
            goal_value=0.0,
        )
        == 0.0
    )


def test_calculate_goal_overview_for_active_goal():
    overview = calculate_goal_overview(
        target_amount=5000.0,
        current_amount=500.0,
        deadline_months=18,
    )

    assert overview == {
        "progress": 10.0,
        "remaining_amount": 4500.0,
        "monthly_amount": 250.0,
        "completed": False,
    }


def test_calculate_goal_overview_for_completed_goal():
    overview = calculate_goal_overview(
        target_amount=5000.0,
        current_amount=6000.0,
        deadline_months=18,
    )

    assert overview == {
        "progress": 100.0,
        "remaining_amount": 0.0,
        "monthly_amount": 0.0,
        "completed": True,
    }


def test_calculate_estimated_months():
    assert (
        calculate_estimated_months(
            remaining_value=1000.0,
            monthly_amount=300.0,
        )
        == 4
    )


def test_estimated_months_for_completed_goal():
    assert (
        calculate_estimated_months(
            remaining_value=0.0,
            monthly_amount=300.0,
        )
        == 0
    )


def test_estimated_months_rejects_zero_monthly_amount():
    assert (
        calculate_estimated_months(
            remaining_value=1000.0,
            monthly_amount=0.0,
        )
        is None
    )


def test_build_goal_payload():
    payload = build_goal_payload(
        name="Viagem",
        target_amount=5000.0,
        current_amount=500.0,
        deadline_months=18,
        priority="alta",
    )

    assert payload == {
        "nome": "Viagem",
        "valor_meta": 5000.0,
        "valor_atual": 500.0,
        "prazo_meses": 18,
        "prioridade": "alta",
    }


def test_goal_screen_starts_with_saved_goals(
    monkeypatch,
) -> None:
    fake_streamlit, events = configure_goal_views(
        monkeypatch
    )

    goals_module.render_goal_simulator(
        user_profile={
            "objetivos_financeiros": [],
        },
        summary={},
        user_id="user-1",
        data_mode="user",
    )

    assert events == [
        "management:user-1:False"
    ]

    assert fake_streamlit.session_state[
        goals_module.GOAL_VIEW_KEY
    ] == goals_module.GOAL_VIEW_MANAGEMENT

    assert fake_streamlit.buttons == [
        ("Minhas metas", "primary"),
        ("Simulador", "secondary"),
    ]


def test_goal_screen_switches_to_simulator(
    monkeypatch,
) -> None:
    fake_streamlit, events = configure_goal_views(
        monkeypatch,
        clicked_label="Simulador",
    )

    goals_module.render_goal_simulator(
        user_profile={
            "objetivos_financeiros": [],
        },
        summary={},
        user_id="user-1",
        data_mode="user",
    )

    assert events == ["simulator"]

    assert fake_streamlit.session_state[
        goals_module.GOAL_VIEW_KEY
    ] == goals_module.GOAL_VIEW_SIMULATOR


def test_demo_goal_management_is_read_only(
    monkeypatch,
) -> None:
    fake_streamlit, events = configure_goal_views(
        monkeypatch
    )

    goals_module.render_goal_simulator(
        user_profile={
            "objetivos_financeiros": [],
        },
        summary={},
        user_id="user-1",
        data_mode="demo",
    )

    assert events == [
        "management:user-1:True"
    ]

    assert fake_streamlit.buttons == [
        ("Minhas metas", "primary"),
        ("Simulador", "secondary"),
    ]


def test_demo_goal_simulator_remains_available(
    monkeypatch,
) -> None:
    _, events = configure_goal_views(
        monkeypatch,
        clicked_label="Simulador",
    )

    goals_module.render_goal_simulator(
        user_profile={
            "objetivos_financeiros": [],
        },
        summary={},
        user_id="user-1",
        data_mode="demo",
    )

    assert events == [
        "simulator",
    ]


def test_demo_goal_management_hides_create_form(
    monkeypatch,
) -> None:
    fake_streamlit = FakeStreamlit()
    events: list[str] = []

    monkeypatch.setattr(
        goals_module,
        "st",
        fake_streamlit,
    )
    monkeypatch.setattr(
        goals_module,
        "_render_goal_form",
        lambda *args, **kwargs: events.append(
            "form"
        ),
    )
    monkeypatch.setattr(
        goals_module,
        "_render_goal_management_cards",
        lambda goals, user_id, read_only=False: events.append(
            f"cards:{read_only}"
        ),
    )

    goals_module._render_goal_management_view(
        [],
        "user-1",
        read_only=True,
    )

    assert events == [
        "cards:True",
    ]
    assert fake_streamlit.buttons == []


def test_demo_goal_cards_hide_edit_and_delete_actions(
    monkeypatch,
) -> None:
    fake_streamlit = FakeStreamlit()
    fake_streamlit.session_state[
        goals_module.GOAL_DELETE_ID_KEY
    ] = "demo-goal-1"

    monkeypatch.setattr(
        goals_module,
        "st",
        fake_streamlit,
    )
    monkeypatch.setattr(
        goals_module,
        "render_html",
        lambda _html: None,
    )

    goals_module._render_goal_management_cards(
        [
            {
                "goal_id": "demo-goal-1",
                "nome": "Reserva",
                "valor_meta": 1500.0,
                "valor_atual": 500.0,
                "prazo_meses": 10,
            }
        ],
        "user-1",
        read_only=True,
    )

    assert fake_streamlit.buttons == []
