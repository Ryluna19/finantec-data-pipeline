# Contrato de Dados — Transações e Importação

## Visão Geral

Este documento descreve o contrato de dados utilizado pelo FinanTec para
representar transações financeiras e explica como diferentes formatos de
entrada são convertidos para esse modelo.

A aplicação possui um formato interno canônico:

```text
data
tipo
descricao
categoria
valor
```

Nem todo arquivo externo precisa começar exatamente com essas cinco colunas.

Existem dois tipos principais de entrada:

```text
Formato FinanTec
→ já segue o contrato canônico

Formato externo
→ passa por conversão ou mapeamento
→ torna-se o contrato canônico
```

Atualmente, a aplicação trabalha com:

- CSV no formato do FinanTec;
- Excel no formato do FinanTec;
- planilhas Excel externas por importação assistida;
- OFX;
- entrada manual pela interface;
- arquivos CSV processados explicitamente pelo pipeline ETL.

Independentemente da origem, uma transação precisa chegar ao modelo interno
válido antes de ser persistida.

---

## Modelo Canônico de Transação

O formato normalizado utilizado pelo projeto possui cinco campos financeiros
principais:

```text
data
tipo
descricao
categoria
valor
```

| Campo | Tipo esperado | Obrigatório | Exemplo | Finalidade |
|---|---|---:|---|---|
| `data` | Data válida | Sim | `2026-08-05` | Data da transação. |
| `tipo` | Texto normalizado | Sim | `receita` | Classifica entrada ou saída. |
| `descricao` | Texto | Sim | `Compra no mercado` | Identifica o evento financeiro. |
| `categoria` | Texto | Sim | `Alimentação` | Agrupa transações para análise. |
| `valor` | Número positivo | Sim | `200.00` | Valor absoluto da transação. |

Depois da persistência, a aplicação pode associar outras informações técnicas ao
registro, como:

- identificador estável;
- usuário proprietário;
- modo de dados;
- origem;
- período;
- informações usadas internamente para sincronização ou importação.

Esses campos técnicos não fazem parte do contrato que a pessoa usuária precisa
preencher em um arquivo.

---

## Origem do Tipo da Transação

Internamente, o campo `tipo` possui apenas dois valores:

```text
receita
despesa
```

O valor persistido permanece positivo.

A direção financeira é representada pelo campo `tipo`, não pelo sinal armazenado
em `valor`.

Exemplo normalizado:

```text
tipo: despesa
valor: 200.00
```

em vez de:

```text
tipo: despesa
valor: -200.00
```

Arquivos externos podem representar essa informação de outras maneiras.

A camada de importação é responsável por converter essas representações para o
modelo canônico.

---

## CSV do FinanTec

### Arquivos utilizados pelo ETL

Arquivos CSV adicionados diretamente para processamento pelo pipeline ficam em:

```text
data/raw/
```

O nome recomendado para arquivos mensais é:

```text
transacoes_AAAA_MM.csv
```

Exemplo:

```text
transacoes_2026_08.csv
```

O pipeline procura arquivos que seguem o padrão:

```text
transacoes_*.csv
```

O trecho `AAAA_MM` é uma convenção para organização.

O requisito técnico relevante para o pipeline é o prefixo:

```text
transacoes_
```

### Estrutura obrigatória

O CSV no formato FinanTec deve possuir:

```text
data,tipo,descricao,categoria,valor
```

Exemplo:

```csv
data,tipo,descricao,categoria,valor
2026-08-01,receita,Bolsa-estágio,Trabalho,1600.00
2026-08-02,despesa,Mercado,Alimentação,220.50
2026-08-03,despesa,Ônibus,Transporte,8.80
2026-08-04,despesa,Transferência para reserva,Reserva,300.00
```

Quando um arquivo declarado como formato FinanTec não possui uma das colunas
obrigatórias, existe um erro estrutural.

Nesse caso, o processamento não deve assumir silenciosamente o significado de
outras colunas.

