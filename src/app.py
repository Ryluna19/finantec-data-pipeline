"""Dashboard Streamlit do FinanTec."""

from __future__ import annotations


from typing import Any

import altair as alt
import pandas as pd
import streamlit as st


from agent import gerar_resposta_finantec
from analytics import (
    calcular_gastos_por_categoria,
    calcular_meta_mensal,
    calcular_resumo_financeiro,
    calcular_simulacoes_de_metas,
    formatar_moeda,
)
from data_loader import (
    carregar_conceitos_financeiros,
    carregar_historico_atendimento,
    carregar_perfil_usuario,
    carregar_produtos_financeiros,
    carregar_rejeicoes,
    carregar_transacoes,
)

from ui_components import (
    COR_DESPESA,
    COR_RECEITA,
    MESES_PTBR,
    ROTULOS_TIPO,
    aplicar_estilo_visual,
    exibir_aviso_visual,
    exibir_cabecalho,
    exibir_diagnostico_financeiro,
    exibir_resumo_financeiro,
)

from prompts import montar_contexto
from transaction_editor import exibir_editor_transacoes_manuais


st.set_page_config(
    page_title="FinanTec",
    page_icon="💰",
    layout="wide",
)

def carregar_dados() -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
    dict[str, Any],
    pd.DataFrame,
]:
    """Carrega e mantém em cache os dados usados pela interface."""
    return (
        carregar_perfil_usuario(),
        carregar_transacoes(),
        carregar_historico_atendimento(),
        carregar_conceitos_financeiros(),
        carregar_produtos_financeiros(),
        carregar_rejeicoes(),
    )


def selecionar_periodo(
    transacoes: pd.DataFrame,
) -> tuple[int, str, pd.DataFrame]:
    """Filtra as transações pelo ano e mês escolhidos na barra lateral."""
    if transacoes.empty:
        st.error("Não há transações disponíveis.")
        st.stop()

    dados = transacoes.copy()
    dados["data"] = pd.to_datetime(dados["data"], errors="coerce")
    dados["ano"] = dados["data"].dt.year
    dados["mes"] = dados["data"].dt.month

    anos = sorted(dados["ano"].dropna().astype(int).unique().tolist())

    if not anos:
        st.error("Nenhum ano válido foi encontrado na base.")
        st.stop()

    st.sidebar.title("Filtros")

    ano = st.sidebar.selectbox(
        "Ano",
        anos,
        index=len(anos) - 1,
        key="filtro_ano",
    )

    meses = sorted(
        dados.loc[dados["ano"] == ano, "mes"].dropna().astype(int).unique().tolist()
    )

    mes = st.sidebar.selectbox(
        "Mês",
        [0, *meses],
        format_func=lambda valor: ("Todos" if valor == 0 else MESES_PTBR[valor]),
        key="filtro_mes",
    )

    filtro_ano = dados["ano"] == ano

    if mes == 0:
        return mes, str(ano), dados.loc[filtro_ano].copy()

    filtro_mes = dados["mes"] == mes
    rotulo = f"{MESES_PTBR[mes]}/{ano}"

    return mes, rotulo, dados.loc[filtro_ano & filtro_mes].copy()


def criar_mensagem_inicial(periodo: str) -> list[dict[str, str]]:
    """Cria a mensagem inicial do chat para o período selecionado."""
    return [
        {
            "role": "assistant",
            "content": (
                f"Olá! Sou o FinanTec. Estou analisando o período "
                f"{periodo}. Posso ajudar você a entender gastos, "
                "metas e conceitos financeiros básicos."
            ),
        }
    ]


def obter_mensagens_do_periodo(
    periodo: str,
) -> list[dict[str, str]]:
    """Mantém um histórico de conversa independente para cada período."""
    mensagens_por_periodo = st.session_state.setdefault(
        "mensagens_por_periodo",
        {},
    )

    if periodo not in mensagens_por_periodo:
        mensagens_por_periodo[periodo] = criar_mensagem_inicial(periodo)

    return mensagens_por_periodo[periodo]


