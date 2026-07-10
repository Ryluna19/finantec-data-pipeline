"""
Interface Streamlit do FinanTec.

Este arquivo organiza a visualização principal do projeto:
- filtro por período;
- entrada manual de transações;
- validação dos dados carregados;
- resumo financeiro;
- tabela de transações;
- gráfico de gastos por categoria;
- simulador de metas;
- chat com IA generativa usando contexto calculado em Python.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from agent import gerar_resposta_finantec
from analytics import (
    calcular_gastos_por_categoria,
    calcular_meta_mensal,
    calcular_resumo_financeiro,
    calcular_simulacoes_de_metas,
    filtrar_transacoes_por_mes,
    formatar_moeda,
    listar_meses_disponiveis,
)
from data_loader import (
    carregar_conceitos_financeiros,
    carregar_historico_atendimento,
    carregar_perfil_usuario,
    carregar_produtos_financeiros,
    carregar_rejeicoes,
    carregar_transacoes,
)
from prompts import montar_contexto
from transaction_editor import exibir_editor_transacoes_manuais

st.set_page_config(
    page_title="FinanTec",
    page_icon="💰",
    layout="wide",
)

MESES_PTBR = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

@st.cache_data
def carregar_dados() -> tuple[
    dict,
    pd.DataFrame,
    pd.DataFrame,
    dict,
    dict,
    pd.DataFrame,
]:
    """
    Carrega todos os dados usados pelo dashboard.

    O cache evita recarregar os mesmos arquivos a cada interação no Streamlit.
    Caso os arquivos sejam alterados durante a execução, pode ser necessário
    limpar o cache ou reiniciar o app.
    """
    perfil_usuario = carregar_perfil_usuario()
    transacoes = carregar_transacoes()
    historico_atendimento = carregar_historico_atendimento()
    conceitos_financeiros = carregar_conceitos_financeiros()
    produtos_financeiros = carregar_produtos_financeiros()
    rejeicoes = carregar_rejeicoes()

    return (
        perfil_usuario,
        transacoes,
        historico_atendimento,
        conceitos_financeiros,
        produtos_financeiros,
        rejeicoes,
    )


def criar_mensagem_inicial(mes: str) -> list[dict[str, str]]:
    """
    Cria a primeira mensagem do chat para o período selecionado.
    """
    return [
        {
            "role": "assistant",
            "content": (
                f"Olá! Sou o FinanTec. Estou analisando o período "
                f"{mes}. Posso ajudar você a entender gastos, "
                f"metas e conceitos financeiros básicos."
            ),
        }
    ]


def selecionar_periodo(
    transacoes: pd.DataFrame,
) -> tuple[int, int, str, pd.DataFrame]:
    """
    Exibe filtros de ano e mês no menu lateral.

    Retorna:
    - ano selecionado
    - mês selecionado (0 = Todos)
    - rótulo do período
    - transações filtradas
    """
    if transacoes.empty:
        st.error("Não há transações disponíveis.")
        st.stop()

    transacoes = transacoes.copy()
    transacoes["ano"] = transacoes["data"].dt.year
    transacoes["mes"] = transacoes["data"].dt.month

    anos_disponiveis = sorted(
        transacoes["ano"].dropna().astype(int).unique().tolist()
    )

    if not anos_disponiveis:
        st.error("Nenhum ano disponível na base.")
        st.stop()

    st.sidebar.title("Filtros")

    ano_selecionado = st.sidebar.selectbox(
        "Ano",
        anos_disponiveis,
        index=len(anos_disponiveis) - 1,
    )

    meses_disponiveis = sorted(
        transacoes.loc[
            transacoes["ano"] == ano_selecionado,
            "mes"
        ].dropna().astype(int).unique().tolist()
    )

    opcoes_mes = [0] + meses_disponiveis

    mes_selecionado = st.sidebar.selectbox(
        "Mês",
        opcoes_mes,
        format_func=lambda mes: "Todos" if mes == 0 else MESES_PTBR[mes],
        index=0,
    )

    if mes_selecionado == 0:
        transacoes_filtradas = transacoes[
            transacoes["ano"] == ano_selecionado
        ].copy()
        rotulo_periodo = f"{ano_selecionado}"
    else:
        transacoes_filtradas = transacoes[
            (transacoes["ano"] == ano_selecionado)
            & (transacoes["mes"] == mes_selecionado)
        ].copy()
        rotulo_periodo = f"{MESES_PTBR[mes_selecionado]}/{ano_selecionado}"

    return (
        ano_selecionado,
        mes_selecionado,
        rotulo_periodo,
        transacoes_filtradas,
    )


def montar_contexto_do_periodo(
    rotulo_periodo: str,
    perfil_usuario: dict,
    resumo: dict[str, Any],
    gastos_por_categoria: pd.Series,
    simulacoes_metas: list[dict],
    historico_atendimento: pd.DataFrame,
    conceitos_financeiros: dict,
    produtos_financeiros: dict,
) -> str:
    """
    Monta o contexto final enviado para a IA no período selecionado.
    """
    contexto = montar_contexto(
        perfil_usuario=perfil_usuario,
        resumo_financeiro=resumo,
        gastos_por_categoria=gastos_por_categoria,
        simulacoes_metas=simulacoes_metas,
        historico_atendimento=historico_atendimento,
        conceitos_financeiros=conceitos_financeiros,
        produtos_financeiros=produtos_financeiros,
    )

    return f"""
