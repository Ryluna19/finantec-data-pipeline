"""
Funções de análise financeira usadas pelo FinanTec.

Este módulo concentra os cálculos financeiros do projeto para evitar que a IA
invente valores. A IA recebe os números já calculados em Python e apenas explica
os resultados de forma contextualizada.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


TIPO_RECEITA = "receita"
TIPO_DESPESA = "despesa"
CATEGORIA_RESERVA = "Reserva"


def garantir_coluna_ano_mes(transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Garante que o DataFrame tenha a coluna ano_mes no formato AAAA-MM.
    """
    if "ano_mes" in transacoes.columns:
        return transacoes

    transacoes = transacoes.copy()
    transacoes["data"] = pd.to_datetime(
        transacoes["data"],
        errors="coerce",
    )
    transacoes["ano_mes"] = transacoes["data"].dt.to_period("M").astype(str)

    return transacoes


def filtrar_por_tipo(transacoes: pd.DataFrame, tipo: str) -> pd.DataFrame:
    """
    Filtra transações pelo tipo informado.
    """
    return transacoes[transacoes["tipo"] == tipo].copy()


def identificar_categoria_reserva(transacoes: pd.DataFrame) -> pd.Series:
    """
    Identifica linhas da categoria Reserva.

    A comparação ignora diferença entre maiúsculas e minúsculas para deixar o
    cálculo mais resistente a pequenas variações nos dados.
    """
    return (
        transacoes["categoria"]
        .astype("string")
        .str.strip()
        .str.casefold()
        == CATEGORIA_RESERVA.casefold()
    )


def calcular_gastos_por_categoria(
    transacoes: pd.DataFrame,
    incluir_reserva: bool = False,
) -> pd.Series:
    """
    Soma os gastos por categoria.

    Por padrão, a categoria Reserva não entra como gasto de consumo, porque
    representa dinheiro guardado, não consumo do período.
    """
    despesas = filtrar_por_tipo(transacoes, TIPO_DESPESA)

    if not incluir_reserva:
        despesas = despesas[~identificar_categoria_reserva(despesas)]

    return (
        despesas.groupby("categoria")["valor"]
        .sum()
        .sort_values(ascending=False)
    )


def calcular_resumo_financeiro(transacoes: pd.DataFrame) -> dict[str, Any]:
    """
    Calcula o resumo financeiro do período analisado.

    O cálculo separa despesas totais, gastos de consumo e valor reservado.
    Isso deixa claro quanto foi consumido e quanto foi separado para reserva.
    """
    receitas = transacoes.loc[
        transacoes["tipo"] == TIPO_RECEITA,
        "valor",
    ].sum()

    despesas_totais = transacoes.loc[
        transacoes["tipo"] == TIPO_DESPESA,
        "valor",
    ].sum()

    despesas = filtrar_por_tipo(transacoes, TIPO_DESPESA)
    valor_reserva = despesas.loc[
        identificar_categoria_reserva(despesas),
        "valor",
    ].sum()

    despesas_do_mes = despesas_totais - valor_reserva
    saldo_disponivel = receitas - despesas_totais

    gastos_por_categoria = calcular_gastos_por_categoria(transacoes)

    maior_categoria = None
    maior_gasto = 0.0

    if not gastos_por_categoria.empty:
        maior_categoria = gastos_por_categoria.index[0]
        maior_gasto = float(gastos_por_categoria.iloc[0])

    return {
        "receitas_totais": float(receitas),
        "despesas_totais": float(despesas_totais),
        "despesas_do_mes": float(despesas_do_mes),
        "valor_guardado_reserva": float(valor_reserva),
        "saldo_disponivel": float(saldo_disponivel),
        "maior_categoria": maior_categoria,
        "maior_gasto": maior_gasto,
    }


def calcular_meta_mensal(
    valor_meta: float,
    prazo_meses: int,
    valor_ja_reservado: float,
) -> dict[str, float | None]:
    """
    Calcula quanto falta para uma meta e o valor mensal necessário.

    Cada meta usa seu próprio valor atual. A reserva geral da pessoa não é
    automaticamente usada para outras metas, como compra de notebook.
    """
    valor_restante = max(valor_meta - valor_ja_reservado, 0)

    if prazo_meses <= 0:
        return {
            "valor_restante": float(valor_restante),
            "valor_mensal_necessario": None,
        }

    valor_mensal_necessario = valor_restante / prazo_meses

    return {
        "valor_restante": float(valor_restante),
        "valor_mensal_necessario": float(valor_mensal_necessario),
    }


def formatar_moeda(valor: float | int | None) -> str:
    """
    Formata valores numéricos no padrão de moeda brasileira.
    """
    if valor is None:
        return "N/A"

    valor_formatado = f"{float(valor):,.2f}"

    return (
        "R$ "
        + valor_formatado.replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def calcular_simulacoes_de_metas(perfil_usuario: dict) -> list[dict[str, Any]]:
    """
    Gera simulações calculadas para todas as metas cadastradas.

    Esses valores são enviados prontos para a IA, reduzindo o risco de erro em
    contas feitas pelo modelo de linguagem.
    """
    simulacoes = []

    for meta in perfil_usuario["objetivos_financeiros"]:
        valor_meta = float(meta["valor_meta"])
        valor_atual = float(meta["valor_atual"])
        prazo_meses = int(meta["prazo_meses"])

        simulacao = calcular_meta_mensal(
            valor_meta=valor_meta,
            prazo_meses=prazo_meses,
            valor_ja_reservado=valor_atual,
        )

        valor_restante = simulacao["valor_restante"]
        valor_mensal_necessario = simulacao["valor_mensal_necessario"]

        simulacoes.append(
            {
                "nome": meta["nome"],
                "valor_meta": valor_meta,
                "valor_meta_formatado": formatar_moeda(valor_meta),
                "valor_atual": valor_atual,
                "valor_atual_formatado": formatar_moeda(valor_atual),
                "valor_restante": valor_restante,
                "valor_restante_formatado": formatar_moeda(valor_restante),
                "prazo_meses": prazo_meses,
                "valor_mensal_necessario": valor_mensal_necessario,
                "valor_mensal_necessario_formatado": formatar_moeda(
                    valor_mensal_necessario
                ),
                "prioridade": meta["prioridade"],
            }
        )

    return simulacoes


def listar_meses_disponiveis(transacoes: pd.DataFrame) -> list[str]:
    """
    Lista os períodos disponíveis na base de transações.
    """
    transacoes = garantir_coluna_ano_mes(transacoes)

    return sorted(
        transacoes["ano_mes"]
        .dropna()
        .unique()
        .tolist()
    )


def filtrar_transacoes_por_mes(
    transacoes: pd.DataFrame,
    ano_mes: str,
) -> pd.DataFrame:
    """
    Filtra as transações de um período específico no formato AAAA-MM.
    """
    transacoes = garantir_coluna_ano_mes(transacoes)

    return transacoes[transacoes["ano_mes"] == ano_mes].copy()