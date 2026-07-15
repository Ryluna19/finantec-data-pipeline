# AI Prompting — Registro histórico do FinanTec

> [!IMPORTANT]
> Este documento preserva a arquitetura da antiga integração com Gemini.
> A API externa, `src/agent.py`, `src/prompts.py` e a configuração por chave
> não fazem mais parte da execução atual. Não houve violação comprovada; a
> integração foi removida preventivamente devido ao risco potencial de expor
> contexto financeiro e pessoal a um serviço externo. Consulte a
> [decisão arquitetural](decisions/001-remove-gemini-integration.md).

## Visão Geral Histórica

O FinanTec Data Pipeline utilizava IA generativa para explicar indicadores financeiros calculados pela aplicação.

A IA não era responsável por calcular receitas, gastos, saldo ou metas. Esses
valores eram calculados previamente em Python e enviados como contexto
estruturado para o modelo.

A responsabilidade da IA era interpretar a pergunta da pessoa usuária e
transformar os dados disponíveis em uma explicação clara, educativa e
contextualizada.

Atualmente, nenhuma dessas informações é enviada externamente. A classificação
e as respostas locais foram preservadas, mas o recurso está congelado fora da
navegação principal.

---

## Princípio Principal

O princípio central do assistente é:

```text
Python calcula → IA explica
```

Essa separação reduz o risco de respostas incorretas, números inventados ou recomendações sem base nos dados.

---

## Classificação Local de Intenção

Antes de enviar uma pergunta para a IA, o FinanTec executa uma
classificação local e determinística.

Essa classificação está em:

```text
src/financial_intents.py
```

## Respostas Determinísticas

As intenções financeiras mais simples não precisam consultar o modelo
generativo.

O módulo:

```text
src/financial_responses.py
```

## Papel Histórico da IA

A IA era usada para:

- responder perguntas sobre o período analisado;
- explicar receitas, gastos, saldo e reserva;
- interpretar gastos por categoria;
- explicar metas financeiras;
- apresentar conceitos financeiros básicos;
- reconhecer limitações quando não houver dados suficientes;
- transformar indicadores calculados em uma explicação mais acessível.

A IA não deve:

- inventar valores;
- inventar datas;
- inventar bancos, produtos ou taxas;
- calcular metas por conta própria;
- recomendar investimentos personalizados;
- consultar dados em tempo real;
- indicar rankings de bancos ou produtos financeiros;
- substituir orientação profissional.

---

## Contexto que Era Enviado para o Modelo

Antes de enviar a pergunta para a IA, a aplicação montava um contexto com informações como:

- perfil fictício da pessoa usuária;
- período analisado;
- resumo financeiro calculado pelo Python;
- gastos por categoria calculados pelo Python;
- simulações de metas calculadas pelo Python;
- histórico de dúvidas simuladas;
- conceitos financeiros disponíveis;
- produtos financeiros informativos;
- limitações do projeto.

Esse contexto é montado em:

```text
src/prompts.py
```

A chamada para a Gemini API é feita em:

```text
src/agent.py
```

---

## System Prompt

O comportamento do assistente é definido por um `SYSTEM_PROMPT`.

As principais regras são:

- usar apenas informações fornecidas no contexto;
- não inventar valores, datas, produtos, taxas, bancos ou dados pessoais;
- informar quando não houver dados suficientes;
- explicar conceitos de forma simples, direta e educativa;
- evitar recomendações personalizadas de investimento;
- não prometer rentabilidade, aprovação de crédito ou resultado financeiro;
- usar os valores calculados pela aplicação Python sem alterá-los;
- responder de forma objetiva;
- evitar blocos de código em respostas comuns;
- limitar respostas longas quando a pessoa não pedir detalhes;
- usar dados de metas já calculados pelo Python;
- responder com limitação clara para perguntas sobre dados atuais ou externos.

---

## Exemplo de Fluxo

```text
Usuário pergunta:
"Em qual categoria eu mais gastei neste período?"

Aplicação:
- identifica o período selecionado;
- filtra as transações;
- calcula gastos por categoria;
- identifica a maior categoria;
- monta o contexto;
- envia a pergunta para a IA.

IA:
- lê os valores calculados;
- responde de forma explicativa;
- não recalcula os números.
```

---

## Evolução Histórica da Persistência

O dashboard inicialmente manteve um histórico de conversa separado por período
apenas na sessão do Streamlit. Em uma etapa posterior, o histórico passou a ser
persistido localmente no SQLite e isolado por usuário, período e modo de dados.

