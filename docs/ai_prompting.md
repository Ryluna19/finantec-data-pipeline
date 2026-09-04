# AI Prompting — Registro histórico do FinanTec

> [!IMPORTANT]
> Este documento preserva a arquitetura e as decisões técnicas da antiga
> experiência de assistente financeiro do FinanTec.
>
> A integração externa com Gemini, sua configuração por chave e o fluxo de chat
> não fazem parte da aplicação atual.
>
> Não houve violação de dados comprovada. A integração foi removida
> preventivamente devido ao risco potencial de enviar contexto financeiro e
> pessoal para um serviço externo.
>
> Consulte:
> [ADR 001 — Remoção da integração externa com Gemini](decisions/001-remove-gemini-integration.md).

## Objetivo deste Documento

Este arquivo existe como registro histórico.

Ele documenta:

- como o antigo assistente foi estruturado;
- quais responsabilidades permaneciam em Python;
- qual contexto podia ser enviado ao modelo;
- quais limitações foram impostas à IA;
- como a conversa chegou a ser persistida;
- quais problemas foram encontrados durante essa fase;
- por que essa arquitetura deixou de fazer parte do produto atual.

Nada descrito aqui deve ser interpretado automaticamente como funcionalidade
ativa da v1.

---

## Visão Geral Histórica

O FinanTec já utilizou IA generativa para explicar indicadores financeiros
calculados pela própria aplicação.

A IA não era responsável pelos principais cálculos.

Valores como:

- receitas;
- despesas;
- saldo;
- reserva;
- gastos por categoria;
- simulações de metas;

eram calculados previamente em Python.

O modelo recebia parte desses resultados como contexto e tinha a função de
transformá-los em explicações mais acessíveis.

A divisão conceitual era:

```text
Python calcula
        ↓
IA explica
```

Essa arquitetura procurava reduzir o risco de:

- valores inventados;
- cálculos inconsistentes;
- interpretação incorreta dos dados;
- recomendações financeiras sem fundamento.

---

## Estado Atual

A arquitetura descrita neste documento foi descontinuada.

Na aplicação atual:

- não existe chamada para Gemini;
- não existe necessidade de chave de API de IA;
- o assistente financeiro não faz parte da navegação;
- o histórico de conversas não faz parte da experiência atual;
- o antigo mecanismo de Insights não faz parte das funcionalidades atuais.

Módulos, testes ou arquivos associados àquela fase podem permanecer no
repositório temporariamente como:

- legado técnico;
- compatibilidade;
- registro histórico.

Sua presença física no código não significa que representem componentes ativos
do produto.

---

## Princípio da Arquitetura Histórica

A principal decisão era manter a responsabilidade pelos valores financeiros no
código determinístico.

```text
dados
        ↓
Python
        ↓
cálculos financeiros
        ↓
contexto estruturado
        ↓
modelo generativo
        ↓
explicação
```

O modelo não deveria substituir as regras de negócio.

---

## Classificação Local de Intenção

Durante essa fase, perguntas podiam passar primeiro por uma classificação local
e determinística.

O código relacionado foi desenvolvido em torno de módulos como:

```text
src/financial_intents.py
```

A ideia era reconhecer perguntas simples antes de decidir se uma chamada ao
modelo generativo seria necessária.

Exemplos conceituais de intenção incluíam perguntas sobre:

- saldo;
- gastos;
- reserva;
- categorias;
- metas.

Essa classificação não deve ser interpretada como uma funcionalidade atual da
interface.

---

## Respostas Determinísticas

Algumas perguntas simples podiam ser respondidas sem IA generativa.

O código relacionado foi concentrado em módulos como:

```text
src/financial_responses.py
```

A intenção era utilizar regras locais sempre que o resultado pudesse ser
produzido de forma previsível.

Conceitualmente:

```text
pergunta simples
        ↓
intenção reconhecida
        ↓
dados calculados localmente
        ↓
resposta determinística
```

Esses módulos podem permanecer no repositório como legado técnico, mas não
representam uma experiência ativa da v1.

---

## Papel Histórico da IA