def montar_contexto_do_periodo(
    periodo: str,
    perfil_usuario: dict[str, Any],
    resumo: dict[str, Any],
    gastos_por_categoria: pd.Series,
    simulacoes_metas: list[dict[str, Any]],
    historico_atendimento: pd.DataFrame,
    conceitos_financeiros: dict[str, Any],
    produtos_financeiros: dict[str, Any],
) -> str:
    """Monta o contexto enviado à IA com os dados do período."""
    contexto = montar_contexto(
        perfil_usuario=perfil_usuario,
        resumo_financeiro=resumo,
        gastos_por_categoria=gastos_por_categoria,
        simulacoes_metas=simulacoes_metas,
        historico_atendimento=historico_atendimento,
        conceitos_financeiros=conceitos_financeiros,
        produtos_financeiros=produtos_financeiros,
    )

    return (f"PERÍODO ANALISADO:\n" f"{periodo}\n\n" f"{contexto}").strip()


def calcular_percentual(parte: float, total: float) -> float:
    """Calcula um percentual sem dividir por zero."""
    return (parte / total) * 100 if total > 0 else 0.0


def preparar_transacoes_para_exibicao(
    transacoes: pd.DataFrame,
) -> pd.DataFrame:
    """Formata as transações para as tabelas da interface."""
    tabela = transacoes.copy()

    tabela["data"] = pd.to_datetime(
        tabela["data"],
        errors="coerce",
    ).dt.strftime("%d/%m/%Y")

    tipos_originais = tabela["tipo"].copy()

    tabela["tipo"] = (
        tabela["tipo"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(ROTULOS_TIPO)
        .fillna(tipos_originais)
    )

    tabela["descricao"] = tabela["descricao"].astype(str).str.strip()

    tabela["categoria"] = tabela["categoria"].astype(str).str.strip()

    tabela["valor"] = tabela["valor"].map(formatar_moeda)

    tabela = tabela.rename(
        columns={
            "data": "Data",
            "tipo": "Tipo",
            "descricao": "Descrição",
            "categoria": "Categoria",
            "valor": "Valor",
        }
    )

    return tabela[
        [
            "Data",
            "Tipo",
            "Descrição",
            "Categoria",
            "Valor",
        ]
    ]


def criar_resumo_mensal(
    transacoes: pd.DataFrame,
) -> pd.DataFrame:
    """Agrupa receitas e despesas por mês."""
    dados = transacoes.copy()
    dados["mes_num"] = dados["data"].dt.month

    resumo = (
        dados.groupby(["mes_num", "tipo"])["valor"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("mes_num")
    )

    for coluna in ("receita", "despesa"):
        if coluna not in resumo.columns:
            resumo[coluna] = 0.0

    resumo["Mês"] = resumo["mes_num"].map(MESES_PTBR)

    return resumo

def exibir_indicadores_complementares(
    transacoes: pd.DataFrame,
    resumo: dict[str, Any],
) -> None:
    """Exibe indicadores auxiliares do período."""
    despesas = transacoes.loc[transacoes["tipo"] == "despesa"]

    gasto_medio = despesas["valor"].mean() if not despesas.empty else 0.0

    percentual_reserva = calcular_percentual(
        resumo["valor_guardado_reserva"],
        resumo["receitas_totais"],
    )

    coluna_total, coluna_media, coluna_reserva = st.columns(3)

    coluna_total.metric(
        "Transações",
        len(transacoes),
    )

    coluna_media.metric(
        "Gasto médio",
        formatar_moeda(gasto_medio),
    )

    coluna_reserva.metric(
        "Renda reservada",
        f"{percentual_reserva:.1f}%",
    )


def exibir_gastos_por_categoria(
    gastos_por_categoria: pd.Series,
    resumo: dict[str, Any],
) -> None:
    """Exibe um gráfico horizontal dos gastos por categoria."""
    st.subheader("Gastos por categoria")

    if gastos_por_categoria.empty:
        st.info("Não há gastos de consumo para exibir neste período.")
        return

    tabela = gastos_por_categoria.rename("Valor").reset_index()

    tabela.columns = ["Categoria", "Valor"]

    grafico = (
        alt.Chart(tabela)
        .mark_bar(
            color=COR_DESPESA,
            cornerRadiusEnd=4,
        )
        .encode(
            x=alt.X(
                "Valor:Q",
                title="Valor",
                axis=alt.Axis(format=",.0f"),
            ),
            y=alt.Y(
                "Categoria:N",
                sort="-x",
                title=None,
            ),
            tooltip=[
                alt.Tooltip(
                    "Categoria:N",
                    title="Categoria",
                ),
                alt.Tooltip(
                    "Valor:Q",
                    title="Valor",
                    format=",.2f",
                ),
            ],
        )
        .properties(
            height=max(
                260,
                len(tabela) * 34,
            )
        )
    )

    st.altair_chart(
        grafico,
        use_container_width=True,
    )

    if resumo["maior_categoria"]:
        exibir_aviso_visual(
            "Maior categoria do período: "
            f"{resumo['maior_categoria']} "
            f"({formatar_moeda(resumo['maior_gasto'])})."
        )


def exibir_ranking_de_categorias(
    gastos_por_categoria: pd.Series,
) -> None:
    """Exibe o ranking das categorias com maior consumo."""
    st.subheader("Ranking de categorias")

    if gastos_por_categoria.empty:
        st.info("Não há categorias de consumo para listar neste período.")
        return

    ranking = (
        gastos_por_categoria.sort_values(ascending=False).rename("Valor").reset_index()
    )

    ranking.columns = ["Categoria", "Valor"]

    ranking.insert(
        0,
        "Posição",
        range(1, len(ranking) + 1),
    )

    ranking["Valor"] = ranking["Valor"].map(formatar_moeda)

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True,
    )


def exibir_evolucao_mensal(
    transacoes: pd.DataFrame,
) -> None:
    """Compara receitas e despesas mês a mês."""
    if transacoes.empty:
        return

    resumo = criar_resumo_mensal(transacoes)

    dados_grafico = resumo.melt(
        id_vars=["Mês", "mes_num"],
        value_vars=["receita", "despesa"],
        var_name="Tipo",
        value_name="Valor",
    )

    dados_grafico["Tipo"] = dados_grafico["Tipo"].map(
        {
            "receita": "Receitas",
            "despesa": "Despesas",
        }
    )

    ordem_meses = resumo["Mês"].tolist()

    st.subheader("Evolução mensal")

    grafico = (
        alt.Chart(dados_grafico)
        .mark_line(
            point=True,
            strokeWidth=3,
        )
        .encode(
            x=alt.X(
                "Mês:N",
                sort=ordem_meses,
                title=None,
            ),
            y=alt.Y(
                "Valor:Q",
                title="Valor",
                axis=alt.Axis(format=",.0f"),
            ),
            color=alt.Color(
                "Tipo:N",
                scale=alt.Scale(
                    domain=[
                        "Receitas",
                        "Despesas",
                    ],
                    range=[
                        COR_RECEITA,
                        COR_DESPESA,
                    ],
                ),
                title=None,
            ),
            tooltip=[
                alt.Tooltip(
                    "Mês:N",
                    title="Mês",
                ),
                alt.Tooltip(
                    "Tipo:N",
                    title="Tipo",
                ),
                alt.Tooltip(
                    "Valor:Q",
                    title="Valor",
                    format=",.2f",
                ),
            ],
        )
        .properties(height=320)
    )

    st.altair_chart(
        grafico,
        use_container_width=True,
    )

    tabela = resumo[
        [
            "Mês",
            "receita",
            "despesa",
        ]
    ].copy()

    tabela.columns = [
        "Mês",
        "Receitas",
        "Despesas",
    ]

    tabela["Receitas"] = tabela["Receitas"].map(formatar_moeda)

    tabela["Despesas"] = tabela["Despesas"].map(formatar_moeda)

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
    )