---

## Recomendações para CSV

Para arquivos criados manualmente:

- utilizar UTF-8;
- manter o cabeçalho na primeira linha;
- utilizar os nomes internos esperados;
- preferir ponto como separador decimal;
- não incluir `R$` diretamente no valor;
- evitar linhas completamente vazias;
- manter o valor como número positivo;
- informar `receita` ou `despesa` explicitamente.

Valor recomendado:

```text
200.50
```

Evitar no formato canônico:

```text
R$ 200,50
```

Arquivos externos que utilizam outras convenções podem precisar do fluxo
assistido de importação em vez do pipeline direto.

---

## Normalização dos Cabeçalhos

Internamente, os campos são:

```text
data
tipo
descricao
categoria
valor
```

No Excel oficial, eles são apresentados visualmente como:

```text
DATA
TIPO
DESCRIÇÃO
CATEGORIA
VALOR
```

Durante os fluxos de importação que oferecem normalização, diferenças simples de
escrita podem ser tratadas.

Exemplos:

```text
DATA
Data
data
```

e:

```text
DESCRIÇÃO
Descrição
descricao
```

A normalização pode remover diferenças de:

- letras maiúsculas e minúsculas;
- acentuação;
- espaços no início ou no final;
- variações simples nos nomes das colunas.

Essa tolerância não elimina a necessidade de confirmar o significado dos campos
em arquivos externos.

---

## Excel no Formato FinanTec

O modelo oficial utiliza:

```text
.xlsx
```

A aba de transações é:

```text
Transacoes
```

Ela possui:

```text
DATA
TIPO
DESCRIÇÃO
CATEGORIA
VALOR
```

O modelo gerado pelo FinanTec contém recursos visuais para facilitar o
preenchimento, como:

- cabeçalhos formatados;
- filtros;
- primeira linha congelada;
- largura ajustada;
- alinhamento por tipo de campo;
- validação de data;
- lista de valores para `TIPO`;
- validação numérica de `VALOR`;
- aba separada de instruções.

O arquivo também contém:

```text
Instrucoes
```

Essa aba não representa transações.

---

## Importação Assistida de Excel

Planilhas externas não precisam possuir exatamente a estrutura do modelo
oficial.

O objetivo da importação assistida é transformar uma planilha existente no
contrato interno do FinanTec.

O fluxo permite analisar o arquivo antes da persistência.

Entre as etapas estão:

```text
arquivo Excel
        ↓
seleção da aba
        ↓
identificação ou escolha do cabeçalho
        ↓
normalização dos nomes
        ↓
sugestão de mapeamento
        ↓
confirmação do mapeamento
        ↓
conversão para o formato FinanTec
        ↓
validação
        ↓
análise de duplicatas
        ↓
prévia
        ↓
persistência
```

### Seleção de aba

Um arquivo externo pode possuir múltiplas abas.

A pessoa usuária escolhe qual delas contém as transações.

O importador não deve assumir que a aba se chama `Transacoes` quando o fluxo
assistido está sendo utilizado.

### Cabeçalho

Planilhas externas também podem conter:

- títulos antes da tabela;
- linhas de descrição;
- espaços vazios;
- cabeçalho fora da primeira linha.

O fluxo assistido permite trabalhar com a linha considerada como cabeçalho antes
de interpretar as transações.

### Mapeamento de campos

As colunas da planilha são associadas aos campos internos necessários.

Por exemplo:

```text
Data da compra
→ data

Histórico
→ descricao

Grupo
→ categoria
```

O objetivo final continua sendo produzir:

```text
data
tipo
descricao
categoria
valor
```

---

## Estratégias de Valor na Importação Assistida

Planilhas externas representam receitas e despesas de formas diferentes.

Por isso, o FinanTec suporta mais de uma estratégia.

### Valor e tipo explícito

Quando existem duas colunas como:

```text
Valor
Tipo
```

elas podem ser mapeadas separadamente.