Quando utilizada, a IA servia principalmente para:

- explicar receitas;
- explicar despesas;
- interpretar saldo;
- contextualizar reserva;
- comentar gastos por categoria;
- explicar metas financeiras;
- apresentar conceitos financeiros básicos;
- transformar indicadores em texto mais acessível;
- reconhecer quando os dados disponíveis eram insuficientes.

A IA não deveria:

- inventar valores;
- inventar datas;
- inventar bancos;
- inventar produtos;
- inventar taxas;
- recalcular valores financeiros críticos;
- recomendar investimentos personalizados;
- afirmar possuir informações em tempo real;
- criar rankings de bancos ou produtos;
- garantir rentabilidade;
- substituir orientação profissional.

---

## Contexto Enviado Historicamente

Antes de uma chamada externa, a aplicação podia montar um contexto contendo
informações como:

- perfil;
- período analisado;
- resumo financeiro calculado;
- gastos por categoria;
- cálculos relacionados às metas;
- parte do histórico de conversa;
- conceitos financeiros;
- produtos financeiros informativos;
- limitações da aplicação.

Durante aquela arquitetura, a montagem do contexto estava associada a código
como:

```text
src/prompts.py
```

e a integração com o modelo estava associada a:

```text
src/agent.py
```

Esses caminhos representam a estrutura daquela fase do projeto e não a
arquitetura atual.

---

## System Prompt Histórico

O antigo `SYSTEM_PROMPT` procurava limitar o comportamento do modelo.

Entre as regras estavam:

- utilizar somente o contexto fornecido;
- não inventar valores;
- não inventar datas;
- não inventar produtos ou taxas;
- informar quando não existissem dados suficientes;
- explicar conceitos de forma simples;
- evitar recomendações personalizadas de investimento;
- não prometer rentabilidade;
- não prometer aprovação de crédito;
- utilizar os valores já calculados pelo Python;
- manter respostas objetivas;
- evitar código em respostas financeiras comuns;
- limitar respostas excessivamente longas;
- utilizar simulações de metas já calculadas;
- reconhecer perguntas que dependessem de informações externas.

Essas regras documentam o comportamento pretendido da integração antiga.

---

## Exemplo Histórico de Fluxo

Uma pergunta poderia seguir este caminho:

```text
Pessoa:
"Em qual categoria eu mais gastei neste período?"

        ↓

Aplicação:
- identifica o período;
- filtra as transações;
- calcula os gastos por categoria;
- identifica a maior categoria;
- monta o contexto.

        ↓

IA:
- recebe os resultados;
- produz uma explicação;
- não recalcula os valores.
```

O princípio importante era manter o cálculo financeiro fora do modelo
generativo.

---

## Persistência Histórica da Conversa

A conversa também passou por diferentes fases.

Inicialmente, o histórico existia apenas durante a sessão do Streamlit.

Depois, foi criada persistência local no SQLite.

O objetivo era separar conversas por:

- usuário;
- período;
- modo de dados.

Exemplo:

```text
usuário A
├── 2026-06
└── 2026-07

usuário B
├── 2026-06
└── 2026-07
```

Isso evitava misturar conversas pertencentes a contextos diferentes.

O código relacionado a essa persistência chegou a ser concentrado em:

```text
src/chat_repository.py
```

O histórico de conversa não faz parte das funcionalidades atuais da v1.

Sua persistência é tratada atualmente como legado técnico.

---

## Contexto Conversacional Recente

Durante a integração generativa, nem todo o histórico precisava ser reenviado ao
modelo.

Foi adotado um limite para o contexto conversacional recente.

A estratégia utilizava apenas uma parte das mensagens anteriores e também
limitava o tamanho individual dos textos.

O objetivo era evitar crescimento indefinido do prompt.

Exemplo conceitual:

```text
Pessoa:
"O que é reserva de emergência?"

FinanTec:
"É um valor separado para situações inesperadas."

Pessoa:
"E quanto falta para a minha?"
```

A mensagem seguinte podia depender do contexto imediatamente anterior sem exigir
o envio de toda a conversa existente.

