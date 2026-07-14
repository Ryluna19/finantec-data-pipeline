"""Componente responsável pelo cabeçalho principal do FinanTec."""

from __future__ import annotations

from ui_components import (
    render_alert,
    render_html,
)


def render_header(
    period: str | None = None,
) -> None:
    """Exibe a identidade visual e os avisos da seção atual."""
    render_html(
        """
        <header class="finantec-brand-header">
            <div class="finantec-brand-title-row">
                <span
                    class="finantec-brand-icon"
                    aria-hidden="true"
                >
                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        <path
                            d="M4 7.5H18C19.1 7.5 20 8.4 20 9.5V17.5C20 18.6 19.1 19.5 18 19.5H5C3.9 19.5 3 18.6 3 17.5V6.5C3 5.4 3.9 4.5 5 4.5H16"
                        />

                        <path
                            d="M3 8H18"
                        />

                        <path
                            d="M15.5 12H20V16H15.5C14.4 16 13.5 15.1 13.5 14C13.5 12.9 14.4 12 15.5 12Z"
                        />

                        <circle
                            cx="16.5"
                            cy="14"
                            r="0.5"
                            fill="currentColor"
                            stroke="none"
                        />
                    </svg>
                </span>

                <div class="finantec-brand-copy">
                    <div class="finantec-brand-eyebrow">
                        Organização financeira
                    </div>

                    <h1>
                        FinanTec
                    </h1>
                </div>
            </div>

            <p class="finantec-brand-description">
                Assistente de organização financeira para estudantes
                e pessoas em início de carreira.
            </p>
        </header>
        """
    )

    render_alert(
        text=(
            "Projeto educativo com dados simulados. "
            "O FinanTec não oferece recomendação personalizada "
            "de investimento."
        ),
        variant="warning",
    )

    if period:
        render_alert(
            text=f"Período analisado: {period}",
            variant="info",
        )