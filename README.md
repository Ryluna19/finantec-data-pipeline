# FinanTec Data Pipeline

Aplicação local de organização financeira com Python, pandas, SQLite e
Streamlit.

O projeto organiza transações financeiras, valida dados, salva as informações
em SQLite e exibe indicadores em um dashboard local.

O repositório inclui uma base de demonstração simulada. A aplicação também
permite registrar dados pessoais localmente, mas não acessa contas bancárias,
Open Finance ou instituições financeiras.

---

## Sobre o Projeto

O FinanTec começou como um pipeline para transformar arquivos brutos de
transações em uma base organizada. Hoje, o SQLite é a fonte principal dos dados
da aplicação, enquanto o ETL permanece disponível para demonstração,
compatibilidade e processamento explícito de arquivos.

A proposta é demonstrar um fluxo completo de dados aplicado a um contexto financeiro pessoal:

```text
Entrada manual ou importação → validação → SQLite → dashboard
```

A direção atual é manter o projeto como uma ferramenta local e pessoal, sem
login, múltiplos usuários reais ou integração bancária.

---

## Objetivo

Demonstrar um fluxo de dados aplicado a uma ferramenta financeira local:

- leitura de múltiplos arquivos CSV;
- validação da estrutura dos dados;
- limpeza e padronização com pandas;
- separação entre transações válidas e rejeitadas;
- geração de relatório de rejeições;
- carga dos dados processados em SQLite;
- análise por período;
- visualização em Streamlit;
- persistência e isolamento local dos principais dados;
- testes automatizados das regras e fluxos de maior risco.
- planejamento mensal de limites por categoria;
- comparação entre valores planejados e gastos efetivamente registrados;


---

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
- criação, acompanhamento e simulação de metas financeiras;
- resumo da validação dos dados no dashboard;
- perfil financeiro local;
- alternância entre dados pessoais e demonstração;
- exclusão segura somente das transações pessoais;
- comando centralizado de execução com `main.py`;
- entrada manual de transações pelo dashboard;
- edição e exclusão de transações persistidas;
- importação e exportação de arquivos CSV e Excel.
- orçamento mensal por categoria;
- criação, edição e exclusão de limites mensais;
- comparação entre valor planejado, gasto real e saldo disponível;
- identificação de categorias próximas ou acima do limite;
- resumo do orçamento mensal na Visão geral;

---

## Tecnologias Utilizadas

- Python
- pandas
- Streamlit
- SQLite
- pytest
- Altair
- openpyxl
- CSV
- JSON

