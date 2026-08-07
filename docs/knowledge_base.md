# Knowledge Base — FinanTec Data Pipeline

> [!NOTE]
> Este documento descreve as principais fontes de dados utilizadas pelo
> FinanTec e preserva o contexto histórico de arquivos que fizeram parte do
> antigo assistente financeiro com Gemini.
>
> As seções relacionadas à IA externa são históricas e não representam a
> execução atual.
>
> Consulte também:
>
> - [Project Overview](project_overview.md)
> - [Contrato de Dados](data_contract.md)
> - [ADR 001 — Remoção da integração externa com Gemini](decisions/001-remove-gemini-integration.md)

## Visão Geral

O FinanTec utiliza diferentes fontes de dados para atender três contextos
principais:

```text
dados pessoais
dados de demonstração
dados históricos/legados
```

A fonte principal de persistência da aplicação atual é o SQLite.

Os arquivos versionados no repositório são utilizados principalmente para:

- demonstração;
- templates;
- processamento pelo ETL;
- documentação;
- compatibilidade;
- preservação histórica.

A aplicação não utiliza dados bancários reais e não se conecta diretamente a
instituições financeiras.

---

## Classificação das Fontes

As fontes podem ser divididas em três grupos.

### Fontes atuais

São utilizadas pela aplicação ou pelo pipeline atual:

- `database/finantec.db`;
- `data/demo/`;
- `data/raw/`;
- `data/processed/`;
- `data/templates/`;
- `data/perfil_usuario.json`.

### Fontes locais geradas durante o uso

Podem ser criadas ou alteradas na máquina em que a aplicação é executada:

- banco SQLite;
- arquivos processados;
- relatórios de rejeição;
- logs;
- arquivos associados a lotes importados;
- dados pessoais persistidos.

Esses conteúdos não devem ser enviados ao GitHub quando contiverem dados de uso
local.

### Fontes históricas

Alguns arquivos permaneceram no projeto como registro da fase anterior com
assistente financeiro:

- `data/historico_atendimento.csv`;
- `data/conceitos_financeiros.json`;
- `data/produtos_financeiros.json`.

Eles não representam funcionalidades atuais da v1.

---

## Fontes de Dados

| Fonte | Formato | Finalidade atual |
|---|---|---|
| `database/finantec.db` | SQLite | Fonte principal dos dados persistidos da aplicação. |
| `data/demo/` | CSV | Transações financeiras simuladas utilizadas na demonstração. |
| `data/raw/` | CSV | Entrada para processamento explícito pelo pipeline e compatibilidade. |
| `data/raw/imported/` | Arquivos locais | Pode armazenar lotes relacionados à importação pela interface. |
| `data/processed/transacoes_processadas.csv` | CSV | Resultado tratado produzido pelo ETL. |
| `data/processed/transacoes_rejeitadas.csv` | CSV | Relatório de registros rejeitados pelo pipeline. |
| `data/perfil_usuario.json` | JSON | Fonte fictícia utilizada na composição de Perfil e Metas da demonstração. |
| `data/templates/transacoes_template.csv` | CSV | Modelo do contrato canônico de transações. |
| `data/historico_atendimento.csv` | CSV | Registro histórico da antiga funcionalidade de conversa. |
| `data/conceitos_financeiros.json` | JSON | Conteúdo educativo preservado da antiga fase de Insights. |
| `data/produtos_financeiros.json` | JSON | Conteúdo informativo preservado da antiga fase de Insights. |
| `data/raw/transacoes_manuais.csv` | CSV | Arquivo legado anterior à persistência direta no SQLite. |

Arquivos gerados em diretórios como:

```text
database/
data/processed/
data/raw/imported/
logs/
```

são considerados dados locais de execução.

---

## SQLite como Fonte Principal

Na v1 atual, o SQLite é a principal fonte de persistência.

A aplicação utiliza o banco para armazenar dados relacionados a diferentes
entidades, incluindo:

- contas locais;
- transações;
- perfil;
- metas;
- orçamento;
- dados auxiliares associados a esses fluxos.

