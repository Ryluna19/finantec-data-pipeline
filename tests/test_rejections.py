import pandas as pd

from scripts.etl_transacoes import gerar_relatorio_rejeicoes


def test_gerar_relatorio_rejeicoes_retorna_apenas_linhas_invalidas():
    transacoes = pd.DataFrame(
        {
            "data": [
                "2026-06-01",
                "data-invalida",
                "2026-06-03",
                "2026-06-04",
            ],
            "tipo": [
                "receita",
                "despesa",
                "outro",
                "despesa",
            ],
            "descricao": [
                "Bolsa-estágio",
                "Data inválida",
                "Tipo inválido",
                "",
            ],
            "categoria": [
                "Trabalho",
                "Alimentação",
                "Compras",
                "Lazer",
            ],
            "valor": [
                "1600.00",
                "50.00",
                "100.00",
                "40.00",
            ],
            "arquivo_origem": [
                "teste.csv",
                "teste.csv",
                "teste.csv",
                "teste.csv",
            ],
        }
    )

    rejeicoes = gerar_relatorio_rejeicoes(transacoes)

    assert len(rejeicoes) == 3
    assert "motivo_rejeicao" in rejeicoes.columns
    assert "arquivo_origem" in rejeicoes.columns

    motivos = " ".join(rejeicoes["motivo_rejeicao"].tolist())

    assert "data invalida ou vazia" in motivos
    assert "tipo invalido" in motivos
    assert "descricao vazia" in motivos


def test_gerar_relatorio_rejeicoes_acumula_mais_de_um_motivo_na_mesma_linha():
    transacoes = pd.DataFrame(
        {
            "data": ["data-invalida"],
            "tipo": ["outro"],
            "descricao": [""],
            "categoria": [""],
            "valor": ["-20.00"],
            "arquivo_origem": ["teste.csv"],
        }
    )

    rejeicoes = gerar_relatorio_rejeicoes(transacoes)

    assert len(rejeicoes) == 1

    motivo = rejeicoes.loc[0, "motivo_rejeicao"]

    assert "data invalida ou vazia" in motivo
    assert "tipo invalido" in motivo
    assert "descricao vazia" in motivo
    assert "categoria vazia" in motivo
    assert "valor menor ou igual a zero" in motivo


def test_gerar_relatorio_rejeicoes_retorna_vazio_quando_nao_ha_erros():
    transacoes = pd.DataFrame(
        {
            "data": [
                "2026-06-01",
                "2026-06-02",
            ],
            "tipo": [
                "receita",
                "despesa",
            ],
            "descricao": [
                "Bolsa-estágio",
                "Mercado",
            ],
            "categoria": [
                "Trabalho",
                "Alimentação",
            ],
            "valor": [
                "1600.00",
                "200.00",
            ],
            "arquivo_origem": [
                "teste.csv",
                "teste.csv",
            ],
        }
    )

    rejeicoes = gerar_relatorio_rejeicoes(transacoes)

    assert rejeicoes.empty