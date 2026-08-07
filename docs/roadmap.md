# Roadmap — FinanTec

## Visão Geral

O FinanTec deve evoluir de forma incremental, preservando uma versão local
funcional antes de mudanças arquiteturais mais profundas.

A v1 consolidou o projeto como uma aplicação de organização financeira pessoal
com persistência local, contas, transações, importação, orçamento, metas,
perfil e gerenciamento dos próprios dados.

O projeto não precisa se transformar em banco digital, sistema empresarial ou
plataforma financeira de grande escala para cumprir seu objetivo.

A prioridade continua sendo:

- resolver problemas concretos;
- manter regras de negócio claras;
- preservar dados existentes;
- evitar infraestrutura sem necessidade;
- tratar privacidade e segurança como requisitos reais;
- evoluir a arquitetura somente quando houver benefício justificável.

A próxima fase deixa de ser expansão funcional da v1 e passa a ser preparação
para uma nova arquitetura.

---

## Estado da Versão 1

A v1 local está funcionalmente concluída.

### Contas

Foram implementados:

- criação de contas locais;
- autenticação por usuário e senha;
- armazenamento de credenciais sem senha em texto puro;
- contexto explícito de usuário;
- isolamento dos principais dados por `user_id`;
- encerramento da sessão;
- exclusão dos dados financeiros preservando a conta;
- exclusão definitiva da conta e seus dados associados.

O sistema atual atende ao contexto local da v1.

Ele ainda não deve ser considerado uma solução de autenticação pronta para uma
aplicação pública em produção.

### Transações

Foram implementados:

- cadastro manual;
- consulta;
- filtros;
- edição;
- exclusão;
- persistência direta no SQLite;
- exportação por período.

### Importação

A aplicação suporta:

- CSV;
- Excel;
- OFX;
- planilhas Excel externas com mapeamento assistido.

O fluxo inclui:

- seleção de aba;
- identificação ou seleção de cabeçalho;
- prévia dos dados;
- mapeamento de colunas;
- valor único;
- tipo explícito;
- débito e crédito separados;
- validação;
- rejeições;
- identificação de possíveis duplicatas;
- comportamento seguro de ignorar duplicatas por padrão;
- opção explícita para importar possíveis duplicatas.

### Orçamento

Foram implementados:

- limites mensais por categoria;
- persistência por usuário;
- criação;
- edição;
- exclusão;
- recorrência entre períodos;
- encerramento de limites;
- alteração a partir de determinado mês;
- comparação entre planejado e gasto;
- indicação de valor disponível ou excedido;
- estados visuais;
- integração com a Visão geral.

### Metas

Foram implementados:

- criação;
- edição;
- exclusão;
- persistência;
- progresso;
- valor restante;
- contribuição mensal;
- simulador separado dos dados persistidos;
- isolamento por usuário;
- contexto demonstrativo separado.

### Perfil

Foram implementados:

- primeiro uso sem perfil automático;
- criação no primeiro salvamento;
- edição;
- fontes de renda;
- cálculo da renda mensal;
- dados financeiros complementares;
- persistência por usuário;
- perfil demonstrativo separado e somente leitura.

### Dados e privacidade

Foram implementados:

- alternância entre dados pessoais e demonstração;
- retorno seguro aos dados pessoais;
- preservação dos dados pessoais durante a demonstração;
- resumo dos dados armazenados;
- exclusão coordenada dos dados financeiros;
- preservação da conta após o reset financeiro;
- exclusão definitiva da conta;
- remoção dos dados associados à conta excluída.

A diferença entre as duas operações é:

```text
Apagar meus dados
→ remove os dados financeiros
→ preserva conta e credenciais

Excluir conta
→ remove conta
→ remove os dados associados
```

### Demonstração

A demonstração permanece isolada do contexto pessoal.

Ela pode ser ativada para apresentação do projeto sem substituir os dados reais
do usuário.

Perfil e Metas fictícios permanecem separados dos registros pessoais.

### ETL

O ETL permanece disponível para:

- base de demonstração;
- processamento explícito;
- validação;
- geração de rejeições;
- compatibilidade histórica.

Ele não é mais pré-requisito para o funcionamento normal da aplicação.

### UX e responsividade

A interface passou por revisão em:

- desktop;
- notebook;
- mobile;
- tema escuro;
- tema claro.

Foram priorizados:

- legibilidade;
- largura controlada;
- ausência de rolagem horizontal global;
- navegação consistente;
- hierarquia dos principais cards;
- comportamento dos formulários e ações destrutivas.

---

## Funcionalidade de IA Descontinuada