def exibir_ultimas_transacoes(
    transacoes: pd.DataFrame,
    limite: int = 5,
) -> None:
    """Exibe as transações mais recentes do período."""
    st.subheader("Últimas transações")

    if transacoes.empty:
        st.info("Nenhuma transação encontrada para o período selecionado.")
        return

    ultimas = transacoes.sort_values(
        by="data",
        ascending=False,
    ).head(limite)

    tabela = preparar_transacoes_para_exibicao(ultimas)

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
    )


def exibir_validacao_dos_dados(
    quantidade_validas: int,
    rejeicoes: pd.DataFrame,
) -> None:
    """Exibe a situação dos dados processados pelo ETL."""
    st.subheader("Validação dos dados")

    coluna_validas, coluna_rejeitadas = st.columns(2)

    coluna_validas.metric(
        "Válidas no período",
        quantidade_validas,
    )

    coluna_rejeitadas.metric(
        "Rejeitadas no último ETL",
        len(rejeicoes),
    )

    if rejeicoes.empty:
        st.success("Nenhuma transação foi rejeitada " "no último processamento.")
        return

    st.warning(
        "Existem transações rejeitadas. " "Consulte a tabela para conferir os motivos."
    )

    with st.expander("Ver transações rejeitadas"):
        st.dataframe(
            rejeicoes,
            use_container_width=True,
            hide_index=True,
        )


