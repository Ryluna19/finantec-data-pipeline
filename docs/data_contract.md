# Contrato de Dados — Transações

Este documento descreve o formato esperado dos arquivos CSV de transações usados pelo pipeline ETL do FinanTec Data Pipeline.

Os arquivos brutos devem ser colocados na pasta:

```text
data/raw/
```

O nome recomendado dos arquivos é:

```text
transacoes_AAAA_MM.csv
```

Exemplo:

```text
transacoes_2026_08.csv
```

O pipeline lê arquivos que seguem o padrão:

```text
transacoes_*.csv
```

Ou seja, o padrão `AAAA_MM` é uma convenção recomendada para organização, mas o requisito técnico principal é o prefixo `transacoes_`.

---

## Colunas Obrigatórias

Os arquivos CSV devem conter as seguintes colunas:

```text
data,tipo,descricao,categoria,valor
```

| Coluna | Tipo esperado | Obrigatória | Exemplo | Descrição |
|---|---|---|---|---|
| `data` | Data no formato `AAAA-MM-DD` | Sim | `2026-08-05` | Data da transação. |
| `tipo` | Texto | Sim | `receita` ou `despesa` | Indica se a transação é entrada ou saída. |
| `descricao` | Texto | Sim | `Compra no mercado` | Descrição curta da transação. |
| `categoria` | Texto | Sim | `Alimentação` | Categoria usada na análise. |
| `valor` | Número decimal positivo | Sim | `200.00` | Valor da transação. |

Se uma coluna obrigatória estiver ausente, o pipeline interrompe a execução.

Esse comportamento é intencional, porque ausência de coluna indica erro estrutural no arquivo.

---

## Formato do CSV

O projeto espera arquivos CSV simples, com cabeçalho na primeira linha.

Exemplo válido:

```csv
data,tipo,descricao,categoria,valor
2026-08-01,receita,Bolsa-estágio,Trabalho,1600.00
2026-08-02,despesa,Mercado,Alimentação,220.50
2026-08-03,despesa,Ônibus,Transporte,8.80
2026-08-04,despesa,Transferência para reserva,Reserva,300.00
```

Recomendações:

- usar codificação UTF-8;
- usar ponto como separador decimal;
- manter o cabeçalho exatamente com os nomes esperados;
- evitar linhas em branco;
- evitar valores monetários com `R$`;
- evitar separador decimal com vírgula.

Exemplo recomendado:

```text
200.50
```

Evite:

```text
R$ 200,50
```

---

## Coluna `data`

A coluna `data` deve representar a data da transação.

Formato recomendado:

```text
AAAA-MM-DD
```

Exemplo:

```text
2026-08-05
```

Valores inválidos serão rejeitados.

Exemplos inválidos:

```text
05/08/2026
agosto
data-invalida
```

---

## Coluna `tipo`

A coluna `tipo` aceita apenas dois valores:

```text
receita
despesa
```

O pipeline padroniza letras maiúsculas/minúsculas e remove espaços extras.

Exemplos aceitos:

```text
Receita
 receita
DESPESA
despesa
```

Todos serão convertidos para:

```text
receita
despesa
```

Exemplos inválidos:

```text
entrada
saida
gasto
outro
```

---

## Coluna `descricao`

A coluna `descricao` deve conter uma descrição curta da transação.

Exemplos válidos:

```text
Bolsa-estágio
Mercado
Ônibus
Curso online
Transferência para reserva
```

Descrições vazias serão rejeitadas.

---

## Coluna `categoria`

A coluna `categoria` deve indicar o agrupamento usado na análise.

As categorias podem ser expandidas, mas os dados simulados do projeto usam principalmente:

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

A categoria `Reserva` possui tratamento especial no projeto: ela representa dinheiro guardado e não entra como gasto de consumo por padrão.

Exemplo:

```csv
2026-08-04,despesa,Transferência para reserva,Reserva,300.00
```

Categorias vazias serão rejeitadas.

O pipeline não bloqueia categorias novas, desde que o campo esteja preenchido.

---

## Coluna `valor`

A coluna `valor` deve conter um número positivo.

Exemplos válidos:

```text
50
50.00
199.90
1600.00
```

Exemplos inválidos:

```text
0
-20
abc
R$ 50,00
```

Valores menores ou iguais a zero são rejeitados.

---

## Regras de Validação

O pipeline rejeita linhas quando:

- a data está vazia ou inválida;
- o tipo está vazio;
- o tipo não é `receita` nem `despesa`;
- a descrição está vazia;
- a categoria está vazia;
- o valor está vazio;
- o valor não é numérico;
- o valor é menor ou igual a zero.

Uma mesma linha pode ter mais de um problema.

Exemplo:

```csv
data,tipo,descricao,categoria,valor
data-invalida,outro,,, -20
```

Essa linha poderia gerar múltiplos motivos de rejeição.

---

## Relatório de Rejeições

Quando existem linhas inválidas, o pipeline gera o arquivo:

```text
data/processed/transacoes_rejeitadas.csv
```

Esse arquivo contém as linhas descartadas e uma coluna extra:

```text
motivo_rejeicao
```

Exemplos de motivos:

```text
data invalida ou vazia
tipo vazio
tipo invalido
descricao vazia
categoria vazia
valor invalido ou vazio
valor menor ou igual a zero
```

Quando uma linha possui mais de um problema, os motivos são acumulados.

Exemplo:

```text
data invalida ou vazia; tipo invalido; categoria vazia
```

Esse relatório é gerado apenas localmente e não é versionado no GitHub.

---

## Arquivos Gerados pelo Pipeline

Ao executar o ETL, o projeto pode gerar:

```text
data/processed/transacoes_processadas.csv
data/processed/transacoes_rejeitadas.csv
database/finantec.db
logs/etl_transacoes.log
```

Esses arquivos são locais e não devem ser enviados para o GitHub.

---

## Arquivo Modelo

Um arquivo modelo está disponível em:

```text
data/templates/transacoes_template.csv
```

Ele pode ser copiado para `data/raw/` e renomeado seguindo o padrão recomendado:

```text
transacoes_AAAA_MM.csv
```

Depois disso, basta preencher as transações mantendo as mesmas colunas.

---

## Exemplo de Fluxo de Uso

```text
1. Copiar data/templates/transacoes_template.csv
2. Renomear para data/raw/transacoes_2026_08.csv
3. Preencher as transações do mês
4. Executar python main.py etl
5. Verificar se houve rejeições
6. Abrir o dashboard com python main.py
```