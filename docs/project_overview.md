# Project Overview — FinanTec Data Pipeline

## Visão Geral

O FinanTec Data Pipeline é um projeto de análise, validação e visualização de dados financeiros simulados.

A aplicação processa arquivos CSV mensais de transações, valida e padroniza os dados com Python e pandas, carrega os resultados em SQLite e apresenta indicadores em um dashboard Streamlit.

Além da visualização dos dados, o projeto possui um assistente com IA generativa que responde perguntas com base nos indicadores calculados pela aplicação e na base de conhecimento do projeto.

O projeto não utiliza dados bancários reais. Todos os dados são simulados.

---

## Problema

Pessoas em início de carreira, estudantes e estagiários geralmente começam a lidar com renda própria sem ter uma visão clara sobre receitas, gastos, reserva e metas financeiras.

Ao mesmo tempo, dados financeiros muitas vezes começam em formatos simples, como planilhas ou arquivos CSV. Antes de gerar qualquer análise confiável, esses dados precisam ser organizados, validados e padronizados.

Sem esse processo, é fácil tirar conclusões erradas a partir de dados incompletos, inconsistentes ou mal estruturados.

---

## Solução

O FinanTec Data Pipeline simula um fluxo em que arquivos financeiros mensais são processados por um pipeline ETL.

O projeto realiza:

- leitura de arquivos CSV brutos;
- validação de colunas obrigatórias;
- limpeza e padronização dos dados;
- separação entre transações válidas e rejeitadas;
- geração de relatório de rejeições com motivo;
- criação de campos auxiliares, como `ano_mes`;
- geração de base processada;
- carga em SQLite;
- visualização dos dados por período;
- simulação de metas financeiras;
- explicação dos indicadores com apoio de IA generativa.

---

## Público-Alvo

O projeto foi pensado para dois públicos principais:

1. Pessoas que querem entender melhor seus gastos, reserva e metas financeiras a partir de dados simples.
2. Recrutadores ou avaliadores técnicos que desejam ver um exemplo prático de Python, ETL, pandas, SQLite, Streamlit, testes automatizados e IA generativa aplicados em um fluxo coerente.

---

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
Separação entre linhas válidas e rejeitadas
        ↓
CSV processado em data/processed/
        ↓
Carga em SQLite
        ↓
Dashboard Streamlit
        ↓
