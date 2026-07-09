from pathlib import Path

import pandas as pd
import pytest

from scripts.etl_transacoes import transformar_transacoes, validar_colunas


def test_validar_colunas_rejeita_arquivo_sem_coluna_obrigatoria():
    transacoes = pd.DataFrame(
        {
            "data": ["2026-06-01"],
            "tipo": ["receita"],
            "descricao": ["Bolsa-estágio"],
            "valor": [1600.00],
        }
    )

    with pytest.raises(ValueError):
        validar_colunas(transacoes, Path("arquivo_invalido.csv"))


def test_transformar_transacoes_limpa_e_padroniza_dados():
    transacoes = pd.DataFrame(
        {
            "data": [
                "2026-06-01",
                "2026-06-02",
                "data-invalida",
                "2026-06-04",
                "2026-06-05",
            ],
            "tipo": [
                " Receita ",
                " DESPESA ",
                "despesa",
                "outro",
                "despesa",
            ],
            "descricao": [
                " Bolsa-estágio ",
                " Mercado ",
                " Linha com data inválida ",
                " Tipo inválido ",
                " Valor inválido ",
            ],
            "categoria": [
                " Trabalho ",
                " Alimentação ",
                " Alimentação ",
                " Outros ",
                " Compras ",
            ],
            "valor": [
                "1600.00",
                "200.00",
                "50.00",
                "10.00",
                "-20.00",
            ],
            "arquivo_origem": [
                "teste.csv",
                "teste.csv",
                "teste.csv",
                "teste.csv",
                "teste.csv",
            ],
        }
    )

    resultado = transformar_transacoes(transacoes)

    assert len(resultado) == 2
    assert resultado["tipo"].tolist() == ["receita", "despesa"]
    assert resultado["categoria"].tolist() == ["Trabalho", "Alimentação"]
    assert resultado["valor"].tolist() == [1600.00, 200.00]
    assert resultado["ano_mes"].tolist() == ["2026-06", "2026-06"]
