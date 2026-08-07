# FinanTec Data Pipeline

Aplicação local de organização financeira com Python, pandas, SQLite e
Streamlit.

O projeto organiza transações financeiras, valida dados, salva as informações
em SQLite e exibe indicadores em uma interface local.

O repositório inclui uma base de demonstração simulada. A aplicação também
permite criar contas locais e registrar dados pessoais, mas não acessa contas
bancárias, Open Finance ou instituições financeiras reais.

---

## Sobre o Projeto

O FinanTec começou como um pipeline para transformar arquivos brutos de
transações em uma base organizada. Hoje, o SQLite é a fonte principal dos dados
da aplicação, enquanto o ETL permanece disponível para demonstração,
compatibilidade e processamento explícito de arquivos.

A proposta atual é demonstrar um fluxo completo de organização financeira
pessoal, combinando persistência, validação e interface:

```text
Conta local
    ↓
Entrada manual ou importação
    ↓
Validação e normalização
    ↓
SQLite
    ↓
Interface Streamlit
```

A versão 1 é uma aplicação local com contas autenticadas e isolamento dos dados
por usuário. O sistema de autenticação atual foi projetado para esse contexto
local e ainda não deve ser tratado como uma solução pronta para exposição
pública ou uso multiusuário em produção.

---

## Objetivo

Demonstrar um fluxo de dados aplicado a uma ferramenta financeira local:

- leitura e importação de diferentes fontes de transações;
- validação da estrutura dos dados;
- limpeza e padronização com pandas;
- separação entre transações válidas e rejeitadas;
- geração de relatório de rejeições;
- carga e persistência dos dados em SQLite;
- autenticação e isolamento local por usuário;
- análise por período;
- visualização em Streamlit;
- persistência dos principais dados financeiros;
- testes automatizados das regras e fluxos de maior risco;
- planejamento mensal de limites por categoria;
- comparação entre valores planejados e gastos efetivamente registrados;
- gerenciamento de metas e perfil financeiro;
- controle dos dados associados à conta.

---

## Funcionalidades

### Contas e dados pessoais

- criação e autenticação de contas locais;
- armazenamento seguro do hash da senha;
- isolamento dos principais dados por usuário;
- perfil financeiro persistido;
- alternância entre dados pessoais e demonstração;
- exclusão dos dados financeiros preservando a conta;
- exclusão definitiva da conta e dos dados associados.

### Transações

- entrada manual de transações pela interface;
- edição e exclusão de transações persistidas;
- filtros e análise por período;
- importação de arquivos CSV e Excel no formato do FinanTec;
- importação de arquivos OFX com conversão automática;
- importação assistida de planilhas Excel externas, com seleção de aba e
  cabeçalho;
- mapeamento de colunas para valor único, tipo explícito ou débito e crédito
  separados;
- prévia e validação antes da importação;
- identificação e tratamento seguro de possíveis duplicatas;
- exportação das transações do período em Excel.

### Organização financeira

- resumo de receitas, gastos, reserva e saldo;
- gráfico de gastos por categoria;
- criação, acompanhamento, edição e exclusão de metas financeiras;
- simulador de metas sem alteração dos dados persistidos;
- orçamento mensal por categoria;
- criação, edição e exclusão de limites mensais;
- continuidade e encerramento de limites entre períodos;
- comparação entre valor planejado, gasto real e saldo disponível;
- identificação de categorias próximas ou acima do limite;
- resumo do orçamento mensal na Visão geral;
- perfil financeiro com fontes de renda e informações pessoais relacionadas ao
  planejamento.

### Pipeline e qualidade dos dados

- pipeline ETL para transações financeiras simuladas;
- leitura de arquivos em `data/raw/`;
- validação de colunas obrigatórias;
- tratamento de datas, tipos, descrições, categorias e valores;
- criação da coluna `ano_mes`;
- remoção de linhas inválidas da base final;
- geração de relatório de transações rejeitadas com motivo da rejeição;
- geração de arquivo tratado em `data/processed/`;
- carga dos dados processados em SQLite;
- resumo da validação dos dados;
- comando centralizado de execução com `main.py`.

