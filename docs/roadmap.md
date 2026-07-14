# Roadmap — FinanTec

## Visão Geral

Este roadmap organiza as próximas evoluções do FinanTec de acordo com o estado atual do projeto.

O objetivo é continuar evoluindo a aplicação de forma incremental, com foco em valor real para portfólio e possível uso como pequeno SaaS, sem adicionar complexidade empresarial antes da hora.

O projeto já deixou de ser apenas um pipeline ETL. Hoje, o FinanTec funciona como uma aplicação de controle financeiro pessoal com persistência em SQLite, entrada manual, importação de planilhas, metas, perfil, histórico de chat e assistente com IA.

A próxima fase deve consolidar essa base antes de avançar para autenticação, PostgreSQL e deploy.

---

## Estado Atual

O FinanTec já possui:

- pipeline ETL com Python e pandas;
- dados de demonstração;
- dashboard em Streamlit;
- filtros por período;
- indicadores financeiros;
- gráficos por categoria;
- diagnóstico financeiro;
- cadastro manual de transações;
- edição e exclusão de transações;
- importação de arquivos CSV e Excel;
- exportação para Excel;
- validação de dados;
- detecção de possíveis duplicatas;
- persistência direta no SQLite;
- isolamento por `user_id`;
- separação entre dados reais e dados de demonstração;
- perfil financeiro persistente;
- metas financeiras persistentes;
- histórico de chat persistente;
- assistente com regras determinísticas e IA generativa;
- reset seguro dos dados do usuário;
- testes automatizados com pytest.

Fluxo principal atual:

```text
Pessoa registra ou importa transações
        ↓
Sistema valida e padroniza os dados
        ↓
Possíveis duplicatas são analisadas
        ↓
SQLite armazena as transações
        ↓
Dashboard calcula e apresenta os indicadores
        ↓
Assistente ajuda a interpretar os resultados
```

---

## Prioridade Atual

### 1. Finalizar a centralização das transações no SQLite

Grande parte do fluxo já foi migrada, mas ainda existem pontos de compatibilidade com arquivos antigos e com o pipeline ETL.

Objetivos:

- confirmar que todas as entradas do usuário gravam diretamente no SQLite;
- manter o ETL apenas onde ele ainda possui responsabilidade real;
- remover caminhos antigos de persistência que não são mais utilizados;
- revisar textos da interface que ainda descrevem fluxos antigos;
- evitar que dados do usuário dependam de arquivos processados para aparecer no dashboard.

Critério de conclusão:

```text
Entrada manual, importação, edição, exclusão e leitura do usuário
funcionam com o SQLite como fonte principal.
```

---

### 2. Revisão direcionada dos módulos transacionais

Depois que a migração para SQLite estiver concluída, será feita uma revisão apenas da área transacional.

Arquivos principais:

- `src/transaction_repository.py`;
- `src/transaction_editor.py`;
- `src/transaction_sync_service.py`;
- `src/transaction_files.py`;
- `src/import_transaction_database_service.py`;
- `src/components/file_transfer.py`;
- `src/components/data_management.py`.

A revisão deve procurar:

- funções redundantes;
- regras repetidas em módulos diferentes;
- wrappers sem responsabilidade real;
- normalizações duplicadas;
- nomes que não representam mais o comportamento;
- código mantido apenas por compatibilidade;
- funções grandes com decisões demais;
- testes que verificam detalhes internos em vez de comportamento.

O objetivo não é reduzir linhas por estética.

O objetivo é:

```text
menos caminhos para a mesma regra
menos código morto
menos testes frágeis
fluxos mais fáceis de entender
```

---

### 3. Consolidar a documentação

A documentação precisa acompanhar o estado real do projeto.

Tarefas:

- manter `docs/project_overview.md` atualizado;
- manter este roadmap apenas com trabalho futuro;
- revisar o README principal;
- documentar claramente como executar a aplicação;
- explicar os modos de dados;
- explicar o papel atual do ETL;
- registrar decisões importantes de arquitetura;
- remover referências a funcionalidades que já foram concluídas.

A documentação deve servir para:

- recrutadores;
- outros desenvolvedores;
- revisões por IA;
- retomada do projeto depois de algum tempo;
- apresentação do projeto em entrevistas.

---

## Próxima Fase Estrutural

### 4. Autenticação

A estrutura interna já utiliza `user_id`, mas ainda não existe autenticação real.

A primeira versão deve ser simples.

Possíveis funcionalidades:

- cadastro;
- login;
- logout;
- senha armazenada com hash;
- sessão autenticada;
- usuário atual definido pela autenticação;
- proteção contra acesso a dados de outro usuário.

Não é necessário implementar inicialmente:

- login social;
- autenticação multifator;
- controle avançado de permissões;
- equipes;
- organizações;
- múltiplos papéis administrativos.

Critério de conclusão:

```text
Dois usuários conseguem usar a aplicação
sem visualizar ou alterar os dados um do outro.
```

---

### 5. Preparação para PostgreSQL

O SQLite é adequado para o estágio atual, mas PostgreSQL será necessário para deploy e uso por múltiplos usuários reais.

Antes da migração:

- reduzir dependências específicas do SQLite;
- centralizar conexões;
- evitar SQL espalhado pela aplicação;
- revisar tipos de dados;
- revisar criação de tabelas;
- preparar configurações por ambiente;
- manter os testes usando bancos temporários.

Durante a migração:

- criar esquema compatível com PostgreSQL;
- migrar repositórios gradualmente;
- manter a interface de acesso aos dados estável;
- testar isolamento por usuário;
- testar integridade das transações;
- documentar o processo de migração.

Não é necessário usar ORM apenas por obrigação.

A escolha entre SQL direto e ORM deve considerar:

- simplicidade;
- manutenção;
- compatibilidade;
- valor de aprendizado;
- impacto no projeto.

---

### 6. Deploy

Depois de autenticação e PostgreSQL, o projeto poderá ser publicado.

Objetivos:

- configurar variáveis de ambiente;
- separar ambiente local e produção;
- proteger chaves da IA;
- configurar banco externo;
- revisar logs;
- revisar mensagens de erro;
- validar comportamento em ambiente remoto;
- testar uso em telas menores.

O primeiro deploy deve priorizar funcionamento e segurança básica, não escala empresarial.

---

## Melhorias de Produto

### 7. Múltiplas contas financeiras

Atualmente, uma conta de usuário representa um único perfil financeiro.

Uma evolução futura poderá permitir separar:

- conta corrente;
- carteira;
- poupança;
- cartão de crédito;
- outras contas.

Essa funcionalidade só deve ser implementada quando houver:

- cadastro de contas;
- filtros por conta;
- indicadores por conta;
- uso claro da informação no dashboard.

Não basta adicionar uma coluna `conta` sem funcionalidade associada.

---

### 8. Relatórios e exportações

Possíveis melhorias:

- relatório mensal em Excel;
- resumo por categoria;
- exportação por período;
- relatório de metas;
- comparação entre meses;
- resumo financeiro para download.

A prioridade deve ser gerar relatórios que respondam perguntas reais, não apenas criar arquivos adicionais.

---

### 9. Evolução do assistente

O assistente já combina regras determinísticas e IA generativa.

Melhorias futuras:

- reconhecer intenções sem depender de frases exatas;
- compreender perguntas informais;
- manter melhor contexto entre mensagens;
- melhorar fallback;
- ampliar testes de frases equivalentes;
- separar perguntas financeiras de perguntas fora do escopo;
- melhorar explicações sem permitir cálculos inventados.

O assistente não deve substituir os cálculos da aplicação.

---

### 10. Refinamento visual

A interface ainda possui áreas que precisam de revisão visual.

Essa etapa deve acontecer depois da estabilização funcional.

Pontos conhecidos:

- reorganizar o acesso ao perfil;
- revisar o nome e espaço da aba do assistente;
- melhorar a tela de metas;
- revisar responsividade;
- limitar largura em monitores grandes;
- melhorar navegação em notebooks;
- revisar consistência entre componentes.

Evitar novos ciclos de microajustes visuais antes de concluir as etapas estruturais.

---

### 11. Experiência mobile

O projeto poderá ser acessado por celular depois do deploy.

Primeiras melhorias possíveis:

- layout responsivo;
- navegação simplificada;
- tabelas adaptadas;
- formulários mais confortáveis;
- botões adequados para toque.

Um aplicativo nativo não é prioridade inicial.

A primeira meta é tornar a versão web utilizável em telas menores.

---

## Qualidade e Testes

Os testes devem continuar focados nos comportamentos de maior risco.

Prioridades:

- isolamento entre usuários;
- persistência;
- criação, edição e exclusão;
- reset seguro;
- validação de arquivos;
- detecção de duplicatas;
- cálculos financeiros;
- metas;
- autenticação;
- migrações de banco.

Evitar criar testes apenas porque uma função existe.

Testes de baixo valor incluem:

- wrappers triviais;
- mensagens exatas da interface;
- detalhes internos sem impacto no comportamento;
- fluxos obsoletos;
- repetição da mesma regra em vários arquivos.

A organização dos testes poderá ser revisada no futuro, mas não deve virar uma grande refatoração enquanto a arquitetura ainda está mudando.

---

## O que Não é Prioridade Agora

Não são prioridade imediata:

- integração com bancos reais;
- Open Finance;
- recomendação de investimentos;
- microsserviços;
- Kubernetes;
- filas distribuídas;
- arquitetura empresarial;
- múltiplas organizações;
- papéis avançados;
- app mobile nativo;
- LangChain por obrigação;
- RAG com embeddings sem necessidade;
- conciliação bancária oficial;
- processamento em grande escala.

Essas tecnologias podem ser válidas em outros projetos, mas não melhoram automaticamente o FinanTec.

---

## Ordem Recomendada

```text
1. Finalizar SQLite como fonte principal
        ↓
2. Revisar módulos transacionais
        ↓
3. Atualizar documentação
        ↓
4. Implementar autenticação
        ↓
5. Preparar e migrar para PostgreSQL
        ↓
6. Fazer deploy
        ↓
7. Evoluir funcionalidades de produto
        ↓
8. Refinar interface e experiência mobile
```

---

## Critério Geral de Prioridade

Antes de adicionar uma funcionalidade, avaliar:

1. Qual problema real ela resolve?
2. O usuário consegue responder uma nova pergunta com ela?
3. Ela melhora o valor do projeto para portfólio?
4. O custo de implementação é proporcional ao benefício?
5. Ela depende de alguma etapa estrutural ainda incompleta?
6. Existe risco de refazer esse trabalho depois?

A direção do FinanTec deve continuar sendo:

```text
produto pequeno
arquitetura coerente
dados confiáveis
escopo controlado
evolução incremental
```