Isso evita misturar perguntas de meses diferentes.

Exemplo:

```text
2026-06 → conversa própria
2026-07 → conversa própria
```

Essa persistência local foi preservada após a remoção do Gemini, embora o
recurso tenha saído da navegação principal.

---

## Perguntas Esperadas

Exemplos de perguntas que o assistente deve responder:

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

---

## Perguntas com Limitação

Algumas perguntas devem ser recusadas ou respondidas com limitação clara.

Exemplo:

```text
Qual banco oferece o melhor CDB hoje?
```

Resposta esperada:

```text
Não tenho dados atualizados sobre bancos, taxas ou rankings de CDB para responder isso com segurança. Posso explicar o que é um CDB com liquidez diária usando a base de conhecimento do projeto.
```

Outro exemplo:

```text
Devo investir todo meu dinheiro em Tesouro Selic?
```

Resposta esperada:

```text
Não posso fazer recomendação personalizada de investimento. Posso explicar o que é Tesouro Selic de forma educativa, com base nas informações disponíveis.
```

Outro exemplo:

```text
Qual investimento vai render mais para mim?
```

Resposta esperada:

```text
Não posso indicar o melhor investimento para você de forma personalizada. O projeto não possui dados suficientes sobre seu perfil real, objetivos completos, tolerância a risco ou taxas atualizadas. Posso explicar diferenças gerais entre produtos financeiros presentes na base de conhecimento.
```

---

## Produtos Financeiros Informativos

O arquivo:

```text
data/produtos_financeiros.json
```

contém produtos financeiros apenas para fins educativos e simulados.

Esses dados não representam:

- recomendação personalizada;
- ranking atualizado;
- consulta em tempo real;
- comparação real entre bancos;
- garantia de rentabilidade.

A IA pode usar esses dados para explicar conceitos, mas não deve afirmar que um produto é o melhor disponível no mercado.

---

## Tratamento de Formatação

Durante os testes, foi identificado que respostas contendo `R$` poderiam ser interpretadas pelo Markdown do Streamlit como fórmula matemática.

Para evitar esse problema, a resposta passa por uma limpeza simples em:

```text
src/agent.py
```

Essa etapa:

- remove crases indesejadas;
- escapa o símbolo `$`;
- melhora a exibição da resposta no dashboard.

---

## Configuração Histórica da IA

A integração com IA dependia de uma chave da Gemini API configurada no arquivo:

```text
.env
```

O projeto possuía um arquivo modelo:

```text
.env.example
```

Exemplo:

```env
GEMINI_API_KEY=SUA_CHAVE_DA_GEMINI_AQUI
```

O arquivo `.env` não deve ser enviado para o GitHub.

O arquivo `.env.example`, a dependência externa e essa configuração foram
removidos junto com a integração.

---

## Histórico Persistente de Conversa

O histórico do assistente é armazenado localmente no SQLite.

A persistência está em:

```text
src/chat_repository.py
```

## Contexto Conversacional Recente na Integração Histórica

Além de persistir o histórico no SQLite, o FinanTec enviava uma pequena parte
da conversa recente para a IA quando a pergunta precisava do modelo generativo.

Eram enviadas no máximo seis mensagens anteriores, excluindo a mensagem inicial
do sistema.

Cada mensagem também possui um limite de caracteres para impedir que o prompt
cresça indefinidamente.

Exemplo:

```text
Pessoa:
"O que é reserva de emergência?"

FinanTec:
"É um valor separado para situações inesperadas."

Pessoa:
"E quanto falta para a minha?"
```

## Limitações Atuais

O projeto ainda não possui:

- testes automatizados para respostas da IA;
- avaliação automática de qualidade das respostas;
- comparação semântica entre resposta esperada e resposta gerada;
- suporte a múltiplos perfis;
- recuperação semântica avançada;
- RAG com embeddings;
- consulta em tempo real a dados financeiros externos.

Esses pontos podem ser evoluídos no futuro, mas não são necessários para a versão atual do pipeline.

---

## Decisão Atual

Durante a fase com Gemini, a direção recomendada era:

```text
dados organizados → cálculos em Python → explicação com IA
```

Essa direção foi substituída pela decisão de manter o produto totalmente local.
O código determinístico e o histórico permanecem como registro técnico, sem
retomar chamadas externas ou apresentar Insights como prioridade do produto.
