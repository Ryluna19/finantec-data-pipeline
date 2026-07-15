# Roadmap — FinanTec

## Visão Geral

O FinanTec deve continuar como um aplicativo financeiro local, simples e
coerente. O objetivo é registrar transações, acompanhar períodos, organizar
metas e demonstrar boas decisões de persistência, validação, privacidade e UX.

O projeto não precisa se transformar em banco digital, sistema empresarial ou
SaaS para cumprir seu papel. A prioridade é fazer o básico parecer um produto
completo, sem acumular funcionalidades ou infraestrutura sem uso claro.

---

## Estado Atual

Já estão implementados:

- SQLite como fonte principal dos dados;
- entrada manual e CRUD de transações;
- importação de CSV e Excel com validação e duplicatas;
- exportação por período;
- separação entre dados pessoais e demonstração;
- perfil com renda calculada pelas fontes cadastradas;
- gerenciamento seguro das transações pessoais;
- metas persistentes e simulador separado;
- navegação principal com Visão geral, Transações e Metas;
- testes automatizados dos principais repositórios e regras;
- ETL mantido para demonstração e compatibilidade.

A integração externa com Gemini foi removida preventivamente. O mecanismo
local de consultas e o histórico foram preservados, mas o recurso está
congelado fora da navegação principal. Consulte a
[decisão arquitetural](decisions/001-remove-gemini-integration.md).

---

## Etapas Concluídas

### Navegação e perfil

- Perfil e Dados e privacidade deixaram as abas principais;
- o perfil passou a abrir em modo de consulta;
- o formulário aparece somente ao solicitar edição;
- campos ligados à antiga IA saíram da interface;
- a renda mensal passou a ser a soma das fontes de renda.

### Dados e privacidade

- distinção clara entre dados pessoais e demonstração;
- resumo dos dados locais;
- ação limitada a apagar somente transações pessoais;
- preservação explícita de perfil, metas, conversas, demonstração e banco.

### Transações

- consulta apresentada antes das ações secundárias;
- cadastro, importação e exportação sob demanda;
- importação e downloads separados em componentes próprios;
- linguagem de interface menos dependente do termo ETL;
- validação exibida somente quando existem rejeições.

### Metas

- separação entre Minhas metas e Simulador;
- formulário fechado inicialmente;
- cartões com progresso, restante e contribuição mensal;
- prioridade removida da interface e preservada internamente;
- edição e exclusão sob demanda.

### Insights

- integração externa removida;
- respostas determinísticas e histórico local preservados;
- recurso retirado da navegação principal;
- evolução funcional congelada por não ser prioridade do produto.

### Documentação

- README, visão geral e roadmap alinhados ao produto local;
- integração com Gemini registrada como decisão arquitetural;
- documentos da fase com IA preservados como registros históricos;
- comandos de testes manuais alinhados aos arquivos existentes.

---

## Próximas Prioridades

### 1. Revisão global de UX e responsividade

Testar pelo menos em:

- celular;
- notebook;
- desktop comum;
- monitor widescreen.

Avaliar:

- largura máxima e espaços vazios;
- rolagem vertical;
- tabelas no celular;
- navegação principal;
- hierarquia entre consulta e ações;
- consistência de títulos, textos e estados vazios;
- tema preto e laranja sem excesso de efeitos.

Essa etapa deve ser global. Microajustes isolados só devem ser feitos quando
corrigirem um problema funcional ou uma inconsistência evidente.

### 2. Completar perfil e privacidade

#### Restaurar perfil padrão

A ação deve:

- mostrar quais campos serão restaurados;
- exigir confirmação;
- substituir somente os dados do perfil;
- preservar transações, metas e conversas.

#### Apagar todos os dados locais

Essa ação só deve existir quando houver um serviço coordenado capaz de apagar:

- transações;
- perfil;
- metas;
- histórico de conversas;
- arquivos relacionados;
- estados de sessão.

Também será necessário impedir a recriação silenciosa pelo seed. A ação não
deve ser chamada de “Excluir conta”, pois não existe autenticação real.

### 3. Limpeza de compatibilidade

Depois da estabilização:

- avaliar campos antigos do perfil;
- revisar wrappers e aliases temporários;
- remover referências internas que não tenham consumidores;
- manter migrações seguras para bancos locais existentes;
- evitar refatorações apenas para reduzir linhas.

### 4. Deploy e evolução estrutural

Somente depois de produto, UX e documentação estarem coerentes:

- avaliar deploy;
- decidir se autenticação realmente agrega valor;
- considerar PostgreSQL apenas se houver necessidade de concorrência ou
  multiusuário;
- preservar SQLite se o uso continuar pessoal e local.

---

## Não Priorizar Agora

- evolução do recurso congelado de Insights;
- nova integração com IA externa;
- Open Finance;
- integração bancária;
- recomendação personalizada de investimentos;
- microserviços;
- Kubernetes;
- filas distribuídas;
- múltiplas organizações;
- app mobile nativo;
- RAG, embeddings ou agentes autônomos;
- infraestrutura paga sem necessidade comprovada.

---

## Qualidade e Testes

Os testes devem continuar focados em comportamentos de risco:

- isolamento entre usuários e modos de dados;
- persistência e CRUD;
- importação, rejeições e duplicatas;
- exclusão limitada e preservação de dados;
- cálculos financeiros e metas;
- migrações de banco;
- composição dos fluxos principais.

Evitar testes de baixo valor para wrappers triviais, detalhes internos ou
mensagens sem impacto no comportamento.

---

## Critério de Prioridade

Antes de iniciar uma mudança, avaliar:

1. Qual problema real ela resolve?
2. O benefício é visível para quem usa ou avalia o projeto?
3. O custo e o risco são proporcionais?
4. A mudança preserva dados existentes?
5. Ela evita arquitetura ou dependências desnecessárias?
6. O código atual confirma que a necessidade ainda existe?

A direção do FinanTec deve permanecer:

```text
produto pequeno
arquitetura coerente
dados confiáveis
privacidade consciente
escopo controlado
evolução incremental
```