def filtrar_tabela_transacoes(
    transacoes: pd.DataFrame,
) -> pd.DataFrame:
    """Aplica filtros de tipo, categoria e descrição."""
    tipos = sorted(transacoes["tipo"].dropna().astype(str).unique().tolist())

    categorias = sorted(transacoes["categoria"].dropna().astype(str).unique().tolist())

    coluna_tipo, coluna_categoria, coluna_busca = st.columns([1, 1, 2])

    tipo = coluna_tipo.selectbox(
        "Tipo",
        ["Todos", *tipos],
        format_func=lambda valor: (
            valor
            if valor == "Todos"
            else ROTULOS_TIPO.get(
                valor,
                valor.title(),
            )
        ),
        key="filtro_tipo_transacoes",
    )

    categoria = coluna_categoria.selectbox(
        "Categoria",
        ["Todas", *categorias],
        key="filtro_categoria_transacoes",
    )

    busca = coluna_busca.text_input(
        "Buscar descrição",
        placeholder="Ex.: mercado, transporte, bolsa",
        key="filtro_busca_transacoes",
    )

    resultado = transacoes.copy()

    if tipo != "Todos":
        resultado = resultado.loc[resultado["tipo"] == tipo]

    if categoria != "Todas":
        resultado = resultado.loc[resultado["categoria"] == categoria]

    if busca.strip():
        resultado = resultado.loc[
            resultado["descricao"]
            .astype(str)
            .str.contains(
                busca.strip(),
                case=False,
                na=False,
            )
        ]

    return resultado


