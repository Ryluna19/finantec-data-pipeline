from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

"""
Pipeline ETL de transacoes financeiras simuladas.

Etapas:
- Extract: le arquivos CSV da pasta data/raw.
- Transform: valida, limpa e padroniza os dados.
- Load: salva os dados tratados em CSV e SQLite.

O pipeline tambem gera um relatorio de linhas rejeitadas quando encontra
dados invalidos.
"""


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"
LOGS_DIR = PROJECT_ROOT / "logs"

ARQUIVO_SAIDA = PROCESSED_DIR / "transacoes_processadas.csv"
ARQUIVO_REJEICOES = PROCESSED_DIR / "transacoes_rejeitadas.csv"
ARQUIVO_BANCO = DATABASE_DIR / "finantec.db"
ARQUIVO_LOG = LOGS_DIR / "etl_transacoes.log"

TABELA_TRANSACOES = "transacoes_processadas"

COLUNAS_OBRIGATORIAS = ["data", "tipo", "descricao", "categoria", "valor"]
TIPOS_VALIDOS = {"receita", "despesa"}


def configurar_logs() -> None:
    """
    Configura logs no terminal e em arquivo.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(ARQUIVO_LOG, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def validar_colunas(transacoes: pd.DataFrame, arquivo: Path) -> None:
    """
    Valida se o arquivo possui as colunas minimas esperadas.

    Se faltar alguma coluna obrigatoria, o pipeline deve parar. Nesse caso,
    o problema esta na estrutura do arquivo, nao apenas em uma linha isolada.
    """
    colunas_ausentes = [
        coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in transacoes.columns
    ]

    if colunas_ausentes:
        raise ValueError(
            f"O arquivo {arquivo.name} nao possui as colunas obrigatorias: "
            f"{', '.join(colunas_ausentes)}"
        )


def ler_transacoes_raw(arquivo: Path) -> pd.DataFrame:
    """
    Le um arquivo CSV bruto da pasta data/raw/.

    A coluna arquivo_origem permite rastrear de qual arquivo cada linha veio.
    """
    logging.info("Lendo arquivo: %s", arquivo.name)

    transacoes = pd.read_csv(arquivo, encoding="utf-8-sig")
    validar_colunas(transacoes, arquivo)

    transacoes = transacoes[COLUNAS_OBRIGATORIAS].copy()
    transacoes["arquivo_origem"] = arquivo.name

    return transacoes


def preparar_transacoes(transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica conversoes basicas antes da validacao final.

    Esta etapa nao remove linhas. Ela apenas padroniza os dados para que seja
    possivel identificar claramente quais linhas sao validas ou rejeitadas.
    """
    transacoes = transacoes.copy()

    transacoes["data"] = pd.to_datetime(
        transacoes["data"],
        errors="coerce",
    )

    transacoes["tipo"] = transacoes["tipo"].astype("string").str.strip().str.lower()

    transacoes["descricao"] = transacoes["descricao"].astype("string").str.strip()

    transacoes["categoria"] = transacoes["categoria"].astype("string").str.strip()

    transacoes["valor"] = pd.to_numeric(
        transacoes["valor"],
        errors="coerce",
    )

    return transacoes


def adicionar_motivo(
    motivos: pd.Series,
    mascara: pd.Series,
    motivo: str,
) -> pd.Series:
    """
    Adiciona um motivo de rejeicao a todas as linhas que atendem a mascara.

    Uma linha pode ter mais de um problema. Por isso, os motivos sao
    concatenados em uma unica coluna.
    """
    mascara = pd.Series(mascara, index=motivos.index).fillna(False)

    motivos.loc[mascara] = motivos.loc[mascara].apply(
        lambda valor_atual: motivo if not valor_atual else f"{valor_atual}; {motivo}"
    )

    return motivos


def identificar_motivos_rejeicao(transacoes: pd.DataFrame) -> pd.Series:
    """
    Identifica os motivos de rejeicao linha a linha.
    """
    motivos = pd.Series("", index=transacoes.index, dtype="object")

    motivos = adicionar_motivo(
        motivos,
        transacoes["data"].isna(),
        "data invalida ou vazia",
    )

    motivos = adicionar_motivo(
        motivos,
        transacoes["tipo"].isna() | (transacoes["tipo"] == ""),
        "tipo vazio",
    )

    motivos = adicionar_motivo(
        motivos,
        transacoes["descricao"].isna() | (transacoes["descricao"] == ""),
        "descricao vazia",
    )

    motivos = adicionar_motivo(
        motivos,
        transacoes["categoria"].isna() | (transacoes["categoria"] == ""),
        "categoria vazia",
    )

    motivos = adicionar_motivo(
        motivos,
        transacoes["valor"].isna(),
        "valor invalido ou vazio",
    )

    tipo_preenchido = ~(transacoes["tipo"].isna() | (transacoes["tipo"] == ""))

    motivos = adicionar_motivo(
        motivos,
        tipo_preenchido & ~transacoes["tipo"].isin(TIPOS_VALIDOS),
        "tipo invalido",
    )

    valor_preenchido = ~transacoes["valor"].isna()

    motivos = adicionar_motivo(
        motivos,
        valor_preenchido & (transacoes["valor"] <= 0),
        "valor menor ou igual a zero",
    )

    return motivos