O banco também permite que os principais registros sejam associados ao usuário
correto.

Fluxo conceitual:

```text
usuário autenticado
        ↓
ação na aplicação
        ↓
validação
        ↓
regra de negócio
        ↓
SQLite
```

Isso substituiu o modelo antigo em que arquivos intermediários tinham um papel
maior no uso normal da aplicação.

---

## Contas e Contexto de Usuário

A v1 possui contas locais.

Cada sessão autenticada estabelece um contexto de usuário utilizado pelos
principais fluxos da aplicação.

Conceitualmente:

```text
conta autenticada
        ↓
user_id
        ↓
transações
perfil
metas
orçamento
dados e privacidade
```

O `user_id` não é informado em arquivos importados pela pessoa usuária.

A aplicação é responsável por associar os registros ao contexto autenticado.

Isso evita que um arquivo determine arbitrariamente quem é proprietário de uma
transação.

---

## Dados Pessoais

Os dados pessoais são aqueles criados ou importados durante o uso da aplicação.

Eles podem incluir:

- transações;
- informações do perfil;
- fontes de renda;
- metas;
- orçamento;
- informações auxiliares relacionadas aos fluxos financeiros.

Um usuário novo pode possuir inicialmente:

```text
zero transações
zero metas
zero orçamento
nenhum perfil configurado
```

Esses estados são válidos.

A aplicação não deve preencher automaticamente o contexto pessoal com dados
fictícios da demonstração.

---

## Dados de Demonstração

O FinanTec possui uma base simulada para permitir que o produto seja explorado
sem exigir dados pessoais.

A personagem fictícia utilizada é:

```text
Marina Costa
```

Marina é apresentada como estudante universitária e estagiária.

O contexto demonstrativo contém exemplos de:

- receitas;
- despesas;
- reserva;
- categorias financeiras;
- metas;
- perfil.

Entre as metas fictícias estão:

- montar uma reserva para imprevistos;
- comprar um notebook.

Essas informações não representam uma pessoa real.

---

## Separação entre Demonstração e Dados Pessoais

A demonstração deve permanecer isolada do contexto pessoal.

O comportamento esperado é:

```text
Meus dados
        ↓
Demonstração
        ↓
Meus dados
```

Ao ativar a demonstração:

- os dados pessoais não devem ser sobrescritos;
- registros pessoais não devem mudar de proprietário;
- informações fictícias não devem ser persistidas como perfil pessoal.

Ao retornar para “Meus dados”, o contexto previamente armazenado continua sendo
utilizado.

---

## Perfil e Metas de Demonstração

O arquivo:

```text
data/perfil_usuario.json
```

é utilizado como fonte fictícia para partes da demonstração.

Perfil e Metas de Marina são compostos separadamente dos registros pessoais.

Conceitualmente:

```text
fonte fictícia
        ↓
composição em memória
        ↓
Perfil e Metas demonstrativos
        ↓
somente leitura
```

Eles não devem ser copiados automaticamente para:

- perfil pessoal;
- metas pessoais.

---

## Transações

Todas as transações utilizadas internamente convergem para um modelo canônico.

Os principais campos são:

```text
data
tipo
descricao
categoria
valor
```

O contrato completo está documentado em:

```text
docs/data_contract.md
```

Diferentes origens podem chegar a esse formato por caminhos diferentes:

```text
entrada manual ─────────┐
CSV FinanTec ───────────┤
Excel FinanTec ─────────┤
Excel externo ──────────┼→ normalização → validação → SQLite
OFX ────────────────────┘
```

Por isso, uma planilha externa ou arquivo OFX não precisa possuir desde a origem
as mesmas cinco colunas do formato canônico.

A conversão ocorre antes da persistência.

---

## CSV do Pipeline

O pipeline explícito trabalha com arquivos CSV em:

```text
data/raw/
```

O padrão esperado é:

```text
transacoes_*.csv
```

Uma convenção recomendada é:

```text
transacoes_AAAA_MM.csv
```