PERÍODO ANALISADO:
{rotulo_periodo}

{contexto}
""".strip()


def obter_mensagens_do_periodo(rotulo_periodo: str) -> list[dict[str, str]]:
    """
    Mantém um histórico de conversa separado para cada período analisado.
    """
    if "mensagens_por_periodo" not in st.session_state:
        st.session_state.mensagens_por_periodo = {}

    if rotulo_periodo not in st.session_state.mensagens_por_periodo:
        st.session_state.mensagens_por_periodo[rotulo_periodo] = criar_mensagem_inicial(
            rotulo_periodo
        )

    return st.session_state.mensagens_por_periodo[rotulo_periodo]


def exibir_cabecalho(rotulo_periodo: str) -> None:
    """
    Exibe o cabeçalho principal do dashboard.
    """
    st.title("💰 FinanTec")
    st.caption(
        "Assistente de organização financeira para estudantes e pessoas em início de carreira."
    )

    st.warning(
        "Projeto educativo com dados simulados. O FinanTec não oferece recomendação "
        "personalizada de investimento."
    )

    st.info(f"Período analisado: **{rotulo_periodo}**")
    
def exibir_evolucao_mensal(transacoes_periodo: pd.DataFrame) -> None:
    """
    Exibe receitas e despesas por mês para a visão anual.
    """
    if transacoes_periodo.empty:
        st.info("Não há dados suficientes para exibir a evolução mensal.")
        return

    dados = transacoes_periodo.copy()
    dados["mes_num"] = dados["data"].dt.month

    resumo_mensal = (
        dados.groupby(["mes_num", "tipo"])["valor"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("mes_num")
    )

    if "receita" not in resumo_mensal.columns:
        resumo_mensal["receita"] = 0.0

    if "despesa" not in resumo_mensal.columns:
        resumo_mensal["despesa"] = 0.0

    resumo_mensal["Mês"] = resumo_mensal["mes_num"].map(MESES_PTBR)

    st.subheader("Receitas e despesas por mês")

    st.line_chart(
        resumo_mensal.set_index("Mês")[["receita", "despesa"]]
    )

    tabela_resumo = resumo_mensal[["Mês", "receita", "despesa"]].copy()
    tabela_resumo.columns = ["Mês", "Receitas", "Despesas"]

    tabela_resumo["Receitas"] = tabela_resumo["Receitas"].map(formatar_moeda)
    tabela_resumo["Despesas"] = tabela_resumo["Despesas"].map(formatar_moeda)

    st.dataframe(
        tabela_resumo,
        use_container_width=True,
        hide_index=True,
    )


def exibir_validacao_dos_dados(
    quantidade_transacoes_validas: int,
    rejeicoes: pd.DataFrame,
) -> None:
    """
    Exibe um resumo simples da qualidade dos dados processados pelo ETL.
    """
    st.subheader("Validação dos dados")

    coluna_validas, coluna_rejeitadas = st.columns(2)

    coluna_validas.metric(
        "Transações válidas no período",
        quantidade_transacoes_validas,
    )

    coluna_rejeitadas.metric(
        "Transações rejeitadas no último ETL",
        len(rejeicoes),
    )

    if rejeicoes.empty:
        st.success("Nenhuma transação rejeitada no último processamento.")
        return

    st.warning(
        "Existem transações rejeitadas no último processamento. "
        "Abra a tabela abaixo para conferir os motivos."
    )

    with st.expander("Ver transações rejeitadas"):
        st.dataframe(rejeicoes, use_container_width=True)


def exibir_resumo_financeiro(resumo: dict[str, Any]) -> None:
    """
    Exibe os principais indicadores financeiros do período.
    """
    st.subheader("Resumo financeiro do período")

    coluna_receita, coluna_consumo, coluna_reserva, coluna_saldo = st.columns(4)

    coluna_receita.metric(
        "Receitas",
        formatar_moeda(resumo["receitas_totais"]),
    )

    coluna_consumo.metric(
        "Gasto de consumo",
        formatar_moeda(resumo["despesas_do_mes"]),
    )

    coluna_reserva.metric(
        "Separado para reserva",
        formatar_moeda(resumo["valor_guardado_reserva"]),
    )

    coluna_saldo.metric(
        "Saldo disponível",
        formatar_moeda(resumo["saldo_disponivel"]),
    )


def exibir_gastos_por_categoria(
    gastos_por_categoria: pd.Series,
    resumo: dict[str, Any],
) -> None:
    """
    Exibe o gráfico de gastos de consumo por categoria.
    """
    st.subheader("Gastos de consumo por categoria")

    if gastos_por_categoria.empty:
        st.info("Não há gastos de consumo para exibir neste período.")
        return

    gastos_tabela = gastos_por_categoria.rename("Valor").reset_index()
    gastos_tabela.columns = ["Categoria", "Valor"]

    st.bar_chart(
        gastos_tabela,
        x="Categoria",
        y="Valor",
    )

    if resumo["maior_categoria"]:
        st.info(
            f"A maior categoria de consumo no período foi "
            f"**{resumo['maior_categoria']}**, com "
            f"{formatar_moeda(resumo['maior_gasto'])}."
        )


def exibir_ranking_de_categorias(gastos_por_categoria: pd.Series) -> None:
    """
    Exibe uma tabela simples com o ranking de gastos por categoria.
    """
    st.subheader("Ranking de categorias")

    if gastos_por_categoria.empty:
        st.info("Não há categorias de consumo para listar neste período.")
        return

    ranking = (
        gastos_por_categoria.sort_values(ascending=False).rename("valor").reset_index()
    )
    ranking.columns = ["Categoria", "Valor"]

    ranking["Valor"] = ranking["Valor"].map(formatar_moeda)

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True,
    )


def exibir_ultimas_transacoes(
    transacoes_periodo: pd.DataFrame,
    limite: int = 5,
) -> None:
    """
    Exibe as últimas transações do período no dashboard principal.
    """
    st.subheader("Últimas transações do período")

    if transacoes_periodo.empty:
        st.info("Nenhuma transação encontrada para o período selecionado.")
        return

    ultimas = transacoes_periodo.sort_values(
        by="data",
        ascending=False,
    ).head(limite)

    ultimas = preparar_transacoes_para_exibicao(ultimas)

    st.dataframe(
        ultimas,
        use_container_width=True,
        hide_index=True,
    )


def preparar_transacoes_para_exibicao(transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara a tabela de transações para exibição no dashboard.
    """
    transacoes_exibicao = transacoes.copy()

    transacoes_exibicao["data"] = pd.to_datetime(
        transacoes_exibicao["data"],
        errors="coerce",
    ).dt.strftime("%d/%m/%Y")

    transacoes_exibicao["valor"] = transacoes_exibicao["valor"].map(formatar_moeda)

    colunas_exibicao = [
        "data",
        "tipo",
        "descricao",
        "categoria",
        "valor",
    ]

    return transacoes_exibicao[colunas_exibicao]


