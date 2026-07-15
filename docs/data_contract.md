# Contrato de Dados — Transações

Este documento descreve o formato esperado dos arquivos CSV e Excel usados pelo pipeline ETL e pela interface de importação do FinanTec Data Pipeline.

Os arquivos CSV brutos adicionados manualmente devem ser colocados na pasta:

```text
data/raw/
```

Os lotes enviados pela interface são armazenados automaticamente em:

```text
data/raw/imported/
```

O nome recomendado para arquivos CSV mensais é:

```text
transacoes_AAAA_MM.csv
```

Exemplo:

```text
transacoes_2026_08.csv
```

O pipeline lê recursivamente arquivos que seguem o padrão:

```text
transacoes_*.csv
```

Portanto, o padrão `AAAA_MM` é uma convenção recomendada para organização. O requisito técnico principal é o prefixo `transacoes_`.

---

## Colunas Obrigatórias

Todos os arquivos de transações devem conter as seguintes colunas:

```text
data,tipo,descricao,categoria,valor
```

| Coluna | Tipo esperado | Obrigatória | Exemplo | Descrição |
|---|---|---|---|---|
| `data` | Data válida | Sim | `2026-08-05` | Data da transação. |
| `tipo` | Texto | Sim | `receita` ou `despesa` | Indica se a transação é entrada ou saída. |
| `descricao` | Texto | Sim | `Compra no mercado` | Descrição curta da transação. |
| `categoria` | Texto | Sim | `Alimentação` | Categoria usada nas análises. |
| `valor` | Número decimal positivo | Sim | `200.00` | Valor da transação. |

Se uma coluna obrigatória estiver ausente, a validação interrompe o processamento do arquivo.

Esse comportamento é intencional, porque a ausência de uma coluna indica um erro estrutural.

---

## Nomes Internos e Rótulos Visuais

Internamente, o FinanTec utiliza os nomes:

```text
data
tipo
descricao
categoria
valor
```

No modelo Excel, os cabeçalhos são apresentados visualmente como:

```text
DATA | TIPO | DESCRIÇÃO | CATEGORIA | VALOR
```

Durante a importação pela interface, os cabeçalhos são normalizados.

Por isso, variações como estas podem ser reconhecidas:

```text
DATA
Data
data

DESCRIÇÃO
Descrição
descricao
```

A normalização remove diferenças de:

- letras maiúsculas e minúsculas;
- acentuação;
- espaços no início e no final;
- espaços internos usados em nomes de colunas.

Para arquivos CSV colocados diretamente em `data/raw/`, recomenda-se manter os nomes internos em letras minúsculas exatamente como definidos no contrato.

---

## Formato do CSV

O projeto espera arquivos CSV simples, com o cabeçalho na primeira linha.

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
- manter o cabeçalho com os nomes internos esperados;
- evitar linhas completamente vazias;
- evitar valores monetários com `R$`;
- evitar vírgula como separador decimal.

Exemplo recomendado:

```text
200.50
```

Evite:

```text
R$ 200,50
```

---

## Importação por Excel

O FinanTec aceita arquivos Excel no formato:

```text
.xlsx
```

O arquivo deve possuir uma aba chamada:

```text
Transacoes
```

A aba deve conter as cinco colunas obrigatórias:

```text
DATA
TIPO
DESCRIÇÃO
CATEGORIA
VALOR
```

O modelo Excel disponibilizado pelo FinanTec inclui:

- cabeçalhos formatados;
- filtros;
- primeira linha congelada;
- linhas de grade;
- largura ajustada para cada coluna;
- alinhamento conforme o tipo de informação;
- validação de data;
- lista suspensa para o tipo;
- validação numérica para o valor;
- aba separada com instruções.

As colunas são alinhadas da seguinte forma:

| Coluna | Alinhamento |
|---|---|
| `DATA` | Centralizado |
| `TIPO` | Centralizado |
| `DESCRIÇÃO` | Esquerda |
| `CATEGORIA` | Esquerda |
| `VALOR` | Direita |

O alinhamento à direita no valor facilita a comparação vertical de quantias.

---

## Coluna `data`

A coluna `data` representa a data da transação.

### Em arquivos CSV

O formato recomendado é:

```text
AAAA-MM-DD
```

Exemplo:

```text
2026-08-05
```

