import pandas as pd

from analytics import (
    calcular_gastos_por_categoria,
    calcular_meta_mensal,
    calcular_resumo_financeiro,
    filtrar_transacoes_por_mes,
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


def test_calcular_meta_mensal_considera_valor_ja_reservado():
    simulacao = calcular_meta_mensal(
        valor_meta=1500.00,
        prazo_meses=10,
        valor_ja_reservado=500.00,
    )

    assert simulacao["valor_restante"] == 1000.00
    assert simulacao["valor_mensal_necessario"] == 100.00


def test_listar_meses_disponiveis():
    transacoes = criar_transacoes_teste()
    meses = listar_meses_disponiveis(transacoes)

    assert meses == ["2026-06", "2026-07"]


def test_filtrar_transacoes_por_mes():
    transacoes = criar_transacoes_teste()
    transacoes_junho = filtrar_transacoes_por_mes(transacoes, "2026-06")

    assert len(transacoes_junho) == 4
    assert transacoes_junho["ano_mes"].unique().tolist() == ["2026-06"]
