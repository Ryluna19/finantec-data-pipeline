# Contrato de Dados — Transações

Este documento descreve o formato esperado dos arquivos CSV de transações usados pelo pipeline ETL do FinanTec Data Pipeline.

Os arquivos brutos devem ser colocados na pasta:

```text
data/raw/
```

O nome dos arquivos deve seguir o padrão:

```text
transacoes_AAAA_MM.csv
```

Exemplo:

```text
transacoes_2026_08.csv
```

---

## Colunas Obrigatórias

| Coluna | Tipo esperado | Obrigatória | Exemplo | Descrição |
|---|---|---|---|---|
| `data` | Data no formato `AAAA-MM-DD` | Sim | `2026-08-05` | Data da transação. |
| `tipo` | Texto | Sim | `receita` ou `despesa` | Indica se a transação é entrada ou saída. |
| `descricao` | Texto | Sim | `Compra no mercado` | Descrição curta da transação. |
| `categoria` | Texto | Sim | `Alimentação` | Categoria usada na análise. |
| `valor` | Número decimal positivo | Sim | `200.00` | Valor da transação. |

---

## Valores Aceitos

### Coluna `tipo`

A coluna `tipo` aceita apenas:

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

---

## Categorias Utilizadas

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

A categoria `Reserva` possui tratamento especial no projeto: ela representa dinheiro guardado e não entra como gasto de consumo.

---

## Regras de Validação

O pipeline remove linhas inválidas quando:

- a data não pode ser convertida;
- o tipo não é `receita` nem `despesa`;
- o valor não é numérico;
- o valor é menor ou igual a zero;
- alguma coluna obrigatória está vazia.

Se uma coluna obrigatória estiver ausente no arquivo, o pipeline interrompe a execução e informa o erro.

---

## Arquivo Modelo

Um arquivo modelo está disponível em:

```text
data/templates/transacoes_template.csv
```

Ele pode ser copiado para `data/raw/` e renomeado seguindo o padrão:

```text
transacoes_AAAA_MM.csv
```

Depois disso, basta preencher as transações mantendo as mesmas colunas.