---

## Tecnologias Utilizadas

- Python
- pandas
- Streamlit
- SQLite
- pytest
- Altair
- openpyxl
- ofxparse2
- CSV
- JSON

---

## Fluxo do Pipeline

O ETL permanece como uma parte independente do projeto para processamento
explícito dos arquivos de entrada:

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
```

Na utilização normal da aplicação, o SQLite funciona como fonte principal para
a interface:

```text
Conta autenticada
    ↓
Entrada manual ou importação
    ↓
Validação
    ↓
SQLite
    ↓
Streamlit
    ↓
Indicadores, orçamento, metas e perfil
```

---

## Etapas do ETL

| Etapa | Descrição |
|---|---|
| Extract | Lê os arquivos CSV mensais armazenados em `data/raw/`. |
| Transform | Valida colunas, converte datas, padroniza textos, trata valores, separa linhas válidas e rejeitadas e cria a coluna `ano_mes`. |
| Load | Salva os dados tratados em CSV processado e em uma base SQLite local. |

Quando existem linhas inválidas, o pipeline também gera:

```text
data/processed/transacoes_rejeitadas.csv
```

Esse arquivo contém as transações descartadas e uma coluna
`motivo_rejeicao`, explicando por que cada linha não entrou na base final.

---

## Estrutura do Projeto

```text
finantec-data-pipeline/
├── assets/
│   ├── branding/
│   └── styles/
├── data/
│   ├── demo/
│   ├── processed/
│   ├── raw/
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
├── manual_tests/
├── scripts/
│   └── etl_transacoes.py
├── src/
│   ├── components/
│   ├── account_repository.py
│   ├── analytics.py
│   ├── app.py
│   ├── budget_repository.py
│   ├── data_loader.py
│   ├── data_reset.py
│   ├── goal_repository.py
│   ├── profile_repository.py
│   ├── transaction_repository.py
│   └── user_context.py
├── tests/
│   └── test_*.py
├── .gitignore
├── AGENTS.md
├── main.py
├── README.md
└── requirements.txt
```

A estrutura acima destaca os componentes principais. O diretório `src/`
também contém serviços auxiliares responsáveis por importação, validação,
sincronização e manipulação das transações.

---

## Documentação

A pasta `docs/` reúne a documentação técnica e de produto do projeto.

| Arquivo | Finalidade |
|---|---|
| `docs/project_overview.md` | Visão geral do projeto, problema, solução, componentes e decisões técnicas. |
| `docs/data_contract.md` | Contrato de dados das transações processadas pelo projeto. |
| `docs/knowledge_base.md` | Explicação das fontes de dados usadas pelo pipeline e pela aplicação. |
| `docs/ai_prompting.md` | Registro histórico da antiga arquitetura de assistente e integração externa. |
| `docs/decisions/001-remove-gemini-integration.md` | Decisão arquitetural de remover a integração com Gemini. |
| `docs/validation.md` | Estratégia de validação atual e registros históricos de testes. |
| `docs/roadmap.md` | Estado da v1 e próximas etapas planejadas para a evolução do projeto. |

---

## Base de Dados Simulada

A base de demonstração representa a vida financeira fictícia de Marina Costa,
uma estudante universitária e estagiária.

Os dados incluem:

- receitas mensais;
- gastos de consumo;
- valor separado para reserva;
- categorias de despesas;
- metas financeiras;
- conceitos financeiros básicos;
- produtos financeiros apenas informativos.

Os arquivos versionados em `data/demo/` representam as transações mensais da
demonstração. O pipeline processa esses arquivos e gera uma base tratada para
análise.

Um uso pessoal novo pode começar sem perfil, metas, orçamento ou transações.
A demonstração não substitui os dados pessoais do usuário e pode ser ativada ou
desativada sem sobrescrever o contexto pessoal da conta.

---

## Como Executar o Projeto

### 1. Clone o repositório

```bash
git clone https://github.com/Ryluna19/finantec-data-pipeline.git
cd finantec-data-pipeline
```

### 2. Crie e ative o ambiente virtual

No Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instale as dependências

```powershell
pip install -r requirements.txt
```

---

## Comandos Principais

Para abrir a aplicação:

```powershell
python main.py
```

Ou:

```powershell
python main.py app
```

Para processar explicitamente os arquivos CSV pelo pipeline ETL:

```powershell
python main.py etl
```

Para executar os testes automatizados:

```powershell
python main.py test
```

Para abrir a aplicação sem executar o ETL:

```powershell
python main.py dev
```

Para ver os comandos disponíveis:

```powershell
python main.py help
```

---

## Arquivos Gerados Localmente

Ao executar a aplicação ou o ETL, o projeto pode gerar arquivos como:

```text
data/processed/transacoes_processadas.csv
data/processed/transacoes_rejeitadas.csv
database/finantec.db
logs/etl_transacoes.log
```

Esses arquivos são gerados localmente e não precisam ser versionados no GitHub.

O arquivo `transacoes_rejeitadas.csv` só é criado quando existem linhas
inválidas nos arquivos de entrada.

O arquivo legado `data/raw/transacoes_manuais.csv` pode existir em instalações
antigas, mas a entrada manual atual grava diretamente no SQLite. Esse arquivo
continua sendo local e não deve ser versionado no GitHub.

---

## Integração Externa Descontinuada

O projeto já utilizou Gemini para complementar consultas financeiras. A
integração foi removida preventivamente porque poderia enviar perguntas,
histórico e contexto financeiro a um serviço externo, um risco incompatível com
a proposta local do produto.

Não houve violação de dados comprovada. A remoção foi uma decisão consciente de
minimização de dados e privacidade por concepção.

Parte do código, dos testes e da documentação dessa fase foi preservada como
registro técnico e histórico. O assistente financeiro, o histórico de
conversas e o antigo recurso de Insights não fazem parte das funcionalidades
atuais da aplicação.

Consulte a
[decisão arquitetural](docs/decisions/001-remove-gemini-integration.md) para o
contexto completo.

---

## Testes Automatizados

O projeto utiliza `pytest` para validar o pipeline, as regras financeiras, a
persistência, o isolamento de dados e os principais fluxos da aplicação.

Entre as principais áreas cobertas estão:

| Área | Finalidade |
|---|---|
| Analytics | Cálculos financeiros, categorias, períodos, saldo e formatação. |
| ETL | Validação, transformação, rejeições e carga dos dados. |
| Contas | Criação, autenticação, senha e isolamento entre usuários. |
| Transações | Identidade, persistência, sincronização, CRUD e importação. |
| Importação | CSV, Excel, OFX, mapeamento assistido e duplicatas. |
| Perfil | Persistência e isolamento das informações financeiras pessoais. |
| Metas | CRUD, isolamento, cálculos e simulação. |
| Orçamento | CRUD, recorrência, períodos, isolamento e acompanhamento dos limites. |
| Dados e privacidade | Exclusão de dados financeiros, preservação da conta e exclusão definitiva da conta. |
| Interface | Estados e funções auxiliares dos principais componentes Streamlit. |

Alguns testes relacionados ao antigo mecanismo local de consultas financeiras
permanecem no repositório como cobertura de código legado. Esse mecanismo não
faz parte da experiência atual da aplicação.

Para executar a suíte:

```powershell
python main.py test
```

Ou diretamente com pytest:

```powershell
pytest
```

---

## Testes Manuais

A pasta `manual_tests/` contém scripts auxiliares usados durante o
desenvolvimento para verificar partes específicas do projeto.

Esses arquivos não substituem os testes automatizados. A validação final da v1
também incluiu testes manuais dos principais fluxos diretamente pela interface,
como:

- criação, edição e exclusão de transações;
- importação e tratamento de duplicatas;
- orçamento mensal;
- metas e simulador;
- perfil financeiro;
- alternância entre dados pessoais e demonstração;
- exclusão dos dados financeiros;
- exclusão de conta;
- responsividade em desktop, notebook e mobile.

Os scripts auxiliares existentes podem ser executados individualmente quando
necessário, por exemplo:

```powershell
python manual_tests/teste_dados.py
python manual_tests/teste_metas.py
python manual_tests/teste_periodos.py
python manual_tests/teste_sqlite.py
```

---

## Limitações

O FinanTec Data Pipeline não:

- acessa contas bancárias reais;
- utiliza Open Finance;
- envia perguntas ou contexto financeiro para serviços externos;
- substitui orientação financeira profissional;
- recomenda investimentos personalizados;
- garante rentabilidade ou resultados financeiros;
- consulta taxas ou produtos financeiros em tempo real;
- executa operações financeiras;
- possui autenticação preparada para exposição pública ou uso multiusuário em
  produção;
- possui infraestrutura de produção, monitoramento ou processo de deploy
  público;
- integra com instituições financeiras reais.

A autenticação existente na v1 protege e separa contas no contexto local da
aplicação. Uma eventual publicação web exigirá nova avaliação de segurança,
sessões, autorização e infraestrutura.

---

## Possíveis Evoluções Futuras

A evolução do projeto deve preservar a v1 local como uma versão funcional e
evitar mudanças arquiteturais sem benefício concreto.

### Hardening da v1

Antes da migração arquitetural, está planejada uma revisão específica de
segurança e qualidade, incluindo:

- autenticação e armazenamento de credenciais;
- isolamento entre usuários;
- consultas e persistência no SQLite;
- importação e manipulação de arquivos;
- dependências;
- segredos e configurações;
- logs e exposição acidental de dados;
- fluxos de exclusão de dados e conta.

O objetivo dessa etapa é corrigir problemas relevantes encontrados na v1, e não
transformá-la em uma aplicação web de produção.

### Versão 2

A direção planejada para a v2 é separar frontend e backend:

```text
React
    ↓ HTTP
