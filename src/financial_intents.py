"""Classificação local de intenções financeiras.

O classificador reconhece perguntas comuns sem depender da API generativa.
Ele não calcula valores nem produz a resposta final: apenas orienta o modelo
sobre qual parte do contexto financeiro deve receber prioridade.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum


class FinancialIntent(StrEnum):
    """Intenções reconhecidas pelo assistente."""

    BALANCE = "saldo"
    INCOME = "receitas"
    EXPENSES = "despesas"
    RESERVE = "reserva"
    TOP_CATEGORY = "maior_categoria"
    PERIOD_SUMMARY = "resumo_do_periodo"
    GOAL = "meta_financeira"
    FINANCIAL_CONCEPT = "conceito_financeiro"
    FINANCIAL_PRODUCT = "produto_financeiro"
    HELP = "ajuda"
    UNKNOWN = "desconhecida"


@dataclass(
    frozen=True,
    slots=True,
)
class IntentRule:
    """Associa uma intenção a padrões de linguagem."""

    intent: FinancialIntent
    patterns: tuple[str, ...]


@dataclass(
    frozen=True,
    slots=True,
)
class IntentClassification:
    """Representa o resultado da classificação local."""

    intent: FinancialIntent
    normalized_question: str
    matched_pattern: str | None = None

    @property
    def is_known(self) -> bool:
        """Indica se uma intenção conhecida foi encontrada."""
        return (
            self.intent
            != FinancialIntent.UNKNOWN
        )


INTENT_RULES = (
    IntentRule(
        intent=FinancialIntent.HELP,
        patterns=(
            (
                r"\b(?:ajuda|me ajuda|pode me ajudar|"
                r"como voce (?:pode )?me ajudar|"
                r"o que voce faz|exemplos? de perguntas?)\b"
            ),
        ),
    ),
    IntentRule(
        intent=(
            FinancialIntent.FINANCIAL_CONCEPT
        ),
        patterns=(
            (
                r"\b(?:o que e|explique|me explique|"
                r"como funciona|qual a diferenca)\b"
            ),
        ),
    ),
    IntentRule(
        intent=FinancialIntent.GOAL,
        patterns=(
            (
                r"\b(?:meta|metas|objetivo|objetivos)\b"
            ),
            (
                r"\bquanto (?:eu )?preciso "
                r"(?:guardar|economizar)\b"
            ),
            r"\bquanto guardar por mes\b",
        ),
    ),
    IntentRule(
        intent=(
            FinancialIntent.FINANCIAL_PRODUCT
        ),
        patterns=(
            (
                r"\b(?:cdb|tesouro selic|tesouro direto|"
                r"poupanca|investimento|investimentos|"
                r"produto financeiro|produtos financeiros|"
                r"renda fixa|liquidez|rentabilidade)\b"
            ),
        ),
    ),
    IntentRule(
        intent=FinancialIntent.TOP_CATEGORY,
        patterns=(
            r"\bcom o que mais gastei\b",
            (
                r"\bonde (?:eu )?"
                r"(?:gastei|estou gastando) mais\b"
            ),
            (
                r"\bem que (?:eu )?"
                r"(?:gastei|estou gastando) mais\b"
            ),
            (
                r"\bqual categoria.{0,30}"
                r"(?:mais gastei|gastei mais|"
                r"pesa mais|mais pesa|maior gasto)\b"
            ),
            (
                r"\bcategoria.{0,30}"
                r"(?:mais gastei|gastei mais|"
                r"pesa mais|mais pesa|maior gasto)\b"
            ),
        ),
    ),
    IntentRule(
        intent=FinancialIntent.RESERVE,
        patterns=(
            (
                r"\b(?:reserva|valor guardado|"
                r"quanto (?:eu )?"
                r"(?:guardei|reservei|separei|"
                r"economizei|poupei))\b"
            ),
        ),
    ),
    IntentRule(
        intent=FinancialIntent.INCOME,
        patterns=(
            (
                r"\b(?:receita|receitas|renda|"
                r"quanto (?:eu )?recebi|"
                r"quanto entrou|total de entradas?|"
                r"dinheiro que entrou)\b"
            ),
        ),
    ),
    IntentRule(
        intent=FinancialIntent.EXPENSES,
        patterns=(
            (
                r"\b(?:despesa|despesas|"
                r"quanto (?:eu )?gastei|"
                r"quanto saiu|total de gastos?|"
                r"gastos? do mes)\b"
            ),
        ),
    ),
    IntentRule(
        intent=FinancialIntent.BALANCE,
        patterns=(
            (
                r"\b(?:saldo|"
                r"quanto (?:ainda )?(?:eu )?tenho|"
                r"quanto (?:eu )?tenho disponivel|"
                r"quanto sobrou|sobrou dinheiro|"
                r"dinheiro disponivel|valor disponivel|"
                r"quanto posso gastar|posso gastar quanto|"
                r"fiquei no positivo|fiquei no negativo|"
                r"estou no vermelho)\b"
            ),
        ),
    ),
    IntentRule(
        intent=FinancialIntent.PERIOD_SUMMARY,
        patterns=(
            (
                r"\b(?:resumo|resumo financeiro|"
                r"visao geral|como estao minhas financas|"
                r"como estou financeiramente|"
                r"situacao financeira|"
                r"balanco do periodo)\b"
            ),
        ),
    ),
)


INTENT_GUIDANCE = {
    FinancialIntent.BALANCE: (
        "Priorize o campo saldo_disponivel do resumo financeiro. "
        "Não use receitas totais como se fossem dinheiro disponível."
    ),
    FinancialIntent.INCOME: (
        "Priorize o campo receitas_totais do resumo financeiro."
    ),
    FinancialIntent.EXPENSES: (
        "Priorize o campo despesas_do_mes do resumo financeiro."
    ),
    FinancialIntent.RESERVE: (
        "Priorize o campo valor_guardado_reserva do resumo financeiro. "
        "Diferencie valor reservado de saldo disponível."
    ),
    FinancialIntent.TOP_CATEGORY: (
        "Use somente o RESUMO DE CATEGORIAS CALCULADO PELO PYTHON. "
        "Não recalcule nem escolha uma categoria diferente."
    ),
    FinancialIntent.PERIOD_SUMMARY: (
        "Apresente uma visão breve das receitas, despesas, reserva "
        "e saldo disponível calculados pela aplicação."
    ),
    FinancialIntent.GOAL: (
        "Use as SIMULAÇÕES DE METAS CALCULADAS PELO PYTHON. "
        "Não refaça os cálculos da meta."
    ),
    FinancialIntent.FINANCIAL_CONCEPT: (
        "Explique o conceito usando apenas a base de conceitos "
        "financeiros disponível no contexto."
    ),
    FinancialIntent.FINANCIAL_PRODUCT: (
        "Use apenas os produtos informativos do contexto. "
        "Caso a pergunta dependa de taxas atuais, comparação de mercado "
        "ou escolha do melhor produto, informe essa limitação."
    ),
    FinancialIntent.HELP: (
        "Explique brevemente os tipos de pergunta que o FinanTec "
        "consegue responder e apresente no máximo quatro exemplos."
    ),
    FinancialIntent.UNKNOWN: (
        "Não force uma interpretação. Responda com base na pergunta "
        "literal e no contexto. Caso faltem dados, informe a limitação."
    ),
}


def normalize_question(
    question: str,
) -> str:
    """Normaliza texto para comparação sem acentos ou pontuação."""
    normalized = unicodedata.normalize(
        "NFKD",
        question,
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    normalized = normalized.lower()

    normalized = re.sub(
        r"[^a-z0-9\s]",
        " ",
        normalized,
    )

    return re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()


def classify_financial_intent(
    question: str,
) -> IntentClassification:
    """Classifica a intenção principal de uma pergunta."""
    normalized_question = (
        normalize_question(
            question
        )
    )

    if not normalized_question:
        return IntentClassification(
            intent=FinancialIntent.UNKNOWN,
            normalized_question="",
        )

    for rule in INTENT_RULES:
        for pattern in rule.patterns:
            if re.search(
                pattern,
                normalized_question,
            ):
                return IntentClassification(
                    intent=rule.intent,
                    normalized_question=(
                        normalized_question
                    ),
                    matched_pattern=pattern,
                )

    return IntentClassification(
        intent=FinancialIntent.UNKNOWN,
        normalized_question=(
            normalized_question
        ),
    )


def get_intent_guidance(
    intent: FinancialIntent,
) -> str:
    """Retorna a orientação associada à intenção."""
    return INTENT_GUIDANCE.get(
        intent,
        INTENT_GUIDANCE[
            FinancialIntent.UNKNOWN
        ],
    )


def build_intent_prompt_context(
    classification: IntentClassification,
) -> str:
    """Monta a seção de intenção enviada ao modelo."""
    guidance = get_intent_guidance(
        classification.intent
    )

    return (
        "INTENÇÃO IDENTIFICADA PELA APLICAÇÃO:\n"
        f"- intenção: {classification.intent.value}\n"
        f"- orientação: {guidance}\n"
        "- observação: esta classificação é heurística. "
        "A pergunta original continua sendo a referência principal."
    )