def separar_transacoes_por_validade(
    transacoes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepara os dados e separa as transacoes entre validas e rejeitadas.

    As rejeicoes recebem uma coluna motivo_rejeicao para facilitar auditoria
    e exibicao no dashboard.
    """
    transacoes_preparadas = preparar_transacoes(transacoes)
    motivos_rejeicao = identificar_motivos_rejeicao(transacoes_preparadas)

    linhas_validas = motivos_rejeicao == ""
    linhas_rejeitadas = ~linhas_validas

    transacoes_validas = transacoes_preparadas.loc[linhas_validas].copy()
    rejeicoes = transacoes_preparadas.loc[linhas_rejeitadas].copy()

    if not rejeicoes.empty:
        rejeicoes["motivo_rejeicao"] = motivos_rejeicao.loc[linhas_rejeitadas]

    return transacoes_validas, rejeicoes


def finalizar_transacoes_validas(transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Finaliza as transacoes validas criando ano_mes e ordenando os dados.
    """
    transacoes_finalizadas = transacoes.copy()

    transacoes_finalizadas["ano_mes"] = (
        transacoes_finalizadas["data"].dt.to_period("M").astype(str)
    )

    return transacoes_finalizadas.sort_values(
        by=["data", "tipo", "categoria"]
    ).reset_index(drop=True)


def transformar_transacoes(transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa, valida e padroniza os dados de transacoes.

    Linhas invalidas sao removidas da base final. O relatorio detalhado de
    rejeicoes e gerado separadamente pela funcao gerar_relatorio_rejeicoes.
    """
    transacoes_validas, rejeicoes = separar_transacoes_por_validade(transacoes)

    if not rejeicoes.empty:
        logging.warning(
            "%s linha(s) foram removidas por dados invalidos.",
            len(rejeicoes),
        )

    return finalizar_transacoes_validas(transacoes_validas)


def gerar_relatorio_rejeicoes(transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Gera um DataFrame com as linhas rejeitadas e o motivo da rejeicao.
    """
    _, rejeicoes = separar_transacoes_por_validade(transacoes)

    return rejeicoes


def salvar_csv_processado(transacoes: pd.DataFrame) -> None:
    """
    Salva as transacoes tratadas em data/processed/.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    transacoes.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig",
    )

    logging.info("Arquivo processado gerado: %s", ARQUIVO_SAIDA)


def salvar_relatorio_rejeicoes(rejeicoes: pd.DataFrame) -> None:
    """
    Salva o relatorio de linhas rejeitadas.

    Se nao houver rejeicoes, remove um relatorio antigo para evitar leitura de
    resultado desatualizado.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if rejeicoes.empty:
        if ARQUIVO_REJEICOES.exists():
            ARQUIVO_REJEICOES.unlink()

        logging.info("Nenhuma linha rejeitada no pipeline.")
        return

    rejeicoes.to_csv(
        ARQUIVO_REJEICOES,
        index=False,
        encoding="utf-8-sig",
    )

    logging.warning(
        "Relatorio de rejeicoes gerado com %s linha(s): %s",
        len(rejeicoes),
        ARQUIVO_REJEICOES,
    )


def salvar_em_sqlite(transacoes: pd.DataFrame) -> None:
    """
    Carrega as transacoes tratadas em uma base SQLite local.

    SQLite foi escolhido para esta etapa por ser simples, gratuito e local.
    """
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(ARQUIVO_BANCO) as conexao:
        transacoes.to_sql(
            TABELA_TRANSACOES,
            conexao,
            if_exists="replace",
            index=False,
        )

    logging.info(
        "Dados carregados no SQLite: %s | tabela: %s",
        ARQUIVO_BANCO,
        TABELA_TRANSACOES,
    )


def executar_etl() -> pd.DataFrame:
    """
    Executa o pipeline completo de transacoes.
    """
    configurar_logs()

    logging.info("Iniciando pipeline ETL de transacoes.")

    arquivos_csv = sorted(RAW_DIR.glob("transacoes_*.csv"))

    if not arquivos_csv:
        raise FileNotFoundError(
            "Nenhum arquivo transacoes_*.csv foi encontrado em data/raw/."
        )

    bases = [ler_transacoes_raw(arquivo) for arquivo in arquivos_csv]

    transacoes_brutas = pd.concat(bases, ignore_index=True)

    transacoes_processadas = transformar_transacoes(transacoes_brutas)
    rejeicoes = gerar_relatorio_rejeicoes(transacoes_brutas)

    salvar_csv_processado(transacoes_processadas)
    salvar_relatorio_rejeicoes(rejeicoes)
    salvar_em_sqlite(transacoes_processadas)

    logging.info(
        "Pipeline concluido. %s transacao(oes) processada(s).",
        len(transacoes_processadas),
    )

    return transacoes_processadas


def executar_etl_com_resumo() -> dict[str, int | bool]:
    """
    Executa o ETL e retorna um resumo simples para uso na interface.
    """
    transacoes_processadas = executar_etl()

    quantidade_rejeicoes = 0

    if ARQUIVO_REJEICOES.exists():
        rejeicoes = pd.read_csv(ARQUIVO_REJEICOES, encoding="utf-8-sig")
        quantidade_rejeicoes = len(rejeicoes)

    return {
        "sucesso": True,
        "transacoes_processadas": len(transacoes_processadas),
        "transacoes_rejeitadas": quantidade_rejeicoes,
    }

if __name__ == "__main__":
    executar_etl()
