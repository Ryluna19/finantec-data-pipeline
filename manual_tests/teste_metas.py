"""
Teste manual de simulação de metas financeiras.

Este script carrega o perfil financeiro simulado e calcula quanto ainda falta
para cada meta cadastrada, além do valor mensal necessário.
"""

from __future__ import annotations

import _path_setup  # noqa: F401

from analytics import calcular_meta_mensal, formatar_moeda
from data_loader import carregar_perfil_usuario
from src.user_context import get_current_user_id


def exibir_simulacao_meta(meta: dict) -> None:
    """
    Exibe a simulação financeira de uma meta específica.
    """
    nome = meta["nome"]
    valor_meta = float(meta["valor_meta"])
    valor_atual = float(meta["valor_atual"])
    prazo_meses = int(meta["prazo_meses"])

    simulacao = calcular_meta_mensal(
        valor_meta=valor_meta,
        prazo_meses=prazo_meses,
        valor_ja_reservado=valor_atual,
    )

    print()
    print(f"Meta: {nome}")
    print(f"Valor da meta: {formatar_moeda(valor_meta)}")
    print(f"Valor atual: {formatar_moeda(valor_atual)}")
    print(f"Valor restante: {formatar_moeda(simulacao['valor_restante'])}")
    print(f"Prazo: {prazo_meses} meses")
    print(
        "Valor mensal necessário: "
        f"{formatar_moeda(simulacao['valor_mensal_necessario'])}"
    )


def main() -> None:
    """
    Executa o teste manual de metas financeiras.
    """
    perfil = carregar_perfil_usuario(
        user_id=get_current_user_id(),
    )
    metas = perfil["objetivos_financeiros"]

    print("=== SIMULAÇÃO DE METAS ===")

    if not metas:
        print("Nenhuma meta financeira encontrada no perfil.")
        return

    for meta in metas:
        exibir_simulacao_meta(meta)


if __name__ == "__main__":
    main()