Exemplo:

```text
transacoes_2026_08.csv
```

Esses arquivos seguem diretamente o contrato canônico:

```text
data,tipo,descricao,categoria,valor
```

Exemplo:

```csv
data,tipo,descricao,categoria,valor
2026-08-05,receita,Bolsa-estágio,Trabalho,1600.00
2026-08-06,despesa,Compra no mercado,Alimentação,200.00
```

---

## Importação pela Interface

A interface permite importar diferentes formatos.

Atualmente estão contemplados:

- CSV;
- Excel;
- OFX;
- Excel externo por mapeamento assistido.

Os arquivos passam por etapas de preparação antes da persistência.

Fluxo geral:

```text
arquivo
        ↓
leitura
        ↓
mapeamento ou conversão
        ↓
normalização
        ↓
validação
        ↓
análise de possíveis duplicatas
        ↓
prévia
        ↓
SQLite
```

---

## Excel Externo

Planilhas externas podem possuir:

- nomes de colunas diferentes;
- múltiplas abas;
- linhas antes do cabeçalho;
- coluna de valor com sinal;
- coluna de tipo separada;
- débito e crédito em colunas distintas.

A importação assistida permite interpretar essas estruturas sem alterar o
modelo interno da aplicação.

Depois da conversão, as transações continuam utilizando:

```text
data
tipo
descricao
categoria
valor
```

---

## OFX

Arquivos OFX seguem uma estrutura própria e não são tratados como planilhas
comuns.

O fluxo é:

```text
OFX
        ↓
parser
        ↓
extração das transações
        ↓
normalização
        ↓
modelo do FinanTec
```

O resultado utiliza as mesmas regras financeiras aplicadas aos demais formatos.

---

## Possíveis Duplicatas

Durante uma importação, a aplicação compara os registros normalizados com os
dados já existentes.

A análise considera principalmente:

```text
data
tipo
descricao
categoria
valor
```

A quantidade de ocorrências também é relevante.

O objetivo é impedir duplicações acidentais sem assumir que toda transação
repetida é inválida.

O comportamento padrão é:

```text
possível duplicata
→ não importar
```

A pessoa usuária pode optar explicitamente por incluir possíveis duplicatas.

---

## Categorias

As categorias permitem agrupar transações para análise.

Entre as categorias presentes nos dados simulados estão:

- Trabalho;
- Alimentação;
- Transporte;
- Serviços;
- Assinaturas;
- Educação;
- Lazer;
- Saúde;
- Compras;
- Reserva.

A aplicação pode trabalhar com outras categorias válidas.

Não existe necessidade de restringir todos os registros a uma lista fixa.

---

## Categoria Reserva

`Reserva` possui significado específico nos cálculos.

Ela representa dinheiro separado para guardar.

Por padrão:

```text
despesa de consumo
≠
reserva
```

Os indicadores distinguem:

- gasto de consumo;
- valor separado para reserva;
- saldo disponível.

Isso evita apresentar dinheiro guardado como se tivesse sido simplesmente
consumido.

---

## Uso dos Dados pelo ETL

O ETL possui três etapas principais.

| Etapa | Uso dos dados |
|---|---|
| Extract | Lê arquivos CSV compatíveis disponíveis para processamento. |
| Transform | Valida, normaliza, converte e separa registros válidos e rejeitados. |
| Load | Produz arquivos processados e persiste a carga correspondente no SQLite. |

Fluxo:

```text
CSV
        ↓
Extract
        ↓
Transform
        ↓
válidos + rejeitados
        ↓
Load
```

O ETL não precisa ser executado automaticamente para que a aplicação seja usada
normalmente.

---

## Relatório de Rejeições

Quando o pipeline encontra registros inválidos, pode gerar:

```text
data/processed/transacoes_rejeitadas.csv
```

O arquivo registra as linhas rejeitadas e seus motivos.

Entre os exemplos estão:

- data inválida ou vazia;
- tipo vazio;
- tipo inválido;
- descrição vazia;
- categoria vazia;
- valor inválido ou vazio;
- valor menor ou igual a zero.