O FinanTec já possuiu um assistente financeiro com integração ao Gemini.

A integração externa foi removida preventivamente devido ao risco de enviar
contexto financeiro para um serviço de terceiros sem benefício proporcional
para a proposta local do projeto.

A decisão está registrada em:

```text
docs/decisions/001-remove-gemini-integration.md
```

O antigo:

- assistente financeiro;
- histórico de conversas;
- mecanismo de Insights;
- fluxo baseado em Gemini;

não faz parte das funcionalidades atuais da v1.

Módulos, testes ou documentos relacionados podem permanecer temporariamente
como legado técnico ou registro histórico quando sua remoção não trouxer
benefício suficiente para justificar uma nova refatoração.

Nova integração externa de IA não é prioridade da evolução atual.

---

## Fechamento da v1

Antes de abrir mudanças arquiteturais da v2, a v1 deve possuir um ponto de
referência estável.

O fechamento inclui:

- validação funcional dos principais fluxos;
- suíte automatizada passando;
- documentação alinhada ao comportamento atual;
- revisão de arquivos versionados;
- repositório limpo;
- commit final da documentação;
- criação de uma versão ou tag de referência para a v1.

Depois desse marco, mudanças profundas deixam de ser feitas diretamente na v1
sem uma justificativa clara.

Correções relevantes ainda poderão ser aplicadas, especialmente quando
envolverem:

- perda de dados;
- segurança;
- autenticação;
- isolamento entre usuários;
- corrupção de persistência;
- regressões funcionais importantes.

---

## Próxima Etapa — Segurança e Hardening

Depois do fechamento da v1, a próxima etapa planejada é uma revisão específica
de segurança.

O objetivo não é transformar a aplicação Streamlit em um sistema público de
produção.

A intenção é:

1. entender as limitações reais da implementação atual;
2. identificar vulnerabilidades ou comportamentos arriscados;
3. corrigir problemas relevantes;
4. usar os resultados para orientar a arquitetura da v2.

### Autenticação

Revisar:

- algoritmo e parâmetros utilizados no hash de senha;
- criação e validação de credenciais;
- regras mínimas de senha;
- comparação segura de hashes;
- necessidade de rehash;
- exposição acidental de credenciais;
- comportamento de login e logout;
- estado da sessão;
- exclusão de conta.

### Autorização e isolamento

Verificar se todas as operações sensíveis utilizam corretamente o contexto do
usuário.

Revisar:

- transações;
- perfil;
- metas;
- orçamento;
- importação;
- exportação;
- reset financeiro;
- exclusão de conta.

O principal objetivo é impedir que um `user_id` incorreto permita leitura,
alteração ou exclusão de informações de outro usuário.

### SQLite

Revisar:

- consultas parametrizadas;
- construção dinâmica de SQL;
- transações;
- integridade das operações destrutivas;
- constraints relevantes;
- tratamento de exceções;
- concorrência esperada no contexto local;
- caminhos utilizados para o arquivo do banco.

### Importação de arquivos

Revisar:

- extensões aceitas;
- tamanho de arquivos;
- nomes de arquivos;
- caminhos;
- conteúdo inesperado;
- planilhas malformadas;
- OFX inválido;
- comportamento diante de arquivos grandes;
- mensagens de erro;
- persistência temporária.

### Dados e privacidade

Revisar:

- dados armazenados no SQLite;
- arquivos locais;
- logs;
- caches;
- estado da sessão;
- exclusão financeira;
- exclusão de conta;
- demonstração;
- possíveis resíduos após operações de remoção.

### Dependências e configuração

Introduzir ou avaliar verificações para:

- dependências vulneráveis;
- pacotes desnecessários;
- versões incompatíveis;
- `.env`;
- secrets;
- arquivos ignorados pelo Git;
- informações sensíveis versionadas acidentalmente.

### Resultado esperado

A auditoria deve terminar com uma classificação simples:

```text
corrigir na v1
→ vulnerabilidade ou risco concreto atual

corrigir durante a fundação da v2
→ problema dependente da nova arquitetura

não priorizar
→ risco irrelevante para o contexto atual
```

---

## Versão 2 — Objetivo Arquitetural

A v2 deve separar frontend, backend e persistência de forma mais explícita.

Direção planejada:

```text
Frontend React
        ↓
HTTP
        ↓
API Python
        ↓
Serviços e regras de negócio
        ↓
Persistência
```

A v2 não deve ser uma reescrita completa feita de uma única vez.

O objetivo é aproveitar regras e comportamentos já validados na v1 e migrar as
funcionalidades gradualmente.

---

## Fundação da v2

