"""
Montagem de prompts e contexto para o assistente FinanTec.

Este módulo separa as regras de comportamento da IA e o contexto enviado para o
modelo generativo. A aplicação calcula os valores financeiros em Python e envia
esses resultados prontos para a IA apenas explicar.
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

Estrutura esperada da resposta:
- Responda diretamente à pergunta.
- Use os dados disponíveis de forma breve.
- Sugira no máximo um próximo passo prático.
- Informe limitações quando necessário.
- Evite respostas longas, repetitivas ou com tom motivacional exagerado.
""".strip()


def formatar_json(dado: Any) -> str:
    """
    Converte dados Python para JSON legível dentro do prompt.

    O parâmetro default=str evita erro com tipos específicos do pandas,
    como Timestamp e valores numéricos próprios da biblioteca.
    """
    return json.dumps(
        dado,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def converter_gastos_para_dict(gastos_por_categoria: pd.Series) -> dict[str, float]:
    """
    Converte a série de gastos por categoria para um dicionário simples.
    """
    return {
        str(categoria): float(valor)
        for categoria, valor in gastos_por_categoria.items()
    }


def resumir_historico_atendimento(
    historico_atendimento: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Seleciona apenas as colunas úteis do histórico de dúvidas.

    O limite evita enviar contexto desnecessariamente grande para a IA.
    """
    colunas_esperadas = ["categoria", "pergunta", "resumo_resposta"]

    colunas_disponiveis = [
        coluna
        for coluna in colunas_esperadas
        if coluna in historico_atendimento.columns
    ]

    if not colunas_disponiveis:
        return []

    historico = historico_atendimento[colunas_disponiveis].tail(
        LIMITE_HISTORICO_ATENDIMENTO
    )

    return historico.to_dict(orient="records")


def montar_contexto(
    perfil_usuario: dict,
    resumo_financeiro: dict,
    gastos_por_categoria: pd.Series,
    simulacoes_metas: list[dict],
    historico_atendimento: pd.DataFrame,
    conceitos_financeiros: dict,
    produtos_financeiros: dict,
) -> str:
    """
    Monta o contexto enviado ao modelo generativo.

    Os cálculos financeiros já chegam prontos nesta função. O papel da IA é
    explicar os indicadores, não recalcular ou inventar valores.
    """
    gastos = converter_gastos_para_dict(gastos_por_categoria)
    historico = resumir_historico_atendimento(historico_atendimento)

    return f"""
PERFIL DA PESSOA USUÁRIA:
{formatar_json(perfil_usuario)}

RESUMO FINANCEIRO CALCULADO PELO PYTHON:
{formatar_json(resumo_financeiro)}

GASTOS POR CATEGORIA CALCULADOS PELO PYTHON:
{formatar_json(gastos)}

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


def montar_mensagem_usuario(pergunta_usuario: str, contexto: str) -> str:
    """
    Junta o contexto da aplicação com a pergunta feita pela pessoa usuária.
    """
    return f"""
{contexto}

PERGUNTA DA PESSOA USUÁRIA:
{pergunta_usuario}
""".strip()