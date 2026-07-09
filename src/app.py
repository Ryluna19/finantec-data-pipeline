from __future__ import annotations

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


st.set_page_config(
    page_title="FinanTec",
    page_icon="💰",
    layout="wide",
)


@st.cache_data
def carregar_dados():
    """
    Carrega todos os dados usados pelo dashboard.

    O cache evita recarregar os mesmos arquivos a cada interação do usuário
    no Streamlit. Caso os arquivos sejam alterados durante a execução,
    pode ser necessário limpar o cache ou reiniciar o app.
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


def criar_mensagem_inicial(mes: str) -> list[dict]:
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


def exibir_validacao_dos_dados(
    quantidade_transacoes_validas: int,
    rejeicoes,
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


(
    perfil_usuario,
    transacoes,
    historico_atendimento,
    conceitos_financeiros,
    produtos_financeiros,
    rejeicoes,
) = carregar_dados()


# Filtro principal do dashboard.
meses_disponiveis = listar_meses_disponiveis(transacoes)

st.sidebar.title("Filtros")
mes_selecionado = st.sidebar.selectbox(
    "Período analisado",
    meses_disponiveis,
    index=len(meses_disponiveis) - 1,
)

transacoes_filtradas = filtrar_transacoes_por_mes(
    transacoes,
    mes_selecionado,
)


# Cálculos financeiros feitos em Python.
# A IA apenas explica os dados; ela não deve inventar valores.
resumo = calcular_resumo_financeiro(transacoes_filtradas)
gastos_por_categoria = calcular_gastos_por_categoria(transacoes_filtradas)
simulacoes_metas = calcular_simulacoes_de_metas(perfil_usuario)


# Montagem do contexto enviado para o modelo generativo.
contexto = montar_contexto(
    perfil_usuario=perfil_usuario,
    resumo_financeiro=resumo,
    gastos_por_categoria=gastos_por_categoria,
    simulacoes_metas=simulacoes_metas,
    historico_atendimento=historico_atendimento,
    conceitos_financeiros=conceitos_financeiros,
    produtos_financeiros=produtos_financeiros,
)

contexto = f"""
PERÍODO ANALISADO:
{mes_selecionado}

{contexto}
""".strip()


# O histórico do chat é separado por mês.
# Assim, trocar o filtro não mistura conversas de períodos diferentes.
if "mensagens_por_mes" not in st.session_state:
    st.session_state.mensagens_por_mes = {}

if mes_selecionado not in st.session_state.mensagens_por_mes:
    st.session_state.mensagens_por_mes[mes_selecionado] = criar_mensagem_inicial(
        mes_selecionado
    )

mensagens_mes = st.session_state.mensagens_por_mes[mes_selecionado]


st.title("💰 FinanTec")
st.caption(
    "Assistente de organização financeira para estudantes e pessoas em início de carreira."
)

st.warning(
    "Projeto educativo com dados simulados. O FinanTec não oferece recomendação "
    "personalizada de investimento."
)

st.info(f"Período analisado: **{mes_selecionado}**")


exibir_validacao_dos_dados(
    quantidade_transacoes_validas=len(transacoes_filtradas),
    rejeicoes=rejeicoes,
)


st.divider()

st.subheader("Resumo financeiro do período")

coluna_receita, coluna_consumo, coluna_reserva, coluna_saldo = st.columns(4)

coluna_receita.metric(
    "Receitas",
    formatar_moeda(resumo["receitas_totais"]),
)

coluna_consumo.metric(
    "Gasto de consumo no período",
    formatar_moeda(resumo["despesas_do_mes"]),
)

coluna_reserva.metric(
    "Valor separado para reserva",
    formatar_moeda(resumo["valor_guardado_reserva"]),
)

coluna_saldo.metric(
    "Saldo disponível",
    formatar_moeda(resumo["saldo_disponivel"]),
)


st.subheader("Gastos de consumo por categoria")

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


st.divider()

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

coluna_mensal.metric(
    "Necessário por mês",
    formatar_moeda(simulacao["valor_mensal_necessario"]),
)

if simulacao["valor_mensal_necessario"] > resumo["saldo_disponivel"]:
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


st.divider()

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

if pergunta_usuario:
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