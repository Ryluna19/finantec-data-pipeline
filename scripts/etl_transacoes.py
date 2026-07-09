"""
Pipeline ETL de transacoes financeiras simuladas.

Etapas:
- Extract: le arquivos CSV da pasta data/raw.
- Transform: valida, limpa e padroniza os dados.
- Load: salva os dados tratados em CSV e SQLite.

O pipeline tambem gera um relatorio de linhas rejeitadas quando encontra dados
invalidos nos arquivos de entrada.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd


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

LOGGER = logging.getLogger(__name__)


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
        force=True,
    )


def validar_colunas(transacoes: pd.DataFrame, arquivo: Path) -> None:
    """
    Valida se o arquivo possui as colunas minimas esperadas.

    Se faltar alguma coluna obrigatoria, o pipeline deve parar. Nesse caso, o
    problema esta na estrutura do arquivo, nao apenas em uma linha isolada.
    """
    colunas_ausentes = [
        coluna
        for coluna in COLUNAS_OBRIGATORIAS
        if coluna not in transacoes.columns
    ]

    if colunas_ausentes:
        raise ValueError(
            f"O arquivo {arquivo.name} nao possui as colunas obrigatorias: "
            f"{', '.join(colunas_ausentes)}"
        )


def listar_arquivos_raw() -> list[Path]:
    """
    Lista os arquivos CSV de transacoes disponiveis na pasta data/raw/.
    """
    arquivos_csv = sorted(RAW_DIR.glob("transacoes_*.csv"))

    if not arquivos_csv:
        raise FileNotFoundError(
            "Nenhum arquivo transacoes_*.csv foi encontrado em data/raw/."
        )

    return arquivos_csv


def ler_transacoes_raw(arquivo: Path) -> pd.DataFrame:
    """
    Le um arquivo CSV bruto da pasta data/raw/.

    A coluna arquivo_origem permite rastrear de qual arquivo cada linha veio.
    """
    LOGGER.info("Lendo arquivo: %s", arquivo.name)

    transacoes = pd.read_csv(arquivo, encoding="utf-8-sig")
    validar_colunas(transacoes, arquivo)

    transacoes = transacoes[COLUNAS_OBRIGATORIAS].copy()
    transacoes["arquivo_origem"] = arquivo.name

    return transacoes


def ler_todas_transacoes_raw() -> pd.DataFrame:
    """
    Le e junta todos os arquivos CSV brutos encontrados em data/raw/.
    """
    arquivos_csv = listar_arquivos_raw()

    bases = [
        ler_transacoes_raw(arquivo)
        for arquivo in arquivos_csv
    ]

    return pd.concat(bases, ignore_index=True)


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

    transacoes["tipo"] = (
        transacoes["tipo"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    transacoes["descricao"] = (
        transacoes["descricao"]
        .astype("string")
        .str.strip()
    )

    transacoes["categoria"] = (
        transacoes["categoria"]
        .astype("string")
        .str.strip()
    )

    transacoes["valor"] = pd.to_numeric(
        transacoes["valor"],
        errors="coerce",
    )

    return transacoes


def campo_vazio(coluna: pd.Series) -> pd.Series:
    """
    Identifica valores vazios em colunas de texto.
    """
    return coluna.isna() | (coluna.astype("string").str.strip() == "")


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
    mascara = (
        pd.Series(mascara, index=motivos.index)
        .fillna(False)
        .astype(bool)
    )

    motivos.loc[mascara] = motivos.loc[mascara].apply(
        lambda valor_atual: motivo
        if not valor_atual
        else f"{valor_atual}; {motivo}"
    )

    return motivos


def identificar_motivos_rejeicao(transacoes: pd.DataFrame) -> pd.Series:
    """
    Identifica os motivos de rejeicao linha a linha.
    """
    motivos = pd.Series("", index=transacoes.index, dtype="object")

    tipo_vazio = campo_vazio(transacoes["tipo"])
    descricao_vazia = campo_vazio(transacoes["descricao"])
    categoria_vazia = campo_vazio(transacoes["categoria"])
    valor_invalido_ou_vazio = transacoes["valor"].isna()

    motivos = adicionar_motivo(
        motivos,
        transacoes["data"].isna(),
        "data invalida ou vazia",
    )

    motivos = adicionar_motivo(
        motivos,
        tipo_vazio,
        "tipo vazio",
    )

    motivos = adicionar_motivo(
        motivos,
        descricao_vazia,
        "descricao vazia",
    )

    motivos = adicionar_motivo(
        motivos,
        categoria_vazia,
        "categoria vazia",
    )

    motivos = adicionar_motivo(
        motivos,
        valor_invalido_ou_vazio,
        "valor invalido ou vazio",
    )

    motivos = adicionar_motivo(
        motivos,
        (~tipo_vazio) & ~transacoes["tipo"].isin(TIPOS_VALIDOS),
        "tipo invalido",
    )

    motivos = adicionar_motivo(
        motivos,
        (~valor_invalido_ou_vazio) & (transacoes["valor"] <= 0),
        "valor menor ou igual a zero",
    )

    return motivos


def separar_transacoes_por_validade(
    transacoes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separa as transacoes em validas e rejeitadas.

    As rejeitadas recebem a coluna motivo_rejeicao para facilitar auditoria e
    correcao dos arquivos de entrada.
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
    Adiciona colunas finais e ordena as transacoes validas.
    """
    transacoes = transacoes.copy()

    transacoes["ano_mes"] = (
        transacoes["data"]
        .dt.to_period("M")
        .astype(str)
    )

    return (
        transacoes.sort_values(by=["data", "tipo", "categoria"])
        .reset_index(drop=True)
    )


def transformar_transacoes(transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e padroniza os dados de transacoes.

    Linhas invalidas sao removidas da base final. O relatorio detalhado de
    rejeicoes e gerado separadamente pela funcao gerar_relatorio_rejeicoes.
    """
    transacoes_validas, rejeicoes = separar_transacoes_por_validade(transacoes)

    if not rejeicoes.empty:
        LOGGER.warning(
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

    LOGGER.info("Arquivo processado gerado: %s", ARQUIVO_SAIDA)


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

        LOGGER.info("Nenhuma linha rejeitada no pipeline.")
        return

    rejeicoes.to_csv(
        ARQUIVO_REJEICOES,
        index=False,
        encoding="utf-8-sig",
    )

    LOGGER.warning(
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

    LOGGER.info(
        "Dados carregados no SQLite: %s | tabela: %s",
        ARQUIVO_BANCO,
        TABELA_TRANSACOES,
    )


def executar_etl() -> pd.DataFrame:
    """
    Executa o pipeline completo de transacoes.
    """
    configurar_logs()

    LOGGER.info("Iniciando pipeline ETL de transacoes.")

    transacoes_brutas = ler_todas_transacoes_raw()

    transacoes_validas, rejeicoes = separar_transacoes_por_validade(
        transacoes_brutas
    )

    if not rejeicoes.empty:
        LOGGER.warning(
            "%s linha(s) foram removidas por dados invalidos.",
            len(rejeicoes),
        )

    transacoes_processadas = finalizar_transacoes_validas(transacoes_validas)

    salvar_csv_processado(transacoes_processadas)
    salvar_relatorio_rejeicoes(rejeicoes)
    salvar_em_sqlite(transacoes_processadas)

    LOGGER.info(
        "Pipeline concluido. %s transacao(oes) processada(s).",
        len(transacoes_processadas),
    )

    return transacoes_processadas


if __name__ == "__main__":
    executar_etl()