Uma linha pode possuir mais de um motivo.

Exemplo:

```text
data invalida ou vazia; tipo invalido; categoria vazia
```

Isso permite investigar por que determinada entrada não passou pela validação.

---

## Uso dos Dados pela Aplicação

Os dados persistidos são utilizados pela interface para diferentes áreas.

### Visão geral

Utiliza informações para apresentar:

- receitas;
- despesas;
- reserva;
- saldo;
- gastos por categoria;
- transações recentes;
- diagnóstico financeiro;
- resumo de orçamento.

### Transações

Utiliza a base para:

- consulta;
- filtros;
- cadastro;
- edição;
- exclusão;
- importação;
- exportação.

### Orçamento

Relaciona os limites planejados às transações reais do período para calcular:

- valor planejado;
- gasto;
- restante;
- excedente;
- percentual utilizado.

### Metas

Utiliza informações persistidas para:

- acompanhamento;
- progresso;
- valor restante;
- contribuição mensal;
- simulações.

### Perfil

Armazena informações utilizadas no contexto financeiro pessoal, como:

- nome de exibição;
- ocupação;
- fontes de renda;
- renda mensal;
- outras informações financeiras configuradas pela pessoa usuária.

### Dados e privacidade

Utiliza os repositórios para:

- resumir os dados armazenados;
- alternar o contexto pessoal e demonstrativo;
- apagar os dados financeiros;
- excluir definitivamente a conta.

---

## Cálculos Financeiros

Os principais cálculos permanecem sob responsabilidade do código Python.

A maior parte das regras analíticas está concentrada em:

```text
src/analytics.py
```

Entre os resultados utilizados pela aplicação estão:

- receitas;
- despesas;
- consumo;
- reserva;
- saldo;
- gastos por categoria;
- indicadores de orçamento;
- cálculos associados a metas.

O princípio continua sendo evitar que valores financeiros importantes dependam
de interpretação probabilística.

---

## Exclusão dos Dados

Existem duas operações distintas.

### Reset financeiro

```text
Apagar meus dados
```

remove os dados financeiros associados à conta, preservando:

- a própria conta;
- credenciais;
- capacidade de autenticação;
- dados da demonstração.

### Exclusão da conta

```text
Excluir conta
```

remove a conta e os dados associados a ela.

Essa separação faz parte das regras atuais de gerenciamento dos dados locais.

---

## Arquivos Locais e Versionamento

Dados produzidos durante a execução não devem ser enviados ao repositório quando
puderem conter informações pessoais ou específicas da máquina local.

Exemplos:

```text
database/finantec.db
data/processed/transacoes_processadas.csv
data/processed/transacoes_rejeitadas.csv
data/raw/imported/
logs/etl_transacoes.log
```

O `.gitignore` deve continuar protegendo esses conteúdos.

Arquivos de demonstração e templates podem permanecer versionados porque são
intencionalmente simulados.

---

## Registro Histórico — Assistente e Gemini

As seções seguintes registram uma fase anterior do projeto.

O FinanTec já possuiu um assistente financeiro integrado ao Gemini.

A integração externa não faz parte da aplicação atual.

Ela foi removida preventivamente porque poderia enviar contexto financeiro para
um serviço de terceiros.

Não existe evidência de que tenha ocorrido uma violação de dados.

A decisão foi motivada por:

- minimização de dados;
- privacidade;
- redução de dependências externas;
- baixo benefício em relação ao risco para o contexto local.

---

## Contexto Enviado Historicamente à IA

Na arquitetura antiga, a aplicação podia montar um contexto contendo:

- perfil;
- período;
- resumo financeiro;
- gastos por categoria;
- cálculos de metas;
- histórico de dúvidas;
- conceitos financeiros;
- produtos financeiros informativos.

A separação conceitual era:

```text
Python calcula
        ↓
IA explica
```

Os cálculos financeiros principais não deveriam ser delegados ao modelo.

Esse fluxo não existe na execução atual.

