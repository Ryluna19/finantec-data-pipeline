# Project Overview — FinanTec Data Pipeline

## Visão Geral

O FinanTec Data Pipeline é um projeto de análise e automação de dados financeiros simulados.

A aplicação processa arquivos CSV mensais de transações, valida e padroniza os dados com Python e pandas, carrega os resultados em SQLite e apresenta indicadores em um dashboard Streamlit.

Além da visualização dos dados, o projeto possui um assistente com IA generativa que responde perguntas com base nos indicadores calculados e na base de conhecimento do projeto.

## Problema

Pessoas em início de carreira, estudantes e estagiários geralmente começam a lidar com renda própria sem ter uma visão clara sobre receitas, gastos, reserva e metas financeiras.

Ao mesmo tempo, dados financeiros costumam vir de fontes simples, como planilhas ou arquivos CSV, que precisam ser organizados antes de gerar qualquer análise confiável.

## Solução

O FinanTec Data Pipeline simula um fluxo em que arquivos financeiros mensais são processados por um pipeline ETL.

O projeto realiza:

- leitura de arquivos CSV brutos;
- validação de colunas obrigatórias;
- limpeza e padronização dos dados;
- criação de campos auxiliares, como `ano_mes`;
- geração de base processada;
- carga em SQLite;
- visualização dos dados por período;
- explicação dos indicadores com apoio de IA generativa.

## Público-Alvo

O projeto foi pensado para dois públicos:

1. Pessoas que querem entender melhor seus gastos e metas financeiras a partir de dados simples.
2. Recrutadores ou avaliadores técnicos que desejam ver um exemplo prático de Python, ETL, pandas, SQLite, Streamlit e IA generativa aplicados em um fluxo coerente.

## Fluxo Principal

```text
CSV bruto em data/raw/
        ↓
Extração dos arquivos
        ↓
Validação de estrutura
        ↓
Transformação com pandas
        ↓
CSV processado em data/processed/
        ↓
Carga em SQLite
        ↓
Dashboard Streamlit
        ↓
Assistente de IA explicando os indicadores



Principais Componentes
Componente	Responsabilidade
data/raw/	Armazena os arquivos CSV brutos de entrada.
scripts/etl_transacoes.py	Executa o pipeline ETL das transações.
data/processed/	Armazena a base processada gerada pelo pipeline.
database/	Armazena o banco SQLite gerado localmente.
src/analytics.py	Centraliza os cálculos financeiros.
src/data_loader.py	Carrega dados de JSON, CSV ou SQLite.
src/app.py	Interface Streamlit do dashboard e chat.
src/agent.py	Integração com a IA generativa.
tests/	Testes automatizados do pipeline e das regras financeiras.


Decisões Técnicas
Uso de SQLite

O SQLite foi escolhido para esta etapa por ser simples, gratuito e local. Ele permite demonstrar a etapa de carga do ETL sem exigir configuração de servidor externo.

Em uma evolução futura, o projeto pode adicionar PostgreSQL como alternativa mais próxima de ambientes produtivos.

Cálculos fora da IA

Os cálculos financeiros são feitos em Python, não pela IA.

A IA recebe os indicadores já calculados e atua apenas na explicação contextualizada dos resultados. Isso reduz o risco de respostas inconsistentes ou números inventados.

Dados simulados

O projeto não utiliza dados bancários reais. Todos os arquivos representam uma pessoa fictícia chamada Marina Costa.

Essa escolha permite demonstrar o fluxo técnico sem expor informações sensíveis.

Limitações

O projeto ainda não possui:

upload de planilhas pelo usuário;
autenticação;
múltiplos usuários;
integração com contas bancárias reais;
deploy público;
PostgreSQL;
automação RPA completa;
testes automatizados para chamadas de IA.

Esses pontos fazem parte do roadmap e podem ser evoluídos de forma incremental.

Status Atual

O projeto já possui:

pipeline ETL funcional;
leitura de múltiplos arquivos CSV;
validação e transformação de dados;
carga em SQLite;
dashboard com filtro por período;
simulador de metas financeiras;
chat com IA generativa;
testes automatizados com pytest;
contrato de dados para arquivos de transações.