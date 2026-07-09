# AI Prompting — FinanTec Data Pipeline

## Visão Geral

O FinanTec Data Pipeline utiliza IA generativa para explicar indicadores financeiros calculados pela aplicação.

A IA não é responsável por calcular receitas, gastos, saldo ou metas. Esses valores são calculados previamente em Python e enviados como contexto estruturado para o modelo.

A responsabilidade da IA é interpretar a pergunta da pessoa usuária e transformar os dados disponíveis em uma explicação clara, educativa e contextualizada.

---

## Princípio Principal

O princípio central do assistente é:

```text
Python calcula → IA explica
```

Essa separação reduz o risco de respostas incorretas, números inventados ou recomendações sem base nos dados.

---

## Papel da IA

A IA é usada para:

- responder perguntas sobre o período analisado;
- explicar gastos por categoria;
- interpretar saldo, consumo e reserva;
- explicar metas financeiras;
- apresentar conceitos financeiros básicos;
- reconhecer limitações quando não houver dados suficientes.

A IA não deve:

- inventar valores;
- calcular metas por conta própria;
- recomendar investimentos personalizados;
- consultar dados em tempo real;
- indicar bancos, taxas ou rankings;
- substituir orientação profissional.

---

## Contexto Enviado para o Modelo

Antes de enviar a pergunta para a IA, a aplicação monta um contexto com informações como:

- perfil fictício da pessoa usuária;
- período analisado;
- resumo financeiro calculado pelo Python;
- gastos por categoria calculados pelo Python;
- simulações de metas calculadas pelo Python;
- histórico de dúvidas simuladas;
- conceitos financeiros disponíveis;
- produtos financeiros informativos.

Esse contexto é montado em:

```text
src/prompts.py
```

---

## System Prompt

O comportamento do assistente é definido por um `SYSTEM_PROMPT`.

As principais regras são:

- usar apenas informações fornecidas no contexto;
- não inventar valores, datas, produtos ou dados pessoais;
- informar quando não houver dados suficientes;
- explicar conceitos de forma simples;
- evitar recomendações personalizadas de investimento;
- não prometer resultados financeiros;
- usar valores calculados pela aplicação Python;
- responder de forma objetiva;
- evitar blocos de código em respostas comuns.

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

---

## Tratamento de Formatação

Durante os testes, foi identificado que respostas contendo `R$` poderiam ser interpretadas pelo Markdown do Streamlit como fórmula matemática.

Para evitar esse problema, a resposta passa por uma limpeza simples em:

```text
src/agent.py
```

Essa etapa remove formatações indesejadas e escapa o símbolo `$` antes da exibição no dashboard.

---

## Limitações Atuais

O projeto ainda não possui:

- memória persistente de conversa fora da sessão do Streamlit;
- histórico armazenado em banco;
- testes automatizados para respostas da IA;
- avaliação automática de qualidade das respostas;
- suporte a múltiplos perfis;
- recuperação semântica avançada;
- RAG com embeddings.

Esses pontos podem ser evoluídos no futuro, mas não são necessários para a versão atual do pipeline.