Exemplo de origem:

```text
Valor: 250,00
Tipo: Despesa
```

Resultado normalizado:

```text
tipo: despesa
valor: 250.00
```

---

### Valor com sinal

Algumas planilhas utilizam o próprio sinal do número para representar a direção
da transação.

Exemplo conceitual:

```text
1500.00
-220.50
```

Nesse modo, a importação interpreta o sinal para determinar a direção financeira
e normaliza o resultado para o contrato interno.

Depois da conversão, `valor` continua sendo armazenado como número positivo e
`tipo` representa a direção.

---

### Débito e crédito separados

Outra estrutura comum utiliza duas colunas:

```text
Débito
Crédito
```

A importação assistida pode tratar esse formato explicitamente.

A interface oferece a opção:

```text
Usar colunas separadas de débito e crédito
```

Depois da conversão, cada registro volta ao modelo:

```text
tipo
valor
```

O formato com débito e crédito separados existe apenas como representação de
entrada.

Ele não altera o contrato interno da aplicação.

---

## Importação OFX

O FinanTec também aceita arquivos OFX.

OFX não utiliza o mesmo formato tabular de CSV ou Excel.

Por isso, esse arquivo passa por uma etapa própria de leitura e conversão:

```text
arquivo OFX
        ↓
parser OFX
        ↓
extração das transações suportadas
        ↓
normalização
        ↓
modelo interno do FinanTec
        ↓
validação
        ↓
análise de duplicatas
```

A implementação trata variações válidas de arquivos OFX e rejeita conteúdo que
não possa ser interpretado com segurança.

A pessoa usuária não precisa editar manualmente um OFX para transformá-lo em
CSV.

Depois da conversão, as transações seguem as mesmas regras internas utilizadas
pelos demais formatos.

---

## Campo `data`

`data` representa a data da transação.

### Formato interno

O formato lógico utilizado pelo projeto é uma data válida.

Em representações textuais, o padrão recomendado é:

```text
AAAA-MM-DD
```

Exemplo:

```text
2026-08-05
```

### CSV

Prefira:

```text
2026-08-05
```

Isso reduz ambiguidades.

### Excel

No modelo oficial, a data é apresentada no padrão brasileiro:

```text
DD/MM/AAAA
```

Exemplo:

```text
05/08/2026
```

A célula deve representar uma data válida, e não apenas um texto visualmente
parecido com uma data.

O modelo possui validação de datas em um intervalo adequado ao preenchimento.

A validação do arquivo auxilia a pessoa usuária, mas a aplicação continua sendo
responsável por validar o valor no momento da importação.

Valores vazios ou inválidos são rejeitados.

Exemplos inválidos:

```text
agosto
data-invalida
```

---

## Campo `tipo`

No modelo interno, os valores permitidos são:

```text
receita
despesa
```

O processo de normalização trata diferenças simples de capitalização e espaços.

Exemplos equivalentes:

```text
Receita
 receita
RECEITA
```

Resultado:

```text
receita
```

Exemplos equivalentes para despesa:

```text
Despesa
 DESPESA
despesa
```

Resultado:

```text
despesa
```

Um arquivo no formato canônico não deve utilizar valores arbitrários como:

```text
entrada
saida
gasto
outro
```

Arquivos externos que usam outra representação devem passar pelo mecanismo
adequado de mapeamento ou conversão.

---

## Campo `descricao`

A descrição identifica o evento financeiro.

Exemplos:

```text
Bolsa-estágio
Compra no mercado
Passagem de ônibus
Curso online
Transferência para reserva
```

O campo aceita texto livre.

Uma descrição vazia é inválida.

A descrição deve indicar o que ocorreu.

A categoria representa o agrupamento.

Exemplo:

```text
Descrição: Compra no supermercado
Categoria: Alimentação
```

---

## Campo `categoria`

A categoria é utilizada para:

- agrupamento;
- indicadores;
- gráficos;
- orçamento;
- análises por categoria.

