"""
Executor principal do FinanTec Data Pipeline.

Este arquivo funciona como uma entrada simples para o projeto, parecido com a
ideia de scripts do npm. Em vez de digitar comandos longos, é possível usar:

- python main.py
- python main.py app
- python main.py etl
- python main.py test
- python main.py dev
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
APP_PATH = PROJECT_ROOT / "src" / "app.py"
ETL_PATH = PROJECT_ROOT / "scripts" / "etl_transacoes.py"

Comando = Callable[[], int]


def executar_comando(comando: list[str]) -> int:
    """
    Executa um comando usando o mesmo Python do ambiente atual.

    Usar sys.executable ajuda a garantir que o comando rode dentro do ambiente
    virtual ativo, quando ele estiver sendo usado.
    """
    processo = subprocess.run(
        comando,
        cwd=PROJECT_ROOT,
        check=False,
    )

    return processo.returncode


def executar_app() -> int:
    """
    Inicia o dashboard Streamlit.
    """
    return executar_comando(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(APP_PATH),
        ]
    )


def executar_etl() -> int:
    """Executa o pipeline ETL como módulo Python."""
    return executar_comando(
        [
            sys.executable,
            "-m",
            "scripts.etl_transacoes",
        ]
    )


def executar_testes() -> int:
    """
    Executa os testes automatizados com pytest.
    """
    return executar_comando(
        [
            sys.executable,
            "-m",
            "pytest",
        ]
    )


def executar_fluxo_dev() -> int:
    """
    Executa o ETL e, se tudo der certo, inicia o dashboard.
    """
    codigo_etl = executar_etl()

    if codigo_etl != 0:
        return codigo_etl

    return executar_app()


def exibir_ajuda() -> int:
    """
    Exibe os comandos disponíveis.
    """
    print(
        """
Uso:
  python main.py          Inicia o dashboard Streamlit
  python main.py app      Inicia o dashboard Streamlit
  python main.py etl      Executa o pipeline ETL
  python main.py test     Executa os testes automatizados
  python main.py tests    Executa os testes automatizados
  python main.py dev      Executa o ETL e inicia o dashboard
  python main.py help     Mostra esta ajuda
""".strip()
    )

    return 0


def obter_comandos() -> dict[str, Comando]:
    """
    Retorna os comandos disponíveis para execução.
    """
    return {
        "app": executar_app,
        "etl": executar_etl,
        "test": executar_testes,
        "tests": executar_testes,
        "dev": executar_fluxo_dev,
        "help": exibir_ajuda,
        "-h": exibir_ajuda,
        "--help": exibir_ajuda,
    }


def main(argumentos: list[str] | None = None) -> int:
    """
    Interpreta o comando recebido pelo terminal e executa a ação correspondente.
    """
    argumentos = argumentos if argumentos is not None else sys.argv[1:]
    comando = argumentos[0].lower() if argumentos else "app"

    comandos = obter_comandos()

    if comando not in comandos:
        print(f"Comando desconhecido: {comando}")
        exibir_ajuda()
        return 1

    return comandos[comando]()


if __name__ == "__main__":
    raise SystemExit(main())