Esse padrão evita ambiguidades durante a leitura do arquivo.

### Em arquivos Excel

A data é exibida no padrão brasileiro:

```text
DD/MM/AAAA
```

Exemplo:

```text
05/08/2026
```

O Excel armazena a informação como um valor real de data, e não apenas como texto.

O modelo possui uma validação que aceita datas entre:

```text
01/01/2000
```

e:

```text
31/12/2100
```

A validação do Excel ajuda a evitar erros de preenchimento, mas a validação realizada pelo FinanTec continua sendo a proteção definitiva durante a importação.

Valores vazios ou inválidos são rejeitados.

Exemplos inválidos para um CSV:

```text
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

No modelo Excel, esses valores aparecem em uma lista suspensa.

O pipeline padroniza letras maiúsculas e minúsculas e remove espaços extras.

Exemplos aceitos:

```text
Receita
 receita
DESPESA
despesa
```

Todos são normalizados para:

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

A coluna `descricao` deve conter um texto curto que identifique a transação.

Exemplos válidos:

```text
Bolsa-estágio
Compra no mercado
Passagem de ônibus
Curso online
Transferência para reserva
```

O campo aceita texto livre.

Descrições vazias são rejeitadas.

A descrição deve registrar o que aconteceu, enquanto a categoria deve representar o agrupamento da transação.

Exemplo:

```text
Descrição: Compra no supermercado
Categoria: Alimentação
```

---

## Coluna `categoria`

A coluna `categoria` indica o agrupamento usado nas análises e nos gráficos.

As categorias podem ser expandidas livremente.

Os dados simulados do projeto utilizam principalmente:

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

Ela representa dinheiro guardado e não entra como gasto de consumo por padrão.

Exemplo:

```csv
2026-08-04,despesa,Transferência para reserva,Reserva,300.00
```

Categorias vazias são rejeitadas.

O FinanTec não bloqueia categorias novas, desde que o campo esteja preenchido.

A restrição a uma lista fixa de categorias poderá ser adicionada futuramente quando existir gerenciamento de categorias pela própria interface.

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

No modelo Excel:

- a coluna possui validação numérica;
- somente valores maiores que zero são aceitos;
- a célula utiliza formatação monetária em reais;
- não é necessário digitar `R$`.

O valor deve ser informado apenas como número.

Exemplo:

```text
200.50
```

O Excel poderá apresentar visualmente:

```text
R$ 200,50
```

A exibição formatada não altera o valor numérico armazenado.

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

Uma mesma linha pode possuir mais de um problema.

Exemplo:

```csv
data,tipo,descricao,categoria,valor
data-invalida,outro,,,-20
```

Essa linha pode gerar múltiplos motivos de rejeição.

As validações existentes no Excel ajudam durante o preenchimento, mas não substituem as validações do pipeline.

A validação do FinanTec também protege contra dados inválidos inseridos por:

- cópia e colagem;
- editores que ignoram as regras do Excel;
- arquivos CSV;
- alterações manuais no arquivo;
- ferramentas externas.

---

## Prévia da Importação

Antes de salvar um lote enviado pela interface, o FinanTec:

1. identifica o tipo do arquivo;
2. lê a aba ou o conteúdo informado;
3. normaliza os cabeçalhos;
4. verifica as colunas obrigatórias;
5. prepara e valida as transações;
6. identifica linhas que já existem;
7. mostra uma prévia no dashboard;
8. informa quantas linhas podem ser importadas.

Linhas inválidas não devem entrar no lote importado.

A interface também informa:

- quantidade total de linhas válidas;
- possíveis correspondências com a base atual;
- quantidade de linhas novas;
- estratégia selecionada para a importação.

---

## Possíveis Duplicatas

A comparação de possíveis duplicatas considera os cinco campos:

```text
data
tipo
descricao
categoria
valor
```

O FinanTec compara também a quantidade de ocorrências.

Exemplo:

- existe uma transação igual na base;
- o arquivo possui duas ocorrências iguais;
- uma ocorrência é considerada existente;
- a outra pode ser considerada nova.

Isso permite manter transações realmente repetidas quando elas representam ocorrências distintas.

Por padrão, o sistema recomenda:

```text
Ignorar linhas que já existem
```

Também pode existir a opção de incluir todas as linhas, inclusive as correspondências encontradas.

Uma linha alterada é considerada uma transação diferente.

Exemplo:

```text
Compra no mercado — R$ 200,00
```

e:

```text
Compra no mercado — R$ 250,00
```

não são consideradas iguais.

Essa comparação não representa uma edição da transação anterior. As
transações persistidas já recebem identificadores estáveis, e a edição ou
exclusão individual usa esses identificadores no SQLite.

---

## Identificação dos Lotes Importados

Cada lote importado recebe um fingerprint gerado a partir do conteúdo normalizado das transações.

O nome original do arquivo não é usado como identificação principal.

Consequências:

```text
Mesmo nome + conteúdo diferente
→ pode gerar um novo lote
```

```text
Nome diferente + mesmo conteúdo
→ representa o mesmo lote
```

```text
Mesmas linhas em ordem diferente
→ representa o mesmo lote
```

O fingerprint considera:

```text
data
tipo
descricao
categoria
valor
```

A ordem das linhas não altera a identificação do lote.

Os lotes enviados pela interface são armazenados em:

```text
data/raw/imported/
```

Os arquivos gerados nessa pasta são locais e não devem ser enviados ao GitHub.

---

## Relatório de Rejeições

Quando existem linhas inválidas durante o ETL, o pipeline gera:

```text
data/processed/transacoes_rejeitadas.csv
```

Esse arquivo contém as linhas descartadas e uma coluna adicional:

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

Esse relatório é gerado apenas localmente e não deve ser versionado no GitHub.

---

## Arquivos Gerados pelo Pipeline

Ao executar o ETL, o projeto pode gerar:

```text
data/processed/transacoes_processadas.csv
data/processed/transacoes_rejeitadas.csv
database/finantec.db
logs/etl_transacoes.log
```

A importação pela interface também pode gerar lotes em:

```text
data/raw/imported/
```

Esses arquivos são locais e não devem ser enviados ao GitHub.

Arquivos `.gitkeep` podem permanecer versionados para preservar a estrutura das pastas vazias.

---

## Arquivo Modelo CSV

O modelo CSV do projeto está disponível em:

```text
data/templates/transacoes_template.csv
```

Ele pode ser copiado para `data/raw/` e renomeado seguindo o padrão recomendado:

```text
transacoes_AAAA_MM.csv
```

Depois disso, basta preencher as transações mantendo as mesmas colunas.

---

## Arquivo Modelo Excel

O modelo Excel é gerado pelo próprio FinanTec e pode ser baixado pela interface.

Ele contém as abas:

```text
Transacoes
Instrucoes
```

A aba `Transacoes` é usada para o preenchimento e posterior importação.

A aba `Instrucoes` apresenta:

- nome de cada campo;
- orientação de preenchimento;
- exemplo de valor.

O arquivo modelo não contém transações reais.

---

## Exportação para Excel

O FinanTec permite exportar as transações do período selecionado para um arquivo `.xlsx`.

O arquivo exportado contém apenas as colunas destinadas ao usuário:

```text
DATA
TIPO
DESCRIÇÃO
CATEGORIA
VALOR
```

Colunas técnicas não são exportadas.

Exemplos de colunas internas removidas:

```text
arquivo_origem
ano_mes
motivo_rejeicao
```

A exportação possui:

- cabeçalho formatado;
- títulos em letras maiúsculas;
- filtros;
- primeira linha congelada;
- formatação brasileira de data;
- formatação monetária;
- alinhamento adequado para cada tipo de dado;
- tabela com linhas alternadas.

O arquivo exportado pode ser importado novamente pelo FinanTec.

As regras de prevenção de duplicatas continuam sendo aplicadas normalmente.

---

## Exemplo de Fluxo com CSV

```text
1. Copiar data/templates/transacoes_template.csv
2. Renomear para data/raw/transacoes_2026_08.csv
3. Preencher as transações do mês
4. Executar python main.py etl
5. Verificar se houve rejeições
6. Abrir o dashboard com python main.py
```

---

## Exemplo de Fluxo com Excel

```text
1. Abrir o FinanTec com python main.py
2. Baixar o modelo Excel pela interface
3. Preencher a aba Transacoes
4. Salvar o arquivo no formato .xlsx
5. Enviar o arquivo pela interface
6. Conferir a prévia e as possíveis duplicatas
7. Confirmar a importação
8. Verificar os dados atualizados no dashboard
```