Esse mecanismo pertence exclusivamente à arquitetura histórica.

---

## Perguntas Históricas Esperadas

Entre os exemplos utilizados durante aquela fase estavam:

```text
Em qual categoria eu mais gastei neste período?
```

```text
Qual é meu saldo neste período?
```

```text
Quanto preciso guardar por mês para comprar o notebook?
```

```text
Quanto preciso guardar por mês para montar a reserva?
```

```text
O que é uma reserva para imprevistos?
```

```text
Quanto eu separei para reserva neste período?
```

As respostas deveriam utilizar valores já produzidos pelas regras da aplicação.

---

## Perguntas que Exigiam Limitação

Perguntas dependentes de informações externas não deveriam produzir respostas
inventadas.

Exemplo:

```text
Qual banco oferece o melhor CDB hoje?
```

Comportamento esperado:

```text
informar que o projeto não possui taxas ou rankings atualizados
        ↓
oferecer apenas uma explicação educativa compatível com os dados disponíveis
```

Outro exemplo:

```text
Devo investir todo meu dinheiro em Tesouro Selic?
```

O modelo deveria evitar recomendação financeira personalizada.

Outro exemplo:

```text
Qual investimento vai render mais para mim?
```

A aplicação não possuía informações suficientes para determinar o investimento
ideal de uma pessoa e também não possuía dados de mercado atualizados.

---

## Produtos Financeiros Informativos

O arquivo:

```text
data/produtos_financeiros.json
```

foi utilizado como fonte educativa durante essa fase.

O conteúdo não representava:

- ranking atualizado;
- comparação real entre bancos;
- consulta em tempo real;
- recomendação personalizada;
- garantia de rentabilidade.

O modelo poderia utilizar essas informações para explicar conceitos, mas não
deveria apresentar um produto como sendo o melhor disponível no mercado.

Esse arquivo permanece como conteúdo histórico do projeto.

---

## Conceitos Financeiros

O arquivo:

```text
data/conceitos_financeiros.json
```

também fazia parte do contexto educativo da antiga experiência.

Ele podia fornecer explicações básicas para temas financeiros sem depender de
uma busca externa.

Esse uso foi descontinuado junto com o assistente.

---

## Histórico Simulado de Atendimento

O arquivo:

```text
data/historico_atendimento.csv
```

foi utilizado durante a fase de experimentação com contexto conversacional.

Ele não representa atualmente uma conversa real ou funcionalidade de chat da
aplicação.

Sua permanência é histórica.

---

## Tratamento de Formatação

Durante os testes da antiga interface de conversa, foi identificado um problema
com textos contendo:

```text
R$
```

O Markdown utilizado pelo Streamlit podia interpretar o símbolo `$` de forma
indesejada.

Naquela implementação, foi adicionada uma etapa simples de tratamento da
resposta antes da exibição.

O código estava associado ao antigo fluxo de agente.

Esse problema não afeta os fluxos financeiros atuais porque a interface de
chat foi retirada.

---

## Configuração Histórica

A integração externa dependia de uma chave da Gemini API.

A configuração utilizava:

```text
.env
```

com uma variável como:

```env
GEMINI_API_KEY=SUA_CHAVE_DA_GEMINI_AQUI
```

Também existiu um arquivo de exemplo para orientar essa configuração.

A chave real não deveria ser versionada.

Depois da remoção da integração:

- a chamada externa foi retirada;
- a configuração deixou de ser necessária;
- a dependência do Gemini foi removida;
- a execução atual deixou de depender de internet para esse recurso.

---

## Problemas Observados Durante a Experiência

A fase com IA ajudou a revelar algumas decisões arquiteturais importantes.

### Modelo tentando interpretar cálculos

Permitir que o modelo recebesse valores brutos e reconstruísse os cálculos
aumentava o risco de inconsistência.

A solução adotada foi:

```text
Python calcula
IA recebe o resultado
```

### Contexto crescente

Conversas muito longas poderiam aumentar indefinidamente o contexto enviado.

A solução foi limitar a quantidade e o tamanho das mensagens recentes.

### Dependência externa

