from pathlib import Path

import pandas as pd
import pytest

from scripts.etl_transacoes import (
    finalizar_transacoes_validas,
    preparar_transacoes,
    separar_transacoes_por_validade,
    transformar_transacoes,
    validar_colunas,
)


def criar_transacoes_brutas_teste():
    return pd.DataFrame(
        {
            "data": [
                "2026-06-01",
                "2026-06-02",
                "data-invalida",
                "2026-06-04",
                "2026-06-05",
                "2026-06-06",
            ],
            "tipo": [
                " Receita ",
                " DESPESA ",
                "despesa",
                "outro",
                "despesa",
                "",
            ],
            "descricao": [
                " Bolsa-estágio ",
                " Mercado ",
                " Linha com data inválida ",
                " Tipo inválido ",
                " Valor negativo ",
                "",
            ],
            "categoria": [
                " Trabalho ",
                " Alimentação ",
                " Alimentação ",
                " Outros ",
                " Compras ",
                " Serviços ",
            ],
            "valor": [
                "1600.00",
                "200.00",
                "50.00",
                "10.00",
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


def test_validar_colunas_rejeita_arquivo_sem_coluna_obrigatoria():
    transacoes = pd.DataFrame(
        {
            "data": ["2026-06-01"],
            "tipo": ["receita"],
            "descricao": ["Bolsa-estágio"],
            "valor": [1600.00],
        }
    )

    with pytest.raises(ValueError) as erro:
        validar_colunas(transacoes, Path("arquivo_invalido.csv"))

    mensagem = str(erro.value)

    assert "arquivo_invalido.csv" in mensagem
    assert "categoria" in mensagem


def test_preparar_transacoes_padroniza_tipos_e_textos():
    transacoes = criar_transacoes_brutas_teste()

    resultado = preparar_transacoes(transacoes)

    assert resultado.loc[0, "tipo"] == "receita"
    assert resultado.loc[1, "tipo"] == "despesa"
    assert resultado.loc[0, "descricao"] == "Bolsa-estágio"
    assert resultado.loc[1, "categoria"] == "Alimentação"
    assert resultado.loc[0, "valor"] == 1600.00
    assert pd.isna(resultado.loc[2, "data"])
    assert pd.isna(resultado.loc[5, "valor"])


def test_separar_transacoes_por_validade_identifica_validas_e_rejeitadas():
    transacoes = criar_transacoes_brutas_teste()

    validas, rejeicoes = separar_transacoes_por_validade(transacoes)

    assert len(validas) == 2
    assert len(rejeicoes) == 4
    assert "motivo_rejeicao" in rejeicoes.columns

    motivos = " ".join(rejeicoes["motivo_rejeicao"].tolist())

    assert "data invalida ou vazia" in motivos
    assert "tipo invalido" in motivos
    assert "valor menor ou igual a zero" in motivos
    assert "tipo vazio" in motivos
    assert "descricao vazia" in motivos
    assert "valor invalido ou vazio" in motivos


def test_transformar_transacoes_limpa_padroniza_e_remove_linhas_invalidas():
    transacoes = criar_transacoes_brutas_teste()

    resultado = transformar_transacoes(transacoes)

    assert len(resultado) == 2
    assert resultado["tipo"].tolist() == ["receita", "despesa"]
    assert resultado["descricao"].tolist() == ["Bolsa-estágio", "Mercado"]
    assert resultado["categoria"].tolist() == ["Trabalho", "Alimentação"]
    assert resultado["valor"].tolist() == [1600.00, 200.00]
    assert resultado["ano_mes"].tolist() == ["2026-06", "2026-06"]


def test_finalizar_transacoes_validas_cria_ano_mes_e_ordena():
    transacoes = pd.DataFrame(
        {
            "data": pd.to_datetime(
                [
                    "2026-07-02",
                    "2026-06-01",
                    "2026-07-01",
                ]
            ),
            "tipo": [
                "despesa",
                "receita",
                "receita",
            ],
            "descricao": [
                "Cinema",
                "Bolsa-estágio",
                "Bolsa-estágio",
            ],
            "categoria": [
                "Lazer",
                "Trabalho",
                "Trabalho",
            ],
            "valor": [
                80.00,
                1600.00,
                1600.00,
            ],
            "arquivo_origem": [
                "teste.csv",
                "teste.csv",
                "teste.csv",
            ],
        }
    )

    resultado = finalizar_transacoes_validas(transacoes)

    assert resultado["ano_mes"].tolist() == [
        "2026-06",
        "2026-07",
        "2026-07",
    ]
    assert resultado["data"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-06-01",
        "2026-07-01",
        "2026-07-02",
    ]