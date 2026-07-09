# FinanTec Data Pipeline

Pipeline de dados financeiros simulados com Python, pandas, SQLite, Streamlit e IA generativa.

Este projeto é uma evolução independente do FinanTec, inspirado em um projeto acadêmico anterior, com foco em ETL, análise de dados, validação, persistência local, visualização de indicadores financeiros e explicação dos dados com IA generativa.

## Sobre o Projeto

O FinanTec Data Pipeline simula um fluxo de processamento de dados financeiros pessoais a partir de arquivos CSV mensais.

A proposta é transformar arquivos brutos de transações em uma base tratada, gerar indicadores financeiros e disponibilizar esses dados em um dashboard interativo com apoio de IA generativa para explicações contextualizadas.

O projeto não utiliza dados bancários reais. Todos os dados são simulados.

A ideia atual é manter o projeto como uma ferramenta local/pessoal de gestão financeira simulada, sem autenticação, múltiplos usuários ou integração bancária real.

## Objetivo

Demonstrar um fluxo básico de dados aplicado a um contexto financeiro:

- leitura de múltiplos arquivos CSV;
- validação da estrutura dos dados;
- limpeza e padronização com pandas;
- geração de relatório de linhas rejeitadas;
- geração de dados processados;
- carga em SQLite;
- análise por período;
- visualização em Streamlit;
- explicação dos indicadores com IA generativa.

## Funcionalidades

- Pipeline ETL para transações financeiras simuladas;
- leitura de arquivos em `data/raw/`;
- validação de colunas obrigatórias;
- tratamento de datas, tipos, descrições, categorias e valores;
- criação da coluna `ano_mes`;
- remoção de linhas inválidas da base final;
- geração de relatório de transações rejeitadas com motivo da rejeição;
- geração de arquivo tratado em `data/processed/`;
- carga dos dados processados em SQLite;
- dashboard com filtro por período;
- resumo de receitas, gastos, reserva e saldo;
- gráfico de gastos por categoria;
- simulador de metas financeiras;
- resumo da validação dos dados no dashboard;
- chat com IA generativa usando contexto dos dados;
- histórico de conversa separado por período analisado;
- comando centralizado de execução com `main.py`.

## Tecnologias Utilizadas

- Python
- pandas
- Streamlit
- SQLite
- pytest
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
Separação entre linhas válidas e rejeitadas
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

| Etapa | Descrição |
|---|---|
| Extract | Lê os arquivos CSV mensais armazenados em `data/raw/`. |
| Transform | Valida colunas, converte datas, padroniza textos, trata valores e cria a coluna `ano_mes`. |
| Load | Salva os dados tratados em CSV processado e em uma base SQLite. |

Quando existem linhas inválidas, o pipeline também gera:

```text
data/processed/transacoes_rejeitadas.csv
```

Esse arquivo contém as transações descartadas e uma coluna `motivo_rejeicao`, explicando por que cada linha não entrou na base final.

## Estrutura do Projeto

```text
finantec-data-pipeline/
├── assets/
├── data/
│   ├── raw/
│   │   ├── transacoes_2026_06.csv
│   │   └── transacoes_2026_07.csv
│   ├── processed/
│   │   └── .gitkeep
│   ├── templates/
│   │   └── transacoes_template.csv
│   ├── conceitos_financeiros.json
│   ├── historico_atendimento.csv
│   ├── perfil_usuario.json
│   ├── produtos_financeiros.json
│   └── transacoes.csv
├── database/
│   └── .gitkeep
├── docs/
│   ├── ai_prompting.md
│   ├── data_contract.md
│   ├── knowledge_base.md
│   ├── project_overview.md
│   ├── roadmap.md
│   └── validation.md
├── logs/
│   └── .gitkeep
├── manual_tests/
│   ├── _path_setup.py
│   ├── teste_contexto.py
│   ├── teste_dados.py
│   ├── teste_ia.py
│   ├── teste_metas.py
│   ├── teste_periodos.py
│   └── teste_sqlite.py
├── scripts/
│   └── etl_transacoes.py
├── src/
│   ├── agent.py
│   ├── analytics.py
│   ├── app.py
│   ├── data_loader.py
│   └── prompts.py
├── tests/
│   ├── test_analytics.py
│   ├── test_etl_pipeline.py
│   ├── test_rejections.py
│   └── test_sqlite_load.py
├── .env.example
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

## Documentação

A pasta `docs/` reúne a documentação técnica e de produto do projeto.

| Arquivo | Finalidade |
|---|---|
| `docs/project_overview.md` | Visão geral do projeto, problema, solução, componentes e decisões técnicas. |
| `docs/data_contract.md` | Contrato de dados dos arquivos CSV de transações. |
| `docs/knowledge_base.md` | Explicação das fontes de dados usadas pelo pipeline, dashboard e IA. |
| `docs/ai_prompting.md` | Regras de prompt, uso da IA e estratégia para reduzir respostas inventadas. |
| `docs/validation.md` | Estratégia de validação, testes automatizados, testes manuais e limitações. |
| `docs/roadmap.md` | Próximas evoluções planejadas para o projeto. |

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

No Windows PowerShell:

```bash
py -m venv .venv
.\.venv\Scripts\Activate.ps1
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

