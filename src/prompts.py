"""Montagem de prompts e contexto para o assistente FinanTec.

A aplicação calcula os indicadores financeiros em Python. O modelo
generativo recebe os resultados prontos e é responsável apenas por
explicá-los de forma clara e contextualizada.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd


LIMITE_HISTORICO_ATENDIMENTO = 8


SYSTEM_PROMPT = """
Você é o FinanTec, um assistente de organização financeira voltado para
estudantes e pessoas em início de carreira.

Seu objetivo é ajudar a pessoa usuária a entender receitas, despesas,
metas financeiras e conceitos básicos de organização financeira.

Regras obrigatórias:
1. Use apenas as informações fornecidas no contexto.
2. Nunca invente valores, datas, produtos, taxas, bancos ou dados pessoais.
3. Quando faltar informação, diga claramente que não há dados suficientes.
4. Explique conceitos de forma simples, direta e educativa.
5. Não faça recomendações personalizadas de investimento.
6. Não garanta rentabilidade, aprovação de crédito ou resultados financeiros.
7. Não substitua orientação profissional.
8. Use os valores calculados pela aplicação Python sem alterá-los.
9. Evite julgamentos sobre os hábitos financeiros da pessoa usuária.
10. Quando for útil, sugira no máximo um próximo passo simples e compatível com os dados.
11. Não use blocos de código nem formatação de código para valores financeiros ou frases comuns.
12. Responda em até 4 parágrafos curtos, exceto quando a pessoa pedir detalhes.
13. Use listas apenas quando elas deixarem a resposta mais clara.
14. Para perguntas sobre metas financeiras, use os dados da seção "SIMULAÇÕES DE METAS CALCULADAS PELO PYTHON".
15. Para metas financeiras, prefira os campos formatados, como valor_meta_formatado, valor_restante_formatado e valor_mensal_necessario_formatado.
16. Para perguntas sobre produtos financeiros, use apenas os produtos informativos fornecidos no contexto.
17. Se a pergunta depender de dados atuais, taxas em tempo real ou comparação de mercado, informe que o contexto não possui dados suficientes.
18. Não diga que um banco, CDB, cartão ou produto é "o melhor" se essa conclusão não estiver explicitamente nos dados fornecidos.
19. A seção "INTENÇÃO IDENTIFICADA PELA APLICAÇÃO" é uma classificação heurística. Use-a como orientação, mas priorize a pergunta literal da pessoa usuária.
20. Para identificar a categoria de maior gasto, use somente a seção "RESUMO DE CATEGORIAS CALCULADO PELO PYTHON". Não compare ou recalcule os valores.
21. Quando a intenção estiver como "desconhecida", não force uma resposta financeira. Informe a limitação quando a pergunta não puder ser respondida pelo contexto.

