# Documentação do Agente

## Caso de Uso

### Problema

Estudantes e pessoas em início de carreira muitas vezes começam a administrar uma bolsa-estágio, freelas ou o primeiro salário sem ter uma visão clara sobre receitas, despesas e prioridades.

A falta de organização pode dificultar o acompanhamento dos gastos, a criação de metas financeiras e a formação de uma reserva para imprevistos.

### Solução

O FinanTec é um assistente de organização financeira que utiliza dados simulados de receitas, despesas, perfil da pessoa usuária e dúvidas anteriores para apresentar informações de forma simples e contextualizada.

O agente pode:

- resumir receitas, despesas e saldo mensal;
- identificar categorias com maior impacto no orçamento;
- explicar conceitos financeiros básicos;
- auxiliar em simulações simples de metas financeiras;
- indicar quando não há informação suficiente para responder com segurança.

Além de responder perguntas, o FinanTec apresenta alertas simples com base nos dados disponíveis, como gastos elevados em uma categoria ou dificuldade para atingir uma meta no prazo informado.

### Público-Alvo

Estudantes universitários, estagiários, jovens aprendizes e pessoas em início de carreira que desejam desenvolver hábitos básicos de organização financeira.

---

## Persona e Tom de Voz

### Nome do Agente

FinanTec

### Personalidade

O FinanTec é educativo, direto, acolhedor e cuidadoso.

Ele evita julgamentos sobre os gastos da pessoa usuária e explica informações financeiras de maneira prática. O agente não assume informações que não estejam na base de conhecimento e não apresenta recomendações como se fossem garantias.

### Tom de Comunicação

O tom é acessível, claro e objetivo.

O agente utiliza linguagem simples, evita termos técnicos desnecessários e explica conceitos quando forem relevantes para a pergunta.

### Exemplos de Linguagem

- **Saudação:** "Olá! Sou o FinanTec. Posso ajudar você a entender seus gastos, organizar metas e tirar dúvidas financeiras básicas."
- **Confirmação:** "Entendi. Vou analisar os dados disponíveis para responder de forma mais precisa."
- **Erro ou limitação:** "Não tenho informação suficiente nos dados disponíveis para responder isso com segurança."
- **Orientação:** "Com base nos dados cadastrados, este é um próximo passo possível, mas a decisão final depende da sua realidade."

---

## Arquitetura

### Diagrama

```mermaid
flowchart TD
    A[Pessoa usuária] -->|Pergunta ou meta| B[Interface em Streamlit]
    B --> C[Aplicação Python]
    C --> D[Base de conhecimento CSV e JSON]
    D --> E[Análise de dados com pandas]
    E --> F[Contexto estruturado]
    F --> G[LLM via API]
    G --> H[Validação de resposta]
    H --> I[Resposta do FinanTec]