Antes de migrar telas, será necessário definir as responsabilidades da nova
arquitetura.

### Backend

O backend Python deverá concentrar:

- autenticação;
- autorização;
- regras financeiras;
- validação;
- persistência;
- importação;
- contratos de dados;
- tratamento de erros.

A escolha específica do framework da API deve ser registrada quando a
implementação começar.

### Frontend

React deverá assumir a responsabilidade pela experiência de interface.

O frontend não deve ser responsável por decidir:

- se o usuário pode acessar um registro;
- se determinada transação pertence à conta;
- como uma senha é validada;
- se uma exclusão é permitida;
- quais regras financeiras são consideradas válidas.

Essas decisões pertencem ao backend.

### Contratos

A comunicação entre frontend e backend deverá utilizar contratos claros para:

- autenticação;
- conta;
- transações;
- importação;
- perfil;
- metas;
- orçamento;
- dados e privacidade.

---

## Sistema de Contas na v2

O sistema atual de contas será usado como referência funcional, não
necessariamente como implementação definitiva.

Na arquitetura web será necessário reavaliar:

- autenticação da API;
- autorização por recurso;
- sessões ou tokens;
- cookies, caso aplicáveis;
- expiração de autenticação;
- proteção contra brute force;
- política de senha;
- troca de senha;
- recuperação de acesso;
- CSRF conforme a estratégia adotada;
- CORS;
- armazenamento seguro de secrets;
- exclusão definitiva da conta;
- invalidação de sessões;
- logging de eventos relevantes sem exposição de dados sensíveis.

Essas decisões devem ser tomadas antes de considerar a autenticação da v2 pronta
para publicação.

---

## Migração Funcional para a v2

Depois da fundação, as funcionalidades devem ser migradas gradualmente.

Uma sequência possível é:

```text
1. conta e autenticação
2. leitura de transações
3. CRUD de transações
4. filtros e indicadores
5. importação
6. perfil
7. metas
8. orçamento
9. dados e privacidade
10. refinamento visual
```

A ordem pode mudar quando a implementação começar.

O princípio mais importante é evitar migrar todas as funcionalidades ao mesmo
tempo sem checkpoints intermediários.

Cada fluxo migrado deve possuir:

- API funcional;
- validação;
- autorização;
- testes;
- comportamento equivalente ou melhor que a v1.

---

## DevOps e Qualidade na v2

DevOps não deve aparecer apenas depois que todo o produto estiver pronto.

As práticas mais úteis devem entrar desde a fundação da v2.

### Integração contínua

Estruturar CI para executar automaticamente verificações como:

```text
push / pull request
        ↓
lint
        ↓
testes
        ↓
análise estática
        ↓
verificação de dependências
        ↓
build
```

### Backend

Avaliar e introduzir gradualmente:

- pytest;
- lint;
- formatter;
- análise estática;
- análise de segurança;
- verificação de dependências vulneráveis;
- cobertura útil de regras críticas.

### Frontend

Introduzir:

- lint;
- build automatizado;
- testes das regras relevantes de interface;
- validação de tipos, caso TypeScript seja adotado;
- verificações automatizadas antes de merge.

### Git

Manter:

- commits pequenos e coerentes;
- branches quando trouxerem benefício;
- pull requests para mudanças maiores quando o fluxo justificar;
- histórico compreensível;
- releases ou tags para marcos importantes.

---

## PostgreSQL e Persistência Futura

PostgreSQL não é requisito para fechar a v1 nem precisa ser adotado no primeiro
commit da v2.

SQLite continua adequado enquanto:

- a aplicação roda localmente;
- existe baixa concorrência;
- não há servidor compartilhado;
- a complexidade adicional não traz benefício.

PostgreSQL passa a fazer mais sentido quando existirem necessidades concretas
como:

- múltiplos usuários simultâneos;
- backend publicado;
- concorrência;
- servidor central;
- deploy persistente;
- infraestrutura de produção.

Quando essa migração acontecer, também será necessário estruturar:

- migrations;
- configuração por ambiente;
- criação segura do schema;
- índices;
- constraints;
- backup;
- recuperação.

A mudança deve acontecer por necessidade arquitetural, não apenas para adicionar
uma tecnologia ao portfólio.

---

## Deploy

Deploy não é a próxima ação imediata.

Antes da publicação deverão existir pelo menos:

- arquitetura web definida;
- autenticação adequada ao ambiente;
- autorização validada;
- revisão de segurança;
- gerenciamento de secrets;
- persistência adequada;
- CI estável;
- tratamento seguro de configurações;
- estratégia de logs;
- estratégia de atualização do banco.

A publicação pode começar com um ambiente simples.

