import pandas as pd

from transaction_editor import (
    COLUNAS_TRANSACOES,
    carregar_transacoes_manuais,
    criar_dataframe_vazio,
    preparar_transacoes_para_salvar,
    salvar_transacoes_manuais,
)


def test_criar_dataframe_vazio_usa_colunas_do_contrato():
    transacoes = criar_dataframe_vazio()

    assert transacoes.empty
    assert transacoes.columns.tolist() == COLUNAS_TRANSACOES


def test_preparar_transacoes_para_salvar_padroniza_dados():
    transacoes = pd.DataFrame(
        {
            "data": [
                "2026-07-10",
                "data-invalida",
            ],
            "tipo": [
                " DESPESA ",
                " Receita ",
            ],
            "descricao": [
                " Mercado ",
                " Bolsa ",
            ],
            "categoria": [
                " Alimentação ",
                " Trabalho ",
            ],
            "valor": [
                "50.50",
                "abc",
            ],
        }
    )

    resultado = preparar_transacoes_para_salvar(transacoes)

    assert resultado.loc[0, "data"] == "2026-07-10"
    assert resultado.loc[1, "data"] == ""
    assert resultado.loc[0, "tipo"] == "despesa"
    assert resultado.loc[1, "tipo"] == "receita"
    assert resultado.loc[0, "descricao"] == "Mercado"
    assert resultado.loc[1, "categoria"] == "Trabalho"
    assert resultado.loc[0, "valor"] == 50.50
    assert pd.isna(resultado.loc[1, "valor"])


def test_carregar_transacoes_manuais_retorna_vazio_quando_arquivo_nao_existe(
    monkeypatch,
    tmp_path,
):
    arquivo_teste = tmp_path / "transacoes_manuais.csv"

    monkeypatch.setattr(
        "transaction_editor.ARQUIVO_TRANSACOES_MANUAIS",
        arquivo_teste,
    )

    transacoes = carregar_transacoes_manuais()

    assert transacoes.empty
    assert transacoes.columns.tolist() == COLUNAS_TRANSACOES


def test_salvar_e_carregar_transacoes_manuais(monkeypatch, tmp_path):
    arquivo_teste = tmp_path / "transacoes_manuais.csv"

    monkeypatch.setattr(
        "transaction_editor.RAW_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        "transaction_editor.ARQUIVO_TRANSACOES_MANUAIS",
        arquivo_teste,
    )

    transacoes = pd.DataFrame(
        {
            "data": ["2026-07-10"],
            "tipo": ["despesa"],
            "descricao": ["Teste mercado"],
            "categoria": ["Alimentação"],
            "valor": [50.00],
        }
    )

    salvar_transacoes_manuais(transacoes)
    transacoes_carregadas = carregar_transacoes_manuais()

    assert arquivo_teste.exists()
    assert len(transacoes_carregadas) == 1
    assert transacoes_carregadas.loc[0, "tipo"] == "despesa"
    assert transacoes_carregadas.loc[0, "descricao"] == "Teste mercado"
    assert transacoes_carregadas.loc[0, "categoria"] == "Alimentação"
    assert transacoes_carregadas.loc[0, "valor"] == 50.00