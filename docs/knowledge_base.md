# Knowledge Base — FinanTec Data Pipeline

## Visão Geral

A base de conhecimento do FinanTec Data Pipeline reúne dados simulados usados para análise financeira, geração de indicadores e respostas contextualizadas do assistente com IA.

A base combina arquivos de transações, perfil fictício da pessoa usuária, histórico de dúvidas, conceitos financeiros e produtos financeiros informativos.

O objetivo é permitir que o assistente responda com base em dados organizados, evitando respostas genéricas ou informações inventadas.

---

## Fontes de Dados

| Fonte | Formato | Finalidade |
|---|---|---|
| `data/raw/` | CSV | Armazena arquivos mensais brutos de transações financeiras simuladas. |
| `data/processed/` | CSV | Armazena a base tratada gerada pelo pipeline ETL. |
| `database/finantec.db` | SQLite | Base local gerada pelo ETL para consulta estruturada dos dados. |
| `data/perfil_usuario.json` | JSON | Contém o perfil fictício da pessoa usuária e suas metas financeiras. |
| `data/historico_atendimento.csv` | CSV | Registra dúvidas anteriores simuladas e respostas resumidas. |
| `data/conceitos_financeiros.json` | JSON | Contém explicações básicas sobre organização financeira. |
| `data/produtos_financeiros.json` | JSON | Contém produtos financeiros apenas para fins educativos. |
| `data/templates/transacoes_template.csv` | CSV | Modelo de preenchimento para novas transações. |

---

## Pessoa Usuária Fictícia

A base utiliza uma pessoa fictícia chamada Marina Costa.

Marina é estudante universitária e estagiária. Ela recebe uma bolsa-estágio mensal, possui uma pequena reserva para imprevistos e deseja organizar melhor seus gastos e metas financeiras.

As metas principais cadastradas são:

- montar uma reserva para imprevistos;
- comprar um notebook.

O uso de uma pessoa fictícia permite demonstrar o fluxo técnico sem utilizar dados pessoais ou bancários reais.

---

## Transações Financeiras

Os arquivos de transações representam receitas e despesas mensais.

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

Ela representa dinheiro guardado e não é considerada gasto de consumo. Por isso, os cálculos financeiros separam:

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
| Transform | Valida colunas, limpa textos, converte datas e valores, remove linhas inválidas e cria `ano_mes`. |
| Load | Salva os dados tratados em `data/processed/` e em SQLite. |

A aplicação usa o SQLite como fonte principal quando o banco existe. Caso contrário, utiliza o CSV processado ou o CSV original como fallback.

---

## Uso dos Dados pelo Dashboard

O dashboard em Streamlit utiliza a base tratada para exibir:

- receitas do período;
- gasto de consumo;
- valor separado para reserva;
- saldo disponível;
- maior categoria de consumo;
- gráfico de gastos por categoria;
- simulação de metas financeiras.

Os cálculos são feitos em Python, principalmente no arquivo:

```text
src/analytics.py
```

---

## Uso dos Dados pela IA

A IA generativa não calcula os valores financeiros principais.

Antes de enviar uma pergunta ao modelo, a aplicação monta um contexto com:

- perfil da pessoa usuária;
- período analisado;
- resumo financeiro calculado;
- gastos por categoria;
- simulações de metas calculadas;
- histórico de dúvidas;
- conceitos financeiros;
- produtos financeiros informativos.

A IA usa esse contexto para explicar os resultados de forma mais clara e acessível.

Essa separação reduz o risco de respostas inconsistentes:

```text
Python calcula → IA explica
```

---

## Limitações da Base

A base de conhecimento não contém:

- dados bancários reais;
- extratos reais;
- dados pessoais reais;
- taxas financeiras em tempo real;
- ranking de bancos;
- recomendação personalizada de investimentos;
- dados de crédito ou empréstimos.

Quando uma pergunta depende de informações externas ou ausentes, o assistente deve informar que não possui dados suficientes para responder com segurança.

---

## Evoluções Possíveis

A base de conhecimento pode evoluir com:

- novos arquivos mensais em `data/raw/`;
- planilha-modelo para preenchimento externo;
- upload de arquivos pelo usuário;
- mais categorias financeiras;
- tabela de categorias padronizadas;
- armazenamento em PostgreSQL;
- múltiplos perfis fictícios;
- relatórios por período;
- integração com automações de arquivos.