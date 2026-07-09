"""
Teste manual de montagem do contexto enviado para a IA.

Este script simula a preparação dos dados que o app envia para o modelo
generativo, usando o período mais recente disponível na base.
"""

from __future__ import annotations

import _path_setup  # noqa: F401

from analytics import (
    calcular_gastos_por_categoria,
    calcular_resumo_financeiro,
    calcular_simulacoes_de_metas,
    filtrar_transacoes_por_mes,
    listar_meses_disponiveis,
)
from data_loader import (
    carregar_conceitos_financeiros,
    carregar_historico_atendimento,
    carregar_perfil_usuario,
    carregar_produtos_financeiros,
    carregar_transacoes,
)
from prompts import montar_contexto


def obter_periodo_mais_recente(transacoes) -> str:
    """
    Retorna o período mais recente disponível na base.
    """
    meses = listar_meses_disponiveis(transacoes)

    if not meses:
        raise ValueError("Nenhum período disponível na base de transações.")

    return meses[-1]


def main() -> None:
    """
    Monta e exibe o contexto enviado para a IA.
    """
    perfil_usuario = carregar_perfil_usuario()
    transacoes = carregar_transacoes()
    historico_atendimento = carregar_historico_atendimento()
    conceitos_financeiros = carregar_conceitos_financeiros()
    produtos_financeiros = carregar_produtos_financeiros()

    mes_selecionado = obter_periodo_mais_recente(transacoes)
    transacoes_filtradas = filtrar_transacoes_por_mes(
        transacoes,
        mes_selecionado,
    )

    resumo_financeiro = calcular_resumo_financeiro(transacoes_filtradas)
    gastos_por_categoria = calcular_gastos_por_categoria(transacoes_filtradas)
    simulacoes_metas = calcular_simulacoes_de_metas(perfil_usuario)

    contexto = montar_contexto(
        perfil_usuario=perfil_usuario,
        resumo_financeiro=resumo_financeiro,
        gastos_por_categoria=gastos_por_categoria,
        simulacoes_metas=simulacoes_metas,
        historico_atendimento=historico_atendimento,
        conceitos_financeiros=conceitos_financeiros,
        produtos_financeiros=produtos_financeiros,
    )

    contexto = f"""
PERÍODO ANALISADO:
{mes_selecionado}

{contexto}
""".strip()

    print("=== CONTEXTO ENVIADO PARA A IA ===")
    print()
    print(contexto)


if __name__ == "__main__":
    main()