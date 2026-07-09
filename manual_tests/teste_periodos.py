"""
Teste manual dos períodos disponíveis no dashboard.

Este script carrega as transações, lista os meses encontrados na base e exibe
um resumo financeiro para cada período.
"""

from __future__ import annotations

import _path_setup  # noqa: F401

from analytics import (
    calcular_resumo_financeiro,
    filtrar_transacoes_por_mes,
    formatar_moeda,
    listar_meses_disponiveis,
)
from data_loader import carregar_transacoes


def exibir_meses_disponiveis(meses: list[str]) -> None:
    """
    Exibe os períodos encontrados na base de transações.
    """
    print("=== MESES DISPONÍVEIS ===")

    for mes in meses:
        print(f"- {mes}")


def exibir_resumo_do_mes(mes: str) -> None:
    """
    Exibe um resumo financeiro do período informado.
    """
    transacoes = carregar_transacoes()
    transacoes_mes = filtrar_transacoes_por_mes(transacoes, mes)
    resumo = calcular_resumo_financeiro(transacoes_mes)

    maior_categoria = resumo["maior_categoria"] or "Nenhuma"

    print()
    print(f"=== RESUMO DE {mes} ===")
    print(f"Receitas: {formatar_moeda(resumo['receitas_totais'])}")
    print(f"Gasto de consumo: {formatar_moeda(resumo['despesas_do_mes'])}")
    print(f"Valor separado para reserva: {formatar_moeda(resumo['valor_guardado_reserva'])}")
    print(f"Saldo disponível: {formatar_moeda(resumo['saldo_disponivel'])}")
    print(
        "Maior categoria: "
        f"{maior_categoria} ({formatar_moeda(resumo['maior_gasto'])})"
    )


def main() -> None:
    """
    Executa o teste manual de períodos.
    """
    transacoes = carregar_transacoes()
    meses = listar_meses_disponiveis(transacoes)

    if not meses:
        print("Nenhum período encontrado na base.")
        return

    exibir_meses_disponiveis(meses)

    for mes in meses:
        exibir_resumo_do_mes(mes)


if __name__ == "__main__":
    main()