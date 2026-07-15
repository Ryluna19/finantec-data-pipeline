# Knowledge Base — FinanTec Data Pipeline

> [!NOTE]
> Este documento preserva a organização da base usada durante a fase com
> Gemini. As seções sobre envio de contexto e respostas com IA são históricas
> e não representam a execução atual. Consulte a
> [visão geral atual](project_overview.md) e a
> [decisão de remover a integração externa](decisions/001-remove-gemini-integration.md).

## Visão Geral

A base de conhecimento do FinanTec Data Pipeline reúne os dados simulados que
acompanham o repositório e registra como eles foram usados nas diferentes fases
do projeto. Entre essas fontes, o perfil fictício e suas metas são usados
ativamente somente no contexto de demonstração; as fontes da antiga integração
externa permanecem como registro histórico.

A base combina arquivos de transações, perfil fictício da pessoa usuária, histórico de dúvidas, conceitos financeiros e produtos financeiros informativos.

O objetivo atual é documentar as fontes da demonstração, o pipeline e as
decisões de cálculo. O uso dessas fontes pela antiga integração externa está
preservado como contexto histórico.

O projeto não utiliza dados bancários reais.

---

## Fontes de Dados

| Fonte | Formato | Finalidade |
|---|---|---|
| `data/demo/` | CSV | Armazena os arquivos versionados de transações financeiras simuladas. |
| `data/raw/` | CSV | Recebe arquivos locais de compatibilidade e lotes importados pela interface. |
| `data/processed/transacoes_processadas.csv` | CSV | Base tratada gerada pelo pipeline ETL. |
| `data/processed/transacoes_rejeitadas.csv` | CSV | Relatório local de linhas rejeitadas e seus motivos, gerado apenas quando há dados inválidos. |
| `database/finantec.db` | SQLite | Fonte principal local, atualizada pela interface e também pelo ETL explícito. |
| `data/perfil_usuario.json` | JSON | Fonte do Perfil e das Metas fictícias da demonstração, compostos em memória e sem persistência nas tabelas pessoais. |
| `data/historico_atendimento.csv` | CSV | Registro simulado preservado da fase histórica de consultas financeiras. |
| `data/conceitos_financeiros.json` | JSON | Conteúdo educativo preservado da fase histórica de Insights. |
| `data/produtos_financeiros.json` | JSON | Conteúdo informativo e simulado preservado da fase histórica de Insights. |
| `data/templates/transacoes_template.csv` | CSV | Modelo de preenchimento para novas transações. |
| `data/raw/transacoes_manuais.csv` | CSV | Arquivo legado de instalações anteriores à persistência manual direta no SQLite. |

Os arquivos gerados em `data/processed/`, `database/` e `logs/` são locais e não são versionados no GitHub.

---

## Pessoa Usuária Fictícia

A base utiliza uma pessoa fictícia chamada Marina Costa.

Marina é estudante universitária e estagiária. Ela recebe uma bolsa-estágio mensal, possui uma pequena reserva para imprevistos e deseja organizar melhor seus gastos e metas financeiras.

As metas principais cadastradas são:

- montar uma reserva para imprevistos;
- comprar um notebook.

O uso de uma pessoa fictícia permite demonstrar o fluxo técnico sem utilizar dados pessoais ou bancários reais.

No contexto demonstrativo, o Perfil e as Metas de Marina são apresentados
somente para leitura. Eles não são copiados para o perfil ou para as metas
pessoais.

---

## Transações Financeiras

Os arquivos de transações representam receitas e despesas mensais.
As transações cadastradas pela interface são validadas e gravadas diretamente
no SQLite. O arquivo `data/raw/transacoes_manuais.csv` permanece apenas como
compatibilidade com instalações antigas e não é criado pelo fluxo atual.

Cada arquivo bruto deve seguir o padrão definido em:

```text
docs/data_contract.md
```

As colunas obrigatórias são:

```text
data,tipo,descricao,categoria,valor
```

Exemplo:

```csv
data,tipo,descricao,categoria,valor
2026-08-05,receita,Bolsa-estágio,Trabalho,1600.00
2026-08-06,despesa,Compra no mercado,Alimentação,200.00
```

O pipeline lê arquivos em `data/raw/` com o padrão:

```text
transacoes_*.csv
```

O padrão recomendado de nome é:

```text
transacoes_AAAA_MM.csv
```

---

## Categorias Utilizadas

As categorias principais usadas nos dados simulados são:

- Trabalho
- Alimentação
- Transporte
- Serviços
- Assinaturas
- Educação
- Lazer
- Saúde
- Compras
- Reserva

A categoria `Reserva` possui tratamento especial no projeto.

Ela representa dinheiro guardado e não é considerada gasto de consumo por padrão. Por isso, os cálculos financeiros separam:

- gasto de consumo;
- valor separado para reserva;
- saldo disponível.

Essa separação evita uma interpretação incorreta de que dinheiro guardado foi simplesmente consumido.

---

## Uso dos Dados pelo Pipeline

O pipeline ETL utiliza os dados da seguinte forma:

