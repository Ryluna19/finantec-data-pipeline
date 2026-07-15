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
- informações do perfil e das metas incluídas no contexto.

O uso de uma API gratuita não significa, por si só, que tenha ocorrido uma
violação de segurança. Também não foi identificada evidência de vazamento de
dados no projeto. Entretanto, o modelo de acesso gratuito e o processamento
por um terceiro não ofereciam benefício ou controle suficientes para justificar
a exposição potencial de informações financeiras e pessoais em uma aplicação
concebida para uso local.

## Decisão

A integração externa com Gemini foi removida preventivamente.

A decisão adotou os princípios de minimização de dados e privacidade por
concepção:

- nenhuma pergunta ou informação financeira é enviada a serviços externos;
- as respostas suportadas são calculadas de forma local e determinística;
- perguntas não reconhecidas recebem um fallback seguro;
- o histórico permanece armazenado localmente no SQLite;
- dependências, chaves, prompts e chamadas externas deixaram de fazer parte da
  execução atual.

Os módulos locais de classificação, respostas e persistência foram preservados
como parte da evolução técnica do projeto. O recurso de Insights foi congelado
e retirado da navegação principal, mas seu código e seus dados não foram
apagados.

## Consequências

### Benefícios

- menor exposição de dados pessoais e financeiros;
- funcionamento sem internet ou chave de API;
- respostas reproduzíveis e testáveis;
- redução de dependências e configuração externa;
- posicionamento mais coerente com um aplicativo financeiro local.

### Limitações aceitas

- menor flexibilidade para interpretar linguagem livre;
- conjunto restrito de perguntas atendidas localmente;
- fallback para temas que não possuem cálculo determinístico;
- manutenção de documentos históricos para registrar a arquitetura anterior.

## Registro histórico

Os documentos `docs/ai_prompting.md`, `docs/knowledge_base.md` e
`docs/validation.md` conservam partes da implementação anterior. Eles não
descrevem a configuração vigente e devem ser lidos como registro da evolução
do projeto.
