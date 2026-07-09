# FinanTec Data Pipeline

Pipeline de dados financeiros simulados com Python, pandas, SQLite, Streamlit e IA generativa.

Este projeto é uma evolução independente do FinanTec, inspirado em um projeto acadêmico anterior, com foco em ETL, análise de dados, automação de arquivos e visualização de indicadores financeiros.

## Sobre o Projeto

O FinanTec Data Pipeline simula um fluxo de processamento de dados financeiros pessoais a partir de arquivos CSV mensais.

A proposta é transformar arquivos brutos de transações em uma base tratada, gerar indicadores financeiros e disponibilizar esses dados em um dashboard interativo com apoio de IA generativa para explicações contextualizadas.

O projeto não utiliza dados bancários reais. Todos os dados são simulados.

## Objetivo

Demonstrar um fluxo básico de dados aplicado a um contexto financeiro:

- leitura de múltiplos arquivos CSV;
- validação de estrutura dos dados;
- limpeza e padronização com pandas;
- geração de dados processados;
- carga em SQLite;
- análise por período;
- visualização em Streamlit;
- explicação dos indicadores com IA generativa.

## Funcionalidades

- Pipeline ETL para transações financeiras simuladas;
- leitura de arquivos em `data/raw/`;
- validação de colunas obrigatórias;
- tratamento de datas, tipos, categorias e valores;
- criação da coluna `ano_mes`;
- geração de arquivo tratado em `data/processed/`;
- carga dos dados processados em SQLite;
- dashboard com filtro por período;
- resumo de receitas, gastos, reserva e saldo;
- gráfico de gastos por categoria;
- simulador de metas financeiras;
- chat com IA generativa usando contexto dos dados;
- histórico de conversa separado por período analisado.

## Tecnologias Utilizadas

- Python
- pandas
- Streamlit
- SQLite
- python-dotenv
- google-genai
- CSV
- JSON
- Gemini API

## Fluxo do Pipeline

```text
data/raw/
        ↓
Extração dos arquivos CSV
        ↓
Validação de colunas obrigatórias
        ↓
Tratamento e padronização com pandas
        ↓
data/processed/transacoes_processadas.csv
        ↓
database/finantec.db
        ↓
Dashboard em Streamlit
        ↓
IA explicando os indicadores calculados
```

## Etapas do ETL

| Etapa     | Descrição                                                                                  |
| --------- | ------------------------------------------------------------------------------------------ |
| Extract   | Lê os arquivos CSV mensais armazenados em `data/raw/`.                                     |
| Transform | Valida colunas, converte datas, padroniza textos, trata valores e cria a coluna `ano_mes`. |
| Load      | Salva os dados tratados em CSV processado e em uma base SQLite.                            |

## Estrutura do Projeto

```text
finantec-data-pipeline/
├── assets/
├── data/
│   ├── raw/
│   │   ├── transacoes_2026_06.csv
│   │   └── transacoes_2026_07.csv
│   ├── processed/
│   ├── conceitos_financeiros.json
│   ├── historico_atendimento.csv
│   ├── perfil_usuario.json
│   ├── produtos_financeiros.json
│   └── transacoes.csv
├── database/
├── docs/
├── logs/
├── scripts/
│   └── etl_transacoes.py
├── src/
│   ├── agent.py
│   ├── analytics.py
│   ├── app.py
│   ├── data_loader.py
│   ├── prompts.py
│   ├── teste_contexto.py
│   ├── teste_dados.py
│   ├── teste_ia.py
│   ├── teste_metas.py
│   └── teste_periodos.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Base de Dados Simulada

A base representa a vida financeira fictícia de Marina Costa, uma estudante universitária e estagiária.

Os dados incluem:

- receitas mensais;
- gastos de consumo;
- valor separado para reserva;
- categorias de despesas;
- metas financeiras;
- conceitos financeiros básicos;
- produtos financeiros apenas informativos.

Os arquivos em `data/raw/` representam transações mensais brutas. O pipeline processa esses arquivos e gera uma base tratada para análise.

## Como Executar o Projeto

### 1. Clone o repositório

```bash
git clone https://github.com/Ryluna19/finantec-data-pipeline.git
cd finantec-data-pipeline
```

### 2. Crie e ative o ambiente virtual

No Windows:

```bash
py -m venv .venv
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure a chave da IA

Crie um arquivo `.env` na raiz do projeto e adicione sua chave da Gemini API:

```env
GEMINI_API_KEY=SUA_CHAVE_AQUI
```

O arquivo `.env` não deve ser enviado para o GitHub.

### 5. Execute o pipeline ETL

```bash
python scripts/etl_transacoes.py
```

Esse comando lê os arquivos em `data/raw/`, processa os dados e gera:

```text
data/processed/transacoes_processadas.csv
database/finantec.db
logs/etl_transacoes.log
```

Os arquivos de banco e log são gerados localmente e não precisam ser versionados.

### 6. Execute o dashboard

```bash
streamlit run src/app.py
```

## Exemplos de Perguntas para o Chat

```text
Em qual categoria eu mais gastei neste período?
```

```text
Qual é meu saldo neste período?
```

```text
Quanto preciso guardar por mês para comprar o notebook?
```

```text
Quanto preciso guardar por mês para montar a reserva?
```

```text
Qual banco oferece o melhor CDB hoje?
```

Para perguntas que dependem de dados externos ou informações em tempo real, o assistente deve informar que não possui dados suficientes.

## Testes

O projeto possui testes automatizados com `pytest` para validar partes importantes do pipeline e da lógica financeira.

### Testes automatizados

| Arquivo                      | Finalidade                                                                                  |
| ---------------------------- | ------------------------------------------------------------------------------------------- |
| `tests/test_analytics.py`    | Testa cálculos financeiros, separação entre consumo e reserva, metas e filtros por período. |
| `tests/test_etl_pipeline.py` | Testa validação de colunas, limpeza, padronização e transformação dos dados brutos.         |
| `tests/test_sqlite_load.py`  | Testa a carga dos dados tratados em uma base SQLite temporária.                             |

Para executar os testes:

````bash
pytest
## Limitações

O FinanTec Data Pipeline não:

- acessa contas bancárias reais;
- utiliza dados financeiros reais de usuários;
- substitui orientação profissional;
- recomenda investimentos personalizados;
- garante rentabilidade ou resultados financeiros;
- consulta taxas ou produtos em tempo real;
- executa operações financeiras.

## Possíveis Evoluções Futuras

Algumas melhorias possíveis:

- permitir upload de uma planilha-modelo pelo usuário;
- criar uma planilha padrão para preenchimento de receitas e despesas;
- adicionar validações mais detalhadas dos arquivos enviados;
- criar relatórios em Excel ou PDF;
- adicionar filtros por categoria;
- carregar o dashboard diretamente a partir do SQLite;
- adicionar PostgreSQL como alternativa ao SQLite;
- criar logs mais detalhados;
- mover arquivos processados automaticamente;
- evoluir para um fluxo simples de RPA;
- adicionar testes automatizados.

## Status

Primeira versão do projeto independente em desenvolvimento.

Fluxo atual:

```text
CSV bruto → ETL com pandas → CSV processado → SQLite → dashboard Streamlit → IA explicando indicadores
````