---

## Histórico de Atendimento

O arquivo:

```text
data/historico_atendimento.csv
```

pertence à fase histórica do assistente.

Ele não representa o histórico de uma funcionalidade atual da v1.

Sua permanência serve apenas como registro técnico ou compatibilidade histórica.

---

## Conceitos Financeiros

O arquivo:

```text
data/conceitos_financeiros.json
```

contém conteúdo educativo que foi utilizado na antiga experiência de Insights.

Esse conteúdo pode permanecer no repositório como material histórico.

Ele não significa que existe atualmente um assistente ativo consumindo essa
base.

---

## Produtos Financeiros Informativos

O arquivo:

```text
data/produtos_financeiros.json
```

contém informações simuladas e educativas.

Esses dados:

- não são atualizados em tempo real;
- não representam ranking de mercado;
- não representam recomendação;
- não substituem consulta a fontes financeiras atuais.

Durante a antiga integração, esse conteúdo servia apenas como contexto
informativo.

---

## Limitações das Fontes

O FinanTec não possui automaticamente:

- dados bancários reais;
- Open Finance;
- sincronização com instituições financeiras;
- extratos bancários em tempo real;
- taxas de investimentos em tempo real;
- ranking atualizado de bancos;
- cotação de ativos;
- recomendação personalizada de investimento;
- execução de operações financeiras;
- consulta externa automática de informações financeiras.

Arquivos importados podem naturalmente conter dados fornecidos pela própria
pessoa usuária.

Isso é diferente de a aplicação acessar uma instituição financeira por conta
própria.

---

## Execução Relacionada aos Dados

O projeto utiliza `main.py` como entrada central.

### Aplicação

```powershell
python main.py
```

ou:

```powershell
python main.py app
```

### ETL explícito

```powershell
python main.py etl
```

### Aplicação sem execução automática do ETL

```powershell
python main.py dev
```

### Testes

```powershell
python main.py test
```

---

## Evolução das Fontes na v2

A v2 deverá preservar a ideia de um modelo financeiro normalizado, mesmo com a
mudança de arquitetura.

Direção planejada:

```text
React
        ↓
API Python
        ↓
regras e validação
        ↓
persistência
```

As fontes de entrada continuarão precisando convergir para contratos claros.

Por exemplo:

```text
entrada manual
CSV
Excel
OFX
        ↓
contrato da API / serviço
        ↓
modelo financeiro normalizado
```

A camada React não deverá conhecer ou decidir regras internas de persistência.

---

## PostgreSQL

PostgreSQL é uma possibilidade futura, não uma exigência do modelo atual.

SQLite continua adequado para a v1 local.

Uma migração para PostgreSQL ganha justificativa quando existirem necessidades
como:

- backend publicado;
- múltiplos usuários simultâneos;
- maior concorrência;
- servidor central;
- infraestrutura de produção.

A mudança do banco não deve alterar o significado básico das entidades
financeiras.

---

## Princípio de Evolução dos Dados

O projeto deve evitar criar um modelo diferente para cada nova origem.

A direção desejada continua sendo:

```text
múltiplas fontes
        ↓
normalização
        ↓
regras compartilhadas
        ↓
persistência consistente
```

Da mesma forma, a evolução para uma arquitetura web não deve transferir regras
sensíveis para o frontend.

Os dados devem continuar sendo validados e associados ao usuário na camada
responsável pelas regras e pela persistência.

---

## Status

Na v1 atual:

```text
SQLite
→ fonte principal

arquivos
→ demonstração, importação, ETL, templates e compatibilidade

dados pessoais
→ associados à conta local

demonstração
→ isolada dos dados pessoais

antiga base de IA
→ histórico técnico
```

O antigo assistente financeiro e o histórico de conversas não fazem parte da
experiência atual.

A próxima evolução relevante relacionada aos dados não é adicionar novas fontes
aleatoriamente, mas revisar segurança, isolamento e persistência durante o
hardening e, posteriormente, preservar esses contratos na arquitetura da v2.