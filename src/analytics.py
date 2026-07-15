"""
Funções de análise financeira usadas pelo FinanTec.

Este módulo concentra os cálculos financeiros do projeto para evitar que a IA
invente valores. A IA recebe os números já calculados em Python e apenas explica
os resultados de forma contextualizada.
"""

from __future__ import annotations

import unicodedata

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

def _normalizar_chave_categoria(
    categoria: object,
) -> str:
    """Cria uma chave comparável para categorias financeiras."""
    texto = " ".join(
        str(
            categoria
            if categoria is not None
            else ""
        )
        .strip()
        .split()
    )

    texto_sem_acentos = unicodedata.normalize(
        "NFKD",
        texto,
    )

    return "".join(
        caractere
        for caractere in texto_sem_acentos
        if not unicodedata.combining(
            caractere
        )
    ).casefold()


def calcular_acompanhamento_orcamento(
    transacoes: pd.DataFrame,
    orcamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Compara valores planejados com os gastos reais por categoria.

    As transações recebidas já devem representar o período desejado.
    Categorias sem orçamento não entram no resultado.
    """
    gastos_por_categoria = (
        calcular_gastos_por_categoria(
            transacoes
        )
    )

    gastos_normalizados: dict[str, float] = {}

    for (
        categoria,
        valor_gasto,
    ) in gastos_por_categoria.items():
        chave_categoria = (
            _normalizar_chave_categoria(
                categoria
            )
        )

        gastos_normalizados[
            chave_categoria
        ] = (
            gastos_normalizados.get(
                chave_categoria,
                0.0,
            )
            + float(
                valor_gasto
            )
        )

    acompanhamento: list[
        dict[str, Any]
    ] = []

    for orcamento in orcamentos:
        categoria = " ".join(
            str(
                orcamento.get(
                    "category",
                    "",
                )
            )
            .strip()
            .split()
        )

        valor_planejado = float(
            orcamento.get(
                "planned_amount",
                0.0,
            )
        )

        if valor_planejado <= 0:
            raise ValueError(
                "O valor planejado deve ser "
                "maior que zero."
            )

        chave_categoria = (
            _normalizar_chave_categoria(
                categoria
            )
        )

        valor_gasto = float(
            gastos_normalizados.get(
                chave_categoria,
                0.0,
            )
        )

        valor_restante = (
            valor_planejado
            - valor_gasto
        )

        percentual_utilizado = (
            valor_gasto
            / valor_planejado
            * 100
        )

        if percentual_utilizado > 100:
            status = "over_limit"

        elif percentual_utilizado >= 80:
            status = "near_limit"

        else:
            status = "within_limit"

        acompanhamento.append(
            {
                "budget_id": orcamento.get(
                    "budget_id"
                ),
                "period": orcamento.get(
                    "period"
                ),
                "category": categoria,
                "planned_amount": (
                    valor_planejado
                ),
                "spent_amount": valor_gasto,
                "remaining_amount": (
                    valor_restante
                ),
                "usage_percentage": (
                    percentual_utilizado
                ),
                "status": status,
            }
        )

    return acompanhamento


def calcular_resumo_orcamento(
    acompanhamento: list[
        dict[str, Any]
    ],
) -> dict[str, float | int]:
    """Resume o acompanhamento das categorias planejadas."""
    total_planejado = sum(
        float(
            item[
                "planned_amount"
            ]
        )
        for item in acompanhamento
    )

    total_gasto = sum(
        float(
            item[
                "spent_amount"
            ]
        )
        for item in acompanhamento
    )

    categorias_acima_do_limite = sum(
        1
        for item in acompanhamento
        if item.get(
            "status"
        ) == "over_limit"
    )

    return {
        "total_planned": float(
            total_planejado
        ),
        "total_spent": float(
            total_gasto
        ),
        "total_remaining": float(
            total_planejado
            - total_gasto
        ),
        "planned_categories": len(
            acompanhamento
        ),
        "categories_over_limit": (
            categorias_acima_do_limite
        ),
    }