"""Testes da limpeza segura dos dados do usuário."""

from __future__ import annotations

import sqlite3

from src.data_reset import (
    count_user_transaction_rows,
    reset_user_transaction_data,
    summarize_user_transaction_data,
)
from src.user_context import (
    LOCAL_USER_ID,
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


def create_test_database(
    database_path,
) -> None:
    """Cria um banco com transações e dados que devem ser preservados."""
    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.executescript(
            """
            CREATE TABLE transacoes_processadas (
                transaction_id TEXT,
                descricao TEXT,
                user_id TEXT,
                data_mode TEXT
            );

            INSERT INTO transacoes_processadas (
                transaction_id,
                descricao,
                user_id,
                data_mode
            )
            VALUES
                (
                    'transaction-user-1',
                    'Mercado',
                    'local-user',
                    'user'
                ),
                (
                    'transaction-user-2',
                    'Transporte',
                    'local-user',
                    'user'
                ),
                (
                    'transaction-demo',
                    'Transação simulada',
                    'local-user',
                    'demo'
                ),
                (
                    'transaction-other-user',
                    'Outro usuário',
                    'other-user',
                    'user'
                );

            CREATE TABLE user_profiles (
                user_id TEXT PRIMARY KEY,
                name TEXT
            );

            INSERT INTO user_profiles (
                user_id,
                name
            )
            VALUES (
                'local-user',
                'Marina'
            );

            CREATE TABLE financial_goals (
                goal_id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT
            );

            INSERT INTO financial_goals (
                goal_id,
                user_id,
                name
            )
            VALUES (
                'goal-1',
                'local-user',
                'Reserva'
            );

            CREATE TABLE chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                content TEXT
            );

            INSERT INTO chat_messages (
                user_id,
                content
            )
            VALUES (
                'local-user',
                'Mensagem preservada'
            );
            """
        )


def count_rows(
    database_path,
    table_name: str,
    where_clause: str = "",
    params: tuple = (),
) -> int:
    """Conta linhas de uma tabela durante os testes."""
    with sqlite3.connect(
        database_path
    ) as connection:
        row = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {table_name}
            {where_clause}
            """,
            params,
        ).fetchone()

    return int(
        row[0]
    )


def test_reset_removes_only_current_user_transactions(
    tmp_path,
) -> None:
    """Remove dados reais sem apagar banco, perfil, metas ou chat."""
    raw_dir = (
        tmp_path
        / "data"
        / "raw"
    )

    processed_dir = (
        tmp_path
        / "data"
        / "processed"
    )

    demo_dir = (
        tmp_path
        / "data"
        / "demo"
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

    create_file(
        manual_file
    )

    create_file(
        imported_file
    )

    create_file(
        monthly_user_file
    )

    create_file(
        raw_gitkeep,
        "",
    )

    create_file(
        imported_gitkeep,
        "",
    )

    create_file(
        processed_file
    )

    create_file(
        rejected_file
    )

    create_file(
        log_path
    )

    create_file(
        demo_file
    )

    create_test_database(
        database_path
    )

    result = (
        reset_user_transaction_data(
            raw_dir=raw_dir,
            processed_dir=processed_dir,
            database_path=database_path,
            log_path=log_path,
            user_id=LOCAL_USER_ID,
        )
    )

    assert not manual_file.exists()
    assert not imported_file.exists()
    assert not monthly_user_file.exists()

    assert not processed_file.exists()
    assert not rejected_file.exists()
    assert not log_path.exists()

    assert raw_gitkeep.exists()
    assert imported_gitkeep.exists()
    assert demo_file.exists()

    assert database_path.exists()

    assert (
        count_rows(
            database_path,
            "transacoes_processadas",
            (
                "WHERE user_id = ? "
                "AND data_mode = ?"
            ),
            (
                LOCAL_USER_ID,
                "user",
            ),
        )
        == 0
    )

    assert (
        count_rows(
            database_path,
            "transacoes_processadas",
            (
                "WHERE user_id = ? "
                "AND data_mode = ?"
            ),
            (
                LOCAL_USER_ID,
                "demo",
            ),
        )
        == 1
    )

    assert (
        count_rows(
            database_path,
            "transacoes_processadas",
            (
                "WHERE user_id = ? "
                "AND data_mode = ?"
            ),
            (
                "other-user",
                "user",
            ),
        )
        == 1
    )

    assert (
        count_rows(
            database_path,
            "user_profiles",
        )
        == 1
    )

    assert (
        count_rows(
            database_path,
            "financial_goals",
        )
        == 1
    )

    assert (
        count_rows(
            database_path,
            "chat_messages",
        )
        == 1
    )

    assert result == {
        "source_files_removed": 3,
        "processed_files_removed": 2,
        "transaction_rows_removed": 2,
        "database_preserved": True,
        "log_removed": True,
    }


def test_reset_handles_missing_files(
    tmp_path,
) -> None:
    """Permite executar o reset quando não existem transações."""
    raw_dir = (
        tmp_path
        / "data"
        / "raw"
    )

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

    result = (
        reset_user_transaction_data(
            raw_dir=raw_dir,
            processed_dir=processed_dir,
            database_path=database_path,
            log_path=log_path,
            user_id=LOCAL_USER_ID,
        )
    )

    assert result == {
        "source_files_removed": 0,
        "processed_files_removed": 0,
        "transaction_rows_removed": 0,
        "database_preserved": False,
        "log_removed": False,
    }


def test_summarize_user_transaction_data_counts_local_data(
    tmp_path,
) -> None:
    """Resume corretamente arquivos e transações do usuário."""
    raw_dir = (
        tmp_path
        / "data"
        / "raw"
    )

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

    create_test_database(
        database_path
    )

    summary = (
        summarize_user_transaction_data(
            raw_dir=raw_dir,
            processed_dir=processed_dir,
            database_path=database_path,
            log_path=log_path,
            user_id=LOCAL_USER_ID,
        )
    )

    assert summary == {
        "source_files": 2,
        "processed_files": 1,
        "transaction_rows": 2,
        "database_exists": True,
        "log_exists": False,
    }


def test_count_user_transaction_rows_isolated_by_user(
    tmp_path,
) -> None:
    """Conta somente as transações reais do usuário informado."""
    database_path = (
        tmp_path
        / "database"
        / "finantec.db"
    )

    create_test_database(
        database_path
    )

    assert (
        count_user_transaction_rows(
            database_path=database_path,
            user_id=LOCAL_USER_ID,
        )
        == 2
    )

    assert (
        count_user_transaction_rows(
            database_path=database_path,
            user_id="other-user",
        )
        == 1
    )