Exemplos utilizados pela demonstração e pela aplicação:

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

A aplicação não exige que todas as transações usem apenas essas categorias.

Categorias novas podem ser utilizadas desde que o valor final seja válido.

Uma categoria vazia não atende ao contrato canônico.

### Categoria Reserva

`Reserva` possui tratamento específico nos cálculos financeiros.

Ela representa dinheiro separado para guardar e não entra como gasto de consumo
por padrão.

Exemplo:

```csv
2026-08-04,despesa,Transferência para reserva,Reserva,300.00
```

---

## Campo `valor`

No modelo interno, `valor` deve ser:

- numérico;
- maior que zero;
- armazenado sem símbolo monetário;
- independente do campo `tipo`.

Exemplos válidos:

```text
50
50.00
199.90
1600.00
```

No formato canônico, exemplos inválidos incluem:

```text
0
-20
abc
R$ 50,00
```

O sinal negativo pode aparecer em determinados formatos externos somente como
informação utilizada durante a conversão.

Depois da normalização, o valor interno é positivo.

No modelo Excel oficial:

- a coluna possui validação numérica;
- somente valores maiores que zero são esperados;
- a célula pode ser exibida com formatação monetária brasileira;
- não é necessário digitar `R$`.

Uma célula pode mostrar:

```text
R$ 200,50
```

enquanto o valor armazenado continua sendo numérico.

---

## Regras de Validação do Modelo Canônico

Uma transação final é inválida quando, entre outras situações:

- a data está vazia;
- a data não pode ser interpretada;
- o tipo está vazio;
- o tipo final não é `receita` nem `despesa`;
- a descrição está vazia;
- a categoria está vazia;
- o valor está vazio;
- o valor não é numérico;
- o valor final é menor ou igual a zero.

Uma linha pode possuir múltiplos problemas.

Exemplo:

```csv
data,tipo,descricao,categoria,valor
data-invalida,outro,,,-20
```

Essa linha pode produzir mais de um motivo de rejeição.

As validações existentes em um arquivo Excel são apenas uma ajuda de
preenchimento.

A aplicação continua validando os dados recebidos para se proteger contra:

- cópia e colagem;
- arquivos alterados manualmente;
- programas que ignoram as validações do Excel;
- arquivos malformados;
- entrada de ferramentas externas.

---

## Normalização Antes da Persistência

Antes de persistir uma transação importada, a aplicação procura transformar a
entrada no mesmo formato utilizado pelas demais origens.

Conceitualmente:

```text
origem
        ↓
leitura
        ↓
mapeamento ou conversão
        ↓
normalização
        ↓
validação
        ↓
modelo canônico
        ↓
persistência
```

Isso reduz a necessidade de regras diferentes para cada tela ou formato de
arquivo.

A origem pode mudar.

O contrato final da transação permanece consistente.

---

## Prévia da Importação

Antes da gravação de um lote enviado pela interface, o FinanTec apresenta uma
etapa de revisão.

Dependendo do formato, o fluxo pode:

1. identificar o tipo de arquivo;
2. ler o conteúdo;
3. selecionar uma aba;
4. definir o cabeçalho;
5. normalizar nomes de colunas;
6. aplicar o mapeamento;
7. converter os registros;
8. validar as transações;
9. identificar possíveis duplicatas;
10. apresentar a prévia;
11. informar quais registros podem ser importados.

Linhas inválidas não devem ser persistidas como transações válidas.

A prévia também ajuda a verificar se o mapeamento selecionado representa
corretamente os dados antes da confirmação.

---

## Possíveis Duplicatas

A análise de possíveis duplicatas compara a representação normalizada da
transação.

Os principais campos considerados são:

```text
data
tipo
descricao
categoria
valor
```

A quantidade de ocorrências também é considerada.

Exemplo:

```text
Banco:
1 × Compra no mercado — R$ 200,00

Arquivo:
2 × Compra no mercado — R$ 200,00
```

