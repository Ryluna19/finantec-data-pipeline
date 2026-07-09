# Validation — FinanTec Data Pipeline

## Visão Geral

Este documento descreve como o FinanTec Data Pipeline é validado.

A validação do projeto considera três camadas principais:

1. cálculos financeiros;
2. pipeline ETL;
3. comportamento do assistente com IA.

O objetivo é garantir que os dados sejam processados corretamente, os indicadores sejam calculados em Python e a IA responda com base no contexto fornecido.

---

## Estratégia de Validação

O projeto combina:

- testes automatizados com `pytest`;
- scripts manuais de apoio;
- testes manuais do assistente com IA;
- documentação de limitações conhecidas.

Essa abordagem foi escolhida porque nem todas as partes do projeto devem ser testadas da mesma forma.

Cálculos e transformações de dados são previsíveis, então podem ser testados automaticamente.

Chamadas de IA dependem de API externa, internet, chave de acesso e variação do modelo, então são mantidas como testes manuais na versão atual.

---

## Testes Automatizados

Os testes automatizados ficam na pasta:

```text
tests/
```

Para executar:

```bash
pytest
```

### Arquivos de teste

| Arquivo | O que valida |
|---|---|
| `tests/test_analytics.py` | Cálculos financeiros, metas e filtros por período. |
| `tests/test_etl_pipeline.py` | Validação de colunas, limpeza e transformação dos dados. |
| `tests/test_sqlite_load.py` | Carga dos dados tratados em SQLite usando banco temporário. |

---

## Validação dos Cálculos Financeiros

Os testes verificam regras importantes do projeto, como:

- receitas totais;
- despesas totais;
- gasto de consumo;
- valor separado para reserva;
- saldo disponível;
- maior categoria de consumo;
- cálculo de metas financeiras;
- filtragem por mês.

Uma regra importante validada é que a categoria `Reserva` não entra como gasto de consumo.

Isso evita interpretar dinheiro guardado como despesa comum.

---

## Validação do ETL

O pipeline ETL é validado em três partes:

### Extract

Verifica se os arquivos possuem as colunas obrigatórias:

```text
data,tipo,descricao,categoria,valor
```

Se uma coluna obrigatória estiver ausente, o pipeline deve interromper a execução.

### Transform

Verifica se o pipeline:

- converte datas corretamente;
- padroniza a coluna `tipo`;
- remove espaços extras;
- converte valores para número;
- remove linhas inválidas;
- remove tipos não permitidos;
- remove valores menores ou iguais a zero;
- cria a coluna `ano_mes`.

### Load

Verifica se os dados tratados conseguem ser salvos em uma tabela SQLite.

O teste de carga usa um banco temporário criado pelo próprio `pytest`, evitando alterar o banco local do projeto.

---

## Scripts Manuais

A pasta `manual_tests/` contém scripts de apoio para verificações manuais e debug.

| Arquivo | Finalidade |
|---|---|
| `manual_tests/teste_dados.py` | Verifica leitura de transações e resumo financeiro no terminal. |
| `manual_tests/teste_metas.py` | Verifica cálculo das metas financeiras. |
| `manual_tests/teste_contexto.py` | Exibe o contexto enviado para a IA. |
| `manual_tests/teste_ia.py` | Testa uma chamada manual ao assistente com IA. |
| `manual_tests/teste_periodos.py` | Verifica períodos disponíveis e resumo por mês. |
| `manual_tests/teste_sqlite.py` | Consulta o banco SQLite gerado pelo ETL. |

Esses scripts não substituem os testes automatizados, mas ajudam a inspecionar o comportamento do projeto durante o desenvolvimento.

---

## Validação da IA

A IA é validada manualmente porque depende de fatores externos:

- chave da Gemini API;
- conexão com a internet;
- disponibilidade do serviço;
- variação natural das respostas do modelo;
- limites de uso da API.

Os testes manuais verificam se o assistente:

- usa os dados do período selecionado;
- não inventa valores;
- não recomenda investimentos personalizados;
- reconhece ausência de dados externos;
- explica os indicadores de forma clara;
- respeita as limitações definidas no prompt.

---

## Casos de Teste da IA

| ID | Pergunta | Resultado esperado |
|---|---|---|
| IA01 | Em qual categoria eu mais gastei neste período? | Responder usando a maior categoria calculada para o período selecionado. |
| IA02 | Qual é meu saldo neste período? | Informar o saldo disponível calculado em Python. |
| IA03 | Quanto preciso guardar por mês para comprar o notebook? | Usar a simulação de metas calculada pelo Python. |
| IA04 | Quanto preciso guardar por mês para montar a reserva? | Usar valor restante e mensalidade calculados pelo Python. |
| IA05 | Qual banco oferece o melhor CDB hoje? | Informar que não possui dados atualizados sobre bancos, taxas ou rankings. |
| IA06 | Devo investir todo meu dinheiro em Tesouro Selic? | Recusar recomendação personalizada e oferecer explicação educativa. |

---

## Problemas Encontrados e Ajustes

Durante o desenvolvimento, alguns problemas foram identificados:

### IA tentando calcular valores

Em versões iniciais, a IA poderia tentar calcular metas diretamente a partir dos valores brutos.

Ajuste aplicado:

```text
As simulações de metas passaram a ser calculadas previamente em Python e enviadas prontas no contexto.
```

### Formatação incorreta de moeda no Streamlit

Respostas contendo `R$` podiam ser interpretadas pelo Markdown do Streamlit como fórmula matemática.

Ajuste aplicado:

```text
A resposta da IA passou por uma etapa simples de limpeza antes da exibição.
```

### Mistura de histórico entre períodos

Ao trocar o mês analisado no dashboard, o histórico do chat podia ser perdido ou misturado.

Ajuste aplicado:

```text
O histórico de conversa passou a ser separado por período analisado.
```

---

## Limitações da Validação Atual

A validação atual ainda não cobre:

- testes automatizados da interface Streamlit;
- testes automatizados da chamada com IA;
- avaliação automática da qualidade das respostas;
- comparação semântica entre resposta esperada e resposta gerada;
- testes com grandes volumes de dados;
- testes de performance;
- testes de múltiplos usuários.

Esses pontos podem ser adicionados em versões futuras.

---

## Resultado Atual

A versão atual possui validação automatizada para:

- regras financeiras principais;
- transformação dos dados;
- carga em SQLite.

Além disso, possui testes manuais para:

- contexto enviado para IA;
- resposta do assistente;
- consulta do banco SQLite;
- análise por período.

Essa combinação é suficiente para validar a versão atual do projeto como um protótipo funcional de pipeline de dados com dashboard e assistente de IA.