O funcionamento do assistente dependia de:

- internet;
- chave de API;
- disponibilidade do provedor;
- limites da API.

Isso adicionava uma dependência que não existia nos fluxos determinísticos da
aplicação.

### Privacidade

A integração também criava a possibilidade de enviar informações financeiras e
pessoais para processamento externo.

Esse risco acabou sendo o fator mais importante para a decisão de remoção.

---

## Motivo da Remoção

A integração externa oferecia uma melhoria de experiência, mas não era
necessária para que as principais funções financeiras do FinanTec funcionassem.

Ao mesmo tempo, poderia envolver o envio de:

- perguntas;
- contexto financeiro;
- perfil;
- indicadores;
- metas;
- histórico recente.

Para um projeto financeiro local, o benefício não justificava essa exposição
potencial.

A decisão foi remover a integração preventivamente.

Não existe evidência de vazamento ocorrido durante a utilização.

A decisão representa:

- minimização de dados;
- privacidade por concepção;
- redução da superfície externa;
- simplificação da arquitetura;
- priorização das funções financeiras centrais.

---

## Situação do Código Legado

Alguns módulos relacionados à experiência antiga podem permanecer no
repositório.

Exemplos históricos incluem:

```text
src/financial_intents.py
src/financial_responses.py
src/chat_repository.py
```

A permanência desses arquivos não significa que exista obrigação de mantê-los
indefinidamente.

A regra adotada para a v1 é não realizar uma grande refatoração apenas para
reduzir arquivos ou linhas quando o código está estável.

Eles poderão ser removidos quando:

- não existirem consumidores relevantes;
- sua remoção não ameaçar compatibilidade necessária;
- houver testes suficientes;
- a alteração trouxer benefício concreto.

A transição arquitetural para a v2 pode ser um momento mais apropriado para
reavaliar esse legado.

---

## O que Não é Limitação da v1

Como o assistente foi descontinuado, itens como:

- RAG;
- embeddings;
- recuperação semântica;
- avaliação automática das respostas do modelo;
- comparação semântica de respostas;
- agentes autônomos;

não são tratados como funcionalidades ausentes ou limitações da v1.

Eles simplesmente não fazem parte do escopo atual.

A ausência dessas tecnologias não impede nenhum dos fluxos financeiros
principais.

---

## Possível Uso de IA no Futuro

Não existe atualmente uma nova integração de IA aprovada para implementação.

Uma eventual retomada só faria sentido se existisse um problema concreto que
justificasse o recurso.

Qualquer nova proposta deveria ser analisada considerando:

- quais dados seriam utilizados;
- se os dados sairiam da aplicação;
- onde o processamento ocorreria;
- custo;
- privacidade;
- segurança;
- benefício real para o usuário;
- possibilidade de solução determinística;
- necessidade de consentimento;
- arquitetura da v2.

O simples fato de o projeto já ter utilizado IA não cria obrigação de
reintroduzi-la.

---

## Relação com uma possível v2

Uma possível evolução para frontend e API separados não depende do retorno do
assistente.

A v2 deve inicialmente priorizar:

```text
frontend
        ↓
API
        ↓
autenticação e autorização
        ↓
regras financeiras
        ↓
persistência
```

IA, caso volte a ser considerada algum dia, deve ser tratada como uma
funcionalidade independente e não como fundamento da arquitetura.

---

## Decisão Atual

A direção histórica era:

```text
dados organizados
        ↓
cálculos em Python
        ↓
explicação com IA
```

A direção atual da v1 publicada é:

```text
dados organizados
        ↓
regras determinísticas
        ↓
persistência configurável
(SQLite ou Turso/libSQL)
        ↓
interface Streamlit
```

Uma eventual evolução arquitetural deverá seguir necessidades confirmadas pelo
feedback externo:

```text
v1 publicada
        ↓
feedback e definição de escopo
        ↓
frontend e API separados
        ↓
migração gradual das funções financeiras
```

O antigo assistente permanece documentado porque fez parte da evolução técnica
do FinanTec.

Ele não faz parte do produto atual e não representa uma prioridade futura.