API Python
    ↓
Regras e serviços da aplicação
    ↓
Persistência
```

Essa evolução deve incluir:

- frontend em React;
- backend Python exposto por API;
- reaproveitamento gradual das regras de negócio já validadas na v1;
- autenticação e autorização projetadas para a arquitetura web;
- testes de backend e frontend;
- validações automatizadas de qualidade e segurança;
- CI desde as etapas iniciais da v2;
- processo de deploy somente quando a aplicação estiver preparada para
  publicação;
- PostgreSQL e migrations quando concorrência, múltiplos usuários ou
  infraestrutura de produção justificarem a mudança.

A migração deve ser incremental. A intenção não é descartar a v1 e reescrever
todo o produto de uma única vez.

---

## Status

A versão 1 local está funcionalmente concluída e em fase de fechamento
documental e estabilização final.

Fluxo principal:

```text
Conta local
    ↓
Entrada manual ou importação
    ↓
Validação
    ↓
SQLite
    ↓
Interface Streamlit
```

Áreas funcionais da v1:

```text
Visão geral
Transações
Orçamento
Metas
Perfil
Dados e privacidade
```

O ETL continua disponível para demonstração, compatibilidade e execução
explícita.

A antiga integração com Gemini, o assistente financeiro, o histórico de
conversas e o mecanismo de Insights permanecem apenas como histórico técnico
quando ainda existem referências no código, nos testes ou na documentação. Eles
não fazem parte da navegação ou das funcionalidades atuais da v1.

A revisão global de responsividade foi concluída em desktop, notebook e mobile.
Os fluxos funcionais principais também passaram por validação manual antes do
fechamento da versão.

A etapa seguinte ao fechamento da v1 será uma revisão de segurança e hardening.
Depois dela, o projeto poderá iniciar a evolução arquitetural gradual para a v2.