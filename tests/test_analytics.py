import pandas as pd

from analytics import (
    calcular_acompanhamento_orcamento,
    calcular_gastos_por_categoria,
    calcular_meta_mensal,
    calcular_resumo_financeiro,
    calcular_resumo_orcamento,
    filtrar_transacoes_por_mes,
    formatar_moeda,
    listar_meses_disponiveis,
)


def criar_transacoes_teste():
    return pd.DataFrame(
        {
            "data": pd.to_datetime(
                [
                    "2026-06-01",
                    "2026-06-02",
                    "2026-06-03",
                    "2026-06-04",
                    "2026-07-01",
                    "2026-07-02",
                ]
            ),
            "tipo": [
                "receita",
                "despesa",
                "despesa",
                "despesa",
                "receita",
                "despesa",
            ],
            "descricao": [
                "Bolsa-estágio",
                "Mercado",
                "Ônibus",
                "Transferência para reserva",
                "Bolsa-estágio",
                "Cinema",
            ],
            "categoria": [
                "Trabalho",
                "Alimentação",
                "Transporte",
                "Reserva",
                "Trabalho",
                "Lazer",
            ],
            "valor": [
                1600.00,
                200.00,
                100.00,
                300.00,
                1600.00,
                80.00,
            ],
            "ano_mes": [
                "2026-06",
                "2026-06",
                "2026-06",
                "2026-06",
                "2026-07",
                "2026-07",
            ],
        }
    )


def test_calcular_resumo_financeiro_separa_consumo_e_reserva():
    transacoes = criar_transacoes_teste()

    resumo = calcular_resumo_financeiro(transacoes)

    assert resumo["receitas_totais"] == 3200.00
    assert resumo["despesas_totais"] == 680.00
    assert resumo["despesas_do_mes"] == 380.00
    assert resumo["valor_guardado_reserva"] == 300.00
    assert resumo["saldo_disponivel"] == 2520.00
    assert resumo["maior_categoria"] == "Alimentação"
    assert resumo["maior_gasto"] == 200.00


def test_calcular_gastos_por_categoria_nao_inclui_reserva_por_padrao():
    transacoes = criar_transacoes_teste()

    gastos = calcular_gastos_por_categoria(transacoes)

    assert "Reserva" not in gastos.index
    assert gastos["Alimentação"] == 200.00
    assert gastos["Transporte"] == 100.00
    assert gastos["Lazer"] == 80.00


def test_calcular_gastos_por_categoria_pode_incluir_reserva():
    transacoes = criar_transacoes_teste()

    gastos = calcular_gastos_por_categoria(
        transacoes,
        incluir_reserva=True,
    )

    assert gastos["Reserva"] == 300.00


def test_calcular_gastos_por_categoria_ignora_reserva_com_variacao_de_texto():
    transacoes = criar_transacoes_teste()
    transacoes.loc[3, "categoria"] = " reserva "

    gastos = calcular_gastos_por_categoria(transacoes)

    assert " reserva " not in gastos.index


def test_calcular_meta_mensal_considera_valor_ja_reservado():
    simulacao = calcular_meta_mensal(
        valor_meta=1500.00,
        prazo_meses=10,
        valor_ja_reservado=500.00,
    )

    assert simulacao["valor_restante"] == 1000.00
    assert simulacao["valor_mensal_necessario"] == 100.00


def test_calcular_meta_mensal_com_prazo_invalido_nao_divide_por_zero():
    simulacao = calcular_meta_mensal(
        valor_meta=1500.00,
        prazo_meses=0,
        valor_ja_reservado=500.00,
    )

    assert simulacao["valor_restante"] == 1000.00
    assert simulacao["valor_mensal_necessario"] is None


def test_formatar_moeda_no_padrao_brasileiro():
    assert formatar_moeda(1234.5) == "R$ 1.234,50"
    assert formatar_moeda(0) == "R$ 0,00"
    assert formatar_moeda(None) == "N/A"


def test_listar_meses_disponiveis():
    transacoes = criar_transacoes_teste()

    meses = listar_meses_disponiveis(transacoes)

    assert meses == ["2026-06", "2026-07"]


def test_listar_meses_disponiveis_cria_ano_mes_quando_coluna_nao_existe():
    transacoes = criar_transacoes_teste().drop(columns=["ano_mes"])

    meses = listar_meses_disponiveis(transacoes)

    assert meses == ["2026-06", "2026-07"]


