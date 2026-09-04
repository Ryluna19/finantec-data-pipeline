# Roadmap — FinanTec

## Objetivo

Este documento registra o estado atual do FinanTec e orienta suas próximas
etapas. Ele não representa uma promessa de implementar todas as possibilidades
listadas.

As decisões devem considerar:

- benefício visível para quem utiliza ou avalia o projeto;
- risco de regressão ou perda de dados;
- aprendizado e valor profissional;
- tempo de implementação e manutenção;
- feedback obtido com a aplicação publicada.

## Estado da V1

A V1 está funcional, publicada e disponível para testes externos.

### Produto

- [x] autenticação e isolamento por usuário;
- [x] contas permanentes protegidas por código de acesso;
- [x] contas temporárias públicas com duração de 24 horas;
- [x] aviso de expiração e remoção dos dados temporários;
- [x] CRUD de transações;
- [x] indicadores e filtros por período;
- [x] importação de CSV, Excel e OFX;
- [x] importação assistida de planilhas externas;
- [x] validação e tratamento de possíveis duplicatas;
- [x] exportação para Excel;
- [x] orçamento mensal por categoria;
- [x] metas e simulador;
- [x] perfil financeiro;
- [x] exclusão de dados e exclusão de conta;
- [x] temas claro e escuro;
- [x] revisão de responsividade.

### Persistência e publicação

- [x] SQLite para execução local;
- [x] abstração comum de conexão com o banco;
- [x] Turso/libSQL para a aplicação publicada;
- [x] isolamento dos testes em relação ao banco remoto;
- [x] configuração de secrets fora do repositório;
- [x] deploy público no Streamlit.

### Segurança aplicada

- [x] armazenamento somente do hash das senhas;
- [x] comparação segura de credenciais;
- [x] bloqueio temporário após falhas consecutivas de login;
- [x] consultas parametrizadas;
- [x] operações associadas ao `user_id` autenticado;
- [x] separação entre contas temporárias e permanentes;
- [x] limpeza coordenada dos dados de contas expiradas;
- [x] remoção da antiga integração externa com Gemini.

### Qualidade

- [x] 455 testes automatizados;
- [x] testes dos principais repositórios e regras de negócio;
- [x] cobertura dos fluxos de importação;
- [x] validação manual dos fluxos principais;
- [x] revisão em desktop, notebook e dispositivos móveis;
- [x] README alinhado à aplicação publicada;
- [x] imagens da aplicação no README.

## Fase atual — fechamento e apresentação

O objetivo atual não é adicionar funcionalidades à V1. A prioridade é encerrar
o ciclo de forma organizada e torná-lo fácil de entender no portfólio.

### Importante

- [ ] alinhar os documentos técnicos restantes ao estado publicado;
- [ ] executar uma verificação final do repositório;
- [ ] confirmar que não existem secrets ou artefatos acidentais versionados;
- [ ] criar uma tag ou release de referência para a V1;
- [ ] coletar feedback de algumas pessoas usando a demonstração pública.

### Opcional

- [ ] registrar problemas reais encontrados durante os testes externos;
- [ ] melhorar textos ou pequenos detalhes visuais apontados por usuários;
- [ ] criar uma breve demonstração em vídeo ou GIF para o portfólio;
- [ ] adicionar CI ao repositório da V1 se o custo permanecer baixo.

### Perfeccionismo neste momento

- expandir a V1 com novas áreas financeiras;
- trocar o Streamlit sem iniciar formalmente a V2;
- reescrever módulos estáveis apenas para reduzir linhas de código;
- adicionar infraestrutura sem um problema operacional concreto;
- buscar cobertura automatizada total.

## Manutenção da V1

Depois do fechamento, mudanças na V1 devem ser pequenas e justificadas.

Corrigir quando houver:

- falha de autenticação ou isolamento;
- perda, mistura ou exclusão incorreta de dados;
- regressão em um fluxo principal;
- erro que impeça o uso da demonstração;
- exposição de credencial ou informação sensível;
- incompatibilidade causada por dependência ou plataforma de deploy.

Evitar adicionar funcionalidades somente para manter o projeto em atividade. A
V1 deve funcionar como uma referência estável e demonstrável.

## Feedback externo

Os testes externos devem responder perguntas concretas:

1. A proposta do produto fica clara na primeira tela?
2. A criação da conta temporária é compreensível?
3. Cadastro, edição e exclusão de transações são fáceis de encontrar?
4. A importação explica adequadamente erros e possíveis duplicatas?
5. Orçamento e metas são compreensíveis sem explicação prévia?
6. A interface apresenta problemas em telas ou navegadores específicos?
7. Quais limitações do Streamlit realmente prejudicam a experiência?

Feedback isolado não precisa gerar uma alteração automática. Priorizar padrões
que apareçam em mais de um teste ou problemas graves confirmados.

## Possível V2

A V2 só deve começar quando houver tempo reservado e um objetivo claro de
arquitetura ou experiência. Ela não deve ser uma sequência indefinida de
alterações dentro da V1.

### Objetivos prováveis

- obter maior controle da interface e da experiência de usuário;
- separar frontend, API e persistência;
- preservar as regras de negócio já validadas;
- tornar autenticação e autorização explícitas no backend;
- criar uma base melhor para testes end-to-end;
- praticar uma stack web relevante para oportunidades profissionais.

### Direção técnica em avaliação

Uma direção coerente com esses objetivos é:

```text
React + TypeScript
        ↓ HTTP
API Node.js + TypeScript
        ↓
PostgreSQL
```

Essa combinação é uma candidata, não uma decisão irreversível. Antes da
implementação, ainda será necessário definir:

- quais regras podem ser reaproveitadas ou precisam ser reimplementadas;
- contrato inicial da API;
- modelo de autenticação e sessão;
- estratégia de migração dos dados;
- hospedagem viável para frontend, API e banco;
- escopo mínimo da primeira entrega.

Não existe necessidade de adicionar outro framework além do necessário para
resolver essas responsabilidades.

## Funcionalidades que a V2 deve preservar

Uma nova interface não pode perder os comportamentos centrais já validados:

- contas e isolamento dos dados;
- transações e filtros por período;
- importação com prévia e validação;
- possíveis duplicatas;
- exportação;
- indicadores financeiros;
- orçamento mensal;
- metas e simulação;
- perfil;
- exclusão dos próprios dados;
- uso de dados fictícios para demonstração.

A migração deve ser incremental. Tentar reproduzir toda a V1 em uma única etapa
aumentaria o risco de regressão e dificultaria validar a nova arquitetura.

## Sequência sugerida para a V2

### 1. Definição

- consolidar os comportamentos que precisam ser preservados;
- escolher o menor escopo vertical utilizável;
- documentar o contrato inicial da API;
- definir autenticação, autorização e modelo de dados.

### 2. Fundação

- criar frontend e API;
- configurar PostgreSQL e migrations;
- configurar testes e integração contínua;
- implementar tratamento centralizado de configuração e erros.

### 3. Primeiro fluxo vertical

Implementar um caminho completo antes de expandir:

```text
autenticação
    ↓
listar transações
    ↓
cadastrar transação
    ↓
persistir no PostgreSQL
    ↓
exibir resultado no frontend
```

### 4. Migração por domínio

Adicionar os demais domínios em etapas protegidas por testes:

1. edição, exclusão e filtros;
2. indicadores;
3. importação e exportação;
4. orçamento;
5. metas;
6. perfil e gerenciamento dos dados.

### 5. Publicação

- ambiente de demonstração;
- secrets separados por ambiente;
- logs e monitoramento básico;
- backup e recuperação compatíveis com o serviço escolhido;
- validação dos fluxos críticos no navegador.

## Fora de prioridade

Continuam fora do escopo enquanto não existir uma necessidade concreta:

- microserviços;
- Kubernetes;
- filas distribuídas;
- aplicativo móvel nativo;
- múltiplas organizações;
- arquitetura empresarial multi-tenant;
- RAG, embeddings ou agentes autônomos;
- integração bancária direta;
- Open Finance;
- recomendação personalizada de investimentos;
- execução automática de operações financeiras.

## Critério de decisão

Antes de iniciar uma mudança relevante, responder:

1. Qual problema real será resolvido?
2. O benefício será visível para usuários ou recrutadores?
3. O custo é proporcional ao resultado?
4. A mudança preserva os dados e os comportamentos existentes?
5. Existem testes capazes de proteger o fluxo?
6. A V1 ou a V2 é o lugar correto para essa alteração?
7. A tecnologia escolhida resolve uma responsabilidade necessária?

## Resumo

```text
V1 publicada
      ↓
documentação e referência de versão
      ↓
feedback externo
      ↓
manutenção somente quando necessária
      ↓
decisão consciente sobre a V2
```
