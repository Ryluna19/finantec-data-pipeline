"""Testes do executor principal do projeto."""

from __future__ import annotations

import main as main_module


def test_dev_command_starts_app_without_running_etl(
    monkeypatch,
) -> None:
    calls: list[str] = []

    def fake_app() -> int:
        calls.append(
            "app"
        )
        return 0

    def fake_etl() -> int:
        calls.append(
            "etl"
        )
        return 0

    monkeypatch.setattr(
        main_module,
        "executar_app",
        fake_app,
    )

    monkeypatch.setattr(
        main_module,
        "executar_etl",
        fake_etl,
    )

    result = main_module.main(
        [
            "dev"
        ]
    )

    assert result == 0
    assert calls == [
        "app"
    ]


def test_etl_command_runs_explicit_etl(
    monkeypatch,
) -> None:
    calls: list[str] = []

    def fake_app() -> int:
        calls.append(
            "app"
        )
        return 0

    def fake_etl() -> int:
        calls.append(
            "etl"
        )
        return 0

    monkeypatch.setattr(
        main_module,
        "executar_app",
        fake_app,
    )

    monkeypatch.setattr(
        main_module,
        "executar_etl",
        fake_etl,
    )

    result = main_module.main(
        [
            "etl"
        ]
    )

    assert result == 0
    assert calls == [
        "etl"
    ]