def filtrar_tabela_transacoes(transacoes: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica filtros simples na tabela de transações do período.
    """
    transacoes_filtradas = transacoes.copy()

    tipos = ["Todos"] + sorted(
        transacoes_filtradas["tipo"].dropna().astype(str).unique().tolist()
    )

    categorias = ["Todas"] + sorted(
        transacoes_filtradas["categoria"].dropna().astype(str).unique().tolist()
    )

    coluna_tipo, coluna_categoria, coluna_busca = st.columns([1, 1, 2])

    tipo_escolhido = coluna_tipo.selectbox(
        "Tipo",
        tipos,
    )

    categoria_escolhida = coluna_categoria.selectbox(
        "Categoria",
        categorias,
    )

    busca = coluna_busca.text_input(
        "Buscar descrição",
        placeholder="Ex: mercado, transporte, bolsa...",
    )

    if tipo_escolhido != "Todos":
        transacoes_filtradas = transacoes_filtradas[
            transacoes_filtradas["tipo"] == tipo_escolhido
        ]

    if categoria_escolhida != "Todas":
        transacoes_filtradas = transacoes_filtradas[
            transacoes_filtradas["categoria"] == categoria_escolhida
        ]

    if busca:
        transacoes_filtradas = transacoes_filtradas[
            transacoes_filtradas["descricao"]
            .astype(str)
            .str.contains(busca, case=False, na=False)
        ]

    return transacoes_filtradas


def exibir_transacoes_do_periodo(transacoes_periodo: pd.DataFrame) -> None:
    """
    Exibe a tabela de transações do período selecionado.
    """
    st.subheader("Transações do período")

    if transacoes_periodo.empty:
        st.info("Nenhuma transação encontrada para o período selecionado.")
        return

    transacoes_filtradas = filtrar_tabela_transacoes(transacoes_periodo)

    receitas = transacoes_filtradas.loc[
        transacoes_filtradas["tipo"] == "receita",
        "valor",
    ].sum()

    despesas = transacoes_filtradas.loc[
        transacoes_filtradas["tipo"] == "despesa",
        "valor",
    ].sum()

    coluna_quantidade, coluna_receitas, coluna_despesas = st.columns(3)

    coluna_quantidade.metric(
        "Transações exibidas",
        len(transacoes_filtradas),
    )

    coluna_receitas.metric(
        "Receitas filtradas",
        formatar_moeda(receitas),
    )

    coluna_despesas.metric(
        "Despesas filtradas",
        formatar_moeda(despesas),
    )

    if transacoes_filtradas.empty:
        st.info("Nenhuma transação encontrada com os filtros selecionados.")
        return

    transacoes_exibicao = preparar_transacoes_para_exibicao(
        transacoes_filtradas.sort_values(
            by="data",
            ascending=False,
        )
    )

    st.dataframe(
        transacoes_exibicao,
        use_container_width=True,
        hide_index=True,
    )


def exibir_simulador_de_metas(
    perfil_usuario: dict,
    resumo: dict[str, Any],
) -> None:
    """
    Exibe o simulador de metas financeiras.
    """
    st.subheader("Simulador de metas financeiras")

    st.write(
        "Escolha uma meta cadastrada no perfil da Marina para estimar quanto ainda "
        "precisa ser guardado por mês."
    )

    metas = perfil_usuario["objetivos_financeiros"]
    nomes_metas = [meta["nome"] for meta in metas]

    nome_meta_escolhida = st.selectbox(
        "Meta",
        nomes_metas,
    )

    meta_escolhida = next(meta for meta in metas if meta["nome"] == nome_meta_escolhida)

    valor_meta = float(meta_escolhida["valor_meta"])
    valor_atual = float(meta_escolhida["valor_atual"])
    prazo_meses = int(meta_escolhida["prazo_meses"])

    simulacao = calcular_meta_mensal(
        valor_meta=valor_meta,
        prazo_meses=prazo_meses,
        valor_ja_reservado=valor_atual,
    )

    coluna_meta, coluna_atual, coluna_restante, coluna_mensal = st.columns(4)

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

    valor_mensal_necessario = simulacao["valor_mensal_necessario"]

    coluna_mensal.metric(
        "Necessário por mês",
        formatar_moeda(valor_mensal_necessario),
    )

    if valor_mensal_necessario is None:
        st.warning(
            "Não foi possível calcular o valor mensal necessário porque o prazo "
            "da meta está inválido."
        )
    elif valor_mensal_necessario > resumo["saldo_disponivel"]:
        st.error(
            "Para essa meta, o valor mensal necessário é maior que o saldo disponível "
            "do período selecionado. Pode ser necessário aumentar o prazo, reduzir "
            "gastos ou buscar renda extra."
        )
    else:
        st.success(
            "Considerando apenas essa meta, o valor mensal necessário cabe no saldo "
            "disponível do período selecionado."
        )

    st.caption(
        "Observação: a análise considera uma meta por vez. Se Marina tentar cumprir "
        "várias metas ao mesmo tempo, será necessário somar os valores mensais."
    )


def exibir_chat(
    mensagens_mes: list[dict[str, str]],
    contexto: str,
) -> None:
    """
    Exibe o chat com o FinanTec e envia perguntas para a IA.
    """
    st.subheader("Converse com o FinanTec")

    st.caption(
        "Teste perguntas como: “Em qual categoria eu mais gastei?”, "
        "“Qual é meu saldo?”, “Quanto preciso guardar para o notebook?” "
        "ou “Qual banco oferece o melhor CDB hoje?”"
    )

    for mensagem in mensagens_mes:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    pergunta_usuario = st.chat_input("Digite sua pergunta sobre organização financeira")

    if not pergunta_usuario:
        return

    mensagens_mes.append(
        {
            "role": "user",
            "content": pergunta_usuario,
        }
    )

    with st.chat_message("user"):
        st.markdown(pergunta_usuario)

    with st.chat_message("assistant"):
        with st.spinner("Analisando os dados disponíveis..."):
            try:
                resposta = gerar_resposta_finantec(
                    pergunta_usuario=pergunta_usuario,
                    contexto=contexto,
                )
                st.markdown(resposta)

            except RuntimeError as erro:
                resposta = str(erro)
                st.error(resposta)

    mensagens_mes.append(
        {
            "role": "assistant",
            "content": resposta,
        }
    )


def exibir_aba_dashboard(
    transacoes_filtradas: pd.DataFrame,
    rejeicoes: pd.DataFrame,
    resumo: dict[str, Any],
    gastos_por_categoria: pd.Series,
) -> None:
    """
    Exibe a visão geral do dashboard.
    """
    exibir_validacao_dos_dados(
        quantidade_transacoes_validas=len(transacoes_filtradas),
        rejeicoes=rejeicoes,
    )

    st.divider()

    exibir_resumo_financeiro(resumo)

    st.divider()

    coluna_grafico, coluna_ranking = st.columns([2, 1])

    with coluna_grafico:
        exibir_gastos_por_categoria(gastos_por_categoria, resumo)

    with coluna_ranking:
        exibir_ranking_de_categorias(gastos_por_categoria)

    st.divider()

    exibir_ultimas_transacoes(transacoes_filtradas)


def main() -> None:
    """
    Executa a interface principal do dashboard.
    """
    (
        perfil_usuario,
        transacoes,
        historico_atendimento,
        conceitos_financeiros,
        produtos_financeiros,
        rejeicoes,
    ) = carregar_dados()

    (
        ano_selecionado,
        mes_selecionado,
        rotulo_periodo,
        transacoes_filtradas,
    ) = selecionar_periodo(transacoes)

    resumo = calcular_resumo_financeiro(transacoes_filtradas)
    gastos_por_categoria = calcular_gastos_por_categoria(transacoes_filtradas)
    simulacoes_metas = calcular_simulacoes_de_metas(perfil_usuario)

    contexto = montar_contexto_do_periodo(
        rotulo_periodo=rotulo_periodo,
        perfil_usuario=perfil_usuario,
        resumo=resumo,
        gastos_por_categoria=gastos_por_categoria,
        simulacoes_metas=simulacoes_metas,
        historico_atendimento=historico_atendimento,
        conceitos_financeiros=conceitos_financeiros,
        produtos_financeiros=produtos_financeiros,
    )

    mensagens_mes = obter_mensagens_do_periodo(rotulo_periodo)

    exibir_cabecalho(rotulo_periodo)

    abrir_editor_transacoes = "resultado_etl" in st.session_state

    with st.expander(
        "Entrada manual de transações",
        expanded=abrir_editor_transacoes,
    ):
        etl_executado = exibir_editor_transacoes_manuais()

    st.caption(
        "Observação: transações manuais só aparecem nos indicadores depois de "
        "clicar em 'Salvar e processar ETL' e no período correspondente à data cadastrada."
    )

    if etl_executado:
        carregar_dados.clear()
        st.rerun()

    aba_dashboard, aba_transacoes, aba_metas, aba_ia = st.tabs(
        [
            "Dashboard",
            "Transações",
            "Metas",
            "IA",
        ]
    )

    with aba_dashboard:
        exibir_aba_dashboard(
            transacoes_filtradas=transacoes_filtradas,
            rejeicoes=rejeicoes,
            resumo=resumo,
            gastos_por_categoria=gastos_por_categoria,
        )

        if mes_selecionado == 0:
            st.divider()
            exibir_evolucao_mensal(transacoes_filtradas)

    with aba_transacoes:
        exibir_transacoes_do_periodo(transacoes_filtradas)

    with aba_metas:
        exibir_simulador_de_metas(perfil_usuario, resumo)

    with aba_ia:
        exibir_chat(
            mensagens_mes=mensagens_mes,
            contexto=contexto,
        )


if __name__ == "__main__":
    main()
