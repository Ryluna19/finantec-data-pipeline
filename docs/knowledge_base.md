# Knowledge Base — FinanTec Data Pipeline

## Objetivo

Este documento descreve as fontes, os contextos e o ciclo de vida dos dados do
FinanTec.

Consulte também:

- [Project Overview](project_overview.md);
- [Contrato de Dados](data_contract.md);
- [Validação](validation.md);
- [ADR 001 — Remoção da integração com Gemini](decisions/001-remove-gemini-integration.md).

## Visão geral

O projeto trabalha com três grupos de dados:

```text
dados persistidos das contas
dados fictícios de demonstração
arquivos de ETL e compatibilidade
```

A persistência é acessada por uma camada comum que suporta:

- SQLite na execução local;
- Turso/libSQL na aplicação publicada.

Arquivos versionados são usados para demonstração, modelos de importação, ETL,
documentação e preservação histórica. Eles não substituem o banco utilizado
pelas operações normais da aplicação.

O FinanTec não consulta bancos, Open Finance ou instituições financeiras.

## Backends de persistência

O backend é selecionado pela variável:

```text
FINANTEC_DATABASE_BACKEND
```

| Valor | Comportamento |
|---|---|
| `sqlite` | Utiliza o arquivo local informado pela aplicação. |
| `turso` | Utiliza um banco remoto Turso por meio do driver libSQL. |

Quando a variável não é informada, o SQLite é utilizado como padrão.

O backend Turso exige:

```text
TURSO_DATABASE_URL
TURSO_AUTH_TOKEN
```

`src/database_connection.py` fornece a interface comum utilizada pelos
repositórios. A escolha do backend não deve alterar o significado das entidades
ou as regras de isolamento por usuário.

## Entidades persistidas

As principais tabelas da aplicação são:

| Tabela | Responsabilidade |
|---|---|
| `user_accounts` | Contas, credenciais protegidas e expiração opcional. |
| `login_attempts` | Falhas consecutivas e bloqueio temporário de login. |
| `transacoes_processadas` | Transações pessoais ou de demonstração. |
| `user_profiles` | Perfil financeiro associado ao usuário. |
| `financial_goals` | Metas financeiras. |
| `financial_goal_seed_state` | Estado auxiliar relacionado aos dados fictícios de metas. |
| `monthly_budgets` | Limites mensais por categoria. |
| `chat_messages` | Compatibilidade com a antiga funcionalidade de conversa. |

Os nomes preservam compatibilidade com a evolução histórica do projeto. Novas
operações não devem depender de tabelas antigas sem necessidade funcional.

## Contas e contexto do usuário

Cada conta possui um `user_id`. Após a autenticação, esse identificador compõe o
contexto utilizado pelas operações de leitura, escrita e exclusão.

```text
conta autenticada
        ↓
user_id da sessão
        ↓
serviço ou repositório
        ↓
registros pertencentes ao usuário
```

O `user_id` não é fornecido nos arquivos importados. A aplicação determina o
proprietário usando a conta autenticada, evitando que um arquivo atribua
transações a outro usuário.

### Conta permanente

Uma conta permanente possui `expires_at` nulo e exige o código de acesso
configurado no ambiente durante o cadastro.

### Conta temporária

Uma conta temporária recebe em `expires_at` o instante correspondente a 24
horas após sua criação.

Durante sua validade:

- os dados permanecem no backend configurado;
- o usuário pode sair e entrar novamente;
- a interface apresenta o tempo restante.

Após a expiração:

- a sessão deixa de ser aceita;
- a autenticação não é permitida;
- a rotina de limpeza remove a conta e seus dados associados.

A limpeza é acionada pela aplicação. Não existe um agendador externo executando
continuamente.

## Dados pessoais

Dados pessoais são aqueles cadastrados ou importados no contexto da conta
ativa. Eles podem incluir:

- transações;
- informações do perfil;
- fontes de renda;
- metas;
- orçamento;
- estados auxiliares vinculados a esses fluxos.

Um usuário novo pode começar com zero transações, metas e limites e sem perfil
configurado. Esses estados vazios são válidos.

A demonstração pública deve ser utilizada somente com dados fictícios.

## Dados de demonstração

O repositório contém dados simulados para apresentar a aplicação sem exigir
informações financeiras reais.

As principais fontes são:

| Fonte | Finalidade |
|---|---|
| `data/demo/` | Transações mensais simuladas. |
| `data/perfil_usuario.json` | Perfil e informações fictícias usadas na demonstração. |

O contexto de demonstração deve permanecer separado dos registros pessoais.
Alternar para a demonstração não pode sobrescrever ou mudar o proprietário dos
dados da conta.

