# Validation — FinanTec Data Pipeline

## Visão Geral

Este documento descreve como o FinanTec Data Pipeline é validado.

A validação do projeto considera quatro camadas principais:

1. cálculos financeiros;
2. pipeline ETL;
3. carga em SQLite;
4. comportamento do assistente com IA.

O objetivo é garantir que os dados sejam processados corretamente, os indicadores sejam calculados em Python e a IA responda com base no contexto fornecido.

---

## Estratégia de Validação

O projeto combina:

- testes automatizados com `pytest`;
- scripts manuais de apoio;
- testes manuais do assistente com IA;
- documentação de limitações conhecidas.

Essa abordagem foi escolhida porque nem todas as partes do projeto devem ser testadas da mesma forma.

Cálculos financeiros, transformação de dados e carga em banco são previsíveis, então podem ser testados automaticamente.

Chamadas de IA dependem de API externa, internet, chave de acesso e variação do modelo, então são mantidas como testes manuais na versão atual.

---

## Testes Automatizados

Os testes automatizados ficam na pasta:

```text
tests/
```

Para executar usando o comando principal do projeto:

```bash
python main.py test
```

Ou diretamente com `pytest`:

```bash
pytest
```

### Arquivos de teste

| Arquivo | O que valida |
|---|---|
| `tests/test_analytics.py` | Cálculos financeiros, metas, formatação de moeda e filtros por período. |
| `tests/test_etl_pipeline.py` | Validação de colunas, preparação dos dados, separação entre linhas válidas e rejeitadas, transformação e ordenação final. |
| `tests/test_rejections.py` | Geração do relatório de transações rejeitadas e acúmulo de motivos de rejeição. |
| `tests/test_sqlite_load.py` | Carga dos dados tratados em SQLite usando banco temporário. |
| `tests/test_transaction_editor.py` | Valida a camada de preparação, salvamento e carregamento das transações manuais. |

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
- prazo inválido em metas;
- formatação de moeda brasileira;
- listagem de períodos disponíveis;
- filtragem por mês.

Uma regra importante validada é que a categoria `Reserva` não entra como gasto de consumo por padrão.

Isso evita interpretar dinheiro guardado como despesa comum.

Também existe teste para garantir que a categoria `Reserva` seja reconhecida mesmo com pequenas variações de texto, como espaços extras ou diferença entre maiúsculas e minúsculas.

---

## Validação do ETL

O pipeline ETL é validado em três partes principais.

### Extract

Verifica se os arquivos possuem as colunas obrigatórias:

```text
data,tipo,descricao,categoria,valor
```

Se uma coluna obrigatória estiver ausente, o pipeline deve interromper a execução.

Esse comportamento é esperado porque a ausência de coluna indica erro estrutural no arquivo, não apenas uma linha inválida.

### Transform

Verifica se o pipeline:

- converte datas corretamente;
- padroniza a coluna `tipo`;
- remove espaços extras;
- converte valores para número;
- identifica linhas inválidas;
- remove tipos não permitidos;
- remove valores menores ou iguais a zero;
- separa transações válidas e rejeitadas;
- cria a coluna `ano_mes`;
- ordena os dados finais.

### Load

Verifica se os dados tratados conseguem ser salvos em uma tabela SQLite.

O teste de carga usa um banco temporário criado pelo próprio `pytest`, evitando alterar o banco local do projeto.

Também é validado que a tabela é substituída corretamente quando a carga é executada novamente.

---

## Relatório de Rejeições

O pipeline gera um relatório de linhas rejeitadas quando encontra dados inválidos nos arquivos de entrada.

O arquivo gerado é:

```text
data/processed/transacoes_rejeitadas.csv
```

Esse arquivo contém as linhas descartadas e uma coluna adicional:

```text
motivo_rejeicao
```

Exemplos de motivos possíveis:

- data inválida ou vazia;
- tipo vazio;
- tipo inválido;
- descrição vazia;
- categoria vazia;
- valor inválido ou vazio;
- valor menor ou igual a zero.

Uma mesma linha pode acumular mais de um motivo de rejeição.

Exemplo:

```text
data invalida ou vazia; tipo invalido; descricao vazia
```

Esse relatório melhora a rastreabilidade do pipeline, porque permite entender por que uma linha não entrou na base final processada.

Como `data/processed/*.csv` está no `.gitignore`, esse relatório é gerado apenas localmente e não é versionado no GitHub.

---

## Scripts Manuais

A pasta `manual_tests/` contém scripts de apoio para verificações manuais e debug.

Esses scripts não substituem os testes automatizados da pasta `tests/`, mas ajudam a inspecionar o comportamento do projeto durante o desenvolvimento.

| Arquivo | Finalidade |
|---|---|
| `manual_tests/teste_dados.py` | Verifica leitura de transações e resumo financeiro geral no terminal. |
| `manual_tests/teste_metas.py` | Verifica cálculo das metas financeiras. |
| `manual_tests/teste_contexto.py` | Exibe o contexto enviado para a IA. |
| `manual_tests/teste_ia.py` | Testa uma chamada manual ao assistente com IA. |
| `manual_tests/teste_periodos.py` | Verifica períodos disponíveis e resumo por mês. |
| `manual_tests/teste_sqlite.py` | Consulta o banco SQLite gerado pelo ETL. |
| `manual_tests/README.md` | Documenta o objetivo dos scripts manuais. |

Para executar os principais testes manuais:

```bash
python manual_tests/teste_dados.py
python manual_tests/teste_metas.py
python manual_tests/teste_periodos.py
python manual_tests/teste_contexto.py
python manual_tests/teste_sqlite.py
```

O teste manual da IA depende da chave Gemini configurada no `.env`:

```bash
python manual_tests/teste_ia.py
```

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

Os cálculos financeiros não são delegados à IA.

A aplicação calcula os valores em Python e envia os resultados prontos no contexto. O papel da IA é explicar os indicadores, não recalcular ou criar valores novos.

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

Durante o desenvolvimento, alguns problemas foram identificados.

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

### Linhas inválidas eram apenas removidas

Inicialmente, linhas inválidas eram descartadas sem um relatório detalhado.

Ajuste aplicado:

```text
O pipeline passou a gerar um relatório de rejeições com o motivo de cada linha descartada.
```

### Configuração da chave da IA

O app depende de uma chave da Gemini API para usar o chat com IA.

Ajuste aplicado:

```text
O projeto passou a usar .env.example como modelo e mensagens de erro mais claras quando o .env ou a GEMINI_API_KEY estão ausentes.
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
- testes de múltiplos usuários;
- testes de entrada manual de transações pela interface.

Esses pontos podem ser adicionados em versões futuras.

---

## Resultado Atual

A versão atual possui validação automatizada para:

- regras financeiras principais;
- cálculo de metas;
- filtros por período;
- transformação dos dados;
- relatório de rejeições;
- carga em SQLite.
- editor manual de transações;
- salvamento e carregamento de transações manuais;

Além disso, possui testes manuais para:

- leitura geral dos dados;
- cálculo de metas;
- contexto enviado para IA;
- resposta do assistente;
- consulta do banco SQLite;
- análise por período.

Essa combinação é suficiente para validar a versão atual do projeto como um protótipo funcional de pipeline de dados com dashboard e assistente de IA.