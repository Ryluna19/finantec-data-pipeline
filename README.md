# FinanTec Data Pipeline

Aplicação de organização financeira com Python, pandas, SQLite, Streamlit e insights calculados localmente.

O projeto organiza transações financeiras, valida dados, salva as informações em SQLite, exibe indicadores em um dashboard e responde consultas financeiras por meio de cálculos locais.

O FinanTec Data Pipeline não utiliza dados bancários reais. Todos os dados são simulados.

---

## Sobre o Projeto

O FinanTec Data Pipeline transforma arquivos brutos de transações financeiras em uma base organizada para análise.

A proposta é demonstrar um fluxo completo de dados aplicado a um contexto financeiro pessoal:

```text
CSV bruto → ETL → SQLite → dashboard → insights financeiros locais
```

A ideia atual é manter o projeto como uma ferramenta local/pessoal de gestão financeira simulada, sem login, múltiplos usuários ou integração bancária real.

---

## Objetivo

Demonstrar um fluxo básico de dados aplicado a finanças pessoais simuladas:

- leitura de múltiplos arquivos CSV;
- validação da estrutura dos dados;
- limpeza e padronização com pandas;
- separação entre transações válidas e rejeitadas;
- geração de relatório de rejeições;
- carga dos dados processados em SQLite;
- análise por período;
- visualização em Streamlit;
- consultas e explicações financeiras calculadas localmente.

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
- simulador de metas financeiras;
- resumo da validação dos dados no dashboard;
- assistente financeiro local para consultas sobre os dados do período;
- histórico de conversa separado por período analisado;
- processamento local das perguntas, sem envio de informações financeiras para serviços externos;
- comando centralizado de execução com `main.py`.
- entrada manual de transações pelo dashboard;
- edição local de transações em formato de tabela com `st.data_editor`;
- salvamento de transações manuais em `data/raw/transacoes_manuais.csv`;

---

## Tecnologias Utilizadas

- Python
- pandas
- Streamlit
- SQLite
- pytest
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
Consultas e insights calculados localmente
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
│   ├── README.md
│   ├── _path_setup.py
│   ├── teste_dados.py
│   ├── teste_metas.py
│   ├── teste_periodos.py
│   └── teste_sqlite.py
├── scripts/
│   └── etl_transacoes.py
├── src/
│   ├── analytics.py
│   ├── app.py
│   ├── data_loader.py
├── tests/
│   ├── test_analytics.py
│   ├── test_etl_pipeline.py
│   ├── test_rejections.py
│   └── test_sqlite_load.py
├── .gitignore
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
| `docs/ai_prompting.md` | Registro da integração externa descontinuada, pendente de revisão documental. |
| `docs/validation.md` | Estratégia de validação, testes automatizados, testes manuais e limitações. |
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

Os arquivos em `data/raw/` representam transações mensais brutas. O pipeline processa esses arquivos e gera uma base tratada para análise.

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
data/raw/transacoes_manuais.csv
```

Esses arquivos são gerados localmente e não precisam ser versionados no GitHub.

O arquivo `transacoes_rejeitadas.csv` só é criado quando existem linhas inválidas nos arquivos de entrada.
O arquivo `data/raw/transacoes_manuais.csv` é criado pelo editor manual de transações e representa dados locais inseridos pela interface. Ele não deve ser versionado no GitHub.
---

## Exemplos de Perguntas para o Assistente Local

```text
Em qual categoria eu mais gastei neste período?
```

```text
Qual é meu saldo neste período?
```

```text
Quanto entrou?
```

```text
Quanto eu gastei?
```

```text
Quanto eu separei para reserva neste período?
```

```text
Me dê um resumo financeiro.
```

As respostas são calculadas localmente. Perguntas não reconhecidas não são enviadas para serviços externos.

---

## Testes Automatizados

O projeto possui testes automatizados com `pytest` para validar partes importantes do pipeline e da lógica financeira.

| Arquivo | Finalidade |
|---|---|
| `tests/test_analytics.py` | Testa cálculos financeiros, separação entre consumo e reserva, metas, formatação de moeda e filtros por período. |
| `tests/test_etl_pipeline.py` | Testa validação de colunas, preparação dos dados, separação entre linhas válidas e rejeitadas, transformação e ordenação final. |
| `tests/test_rejections.py` | Testa a geração do relatório de transações rejeitadas e seus motivos. |
| `tests/test_sqlite_load.py` | Testa a carga dos dados tratados em uma base SQLite temporária. |
| `tests/test_transaction_editor.py` | Testa preparação, salvamento e carregamento das transações manuais. |

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
- utiliza dados financeiros reais de usuários;
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

- melhorar a entrada manual de transações pela interface;
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
- persistir histórico de conversas em banco;
- ampliar a cobertura de testes automatizados.

---

## Status

Projeto independente em desenvolvimento.

Fluxo atual:

```text
CSV bruto → ETL com pandas → CSV processado → SQLite → dashboard Streamlit → insights financeiros locais
```

Direção futura:

```text
Controle financeiro local → validação dos dados → SQLite → dashboard → insights financeiros locais
```