| Etapa | Uso dos dados |
|---|---|
| Extract | Lê os arquivos CSV disponíveis em `data/raw/`. |
| Transform | Valida colunas, limpa textos, converte datas e valores, separa linhas válidas e rejeitadas, e cria `ano_mes`. |
| Load | Salva os dados tratados em `data/processed/` e em SQLite. |

A aplicação usa o SQLite como fonte principal. Antes da criação da tabela
particionada, existe somente um fallback de compatibilidade para o CSV
processado do usuário local; arquivos brutos não são processados
automaticamente ao abrir o aplicativo.

Fluxo simplificado:

```text
Entrada manual ou importação → validação → SQLite → dashboard

CSV de demonstração → ETL explícito → CSV processado → SQLite

Perfil e metas fictícios → composição em memória → interface somente leitura
```

---

## Relatório de Rejeições

Quando o pipeline encontra linhas inválidas nos arquivos de entrada, ele gera um relatório local:

```text
data/processed/transacoes_rejeitadas.csv
```

Esse relatório contém as linhas descartadas e uma coluna:

```text
motivo_rejeicao
```

Exemplos de motivos:

- data inválida ou vazia;
- tipo vazio;
- tipo inválido;
- descrição vazia;
- categoria vazia;
- valor inválido ou vazio;
- valor menor ou igual a zero.

Uma mesma linha pode acumular mais de um motivo.

Esse relatório melhora a rastreabilidade do pipeline e ajuda a corrigir arquivos de entrada sem perder a informação de por que uma transação foi descartada.

---

## Uso dos Dados pelo Dashboard

O dashboard em Streamlit utiliza a base tratada para exibir:

- período analisado;
- quantidade de transações válidas;
- rejeições disponíveis no processamento ou na importação atual;
- receitas do período;
- gasto de consumo;
- valor separado para reserva;
- saldo disponível;
- maior categoria de consumo;
- gráfico de gastos por categoria;
- simulação de metas financeiras;
- consulta e gerenciamento das transações;
- acompanhamento de metas pessoais persistentes e metas fictícias somente
  para leitura.

Os cálculos são feitos em Python, principalmente no arquivo:

```text
src/analytics.py
```

A interface principal fica em:

```text
src/app.py
```

---

## Registro Histórico: Uso dos Dados pela IA

Todo o conteúdo desta seção descreve a integração externa descontinuada. A
execução atual não monta nem envia esse contexto para serviços externos.

A IA generativa não calculava os valores financeiros principais.

Antes de enviar uma pergunta ao modelo, a aplicação monta um contexto com:

- perfil da pessoa usuária;
- período analisado;
- resumo financeiro calculado;
- gastos por categoria calculados;
- simulações de metas calculadas;
- histórico de dúvidas;
- conceitos financeiros disponíveis;
- produtos financeiros informativos;
- limitações do projeto.

A IA usava esse contexto para explicar os resultados de forma mais clara e acessível.

A separação principal do projeto é:

```text
Python calcula → IA explica
```

Essa decisão reduz o risco de respostas inconsistentes, cálculos errados ou valores inventados.

---

## Produtos Financeiros Informativos

O arquivo:

```text
data/produtos_financeiros.json
```

contém informações educativas e simuladas sobre produtos financeiros.

Esses dados não representam consulta em tempo real, ranking de mercado, recomendação personalizada ou comparação atualizada entre bancos.

Na integração histórica, a IA podia explicar conceitos usando esses dados, mas
não deveria afirmar que um produto era o melhor disponível no mercado.

Perguntas como:

```text
Qual banco oferece o melhor CDB hoje?
```

devem ser respondidas com limitação clara, porque o projeto não possui dados atualizados de taxas, bancos ou rankings.

---

## Limitações da Base

A base de conhecimento não contém:

- dados bancários reais;
- extratos reais;
- dados pessoais reais;
- taxas financeiras em tempo real;
- ranking de bancos;
- cotação de investimentos;
- recomendação personalizada de investimentos;
- dados de crédito ou empréstimos;
- integração com instituições financeiras;
- informações externas consultadas pela IA em tempo real.

Na fase histórica, perguntas dependentes de informações externas ou ausentes
deveriam receber uma limitação clara. Atualmente o recurso está congelado fora
da navegação principal.

---

## Execução Relacionada aos Dados

O projeto possui um arquivo `main.py` para facilitar a execução.

Para processar os dados:

```bash
python main.py etl
```

Para abrir o dashboard:

```bash
python main.py
```

Para rodar os testes automatizados:

```bash
python main.py test
```

Para abrir o dashboard sem executar o ETL antes:

```bash
python main.py dev
```

---

## Evoluções Possíveis

A base de conhecimento pode evoluir com:

- novos arquivos mensais em `data/raw/`;
- entrada manual de transações pela interface;
- upload de planilha-modelo;
- mais categorias financeiras;
- tabela de categorias padronizadas;
- relatórios por período;
- exportação em Excel ou PDF;
- armazenamento em PostgreSQL;
- automações simples de arquivos;
- fluxo mais próximo de um controlador financeiro pessoal/local.

A direção futura mais coerente é permitir que a pessoa registre ou importe seus próprios dados em uma experiência parecida com uma planilha simples de gastos.

Essa evolução deve manter o projeto focado em uso local/pessoal, sem exigir login, múltiplos usuários ou integração bancária real neste momento.