---

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
Indicadores e metas calculados localmente
```

---

## Etapas do ETL

| Etapa | Descrição |
|---|---|
| Extract | Lê os arquivos CSV mensais armazenados em `data/raw/`. |
| Transform | Valida colunas, converte datas, padroniza textos, trata valores, separa linhas válidas e rejeitadas, e cria a coluna `ano_mes`. |
| Load | Salva os dados tratados em CSV processado e em uma base SQLite local. |

Quando existem linhas inválidas, o pipeline também gera:

```text
data/processed/transacoes_rejeitadas.csv
```

Esse arquivo contém as transações descartadas e uma coluna `motivo_rejeicao`, explicando por que cada linha não entrou na base final.

---

## Estrutura do Projeto

```text
finantec-data-pipeline/
├── assets/
│   └── styles.css
├── data/
│   ├── raw/
│   ├── processed/
│   └── templates/
├── database/
├── docs/
│   ├── decisions/
│   ├── ai_prompting.md
│   ├── data_contract.md
│   ├── knowledge_base.md
│   ├── project_overview.md
│   ├── roadmap.md
│   └── validation.md
├── logs/
│   └── .gitkeep
├── manual_tests/
│   ├── README.md
│   ├── _path_setup.py
│   ├── teste_dados.py
│   ├── teste_metas.py
│   ├── teste_periodos.py
│   └── teste_sqlite.py
├── scripts/
│   └── etl_transacoes.py
├── src/
│   ├── components/
│   ├── analytics.py
│   ├── app.py
│   ├── budget_repository.py
│   ├── data_loader.py
│   ├── data_reset.py
│   ├── goal_repository.py
│   ├── profile_repository.py
│   └── transaction_repository.py
├── tests/
│   └── test_*.py
├── .gitignore
├── AGENTS.md
├── main.py
├── README.md
└── requirements.txt
```

---

## Documentação

A pasta `docs/` reúne a documentação técnica e de produto do projeto.

| Arquivo | Finalidade |
|---|---|
| `docs/project_overview.md` | Visão geral do projeto, problema, solução, componentes e decisões técnicas. |
| `docs/data_contract.md` | Contrato de dados dos arquivos CSV de transações. |
| `docs/knowledge_base.md` | Explicação das fontes de dados usadas pelo pipeline e pelo dashboard. |
| `docs/ai_prompting.md` | Registro histórico da integração externa descontinuada. |
| `docs/decisions/001-remove-gemini-integration.md` | Decisão arquitetural de remover a integração com Gemini. |
| `docs/validation.md` | Estratégia de validação atual e registros históricos de testes. |
| `docs/roadmap.md` | Próximas evoluções planejadas para o projeto. |

---

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

Os arquivos versionados em `data/demo/` representam as transações mensais
da demonstração. O pipeline processa esses arquivos e gera uma base tratada
para análise.

Um uso pessoal novo pode começar sem perfil e sem metas. A demonstração não
preenche esses dados pessoais: o Perfil e as Metas fictícias são apresentados
somente no contexto demonstrativo e em modo de leitura.

---

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

## Comandos Principais

Para abrir o dashboard:

```bash
python main.py
```

Ou:

```bash
python main.py app
```

Para processar explicitamente os arquivos CSV pelo pipeline ETL:

```bash
python main.py etl
```

Para executar os testes automatizados:

```bash
python main.py test
```

Para abrir o dashboard sem executar o ETL:

```bash
python main.py dev
```

Para ver os comandos disponíveis:

```bash
python main.py help
```

---

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
O arquivo legado `data/raw/transacoes_manuais.csv` pode existir em instalações
antigas, mas a entrada manual atual grava diretamente no SQLite. Esse arquivo
continua sendo local e não deve ser versionado no GitHub.

---

## Integração Externa Descontinuada

O projeto já utilizou Gemini para complementar consultas financeiras. A
integração foi removida preventivamente porque poderia enviar perguntas,
histórico e contexto financeiro a um serviço externo, um risco incompatível
com a proposta local do produto.

Não houve violação de dados comprovada. A remoção foi uma decisão consciente de
minimização de dados e privacidade por concepção.

Os módulos locais de classificação, respostas determinísticas e persistência de
conversas foram preservados como registro técnico, mas o recurso está congelado
e não aparece na navegação principal.

Consulte a
[decisão arquitetural](docs/decisions/001-remove-gemini-integration.md) para o
contexto completo.

---

## Testes Automatizados

O projeto possui testes automatizados com `pytest` para validar o pipeline, as
regras financeiras, a persistência e os principais fluxos da aplicação.

| Arquivo | Finalidade |
|---|---|
| `tests/test_analytics.py` | Testa cálculos financeiros, separação entre consumo e reserva, metas, formatação de moeda e filtros por período. |
| `tests/test_etl_pipeline.py` | Testa validação de colunas, preparação dos dados, separação entre linhas válidas e rejeitadas, transformação e ordenação final. |
| `tests/test_transaction_*.py` | Testa identidade, arquivos, repositórios, sincronização, CRUD e composição da tela de transações. |
| `tests/test_goal_*.py` | Testa persistência, isolamento, cálculos e composição da tela de metas. |
| `tests/test_budget_repository.py` | Testa persistência, isolamento, validações e CRUD dos limites mensais. |
| `tests/test_budget_component.py` | Testa períodos, estados, resumos e funções auxiliares da interface de orçamento. |
| `tests/test_profile_*.py` | Testa perfil, fontes de renda e persistência. |
| `tests/test_data_reset.py` | Testa a exclusão limitada às transações pessoais e arquivos relacionados. |
| `tests/test_financial_*.py` | Preserva testes do mecanismo local e determinístico de consultas financeiras. |

Para executar os testes:

```bash
python main.py test
```

Ou diretamente com pytest:

```bash
pytest
```

---

## Testes Manuais

A pasta `manual_tests/` contém scripts auxiliares usados para verificar partes do projeto durante o desenvolvimento.

Esses arquivos não substituem os testes automatizados, mas ajudam a validar manualmente pontos como leitura de dados, períodos disponíveis e conexão com SQLite.

Exemplos:

```bash
python manual_tests/teste_dados.py
python manual_tests/teste_metas.py
python manual_tests/teste_periodos.py
python manual_tests/teste_sqlite.py
```

---

## Limitações

O FinanTec Data Pipeline não:

- acessa contas bancárias reais;
- envia perguntas ou contexto financeiro para serviços externos;
- substitui orientação profissional;
- recomenda investimentos personalizados;
- garante rentabilidade ou resultados financeiros;
- consulta taxas ou produtos em tempo real;
- executa operações financeiras;
- possui login, autenticação ou múltiplos usuários;
- integra com instituições financeiras reais.

---

## Possíveis Evoluções Futuras

Algumas melhorias possíveis:

- planejar a exclusão coordenada de todos os dados locais;
- manter a experiência em mobile, notebook e widescreen protegida contra
  regressões;
- limpar compatibilidades antigas somente quando houver migração segura;
- ampliar relatórios somente quando responderem a necessidades reais;
- avaliar deploy, autenticação e PostgreSQL depois da estabilização local.

---

## Status

Projeto independente em desenvolvimento.

Fluxo atual:

```text
Entrada manual ou importação → validação → SQLite → dashboard Streamlit
```

Navegação principal:

```text
Visão geral → Transações → Orçamento → Metas
```

O ETL continua disponível para demonstração, compatibilidade e execução
explícita. O mecanismo local de Insights está congelado fora da navegação
principal. A primeira revisão global de responsividade foi concluída e a
documentação descreve o estado atual e o histórico das decisões do produto.