### 5. Execute o projeto

Para abrir o dashboard:

```bash
python main.py
```

Ou:

```bash
python main.py app
```

Para executar o pipeline ETL:

```bash
python main.py etl
```

Para executar os testes automatizados:

```bash
python main.py test
```

Para executar o ETL e depois abrir o dashboard:

```bash
python main.py dev
```

## Arquivos Gerados Localmente

Ao executar o ETL, o projeto pode gerar os seguintes arquivos:

```text
data/processed/transacoes_processadas.csv
data/processed/transacoes_rejeitadas.csv
database/finantec.db
logs/etl_transacoes.log
```

Esses arquivos são gerados localmente e não precisam ser versionados no GitHub.

O arquivo `transacoes_rejeitadas.csv` só é criado quando existem linhas inválidas nos arquivos de entrada.

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

| Arquivo | Finalidade |
|---|---|
| `tests/test_analytics.py` | Testa cálculos financeiros, separação entre consumo e reserva, metas e filtros por período. |
| `tests/test_etl_pipeline.py` | Testa validação de colunas, limpeza, padronização e transformação dos dados brutos. |
| `tests/test_rejections.py` | Testa a geração do relatório de transações rejeitadas e seus motivos. |
| `tests/test_sqlite_load.py` | Testa a carga dos dados tratados em uma base SQLite temporária. |

Para executar os testes:

```bash
python main.py test
```

Ou diretamente com pytest:

```bash
pytest
```

## Testes Manuais

A pasta `manual_tests/` contém scripts auxiliares usados para verificar partes do projeto durante o desenvolvimento.

Esses arquivos não substituem os testes automatizados, mas ajudam a validar manualmente pontos como contexto enviado para IA, leitura de dados, períodos disponíveis e conexão com SQLite.

Exemplo:

```bash
python manual_tests/teste_periodos.py
```

## Limitações

O FinanTec Data Pipeline não:

- acessa contas bancárias reais;
- utiliza dados financeiros reais de usuários;
- substitui orientação profissional;
- recomenda investimentos personalizados;
- garante rentabilidade ou resultados financeiros;
- consulta taxas ou produtos em tempo real;
- executa operações financeiras;
- possui login, autenticação ou múltiplos usuários;
- integra com instituições financeiras reais.

## Possíveis Evoluções Futuras

Algumas melhorias possíveis:

- permitir entrada manual de transações pela interface;
- permitir upload de uma planilha-modelo;
- criar uma experiência parecida com uma planilha simples de gastos;
- adicionar validações mais detalhadas dos arquivos enviados;
- criar relatórios em Excel ou PDF;
- adicionar filtros por categoria;
- carregar o dashboard com consultas mais específicas ao SQLite;
- adicionar PostgreSQL como alternativa futura ao SQLite;
- criar logs mais detalhados;
- mover arquivos processados automaticamente;
- evoluir para um fluxo simples de automação/RPA;
- ampliar a cobertura de testes automatizados.

## Status

Projeto independente em desenvolvimento.

Fluxo atual:

```text
CSV bruto → ETL com pandas → CSV processado → SQLite → dashboard Streamlit → IA explicando indicadores
```

Direção futura:

```text
Controle financeiro local → validação dos dados → SQLite → dashboard → IA explicando indicadores
```