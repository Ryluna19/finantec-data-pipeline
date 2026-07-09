# Base de Conhecimento

## Objetivo

A base de conhecimento do FinanTec reúne dados simulados e conteúdos educativos usados para responder perguntas sobre organização financeira de estudantes e pessoas em início de carreira.

Ela foi criada para que o agente responda usando contexto, evitando respostas genéricas ou números inventados.

---

## Fontes de Dados

| Arquivo | Formato | Finalidade |
|---|---|---|
| `perfil_usuario.json` | JSON | Armazena o perfil financeiro da pessoa usuária, sua renda, objetivos e situação atual. |
| `transacoes.csv` | CSV | Registra receitas e despesas de um mês para análise do orçamento. |
| `historico_atendimento.csv` | CSV | Reúne dúvidas anteriores e orientações já apresentadas à pessoa usuária. |
| `conceitos_financeiros.json` | JSON | Contém explicações educativas sobre orçamento, gastos, metas, cartão de crédito e reserva para imprevistos. |
| `produtos_financeiros.json` | JSON | Apresenta produtos financeiros apenas como conteúdo informativo e educacional. |

---

## Perfil da Pessoa Usuária

A pessoa fictícia utilizada no projeto é Marina Costa.

Marina tem 21 anos, é estudante universitária e estagiária. Sua principal renda mensal é uma bolsa-estágio de R$ 1.600,00.

Ela possui uma pequena reserva para imprevistos e definiu duas metas financeiras:

- montar uma reserva para imprevistos;
- comprar um notebook.

A principal dificuldade relatada por Marina é reduzir gastos por impulso e conseguir guardar dinheiro de forma consistente.

---

## Dados de Transações

O arquivo `transacoes.csv` representa um mês de movimentações financeiras simuladas.

As transações são classificadas em receita ou despesa e possuem categorias como:

- alimentação;
- transporte;
- serviços;
- assinaturas;
- educação;
- lazer;
- saúde;
- compras;
- reserva.

Esses dados serão analisados com Python e pandas para calcular:

- total de receitas;
- total de despesas;
- saldo mensal;
- gastos por categoria;
- categorias com maior impacto no orçamento.

---

## Uso dos Dados pelo Agente

O FinanTec deve utilizar cada fonte de forma adequada:

| Situação | Fonte principal |
|---|---|
| Pergunta sobre renda, objetivos ou reserva atual | `perfil_usuario.json` |
| Pergunta sobre gastos, saldo ou categorias | `transacoes.csv` |
| Pergunta sobre dúvidas já apresentadas | `historico_atendimento.csv` |
| Pergunta sobre conceitos financeiros básicos | `conceitos_financeiros.json` |
| Pergunta sobre produtos financeiros | `produtos_financeiros.json` |

Valores financeiros devem ser calculados pela aplicação em Python antes de serem enviados como contexto para a IA.

---

## Regras de Atualização

A base de conhecimento pode ser expandida futuramente com:

- novos meses de transações;
- novas metas financeiras;
- mais dúvidas no histórico de atendimento;
- novos conceitos educativos;
- novos produtos financeiros informativos.

Mesmo com novos dados, o projeto continuará utilizando apenas informações simuladas.

---

## Limites da Base

A base de conhecimento não contém:

- dados bancários reais;
- informações de cartão de crédito real;
- dados pessoais de usuários reais;
- cotações financeiras em tempo real;
- recomendações personalizadas de investimento;
- informações sobre crédito, empréstimos ou aprovação financeira.

Quando uma pergunta depender de dados que não existem na base, o FinanTec deverá informar essa limitação com clareza.
