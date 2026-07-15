"""Testes dos componentes de consulta de transações."""

from __future__ import annotations

import pandas as pd

from components import tables


class DummyContext:
    """Simula um contexto visual do Streamlit."""

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
    """Registra somente as chamadas da validação de dados."""

    def __init__(self) -> None:
        self.warning_messages: list[str] = []
        self.expander_labels: list[str] = []
        self.dataframes: list[pd.DataFrame] = []

    def warning(
        self,
        message,
        *args,
        **kwargs,
    ) -> None:
        self.warning_messages.append(
            str(
                message
            )
        )

    def expander(
        self,
        label,
        *args,
        **kwargs,
    ) -> DummyContext:
        self.expander_labels.append(
            str(
                label
            )
        )

        return DummyContext()

    def dataframe(
        self,
        dataframe,
        *args,
        **kwargs,
    ) -> None:
        self.dataframes.append(
            dataframe.copy()
        )


def test_data_validation_renders_nothing_without_rejections(
    monkeypatch,
) -> None:
    fake_streamlit = FakeStreamlit()

    monkeypatch.setattr(
        tables,
        "st",
        fake_streamlit,
    )

    tables.render_data_validation(
        valid_count=3,
        rejections=pd.DataFrame(),
    )

    assert fake_streamlit.warning_messages == []
    assert fake_streamlit.expander_labels == []
    assert fake_streamlit.dataframes == []


def test_data_validation_shows_rejection_count_and_table(
    monkeypatch,
) -> None:
    fake_streamlit = FakeStreamlit()

    monkeypatch.setattr(
        tables,
        "st",
        fake_streamlit,
    )

    rejections = pd.DataFrame(
        [
            {
                "descricao": "Linha inválida 1",
                "motivo_rejeicao": "Valor ausente",
            },
            {
                "descricao": "Linha inválida 2",
                "motivo_rejeicao": "Data inválida",
            },
        ]
    )

    tables.render_data_validation(
        valid_count=3,
        rejections=rejections,
    )

    assert len(
        fake_streamlit.warning_messages
    ) == 1

    assert "2 transações" in (
        fake_streamlit.warning_messages[0]
    )

    assert fake_streamlit.expander_labels == [
        "Ver transações que precisam de correção"
    ]

    assert len(
        fake_streamlit.dataframes
    ) == 1

    assert fake_streamlit.dataframes[
        0
    ].equals(
        rejections
    )