Quando o modo de demonstração somente leitura está ativo, ações de escrita são
bloqueadas.

## Transações

O modelo financeiro normalizado possui os campos principais:

```text
data
tipo
descricao
categoria
valor
```

Depois da validação, a aplicação associa informações técnicas como:

- identificador da transação;
- usuário proprietário;
- modo de dados;
- origem;
- período;
- identidade do lote ou conteúdo importado.

O contrato completo está em [data_contract.md](data_contract.md).

## Fontes de entrada

As transações podem entrar por:

- cadastro manual;
- CSV no formato do FinanTec;
- Excel no formato do FinanTec;
- Excel externo por mapeamento assistido;
- OFX;
- CSV processado pelo ETL explícito.

Todas as origens devem convergir para o mesmo modelo normalizado antes da
persistência.

```text
entrada manual
CSV
Excel
OFX
        ↓
normalização e validação
        ↓
modelo canônico
        ↓
persistência associada ao usuário
```

## ETL e arquivos

O ETL continua disponível para processamento explícito de CSV. Ele não é um
pré-requisito para iniciar a interface.

| Caminho | Finalidade |
|---|---|
| `data/raw/` | Entradas do pipeline explícito. |
| `data/processed/transacoes_processadas.csv` | Registros válidos produzidos pelo ETL. |
| `data/processed/transacoes_rejeitadas.csv` | Linhas rejeitadas e seus motivos. |
| `data/templates/transacoes_template.csv` | Modelo do formato canônico. |
| `data/raw/imported/` | Compatibilidade com lotes locais de importação. |
| `logs/etl_transacoes.log` | Registro local da execução do ETL. |

Arquivos gerados durante a execução não devem ser versionados quando puderem
conter dados pessoais ou específicos da máquina.

## Arquivos históricos

Alguns arquivos preservam o contexto de uma funcionalidade antiga de
assistente financeiro:

- `data/historico_atendimento.csv`;
- `data/conceitos_financeiros.json`;
- `data/produtos_financeiros.json`.

Esses arquivos não representam integrações ou recursos ativos da aplicação.

O arquivo `data/raw/transacoes_manuais.csv` também pode existir em instalações
antigas. O cadastro manual atual persiste diretamente no backend configurado.

## Cálculos financeiros

Os cálculos ficam sob responsabilidade do código Python, principalmente em
`src/analytics.py`.

Entre os resultados estão:

- receitas;
- despesas de consumo;
- reserva;
- saldo;
- gastos por categoria;
- utilização do orçamento;
- progresso e simulação de metas.

Valores financeiros importantes não dependem de interpretação probabilística
ou de serviços externos de IA.

## Exclusão e ciclo de vida

### Apagar dados financeiros

Remove os registros financeiros associados ao usuário e preserva:

- conta;
- credenciais;
- capacidade de autenticação;
- dados fictícios de demonstração.

### Excluir conta

Remove a conta, as tentativas de login e os dados financeiros associados.

### Limpar contas vencidas

Identifica contas com `expires_at` encerrado e reutiliza o fluxo coordenado de
exclusão para remover seus registros.

Em todos os casos, dados pertencentes a outros usuários devem permanecer
inalterados.

## Versionamento e secrets

O `.gitignore` protege os principais artefatos locais:

```text
.env
.env.*
.streamlit/secrets.toml
database/*.db
database/*.sqlite
data/processed/*.csv
data/raw/imported/*.csv
logs/*.log
```

Não devem ser versionados:

- tokens do Turso;
- códigos de cadastro;
- bancos com dados pessoais;
- arquivos importados por usuários;
- relatórios e logs gerados localmente.

Arquivos de demonstração e modelos podem permanecer no Git porque contêm dados
simulados e fazem parte intencionalmente do projeto.

## Evolução futura

Uma possível V2 pode substituir a interface e o backend atuais, mas deve
preservar os princípios de dados já validados:

- um contrato normalizado para múltiplas origens;
- propriedade definida pelo usuário autenticado;
- validação antes da persistência;
- regras financeiras fora do frontend;
- migrations para mudanças de schema;
- exclusão coordenada dos registros associados.

PostgreSQL é uma direção possível para uma arquitetura com API separada e maior
concorrência. A mudança de banco não deve alterar o significado básico das
entidades.

## Status

Na V1 publicada:

```text
Turso/libSQL
→ persistência remota

SQLite
→ desenvolvimento e testes locais

arquivos versionados
→ demonstração, modelos, ETL e histórico

dados pessoais
→ associados ao user_id autenticado

contas temporárias
→ persistência por 24 horas e limpeza após expiração
```