Assistente de IA explicando os indicadores
```

---

## Principais Componentes

| Componente | Responsabilidade |
|---|---|
| `data/raw/` | Armazena os arquivos CSV brutos de entrada. |
| `data/templates/` | Contém o modelo de CSV para novas transações. |
| `data/processed/` | Armazena localmente os arquivos processados e relatórios gerados pelo ETL. |
| `database/` | Armazena localmente o banco SQLite gerado pelo pipeline. |
| `logs/` | Armazena localmente os logs de execução do ETL. |
| `scripts/etl_transacoes.py` | Executa o pipeline ETL das transações. |
| `src/analytics.py` | Centraliza os cálculos financeiros. |
| `src/data_loader.py` | Carrega dados de JSON, CSV ou SQLite. |
| `src/app.py` | Interface Streamlit do dashboard e chat. |
| `src/agent.py` | Integração com a IA generativa. |
| `src/prompts.py` | Montagem do contexto e regras de comportamento da IA. |
| `tests/` | Testes automatizados do pipeline, cálculos financeiros, rejeições e carga SQLite. |
| `manual_tests/` | Scripts auxiliares para verificações manuais durante o desenvolvimento. |
| `main.py` | Entrada principal para executar app, ETL e testes com comandos simples. |

---

## Decisões Técnicas

### Uso de SQLite

O SQLite foi escolhido por ser simples, gratuito e local. Ele permite demonstrar a etapa de carga do ETL sem exigir configuração de servidor externo.

Para a versão atual, SQLite é suficiente porque o projeto trabalha com dados simulados e execução local.

Em uma evolução futura, PostgreSQL pode ser adicionado como alternativa mais próxima de ambientes produtivos.

---

### Cálculos fora da IA

Os cálculos financeiros são feitos em Python, não pela IA.

A IA recebe os indicadores já calculados e atua apenas na explicação contextualizada dos resultados.

Essa decisão reduz o risco de respostas inconsistentes, cálculos errados ou números inventados.

---

### Relatório de rejeições

O pipeline não apenas remove linhas inválidas. Ele também gera um relatório local com os motivos de rejeição.

Arquivo gerado quando há linhas inválidas:

```text
data/processed/transacoes_rejeitadas.csv
```

Exemplos de motivos:

- data inválida ou vazia;
- tipo inválido;
- descrição vazia;
- categoria vazia;
- valor inválido ou vazio;
- valor menor ou igual a zero.

Isso melhora a rastreabilidade do pipeline e facilita a correção dos arquivos de entrada.

---

### Dados simulados

O projeto não utiliza dados bancários reais.

A base representa uma pessoa fictícia chamada Marina Costa. Essa escolha permite demonstrar o fluxo técnico sem expor informações sensíveis.

---

### Execução simplificada

O projeto possui um arquivo `main.py` para centralizar comandos comuns.

Exemplos:

```bash
python main.py app
python main.py etl
python main.py test
python main.py dev
```

Isso torna o uso mais simples e aproxima a experiência de execução de projetos que usam scripts, como `npm run dev` em aplicações Node.js.

---

## Validação

A validação do projeto usa uma combinação de testes automatizados e scripts manuais.

Os testes automatizados cobrem:

- cálculos financeiros;
- metas financeiras;
- filtros por período;
- transformação dos dados;
- separação entre transações válidas e rejeitadas;
- relatório de rejeições;
- carga em SQLite com banco temporário.

Os scripts manuais ajudam a verificar:

- leitura dos dados;
- períodos disponíveis;
- contexto enviado para a IA;
- chamada manual ao assistente;
- consulta ao banco SQLite gerado pelo ETL.

---

## Limitações

O projeto ainda não possui:

- upload de planilhas pela interface;
- entrada manual de transações;
- autenticação;
- múltiplos usuários;
- controle de permissões;
- integração com contas bancárias reais;
- deploy público;
- PostgreSQL;
- automação RPA completa;
- testes automatizados da interface Streamlit;
- testes automatizados para chamadas de IA.

Esses pontos fazem parte do roadmap e podem ser evoluídos de forma incremental.

---

## Direção Futura

A direção futura mais coerente é evoluir o projeto para uma ferramenta local de controle financeiro pessoal.

A ideia não é criar um sistema multiusuário com login, autenticação e integração bancária real neste momento.

A evolução mais útil seria permitir que uma pessoa registre ou importe suas próprias transações em uma experiência parecida com uma planilha simples de gastos.

Fluxo futuro possível:

```text
Pessoa registra ou importa transações
        ↓
Sistema valida os dados
        ↓
Pipeline organiza e salva em SQLite
        ↓
Dashboard mostra indicadores
        ↓
IA ajuda a interpretar os resultados
```

Essa direção mantém o projeto simples, útil e tecnicamente defensável.

---

## Status Atual

O projeto já possui:

- pipeline ETL funcional;
- leitura de múltiplos arquivos CSV;
- validação e transformação de dados;
- relatório de rejeições;
- carga em SQLite;
- dashboard com filtro por período;
- resumo financeiro;
- gráfico de gastos por categoria;
- simulador de metas financeiras;
- chat com IA generativa;
- histórico de conversa separado por período;
- testes automatizados com pytest;
- testes manuais documentados;
- contrato de dados para arquivos de transações;
- comando principal com `main.py`.

Fluxo atual:

```text
CSV bruto → ETL com pandas → CSV processado → SQLite → dashboard Streamlit → IA explicando indicadores
```