Não existe necessidade atual de infraestrutura complexa.

---

## Observabilidade e Operação

Somente quando houver uma aplicação publicada, avaliar:

- logs estruturados;
- monitoramento de erros;
- métricas básicas;
- health checks;
- alertas;
- backup;
- recuperação;
- acompanhamento de falhas de autenticação;
- acompanhamento de erros da API.

A observabilidade deve responder a problemas concretos da aplicação e não ser
adicionada apenas para aumentar a quantidade de ferramentas utilizadas.

---

## Limpeza de Legado

A limpeza de compatibilidades antigas deixa de ser uma prioridade principal.

Elementos legados podem ser removidos quando:

- não possuem consumidores;
- não representam dados que ainda precisam ser migrados;
- sua remoção reduz risco ou manutenção;
- existem testes suficientes para proteger o comportamento alterado.

Não realizar refatorações apenas para:

- reduzir número de arquivos;
- reduzir número de linhas;
- remover wrappers triviais sem benefício;
- modernizar código estável sem necessidade funcional.

Partes relacionadas ao antigo assistente poderão ser revisitadas durante a
transição para a v2, quando ficar claro se ainda possuem algum consumidor
válido.

---

## Não Priorizar

Continuam fora das prioridades atuais:

- nova integração externa com IA;
- Open Finance;
- integração bancária direta;
- recomendação personalizada de investimentos;
- execução automática de operações financeiras;
- microserviços;
- Kubernetes;
- filas distribuídas;
- múltiplas organizações;
- arquitetura multi-tenant empresarial;
- aplicativo mobile nativo;
- RAG;
- embeddings;
- agentes autônomos;
- infraestrutura paga sem necessidade comprovada.

Esses itens podem ser reavaliados no futuro somente se aparecer um problema
concreto que justifique sua adoção.

---

## Qualidade e Testes

Os testes devem continuar focados em comportamento e risco.

Priorizar cobertura para:

- autenticação;
- autorização;
- isolamento entre usuários;
- persistência;
- CRUD;
- importação;
- validação;
- rejeições;
- duplicatas;
- exclusão de dados;
- exclusão de conta;
- cálculos financeiros;
- orçamento;
- metas;
- migrations quando existirem;
- contratos da API;
- fluxos críticos da v2.

Evitar testes de baixo valor para:

- wrappers triviais;
- detalhes internos sem impacto observável;
- textos exatos sem significado funcional;
- implementação que pode ser refatorada sem alterar comportamento.

Testes end-to-end de navegador passam a ter mais valor quando a v2 possuir
frontend e backend separados.

---

## Critério de Prioridade

Antes de iniciar uma mudança, avaliar:

1. Qual problema real ela resolve?
2. O benefício é visível para quem usa ou avalia o projeto?
3. O custo e o risco são proporcionais?
4. A mudança preserva os dados existentes?
5. Ela reduz ou aumenta a superfície de segurança?
6. A arquitetura atual é o lugar certo para resolver esse problema?
7. A solução introduz uma dependência realmente necessária?
8. Existem testes capazes de proteger a mudança?
9. O código atual confirma que a necessidade ainda existe?

A direção do FinanTec deve permanecer:

```text
produto pequeno
        ↓
regras confiáveis
        ↓
dados protegidos
        ↓
arquitetura coerente
        ↓
automação de qualidade
        ↓
evolução incremental
```

---

## Sequência Planejada

O roadmap atual pode ser resumido em:

```text
V1 LOCAL
✓ funcionalidades principais
✓ contas locais
✓ persistência
✓ importação
✓ orçamento
✓ metas
✓ perfil
✓ dados e privacidade
✓ responsividade
✓ validação funcional

        ↓

FECHAMENTO V1
→ documentação
→ suíte final
→ Git limpo
→ versão/tag

        ↓

HARDENING
→ autenticação
→ isolamento
→ SQLite
→ arquivos
→ dependências
→ secrets
→ logs
→ exclusão de dados

        ↓

V2 — FUNDAÇÃO
→ React
→ API Python
→ contratos
→ autenticação
→ autorização
→ testes
→ CI

        ↓

V2 — MIGRAÇÃO
→ transações
→ importação
→ perfil
→ metas
→ orçamento
→ privacidade

        ↓

INFRAESTRUTURA
→ PostgreSQL quando necessário
→ migrations
→ staging
→ deploy
→ monitoramento
→ backup
```

Esse roadmap representa uma direção, não uma obrigação de implementar todas as
etapas ou tecnologias.

Cada fase deve ser reavaliada com base no estado real do projeto no momento em
que for iniciada.