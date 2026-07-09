"""
Teste manual da integração com IA generativa.

Este script monta o contexto do período mais recente disponível e envia uma
pergunta fixa para o assistente FinanTec.

Diferente dos testes automatizados, este script depende de:
- arquivo .env configurado;
- variável GEMINI_API_KEY preenchida;
- conexão com a internet;
- disponibilidade da Gemini API.
"""

from __future__ import annotations

import _path_setup  # noqa: F401

from agent import gerar_resposta_finantec
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


def montar_contexto_teste() -> tuple[str, str]:
    """
    Monta o contexto usado no teste manual da IA.
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

    return mes_selecionado, contexto


def main() -> None:
    """
    Executa uma pergunta manual para validar a resposta da IA.
    """
    mes_selecionado, contexto = montar_contexto_teste()

    pergunta = (
        "Em qual categoria eu mais gastei neste período "
        "e o que posso observar sobre isso?"
    )

    print("=== TESTE MANUAL DA IA ===")
    print(f"Período analisado: {mes_selecionado}")
    print()
    print("Pergunta enviada ao FinanTec:")
    print(pergunta)
    print()
    print("Resposta:")

    resposta = gerar_resposta_finantec(
        pergunta_usuario=pergunta,
        contexto=contexto,
    )

    print(resposta)


if __name__ == "__main__":
    main()