def exibir_transacoes_do_periodo(
    transacoes: pd.DataFrame,
) -> None:
    """Exibe as transações e os totais dos filtros."""
    st.subheader("Transações do período")

    st.caption(
        "Use os filtros para consultar receitas, despesas, "
        "categorias ou descrições específicas."
    )

    if transacoes.empty:
        st.info("Nenhuma transação encontrada para o período selecionado.")
        return

    filtradas = filtrar_tabela_transacoes(transacoes)

    receitas = filtradas.loc[
        filtradas["tipo"] == "receita",
        "valor",
    ].sum()

    despesas = filtradas.loc[
        filtradas["tipo"] == "despesa",
        "valor",
    ].sum()

    coluna_total, coluna_receitas, coluna_despesas = st.columns(3)

    coluna_total.metric(
        "Transações",
        len(filtradas),
    )

    coluna_receitas.metric(
        "Receitas",
        formatar_moeda(receitas),
    )

    coluna_despesas.metric(
        "Despesas",
        formatar_moeda(despesas),
    )

    if filtradas.empty:
        st.info("Nenhuma transação corresponde " "aos filtros selecionados.")
        return

    tabela = preparar_transacoes_para_exibicao(
        filtradas.sort_values(
            by="data",
            ascending=False,
        )
    )

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
    )


def exibir_simulador_de_metas(
    perfil_usuario: dict[str, Any],
    resumo: dict[str, Any],
) -> None:
    """Exibe a simulação de uma meta financeira."""
    st.subheader("Simulador de metas")

    st.caption(
        "Escolha uma meta para estimar quanto " "ainda precisa ser guardado por mês."
    )

    metas = perfil_usuario["objetivos_financeiros"]
    nomes = [meta["nome"] for meta in metas]

    nome_escolhido = st.selectbox(
        "Meta",
        nomes,
        key="meta_selecionada",
    )

    meta = next(item for item in metas if item["nome"] == nome_escolhido)

    valor_meta = float(meta["valor_meta"])
    valor_atual = float(meta["valor_atual"])
    prazo_meses = int(meta["prazo_meses"])

    simulacao = calcular_meta_mensal(
        valor_meta=valor_meta,
        prazo_meses=prazo_meses,
        valor_ja_reservado=valor_atual,
    )

    valor_mensal = simulacao["valor_mensal_necessario"]

    (
        coluna_meta,
        coluna_atual,
        coluna_restante,
        coluna_mensal,
    ) = st.columns(4)

    coluna_meta.metric(
        "Valor da meta",
        formatar_moeda(valor_meta),
    )

    coluna_atual.metric(
        "Valor atual",
        formatar_moeda(valor_atual),
    )

    coluna_restante.metric(
        "Falta guardar",
        formatar_moeda(simulacao["valor_restante"]),
    )

    coluna_mensal.metric(
        "Necessário por mês",
        formatar_moeda(valor_mensal),
    )

    if valor_mensal is None:
        st.warning("Não foi possível calcular a meta " "porque o prazo é inválido.")
    elif valor_mensal > resumo["saldo_disponivel"]:
        st.error(
            "O valor mensal necessário ultrapassa "
            "o saldo disponível do período. "
            "Considere ajustar o prazo, os gastos ou a renda."
        )
    else:
        st.success("O valor mensal necessário cabe " "no saldo disponível do período.")

    st.caption(
        "A análise considera uma meta por vez. "
        "Para várias metas, some os valores mensais necessários."
    )


def exibir_chat(
    mensagens: list[dict[str, str]],
    contexto: str,
) -> None:
    """Exibe o chat contextual do FinanTec."""
    st.subheader("Converse com o FinanTec")

    st.caption(
        "Exemplos: “Em qual categoria eu mais gastei?”, "
        "“Qual é meu saldo?” ou "
        "“Quanto preciso guardar para o notebook?”"
    )

    for mensagem in mensagens:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    pergunta = st.chat_input(
        "Digite sua pergunta sobre organização financeira",
        key="pergunta_finantec",
    )

    if not pergunta:
        return

    mensagens.append(
        {
            "role": "user",
            "content": pergunta,
        }
    )

    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Analisando os dados disponíveis..."):
            try:
                resposta = gerar_resposta_finantec(
                    pergunta_usuario=pergunta,
                    contexto=contexto,
                )
                st.markdown(resposta)
            except RuntimeError as erro:
                resposta = str(erro)
                st.error(resposta)

    mensagens.append(
        {
            "role": "assistant",
            "content": resposta,
        }
    )