def test_filtrar_transacoes_por_mes():
    transacoes = criar_transacoes_teste()

    transacoes_junho = filtrar_transacoes_por_mes(transacoes, "2026-06")

    assert len(transacoes_junho) == 4
    assert transacoes_junho["ano_mes"].unique().tolist() == ["2026-06"]


def test_filtrar_transacoes_por_mes_cria_ano_mes_quando_coluna_nao_existe():
    transacoes = criar_transacoes_teste().drop(columns=["ano_mes"])

    transacoes_julho = filtrar_transacoes_por_mes(transacoes, "2026-07")

    assert len(transacoes_julho) == 2
    assert transacoes_julho["ano_mes"].unique().tolist() == ["2026-07"]

def test_acompanhamento_orcamento_compara_planejado_e_gasto_real():
    transacoes = filtrar_transacoes_por_mes(
        criar_transacoes_teste(),
        "2026-06",
    )

    orcamentos = [
        {
            "budget_id": "budget-1",
            "period": "2026-06",
            "category": "Alimentação",
            "planned_amount": 250.0,
        },
        {
            "budget_id": "budget-2",
            "period": "2026-06",
            "category": "Transporte",
            "planned_amount": 200.0,
        },
        {
            "budget_id": "budget-3",
            "period": "2026-06",
            "category": "Saúde",
            "planned_amount": 300.0,
        },
    ]

    acompanhamento = calcular_acompanhamento_orcamento(
        transacoes=transacoes,
        orcamentos=orcamentos,
    )

    por_categoria = {item["category"]: item for item in acompanhamento}

    alimentacao = por_categoria["Alimentação"]

    assert alimentacao["spent_amount"] == 200.0

    assert alimentacao["remaining_amount"] == 50.0

    assert alimentacao["usage_percentage"] == 80.0

    assert alimentacao["status"] == "near_limit"

    transporte = por_categoria["Transporte"]

    assert transporte["spent_amount"] == 100.0

    assert transporte["status"] == "within_limit"

    saude = por_categoria["Saúde"]

    assert saude["spent_amount"] == 0.0

    assert saude["remaining_amount"] == 300.0

    assert len(acompanhamento) == 3


def test_acompanhamento_normaliza_categoria_e_detecta_estouro():
    transacoes = filtrar_transacoes_por_mes(
        criar_transacoes_teste(),
        "2026-06",
    )

    acompanhamento = calcular_acompanhamento_orcamento(
        transacoes=transacoes,
        orcamentos=[
            {
                "budget_id": "budget-1",
                "period": "2026-06",
                "category": ("  ALIMENTACAO  "),
                "planned_amount": 150.0,
            }
        ],
    )

    resultado = acompanhamento[0]

    assert resultado["spent_amount"] == 200.0

    assert resultado["remaining_amount"] == -50.0

    assert resultado["status"] == "over_limit"


def test_acompanhamento_considera_cem_por_cento_proximo_do_limite():
    transacoes = filtrar_transacoes_por_mes(
        criar_transacoes_teste(),
        "2026-06",
    )

    acompanhamento = calcular_acompanhamento_orcamento(
        transacoes=transacoes,
        orcamentos=[
            {
                "period": "2026-06",
                "category": ("Alimentação"),
                "planned_amount": 200.0,
            }
        ],
    )

    assert acompanhamento[0]["usage_percentage"] == 100.0

    assert acompanhamento[0]["status"] == "near_limit"


def test_calcular_resumo_orcamento():
    transacoes = filtrar_transacoes_por_mes(
        criar_transacoes_teste(),
        "2026-06",
    )

    acompanhamento = calcular_acompanhamento_orcamento(
        transacoes=transacoes,
        orcamentos=[
            {
                "period": "2026-06",
                "category": ("Alimentação"),
                "planned_amount": 150.0,
            },
            {
                "period": "2026-06",
                "category": ("Transporte"),
                "planned_amount": 200.0,
            },
        ],
    )

    resumo = calcular_resumo_orcamento(acompanhamento)

    assert resumo["total_planned"] == 350.0

    assert resumo["total_spent"] == 300.0

    assert resumo["total_remaining"] == 50.0

    assert resumo["planned_categories"] == 2

    assert resumo["categories_over_limit"] == 1


def test_calcular_resumo_orcamento_vazio():
    resumo = calcular_resumo_orcamento([])

    assert resumo == {
        "total_planned": 0.0,
        "total_spent": 0.0,
        "total_remaining": 0.0,
        "planned_categories": 0,
        "categories_over_limit": 0,
    }
