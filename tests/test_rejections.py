import pandas as pd

from scripts.etl_transacoes import gerar_relatorio_rejeicoes


def test_gerar_relatorio_rejeicoes_identifica_linhas_invalidas():
    transacoes = pd.DataFrame(
        {
            "data": [
                "2026-06-01",
                "data-invalida",
                "2026-06-03",
                "2026-06-04",
                "2026-06-05",
                "2026-06-06",
            ],
            "tipo": [
                "receita",
                "despesa",
                "outro",
                "despesa",
                "despesa",
                "",
            ],
            "descricao": [
                "Bolsa-estágio",
                "Data inválida",
                "Tipo inválido",
                "",
                "Valor negativo",
                "Tipo vazio",
            ],
            "categoria": [
                "Trabalho",
                "Alimentação",
                "Compras",
                "Lazer",
                "",
                "Serviços",
            ],
            "valor": [
                "1600.00",
                "50.00",
                "100.00",
                "40.00",
                "-20.00",
                "abc",
            ],
            "arquivo_origem": [
                "teste.csv",
                "teste.csv",
                "teste.csv",
                "teste.csv",
                "teste.csv",
                "teste.csv",
            ],
        }
    )

    rejeicoes = gerar_relatorio_rejeicoes(transacoes)

    assert len(rejeicoes) == 5
    assert "motivo_rejeicao" in rejeicoes.columns

    motivos = " ".join(rejeicoes["motivo_rejeicao"].tolist())

    assert "data invalida ou vazia" in motivos
    assert "tipo invalido" in motivos
    assert "descricao vazia" in motivos
    assert "categoria vazia" in motivos
    assert "valor menor ou igual a zero" in motivos
    assert "valor invalido ou vazio" in motivos