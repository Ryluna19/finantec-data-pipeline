"""Componentes visuais compartilhados do FinanTec."""

from __future__ import annotations

from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Any

import streamlit as st

from analytics import formatar_moeda


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARQUIVO_ESTILOS = PROJECT_ROOT / "assets" / "styles.css"

COR_RECEITA = "#22c55e"
COR_DESPESA = "#ff7a00"

MESES_PTBR = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

ROTULOS_TIPO = {
    "receita": "Receita",
    "despesa": "Despesa",
}

VARIANTES_AVISO = {
    "info",
    "warning",
    "success",
    "error",
}


def aplicar_estilo_visual() -> None:
    """Carrega o arquivo CSS principal."""
    if not ARQUIVO_ESTILOS.exists():
        st.warning(
            f"Arquivo de estilos não encontrado: {ARQUIVO_ESTILOS}"
        )
        return

    estilos = ARQUIVO_ESTILOS.read_text(encoding="utf-8")

    st.markdown(
        f"<style>{estilos}</style>",
        unsafe_allow_html=True,
    )


def renderizar_html(conteudo: str) -> None:
    """Renderiza HTML sem o Markdown quebrar sua estrutura."""
    html_compacto = " ".join(
        linha.strip()
        for linha in dedent(conteudo).splitlines()
        if linha.strip()
    )

    st.markdown(
        html_compacto,
        unsafe_allow_html=True,
    )


def exibir_aviso_visual(
    texto: str,
    variante: str = "info",
) -> None:
    """Exibe um aviso usando o estilo do FinanTec."""
    variante_segura = (
        variante
        if variante in VARIANTES_AVISO
        else "info"
    )

    renderizar_html(
        f"""
        <div class="finantec-alert {escape(variante_segura)}">
            {escape(texto)}
        </div>
        """
    )


def exibir_cabecalho(periodo: str) -> None:
    """Exibe o cabeçalho principal."""
    st.title("💰 FinanTec")

    st.caption(
        "Assistente de organização financeira para estudantes "
        "e pessoas em início de carreira."
    )

    exibir_aviso_visual(
        "Projeto educativo com dados simulados. "
        "O FinanTec não oferece recomendação personalizada "
        "de investimento.",
        variante="warning",
    )

    exibir_aviso_visual(
        f"Período analisado: {periodo}",
        variante="info",
    )


def exibir_resumo_financeiro(
    resumo: dict[str, Any],
) -> None:
    """Exibe saldo, receitas, consumo e reserva."""
    st.subheader("Resumo financeiro")

    receitas = resumo["receitas_totais"]
    consumo = resumo["despesas_do_mes"]
    reserva = resumo["valor_guardado_reserva"]
    saldo = resumo["saldo_disponivel"]

    descricao_saldo = (
        "Saldo disponível após gastos de consumo e reserva."
        if saldo >= 0
        else "O período fechou com saldo negativo."
    )

    renderizar_html(
        f"""
        <div class="finantec-overview-grid">
            <div class="finantec-balance-panel">
                <div class="finantec-balance-label">
                    Saldo do período
                </div>

                <div class="finantec-balance-value">
                    {escape(formatar_moeda(saldo))}
                </div>

                <div class="finantec-balance-desc">
                    {escape(descricao_saldo)}
                </div>
            </div>

            <div class="finantec-mini-grid">
                <div class="finantec-mini-card receita">
                    <div class="finantec-mini-title">
                        Receitas
                    </div>

                    <div class="finantec-mini-value">
                        {escape(formatar_moeda(receitas))}
                    </div>

                    <div class="finantec-mini-desc">
                        Total recebido no período.
                    </div>
                </div>

                <div class="finantec-mini-card consumo">
                    <div class="finantec-mini-title">
                        Consumo
                    </div>

                    <div class="finantec-mini-value">
                        {escape(formatar_moeda(consumo))}
                    </div>

                    <div class="finantec-mini-desc">
                        Despesas sem contar reserva.
                    </div>
                </div>

                <div class="finantec-mini-card reserva">
                    <div class="finantec-mini-title">
                        Reserva
                    </div>

                    <div class="finantec-mini-value">
                        {escape(formatar_moeda(reserva))}
                    </div>

                    <div class="finantec-mini-desc">
                        Valor separado para guardar.
                    </div>
                </div>
            </div>
        </div>
        """
    )


def exibir_diagnostico_financeiro(
    resumo: dict[str, Any],
) -> None:
    """Resume a situação financeira e a distribuição da renda."""
    st.subheader("Diagnóstico rápido")

    receitas = resumo["receitas_totais"]
    consumo = resumo["despesas_do_mes"]
    reserva = resumo["valor_guardado_reserva"]
    saldo = resumo["saldo_disponivel"]

    percentual_consumo = (
        (consumo / receitas) * 100
        if receitas > 0
        else 0.0
    )

    percentual_reserva = (
        (reserva / receitas) * 100
        if receitas > 0
        else 0.0
    )

    if saldo > 0:
        titulo = "Período com sobra financeira"
        texto = (
            f"O período fechou com {formatar_moeda(saldo)} disponíveis. "
            f"O consumo usou {percentual_consumo:.1f}% da renda e "
            f"{percentual_reserva:.1f}% foi separado para reserva."
        )
    elif saldo == 0:
        titulo = "Período sem sobra"
        texto = (
            "As receitas cobriram exatamente os gastos e a reserva. "
            "Não houve saldo disponível ao final."
        )
    else:
        titulo = "Período negativo"
        texto = (
            f"O período fechou negativo em "
            f"{formatar_moeda(abs(saldo))}. "
            "Os gastos e reservas ultrapassaram as receitas."
        )

    largura_consumo = min(percentual_consumo, 100)
    largura_reserva = min(percentual_reserva, 100)

    renderizar_html(
        f"""
        <div class="finantec-diagnosis-panel">
            <div class="finantec-diagnosis-title">
                {escape(titulo)}
            </div>

            <div class="finantec-diagnosis-text">
                {escape(texto)}
            </div>

            <div class="finantec-diagnosis-grid">
                <div>
                    <div class="finantec-bar-label">
                        Consumo da renda: {percentual_consumo:.1f}%
                    </div>

                    <div class="finantec-bar-track">
                        <div
                            class="finantec-bar-fill orange"
                            style="width: {largura_consumo:.1f}%;">
                        </div>
                    </div>
                </div>

                <div>
                    <div class="finantec-bar-label">
                        Reserva da renda: {percentual_reserva:.1f}%
                    </div>

                    <div class="finantec-bar-track">
                        <div
                            class="finantec-bar-fill green"
                            style="width: {largura_reserva:.1f}%;">
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    )