def exibir_aba_dashboard(
    transacoes: pd.DataFrame,
    resumo: dict[str, Any],
    gastos_por_categoria: pd.Series,
    mostrar_evolucao_anual: bool,
) -> None:
    """Compõe a visão geral do dashboard."""
    st.header("Visão geral")

    exibir_resumo_financeiro(resumo)

    st.divider()

    exibir_diagnostico_financeiro(resumo)

    st.divider()

    exibir_indicadores_complementares(
        transacoes,
        resumo,
    )

    st.divider()

    coluna_grafico, coluna_ranking = st.columns([2, 1])

    with coluna_grafico:
        exibir_gastos_por_categoria(
            gastos_por_categoria,
            resumo,
        )

    with coluna_ranking:
        exibir_ranking_de_categorias(gastos_por_categoria)

    if mostrar_evolucao_anual:
        st.divider()
        exibir_evolucao_mensal(transacoes)

    st.divider()

    exibir_ultimas_transacoes(transacoes)


def exibir_aba_transacoes(
    transacoes: pd.DataFrame,
    rejeicoes: pd.DataFrame,
) -> None:
    """Compõe entrada, validação e consulta de transações."""
    abrir_editor = "resultado_etl" in st.session_state

    with st.expander(
        "Entrada manual de transações",
        expanded=abrir_editor,
    ):
        etl_executado = exibir_editor_transacoes_manuais()

    if etl_executado:
        carregar_dados.clear()
        st.rerun()

    st.caption(
        "Transações manuais aparecem nos indicadores "
        "após o processamento do ETL e no período "
        "correspondente à data cadastrada."
    )

    st.divider()

    exibir_validacao_dos_dados(
        len(transacoes),
        rejeicoes,
    )

    st.divider()

    exibir_transacoes_do_periodo(transacoes)


def main() -> None:
    """Executa a interface principal."""
    aplicar_estilo_visual()

    (
        perfil_usuario,
        transacoes,
        historico_atendimento,
        conceitos_financeiros,
        produtos_financeiros,
        rejeicoes,
    ) = carregar_dados()

    (
        mes_selecionado,
        periodo,
        transacoes_filtradas,
    ) = selecionar_periodo(transacoes)

    resumo = calcular_resumo_financeiro(transacoes_filtradas)

    gastos_por_categoria = calcular_gastos_por_categoria(transacoes_filtradas)

    simulacoes_metas = calcular_simulacoes_de_metas(perfil_usuario)

    contexto = montar_contexto_do_periodo(
        periodo=periodo,
        perfil_usuario=perfil_usuario,
        resumo=resumo,
        gastos_por_categoria=gastos_por_categoria,
        simulacoes_metas=simulacoes_metas,
        historico_atendimento=historico_atendimento,
        conceitos_financeiros=conceitos_financeiros,
        produtos_financeiros=produtos_financeiros,
    )

    mensagens = obter_mensagens_do_periodo(periodo)

    exibir_cabecalho(periodo)

    (
        aba_dashboard,
        aba_transacoes,
        aba_metas,
        aba_ia,
    ) = st.tabs(
        [
            "Dashboard",
            "Transações",
            "Metas",
            "IA",
        ]
    )

    with aba_dashboard:
        exibir_aba_dashboard(
            transacoes=transacoes_filtradas,
            resumo=resumo,
            gastos_por_categoria=gastos_por_categoria,
            mostrar_evolucao_anual=mes_selecionado == 0,
        )

    with aba_transacoes:
        exibir_aba_transacoes(
            transacoes=transacoes_filtradas,
            rejeicoes=rejeicoes,
        )

    with aba_metas:
        exibir_simulador_de_metas(
            perfil_usuario,
            resumo,
        )

    with aba_ia:
        exibir_chat(
            mensagens,
            contexto,
        )


if __name__ == "__main__":
    main()