Nesse cenário, uma ocorrência pode corresponder ao registro existente e a outra
a uma nova ocorrência legítima.

O objetivo não é eliminar automaticamente todas as repetições.

É evitar duplicações acidentais sem impedir transações realmente repetidas.

### Comportamento padrão

Quando a aplicação encontra possíveis duplicatas, o padrão seguro é:

```text
não importar as possíveis duplicatas
```

Na interface, a pessoa usuária pode ativar explicitamente:

```text
Importar também as possíveis duplicatas
```

Essa escolha altera somente aquele fluxo de confirmação.

### Alteração dos valores

Uma transação com conteúdo diferente não é considerada idêntica.

Exemplo:

```text
Compra no mercado — R$ 200,00
```

e:

```text
Compra no mercado — R$ 250,00
```

representam registros diferentes.

A análise de duplicatas de importação também não substitui o mecanismo de edição.

Depois da persistência, registros individuais possuem identificadores estáveis
utilizados pelas operações de edição e exclusão.

---

## Identificação de Lotes

Lotes importados podem receber um fingerprint baseado no conteúdo normalizado.

O nome original do arquivo não é a identidade principal do lote.

Consequências esperadas:

```text
mesmo nome + conteúdo diferente
→ conteúdos diferentes
```

```text
nome diferente + mesmo conteúdo
→ conteúdo equivalente
```

A identificação baseada no conteúdo evita depender somente do nome escolhido
pela pessoa usuária.

Quando a implementação considera o conjunto normalizado das transações, mudanças
irrelevantes de nome de arquivo não criam uma identidade financeira nova por si
só.

---

## Arquivos e lotes de importação

Arquivos enviados pela interface são processados e normalizados antes da
persistência das transações.

Alguns fluxos de compatibilidade na execução local podem utilizar:

```text
data/raw/imported/
```

Essa pasta é um artefato de execução, não a fonte principal dos dados. Arquivos
importados ou gerados não devem ser enviados ao repositório quando puderem
conter informações pessoais.

---

## Relatório de Rejeições do ETL

Quando o pipeline explícito encontra linhas inválidas, pode gerar:

```text
data/processed/transacoes_rejeitadas.csv
```

O arquivo contém os registros descartados e:

```text
motivo_rejeicao
```

Exemplos:

```text
data invalida ou vazia
tipo vazio
tipo invalido
descricao vazia
categoria vazia
valor invalido ou vazio
valor menor ou igual a zero
```

Múltiplos problemas podem ser combinados.

Exemplo:

```text
data invalida ou vazia; tipo invalido; categoria vazia
```

O relatório é local e não deve ser versionado.

---

## Artefatos gerados localmente

A execução local ou o pipeline podem produzir:

```text
data/processed/transacoes_processadas.csv
data/processed/transacoes_rejeitadas.csv
database/finantec.db
logs/etl_transacoes.log
data/raw/imported/
```

O arquivo `database/finantec.db` existe somente quando o backend SQLite é
utilizado. Na aplicação publicada, os registros persistidos são enviados ao
Turso.

Esses artefatos não devem ser enviados ao GitHub quando contiverem dados
pessoais. Arquivos `.gitkeep` podem permanecer versionados apenas para preservar
os diretórios necessários.

---

## Modelo CSV

O modelo CSV está disponível em:

```text
data/templates/transacoes_template.csv
```

Ele utiliza o contrato canônico:

```text
data,tipo,descricao,categoria,valor
```

Para uso direto com o ETL, ele pode ser copiado para:

```text
data/raw/
```

e receber um nome como:

```text
transacoes_2026_08.csv
```

---

## Modelo Excel

O modelo Excel é gerado pelo FinanTec e pode ser obtido pela interface.

Ele possui:

```text
Transacoes
Instrucoes
```

A aba `Transacoes` utiliza:

```text
DATA
TIPO
DESCRIÇÃO
CATEGORIA
VALOR
```

