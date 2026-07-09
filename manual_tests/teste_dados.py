"""
Teste manual de leitura e análise geral dos dados.

Este script carrega a base completa de transações e exibe um resumo financeiro
geral, além dos gastos de consumo por categoria.
"""

from __future__ import annotations

import _path_setup  # noqa: F401

from analytics import (
    calcular_gastos_por_categoria,
    calcular_resumo_financeiro,
    formatar_moeda,
)
from data_loader import carregar_transacoes


def exibir_resumo_financeiro() -> None:
    """
    Exibe o resumo financeiro considerando toda a base carregada.
    """
    transacoes = carregar_transacoes()
    resumo = calcular_resumo_financeiro(transacoes)

    maior_categoria = resumo["maior_categoria"] or "Nenhuma"

    print("=== RESUMO FINANCEIRO DA BASE COMPLETA ===")
    print(f"Total de transações carregadas: {len(transacoes)}")
    print(f"Receitas: {formatar_moeda(resumo['receitas_totais'])}")
    print(f"Gasto de consumo: {formatar_moeda(resumo['despesas_do_mes'])}")
    print(
        f"Valor separado para reserva: {formatar_moeda(resumo['valor_guardado_reserva'])}"
    )
    print(f"Saldo disponível: {formatar_moeda(resumo['saldo_disponivel'])}")
    print(
        "Maior categoria de consumo: "
        f"{maior_categoria} ({formatar_moeda(resumo['maior_gasto'])})"
    )


def exibir_gastos_por_categoria() -> None:
    """
    Exibe os gastos de consumo agrupados por categoria.
    """
    transacoes = carregar_transacoes()
    gastos_por_categoria = calcular_gastos_por_categoria(transacoes)

    print()
    print("=== GASTOS DE CONSUMO POR CATEGORIA ===")

    if gastos_por_categoria.empty:
        print("Nenhum gasto de consumo encontrado.")
        return

    for categoria, valor in gastos_por_categoria.items():
        print(f"{categoria}: {formatar_moeda(valor)}")


def main() -> None:
    """
    Executa o teste manual de dados.
    """
    exibir_resumo_financeiro()
    exibir_gastos_por_categoria()


if __name__ == "__main__":
    main()
