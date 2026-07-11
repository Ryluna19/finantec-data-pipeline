"""Testes da seleção de fontes do pipeline ETL."""

from scripts import etl_transacoes


def create_csv_file(
    file_path,
) -> None:
    """Cria um CSV mínimo seguindo o contrato."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        (
            "data,tipo,descricao,categoria,valor\n"
            "2026-07-10,despesa,Teste,Lazer,10.00\n"
        ),
        encoding="utf-8",
    )


def test_find_transaction_files_uses_raw_by_default(
    monkeypatch,
    tmp_path,
) -> None:
    """Usa somente dados reais no modo padrão."""
    raw_dir = tmp_path / "raw"
    demo_dir = tmp_path / "demo"

    raw_file = (
        raw_dir
        / "transacoes_reais.csv"
    )

    demo_file = (
        demo_dir
        / "transacoes_demo.csv"
    )

    create_csv_file(raw_file)
    create_csv_file(demo_file)

    monkeypatch.setattr(
        etl_transacoes,
        "RAW_DIR",
        raw_dir,
    )

    monkeypatch.setattr(
        etl_transacoes,
        "DEMO_DIR",
        demo_dir,
    )

    files = (
        etl_transacoes
        .find_transaction_files()
    )

    assert files == [raw_file]
    assert demo_file not in files


def test_find_transaction_files_uses_demo_when_requested(
    monkeypatch,
    tmp_path,
) -> None:
    """Usa somente dados simulados no modo de demonstração."""
    raw_dir = tmp_path / "raw"
    demo_dir = tmp_path / "demo"

    raw_file = (
        raw_dir
        / "transacoes_reais.csv"
    )

    demo_file = (
        demo_dir
        / "transacoes_demo.csv"
    )

    create_csv_file(raw_file)
    create_csv_file(demo_file)

    monkeypatch.setattr(
        etl_transacoes,
        "RAW_DIR",
        raw_dir,
    )

    monkeypatch.setattr(
        etl_transacoes,
        "DEMO_DIR",
        demo_dir,
    )

    files = (
        etl_transacoes
        .find_transaction_files(
            use_demo_data=True
        )
    )

    assert files == [demo_file]
    assert raw_file not in files


def test_real_mode_does_not_fallback_to_demo(
    monkeypatch,
    tmp_path,
) -> None:
    """Impede que dados fictícios apareçam automaticamente."""
    raw_dir = tmp_path / "raw"
    demo_dir = tmp_path / "demo"

    demo_file = (
        demo_dir
        / "transacoes_demo.csv"
    )

    create_csv_file(demo_file)

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    monkeypatch.setattr(
        etl_transacoes,
        "RAW_DIR",
        raw_dir,
    )

    monkeypatch.setattr(
        etl_transacoes,
        "DEMO_DIR",
        demo_dir,
    )

    files = (
        etl_transacoes
        .find_transaction_files()
    )

    assert files == []