A aba `Instrucoes` explica o preenchimento.

O modelo não contém transações reais.

---

## Exportação para Excel

A aplicação permite exportar as transações do período selecionado.

O arquivo `.xlsx` apresenta apenas informações destinadas à pessoa usuária:

```text
DATA
TIPO
DESCRIÇÃO
CATEGORIA
VALOR
```

Informações técnicas internas não devem aparecer na exportação comum.

Entre exemplos de dados técnicos estão:

```text
identificadores internos
user_id
data_mode
arquivo_origem
ano_mes
motivo_rejeicao
```

A exportação pode aplicar recursos visuais como:

- cabeçalho formatado;
- filtros;
- primeira linha congelada;
- data em formato brasileiro;
- formatação monetária;
- alinhamento por tipo de campo;
- tabela formatada.

O arquivo exportado pode ser utilizado novamente como entrada compatível.

Nesse caso, as regras de validação e análise de possíveis duplicatas continuam
sendo aplicadas.

---

## Persistência e Usuário

O contrato de arquivo não exige que a pessoa usuária forneça:

```text
user_id
```

A associação entre transação e conta é responsabilidade da aplicação.

Durante a persistência de dados pessoais:

```text
usuário autenticado
        ↓
importação ou cadastro
        ↓
validação
        ↓
associação ao contexto atual
        ↓
backend configurado
(SQLite ou Turso/libSQL)
```

Um arquivo não deve decidir arbitrariamente qual usuário será proprietário da
transação.

Essa informação vem do contexto autenticado da aplicação.

---

## Dados Pessoais e Demonstração

Transações pessoais e demonstração devem permanecer em contextos distintos.

O conteúdo de um arquivo importado pela pessoa usuária pertence ao contexto
pessoal da conta ativa.

A alternância para demonstração não deve:

- transformar os registros pessoais em demonstração;
- sobrescrever os registros pessoais;
- mudar o proprietário dos registros.

Da mesma forma, dados fictícios utilizados para demonstrar o produto não devem
ser tratados como importações pessoais comuns.

---

## Exemplos de Fluxo

### CSV pelo ETL

```text
1. Copiar data/templates/transacoes_template.csv
2. Renomear para data/raw/transacoes_2026_08.csv
3. Preencher as transações
4. Executar python main.py etl
5. Verificar possíveis rejeições
6. Abrir a aplicação
```

### Excel oficial pela interface

```text
1. Abrir o FinanTec
2. Obter o modelo Excel
3. Preencher a aba Transacoes
4. Salvar como .xlsx
5. Enviar pela interface
6. Conferir a prévia
7. Conferir possíveis duplicatas
8. Confirmar
9. Verificar as transações persistidas
```

### Excel externo

```text
1. Abrir o FinanTec
2. Selecionar o arquivo Excel externo
3. Escolher a aba
4. Confirmar ou selecionar o cabeçalho
5. Conferir o mapeamento sugerido
6. Ajustar o mapeamento quando necessário
7. Escolher a estratégia de valor adequada
8. Conferir a prévia
9. Conferir possíveis duplicatas
10. Confirmar a importação
```

### OFX

```text
1. Obter o arquivo OFX
2. Enviar o arquivo pela interface
3. Aguardar a leitura e conversão
4. Conferir a prévia
5. Conferir possíveis duplicatas
6. Confirmar a importação
```

---

## Invariantes do Contrato

Independentemente da origem, uma transação válida persistida deve preservar os
seguintes princípios:

```text
data válida
tipo conhecido
descrição preenchida
categoria preenchida
valor positivo
proprietário definido pela aplicação
```

Arquivos externos podem possuir estruturas diferentes.

A diferença deve ser resolvida antes da persistência.

O princípio central é:

```text
múltiplas entradas
        ↓
um modelo normalizado
        ↓
uma regra de persistência
```

Essa abordagem permite ampliar os formatos de importação sem criar um modelo
financeiro diferente para cada origem.
