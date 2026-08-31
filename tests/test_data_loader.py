"""Testes do carregamento das transações do dashboard."""

from src import data_loader


def test_carregar_transacoes_csv_returns_empty_without_processed_file(
    monkeypatch,
    tmp_path,
) -> None:
    """Não usa dados antigos como fallback após um reset."""
    missing_processed_file = (
        tmp_path
        / "transacoes_processadas.csv"
    )

    monkeypatch.setattr(
        data_loader,
        "ARQUIVO_TRANSACOES_PROCESSADAS",
        missing_processed_file,
    )

    transactions = (
        data_loader
        .carregar_transacoes_csv()
    )

    assert transactions.empty

    assert transactions.columns.tolist() == [
        "data",
        "tipo",
        "descricao",
        "categoria",
        "valor",
        "arquivo_origem",
        "ano_mes",
    ]
    
def test_carregar_transacoes_remote_backend_does_not_use_csv_fallback(
    monkeypatch,
) -> None:
    """Não usa o CSV local como fallback em um backend remoto vazio."""

    def fail_if_csv_is_loaded():
        raise AssertionError(
            "O CSV local não deve ser carregado em backend remoto."
        )

    monkeypatch.setattr(
        data_loader,
        "database_uses_local_file",
        lambda: False,
    )

    monkeypatch.setattr(
        data_loader,
        "sqlite_table_exists",
        lambda **kwargs: False,
    )

    monkeypatch.setattr(
        data_loader,
        "carregar_transacoes_csv",
        fail_if_csv_is_loaded,
    )

    transactions = (
        data_loader
        .carregar_transacoes()
    )

    assert transactions.empty

    assert transactions.columns.tolist() == [
        "data",
        "tipo",
        "descricao",
        "categoria",
        "valor",
        "arquivo_origem",
        "ano_mes",
    ]