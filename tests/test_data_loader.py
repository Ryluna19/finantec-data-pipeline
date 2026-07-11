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