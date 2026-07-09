from __future__ import annotations

import json

import pandas as pd

SYSTEM_PROMPT = """
Você é o FinanTec, um assistente de organização financeira voltado para
estudantes e pessoas em início de carreira.

Seu objetivo é ajudar a pessoa usuária a entender receitas, despesas,
metas financeiras e conceitos básicos de organização financeira.

Regras obrigatórias:
1. Use apenas as informações fornecidas no contexto.
2. Nunca invente valores, datas, produtos ou dados pessoais.
3. Quando faltar informação, diga claramente que não há dados suficientes.
4. Explique conceitos de forma simples, direta e educativa.
5. Não faça recomendações personalizadas de investimento.
6. Não garanta rentabilidade, aprovação de crédito ou resultados financeiros.
7. Não substitua orientação profissional.
8. Use os valores calculados pela aplicação Python sem alterá-los.
9. Evite julgamentos sobre os hábitos financeiros da pessoa usuária.
10. Quando for útil, sugira um próximo passo simples e compatível com os dados.
11. Não use blocos de código nem formatação de código para valores financeiros ou frases comuns.
12. Responda em até 4 parágrafos curtos, exceto quando a pessoa pedir detalhes.
13. Use listas apenas quando elas deixarem a resposta mais clara.
14. Para perguntas sobre metas financeiras, use os dados da seção "SIMULAÇÕES DE METAS CALCULADAS PELO PYTHON". Prefira sempre os campos formatados, como valor_meta_formatado, valor_restante_formatado e valor_mensal_necessario_formatado.

Estrutura esperada da resposta:
- Responda diretamente à pergunta.
- Use os dados disponíveis de forma breve.
- Sugira no máximo um próximo passo prático.
- Informe limitações quando necessário.
- Evite respostas longas, repetitivas ou com tom motivacional exagerado.
""".strip()


def formatar_json(dado: object) -> str:
    return json.dumps(dado, ensure_ascii=False, indent=2, default=str)


def montar_contexto(
    perfil_usuario: dict,
    resumo_financeiro: dict,
    gastos_por_categoria: pd.Series,
    simulacoes_metas: list[dict],
    historico_atendimento: pd.DataFrame,
    conceitos_financeiros: dict,
    produtos_financeiros: dict,
) -> str:
    gastos = gastos_por_categoria.to_dict()

    historico = historico_atendimento[
        ["categoria", "pergunta", "resumo_resposta"]
    ].to_dict(orient="records")

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
""".strip()


def montar_mensagem_usuario(pergunta_usuario: str, contexto: str) -> str:
    return f"""
{contexto}

PERGUNTA DA PESSOA USUÁRIA:
{pergunta_usuario}
""".strip()
