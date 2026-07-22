"""Testes dos cálculos usados pelo componente de metas."""

from __future__ import annotations

from datetime import date

import components.goals as goals_module

from components.goals import (
    build_free_simulation_goal,
    build_goal_payload,
    build_goal_summary_html,
    calculate_estimated_months,
    calculate_goal_deadline,
    calculate_goal_overview,
    calculate_goal_progress,
    get_goal_reference_date,
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



def test_build_goal_summary_html_uses_single_compact_panel():
    html = build_goal_summary_html(
        goal_name="Notebook <novo>",
        goal_value=5000.0,
        current_value=1000.0,
        remaining_value=4000.0,
        fourth_label="Necessário por mês",
        fourth_value="R$ 500,00",
        fourth_description="Para concluir em 8 meses.",
    )

    assert (
        'class="finantec-goal-simulation-panel"'
        in html
    )

    assert html.count(
        'class="finantec-goal-summary-item'
    ) == 4

    assert "finantec-goal-card" not in html

    assert "Notebook &lt;novo&gt;" in html

    assert "Para concluir em 8 meses." in html


def test_completed_goal_summary_uses_completed_state():
    html = build_goal_summary_html(
        goal_name="Notebook",
        goal_value=5000.0,
        current_value=5000.0,
        remaining_value=0.0,
        fourth_label="Situação",
        fourth_value="Concluída",
        fourth_description="O valor da meta já foi alcançado.",
    )

    assert (
        'class="finantec-goal-simulation-panel completed"'
        in html
    )

    assert "Meta concluída" in html



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


def test_goal_deadline_changes_with_reference_date():
    deadline = date(
        2026,
        10,
        1,
    )

    july_result = calculate_goal_deadline(
        deadline_date=deadline,
        reference_date=date(
            2026,
            7,
            1,
        ),
    )

    august_result = calculate_goal_deadline(
        deadline_date=deadline,
        reference_date=date(
            2026,
            8,
            1,
        ),
    )

    assert july_result["days_remaining"] == 92
    assert august_result["days_remaining"] == 61

    assert (
        august_result["planning_months"]
        < july_result["planning_months"]
    )


def test_monthly_goal_increases_as_deadline_approaches():
    july_overview = calculate_goal_overview(
        target_amount=6500.0,
        current_amount=500.0,
        deadline_date=date(
            2026,
            10,
            1,
        ),
        reference_date=date(
            2026,
            7,
            1,
        ),
    )

    august_overview = calculate_goal_overview(
        target_amount=6500.0,
        current_amount=500.0,
        deadline_date=date(
            2026,
            10,
            1,
        ),
        reference_date=date(
            2026,
            8,
            1,
        ),
    )

    assert (
        august_overview["monthly_amount"]
        > july_overview["monthly_amount"]
    )


def test_reference_date_can_be_overridden(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        goals_module.GOAL_REFERENCE_DATE_ENV,
        "2026-09-20",
    )

    assert get_goal_reference_date() == date(
        2026,
        9,
        20,
    )


def test_build_free_simulation_goal():
    goal = build_free_simulation_goal(
        name="Notebook",
        target_amount=6000.0,
        current_amount=500.0,
        deadline_date=date(
            2027,
            1,
            20,
        ),
        reference_date=date(
            2026,
            7,
            21,
        ),
    )

    assert goal == {
        "goal_id": "free-goal-simulation",
        "nome": "Notebook",
        "valor_meta": 6000.0,
        "valor_atual": 500.0,
        "data_limite": "2027-01-20",
        "prazo_meses": 7,
        "prioridade": "média",
        "status": "active",
    }


def test_free_simulation_rejects_past_deadline():
    try:
        build_free_simulation_goal(
            name="Viagem",
            target_amount=2000.0,
            current_amount=0.0,
            deadline_date=date(
                2026,
                7,
                20,
            ),
            reference_date=date(
                2026,
                7,
                21,
            ),
        )

    except ValueError as error:
        assert "passado" in str(error)

    else:
        raise AssertionError(
            "A data no passado deveria ser rejeitada."
        )


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


def test_build_goal_payload_with_deadline_date():
    payload = build_goal_payload(
        name="Viagem",
        target_amount=5000.0,
        current_amount=500.0,
        deadline_date=date(
            2027,
            1,
            20,
        ),
        priority="alta",
    )

    assert payload == {
        "nome": "Viagem",
        "valor_meta": 5000.0,
        "valor_atual": 500.0,
        "data_limite": "2027-01-20",
        "prioridade": "alta",
    }


def test_simulator_without_saved_goal_uses_free_mode(
    monkeypatch,
) -> None:
    fake_streamlit = FakeStreamlit()
    events: list[float] = []

    monkeypatch.setattr(
        goals_module,
        "st",
        fake_streamlit,
    )

    monkeypatch.setattr(
        goals_module,
        "_render_free_goal_simulation",
        lambda summary: events.append(
            float(
                summary.get(
                    "saldo_disponivel",
                    0.0,
                )
            )
        ),
    )

    goals_module._render_goal_simulator_view(
        [],
        {
            "saldo_disponivel": 850.0,
        },
    )

    assert events == [850.0]

    assert fake_streamlit.session_state[
        goals_module.GOAL_SIMULATION_SOURCE_KEY
    ] == goals_module.SIMULATION_SOURCE_FREE


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