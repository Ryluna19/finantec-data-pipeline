# ADR 001 — Remoção da integração externa com Gemini

- **Status:** aceita
- **Data:** julho de 2026
- **Escopo:** consultas financeiras e histórico de conversa

## Contexto

O FinanTec já utilizou a API do Gemini como complemento para responder
perguntas que não eram atendidas pelas regras locais.

Para gerar essas respostas, a integração poderia enviar a um serviço externo:

- a pergunta da pessoa usuária;
- parte do histórico recente da conversa;
- indicadores financeiros calculados para o período;
- informações do perfil;
- informações das metas incluídas no contexto.

O uso de uma API gratuita não significa, por si só, que tenha ocorrido uma
violação de segurança.

Também não foi identificada evidência de vazamento de dados no projeto.

Entretanto, o processamento por um terceiro não oferecia benefício ou controle
suficientes para justificar a exposição potencial de informações financeiras e
pessoais em uma aplicação concebida principalmente para uso local.

---

## Decisão

A integração externa com Gemini foi removida preventivamente.

A decisão adotou princípios de minimização de dados e privacidade por concepção.

Como consequência imediata daquela decisão:

- perguntas e informações financeiras deixaram de ser enviadas ao Gemini;
- chamadas externas relacionadas ao assistente foram removidas da execução;
- a configuração por chave de API deixou de ser necessária;
- prompts destinados ao serviço externo deixaram de fazer parte do fluxo ativo;
- consultas suportadas continuaram podendo utilizar regras locais e
  determinísticas;
- o histórico de conversa permaneceu, naquele momento, armazenado localmente;
- módulos locais relacionados à classificação e às respostas foram preservados.

O antigo recurso de Insights deixou de depender de IA externa e foi retirado da
navegação principal.

A remoção do Gemini não exigiu a exclusão imediata de todo código relacionado à
experiência anterior.

---

## Alternativas Consideradas

### Manter Gemini

Permitiria maior flexibilidade para interpretar linguagem natural, mas
preservaria:

- dependência de serviço externo;
- necessidade de configuração;
- envio potencial de contexto financeiro;
- comportamento menos determinístico;
- maior superfície de privacidade.

Essa alternativa foi rejeitada.

### Reduzir o contexto enviado

Seria possível diminuir a quantidade de informações enviadas ao modelo.

Mesmo assim, a aplicação continuaria dependente de processamento externo e
ainda precisaria decidir quais informações poderiam sair do ambiente local.

Essa alternativa não eliminava a preocupação central.

### Manter apenas respostas locais

Foi a alternativa adotada inicialmente após a remoção do Gemini.

Ela permitia preservar parte da experiência sem transmitir informações para
serviços externos.

---

## Consequências

### Benefícios

A decisão trouxe:

- menor exposição potencial de dados pessoais e financeiros;
- funcionamento sem internet para esse fluxo;
- ausência de dependência de chave de API;
- respostas locais reproduzíveis;
- maior facilidade de teste;
- redução de dependências externas;
- arquitetura mais coerente com uma aplicação financeira local.

### Limitações aceitas naquele momento

A remoção da IA generativa reduziu:

- flexibilidade para interpretar linguagem livre;
- variedade de perguntas compreendidas;
- capacidade de produzir respostas abertas;
- continuidade de perguntas fora das intenções previstas.

Essas limitações foram consideradas aceitáveis porque o assistente não era
necessário para os principais fluxos financeiros do produto.

---

## Evolução Posterior

Depois desta decisão, o produto continuou evoluindo.

O mecanismo local que havia sido preservado deixou de fazer parte da experiência
principal e o antigo assistente financeiro foi posteriormente retirado das
funcionalidades atuais da aplicação.

Na v1 atual:

```text
Gemini
→ removido

assistente financeiro
→ não faz parte do produto atual

Insights
→ não faz parte da navegação atual

histórico de conversas
→ não faz parte da experiência atual

módulos e dados remanescentes
→ legado técnico ou registro histórico
```

A publicação posterior da V1 não alterou esta decisão. A aplicação continua sem
enviar os dados financeiros cadastrados para um serviço externo de IA.
