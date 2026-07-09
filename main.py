from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
APP_PATH = PROJECT_ROOT / "src" / "app.py"
ETL_PATH = PROJECT_ROOT / "scripts" / "etl_transacoes.py"


def executar_comando(comando: list[str]) -> int:
    """
    Executa um comando usando o mesmo Python do ambiente atual.
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
    """
    Executa o pipeline ETL.
    """
    return executar_comando(
        [
            sys.executable,
            str(ETL_PATH),
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


def executar_fluxo_completo() -> int:
    """
    Executa o ETL e, se tudo der certo, inicia o dashboard.
    """
    codigo_etl = executar_etl()

    if codigo_etl != 0:
        return codigo_etl

    return executar_app()


def exibir_ajuda() -> None:
    print(
        """
Uso:
  python main.py          Inicia o dashboard Streamlit
  python main.py app      Inicia o dashboard Streamlit
  python main.py etl      Executa o pipeline ETL
  python main.py test     Executa os testes automatizados
  python main.py dev      Executa o ETL e inicia o dashboard
  python main.py help     Mostra esta ajuda
""".strip()
    )


def main() -> int:
    comando = sys.argv[1].lower() if len(sys.argv) > 1 else "app"

    comandos = {
        "app": executar_app,
        "etl": executar_etl,
        "test": executar_testes,
        "tests": executar_testes,
        "dev": executar_fluxo_completo,
        "help": lambda: (exibir_ajuda() or 0),
        "-h": lambda: (exibir_ajuda() or 0),
        "--help": lambda: (exibir_ajuda() or 0),
    }

    if comando not in comandos:
        print(f"Comando desconhecido: {comando}")
        exibir_ajuda()
        return 1

    return comandos[comando]()


if __name__ == "__main__":
    raise SystemExit(main())