Estrutura esperada da resposta:
- Responda diretamente à pergunta.
- Use os dados disponíveis de forma breve.
- Sugira no máximo um próximo passo prático.
- Informe limitações quando necessário.
- Evite respostas longas, repetitivas ou com tom motivacional exagerado.
""".strip()


def formatar_json(
    dado: Any,
) -> str:
    """Converte dados Python para JSON legível."""
    return json.dumps(
        dado,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def converter_gastos_para_dict(
    gastos_por_categoria: pd.Series,
) -> dict[str, float]:
    """Converte gastos válidos para um dicionário simples."""
    gastos: dict[
        str,
        float,
    ] = {}

    for categoria, valor in (
        gastos_por_categoria.items()
    ):
        valor_numerico = pd.to_numeric(
            valor,
            errors="coerce",
        )

        if pd.isna(
            valor_numerico
        ):
            continue

        gastos[
            str(
                categoria
            )
        ] = float(
            valor_numerico
        )

    return gastos


def resumir_gastos_por_categoria(
    gastos: dict[str, float],
) -> dict[str, Any]:
    """Calcula previamente as categorias de maior gasto."""
    if not gastos:
        return {
            "categorias_com_maior_gasto": [],
            "maior_valor": None,
            "ha_empate": False,
            "quantidade_categorias": 0,
            "total_categorizado": 0.0,
        }

    maior_valor = max(
        gastos.values()
    )

    categorias_com_maior_gasto = [
        categoria
        for categoria, valor in gastos.items()
        if valor == maior_valor
    ]

    return {
        "categorias_com_maior_gasto": (
            categorias_com_maior_gasto
        ),
        "maior_valor": float(
            maior_valor
        ),
        "ha_empate": (
            len(
                categorias_com_maior_gasto
            )
            > 1
        ),
        "quantidade_categorias": len(
            gastos
        ),
        "total_categorizado": float(
            sum(
                gastos.values()
            )
        ),
    }


def resumir_historico_atendimento(
    historico_atendimento: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Seleciona apenas as colunas úteis do histórico."""
    colunas_esperadas = [
        "categoria",
        "pergunta",
        "resumo_resposta",
    ]

    colunas_disponiveis = [
        coluna
        for coluna in colunas_esperadas
        if coluna
        in historico_atendimento.columns
    ]

    if not colunas_disponiveis:
        return []

    historico = (
        historico_atendimento[
            colunas_disponiveis
        ]
        .tail(
            LIMITE_HISTORICO_ATENDIMENTO
        )
    )

    return historico.to_dict(
        orient="records"
    )


def montar_contexto(
    perfil_usuario: dict,
    resumo_financeiro: dict,
    gastos_por_categoria: pd.Series,
    simulacoes_metas: list[dict],
    historico_atendimento: pd.DataFrame,
    conceitos_financeiros: dict,
    produtos_financeiros: dict,
) -> str:
    """Monta o contexto enviado ao modelo generativo."""
    gastos = converter_gastos_para_dict(
        gastos_por_categoria
    )

    resumo_categorias = (
        resumir_gastos_por_categoria(
            gastos
        )
    )

    historico = (
        resumir_historico_atendimento(
            historico_atendimento
        )
    )

    return f"""
PERFIL DA PESSOA USUÁRIA:
{formatar_json(perfil_usuario)}

RESUMO FINANCEIRO CALCULADO PELO PYTHON:
{formatar_json(resumo_financeiro)}

GASTOS POR CATEGORIA CALCULADOS PELO PYTHON:
{formatar_json(gastos)}

RESUMO DE CATEGORIAS CALCULADO PELO PYTHON:
{formatar_json(resumo_categorias)}

SIMULAÇÕES DE METAS CALCULADAS PELO PYTHON:
{formatar_json(simulacoes_metas)}

HISTÓRICO DE DÚVIDAS:
{formatar_json(historico)}

CONCEITOS FINANCEIROS DISPONÍVEIS:
{formatar_json(conceitos_financeiros)}

PRODUTOS FINANCEIROS INFORMATIVOS:
{formatar_json(produtos_financeiros)}

LIMITAÇÕES IMPORTANTES:
- Os dados financeiros são simulados.
- O assistente não acessa dados bancários reais.
- O assistente não consulta taxas, produtos ou cotações em tempo real.
- Produtos financeiros no contexto são apenas informativos.
- Qualquer pergunta sobre "melhor produto hoje" deve ser respondida com cautela, informando a limitação dos dados.
""".strip()


def montar_mensagem_usuario(
    pergunta_usuario: str,
    contexto: str,
    contexto_intencao: str | None = None,
) -> str:
    """Junta contexto, intenção e pergunta da pessoa usuária."""
    secoes = [
        contexto.strip(),
    ]

    if (
        contexto_intencao
        and contexto_intencao.strip()
    ):
        secoes.append(
            contexto_intencao.strip()
        )

    secoes.append(
        (
            "PERGUNTA DA PESSOA USUÁRIA:\n"
            f"{pergunta_usuario.strip()}"
        )
    )

    return "\n\n".join(
        secoes
    )