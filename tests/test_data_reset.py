"""Testes da limpeza segura dos dados do usuário."""

from src.data_reset import (
    reset_user_transaction_data,
    summarize_user_transaction_data,
)


def create_file(
    file_path,
    content: str = "test",
) -> None:
    """Cria um arquivo e suas pastas para os testes."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        content,
        encoding="utf-8",
    )


def test_reset_removes_user_data_and_preserves_demo(
    tmp_path,
) -> None:
    """Remove dados reais sem tocar nos arquivos de demonstração."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = (
        tmp_path
        / "data"
        / "processed"
    )

    demo_dir = tmp_path / "data" / "demo"

    database_path = (
        tmp_path
        / "database"
        / "finantec.db"
    )

    log_path = (
        tmp_path
        / "logs"
        / "etl_transacoes.log"
    )

    manual_file = (
        raw_dir
        / "transacoes_manuais.csv"
    )

    imported_file = (
        raw_dir
        / "imported"
        / "transacoes_importadas_teste.csv"
    )

    monthly_user_file = (
        raw_dir
        / "transacoes_2026_08.csv"
    )

    raw_gitkeep = (
        raw_dir
        / ".gitkeep"
    )

    imported_gitkeep = (
        raw_dir
        / "imported"
        / ".gitkeep"
    )

    processed_file = (
        processed_dir
        / "transacoes_processadas.csv"
    )

    rejected_file = (
        processed_dir
        / "transacoes_rejeitadas.csv"
    )

    demo_file = (
        demo_dir
        / "transacoes_2026_06.csv"
    )

    create_file(manual_file)
    create_file(imported_file)
    create_file(monthly_user_file)
    create_file(raw_gitkeep, "")
    create_file(imported_gitkeep, "")
    create_file(processed_file)
    create_file(rejected_file)
    create_file(database_path)
    create_file(log_path)
    create_file(demo_file)

    result = reset_user_transaction_data(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        database_path=database_path,
        log_path=log_path,
    )

    assert not manual_file.exists()
    assert not imported_file.exists()
    assert not monthly_user_file.exists()

    assert not processed_file.exists()
    assert not rejected_file.exists()
    assert not database_path.exists()
    assert not log_path.exists()

    assert raw_gitkeep.exists()
    assert imported_gitkeep.exists()
    assert demo_file.exists()

    assert (
        result["source_files_removed"]
        == 3
    )

    assert (
        result["processed_files_removed"]
        == 2
    )

    assert (
        result["database_removed"]
        is True
    )

    assert (
        result["log_removed"]
        is True
    )


def test_reset_handles_missing_files(
    tmp_path,
) -> None:
    """Permite executar o reset quando não existem dados."""
    raw_dir = tmp_path / "data" / "raw"

    processed_dir = (
        tmp_path
        / "data"
        / "processed"
    )

    database_path = (
        tmp_path
        / "database"
        / "finantec.db"
    )

    log_path = (
        tmp_path
        / "logs"
        / "etl_transacoes.log"
    )

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    result = reset_user_transaction_data(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        database_path=database_path,
        log_path=log_path,
    )

    assert result == {
        "source_files_removed": 0,
        "processed_files_removed": 0,
        "database_removed": False,
        "log_removed": False,
    }

def test_summarize_user_transaction_data_counts_local_files(
    tmp_path,
) -> None:
    """Resume corretamente os dados locais existentes."""
    raw_dir = tmp_path / "data" / "raw"

    processed_dir = (
        tmp_path
        / "data"
        / "processed"
    )

    database_path = (
        tmp_path
        / "database"
        / "finantec.db"
    )

    log_path = (
        tmp_path
        / "logs"
        / "etl_transacoes.log"
    )

    create_file(
        raw_dir
        / "transacoes_manuais.csv"
    )

    create_file(
        raw_dir
        / "imported"
        / "transacoes_importadas_teste.csv"
    )

    create_file(
        processed_dir
        / "transacoes_processadas.csv"
    )

    create_file(
        database_path
    )

    summary = (
        summarize_user_transaction_data(
            raw_dir=raw_dir,
            processed_dir=processed_dir,
            database_path=database_path,
            log_path=log_path,
        )
    )

    assert summary == {
        "source_files": 2,
        "processed_files": 1,
        "database_exists": True,
        "log_exists": False,
    }