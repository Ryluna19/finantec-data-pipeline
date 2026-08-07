# Project Overview — FinanTec

## Visão Geral

O FinanTec é uma aplicação local de organização financeira desenvolvida com
Python, Streamlit, pandas e SQLite.

O projeto começou como um pipeline ETL para processar transações simuladas em
CSV. Com sua evolução, o SQLite tornou-se a principal fonte dos dados da
aplicação e a interface passou a concentrar os principais fluxos financeiros,
incluindo:

- contas locais;
- transações;
- importação e exportação;
- orçamento;
- metas;
- perfil;
- gerenciamento de dados e privacidade.

O ETL foi preservado para demonstração, compatibilidade e processamento
explícito de arquivos.

O objetivo do produto é fazer o básico de um controlador financeiro pessoal
parecer completo e confiável, valorizando:

- regras de negócio claras;
- persistência e isolamento de dados;
- importação e validação;
- testes automatizados;
- privacidade;
- interface funcional e responsiva;
- evolução incremental;
- decisões técnicas documentadas.

O FinanTec não pretende ser banco digital, sistema empresarial ou plataforma de
investimentos.

---

## Problema e Solução

Quem começa a organizar a própria renda frequentemente utiliza planilhas ou
anotações dispersas. Isso dificulta consolidar receitas, despesas, reservas,
saldo, metas e limites mensais, além de aumentar o risco de formatos inválidos
e registros duplicados.

O FinanTec centraliza esses fluxos em uma aplicação local:

- permite criar e autenticar contas locais;
- registra e consulta transações;
- importa arquivos CSV, Excel e OFX;
- auxilia o mapeamento de planilhas Excel com estruturas externas;
- valida os dados e sinaliza linhas rejeitadas;
- identifica possíveis duplicatas e utiliza a opção segura de ignorá-las por
  padrão;
- calcula indicadores por período;
- acompanha metas persistentes;
- planeja limites mensais por categoria;
- compara valores planejados com os gastos registrados;
- mantém um perfil financeiro;
- separa dados pessoais e demonstração;
- permite apagar os dados financeiros preservando a conta;
- permite excluir definitivamente a conta e os dados associados.

---

## Público e Escopo

O uso atual é pessoal e local.

O projeto também serve como portfólio técnico para demonstrar:

- Python;
- pandas;
- Streamlit;
- SQLite;
- modelagem e persistência de dados;
- autenticação local;
- isolamento por usuário;
- ETL;
- importação de arquivos;
- testes automatizados;
- evolução incremental de arquitetura.

Não fazem parte do escopo atual:

- integração bancária;
- Open Finance;
- recomendação personalizada de investimentos;
- execução de operações financeiras;
- infraestrutura pública de produção;
- autenticação preparada para exposição pública;
- processamento financeiro em grande escala;
- microsserviços.

A existência de contas locais na v1 não significa que o sistema de autenticação
atual esteja preparado para uma aplicação web pública. Essa responsabilidade
será reavaliada na evolução arquitetural do projeto.

---

## Fluxos de Dados

### Dados pessoais

O fluxo principal da v1 é:

```text
Conta autenticada
        ↓
Entrada manual ou importação
        ↓
Validação e padronização
        ↓
Análise de possíveis duplicatas
        ↓
Gravação no SQLite
        ↓
Consulta e indicadores
        ↓
Orçamento, metas e perfil
```

As transações podem ser cadastradas manualmente ou importadas a partir de
arquivos suportados pela aplicação.

O SQLite é a fonte principal para os dados pessoais persistidos.

Um contexto pessoal novo pode começar sem:

- transações;
- perfil;
- metas;
- orçamento.

Esses estados vazios são válidos e não recebem automaticamente informações
fictícias da demonstração.

Os principais registros pessoais são associados a um `user_id`, permitindo que
as contas locais mantenham seus dados separados.

### Demonstração

A demonstração utiliza dados simulados e permanece separada do contexto pessoal.

As transações de demonstração seguem o fluxo:

```text
Arquivos CSV de demonstração
        ↓
ETL com pandas
        ↓
Registros válidos e rejeitados
        ↓
Carga da partição de demonstração no SQLite
        ↓
Interface em modo de demonstração
```

Perfil e Metas fictícios seguem um fluxo separado e são utilizados somente para
apresentação:

```text
Fonte fictícia versionada
        ↓
Composição em memória
        ↓
Perfil e Metas de demonstração
```

A alternância para demonstração não deve sobrescrever os dados pessoais da
conta.

Ao retornar para “Meus dados”, o contexto pessoal previamente armazenado volta
a ser utilizado.

### ETL e compatibilidade

O ETL não é mais um pré-requisito para o uso normal da aplicação.

Ele permanece disponível para:

- processar explicitamente arquivos CSV;
- preparar a base de demonstração;
- gerar registros válidos e rejeitados;
- manter compatibilidade com partes históricas do projeto.

---

## Funcionalidades Atuais

### Contas

A v1 possui um sistema de contas locais.

Entre os fluxos existentes estão:

- criação de conta;
- autenticação por usuário e senha;
- contexto de usuário durante a sessão;
- isolamento dos principais registros por `user_id`;
- encerramento da sessão;
- exclusão definitiva da conta.

A autenticação atual deve ser interpretada dentro do contexto de uma aplicação
local. Uma publicação futura exigirá nova avaliação de segurança, autorização,
sessões e infraestrutura.

### Visão geral

A tela principal apresenta:

- receitas;
- despesas;
- reserva;
- saldo disponível;
- gastos por categoria;
- diagnóstico financeiro simples;
- filtros por período;
- transações recentes;
- resumo do orçamento quando aplicável.

### Transações

A área de Transações concentra:

- consulta dos registros;
- filtros;
- cadastro manual sob demanda;
- edição de registros persistidos;
- exclusão com confirmação;
- importação;
- exportação;
- validação dos dados.

A exportação considera o período selecionado.

### Importação

A aplicação suporta diferentes caminhos de importação:

- CSV no formato esperado pelo FinanTec;
- Excel no formato esperado pelo FinanTec;
- OFX;
- planilhas Excel externas por meio de mapeamento assistido.

Na importação assistida, é possível:

- selecionar a aba;
- identificar ou selecionar o cabeçalho;
- mapear data;
- mapear descrição;
- mapear categoria opcional;
- utilizar uma coluna de valor;
- utilizar tipo explícito;
- utilizar colunas separadas de débito e crédito;
- visualizar uma prévia antes da gravação;
- identificar linhas inválidas;
- identificar possíveis duplicatas.

Quando possíveis duplicatas são encontradas, o comportamento padrão é não
importá-las. O usuário pode optar explicitamente por incluí-las.

### Metas

A área de Metas é dividida entre acompanhamento e simulação.

Em “Minhas metas”:

- ausência de metas é um estado válido;
- novas metas podem ser criadas;
- metas existentes podem ser editadas;
- exclusão exige confirmação;
- são exibidos valor atual, valor restante, progresso e contribuição mensal;
- registros pessoais permanecem associados ao usuário.

No simulador:

- o usuário pode selecionar uma meta;
- pode simular diferentes prazos ou valores mensais;
- a simulação não altera automaticamente a meta persistida.

As metas de demonstração são apresentadas somente no contexto fictício.

### Orçamento

O orçamento permite planejamento de gastos por categoria.

Entre as funcionalidades estão:

- criação de limites;
- edição;
- exclusão;
- recorrência entre períodos;
- encerramento de um limite;
- alteração de um limite a partir de determinado período;
- comparação entre planejado e gasto real;
- cálculo do valor restante ou excedido;
- identificação visual de categorias próximas ou acima do limite;
- resumo mensal na Visão geral.

A ausência de orçamento é um estado válido.

Os limites pessoais são isolados por usuário.

O orçamento não é editável durante o modo de demonstração.

### Perfil

O perfil financeiro pode ser criado e atualizado pelo usuário.

Entre as informações utilizadas estão:

- nome de exibição;
- ocupação;
- idade;
- fontes de renda;
- renda mensal;
- informações relacionadas a dívidas e cartão de crédito.

A ausência de perfil é válida no primeiro uso.

O perfil é uma entidade separada das Metas.

Registros antigos podem continuar sendo interpretados internamente quando isso
for necessário para compatibilidade.

No modo de demonstração, o perfil fictício é apresentado somente para leitura.

### Dados e privacidade

A área de Dados e privacidade permite controlar o contexto utilizado pela
aplicação.

Entre os fluxos existentes estão:

- visualização do modo atual;
- alternância entre dados pessoais e demonstração;
- retorno aos dados pessoais;
- resumo dos dados armazenados;
- exclusão dos dados financeiros;
- exclusão definitiva da conta.

A ação “Apagar meus dados” remove os dados financeiros associados ao usuário,
incluindo registros como:

- transações pessoais;
- perfil;
- metas;
- estado relacionado às metas;
- orçamento;
- outros dados pessoais legados ainda associados ao usuário.

A conta e suas credenciais são preservadas.

A demonstração também permanece disponível.

A ação “Excluir conta” possui responsabilidade diferente:

```text
Apagar meus dados
→ preserva a conta

Excluir conta
→ remove a conta e os dados associados
```

A exclusão definitiva exige nova confirmação da identidade antes da operação.

---

## Funcionalidade de IA Descontinuada

O FinanTec já utilizou a API do Gemini como parte de um antigo assistente
financeiro.

Essa integração poderia enviar para um serviço externo informações como:

- perguntas;
- contexto financeiro;
- indicadores;
- perfil;
- histórico da conversa.

Não existe evidência de que tenha ocorrido uma violação de dados.

A integração foi removida preventivamente por motivos de:

- minimização de dados;
- privacidade por concepção;
- redução de dependências externas;
- baixo benefício em relação ao risco para um aplicativo financeiro local.

A decisão está registrada em:

[ADR 001 — Remoção da integração externa com Gemini](decisions/001-remove-gemini-integration.md)

O assistente financeiro, o histórico de conversas e o antigo recurso de
Insights não fazem parte das funcionalidades atuais da v1.

Código, testes ou documentação relacionados podem permanecer no repositório
como registro técnico ou compatibilidade histórica enquanto sua remoção não
trouxer benefício suficiente para justificar uma nova refatoração.

---

## Arquitetura Atual

### Interface

A interface da v1 utiliza:

- Streamlit;
- componentes separados por responsabilidade;
- CSS personalizado;
- temas claro e escuro;
- responsividade;
- estado de sessão para interações temporárias.

A interface foi validada em:

- desktop;
- notebook;
- dispositivos móveis.

### Regras e serviços

As regras de negócio são implementadas principalmente em Python.

A arquitetura busca manter cálculos e persistência fora dos componentes
puramente visuais sempre que possível.

Existem serviços específicos para responsabilidades como:

- cadastro manual;
- importação;
- sincronização;
- validação;
- identidade de transações;
- gerenciamento de arquivos.

A validação de transações é compartilhada entre diferentes caminhos de entrada
para reduzir inconsistências.

### Contexto de usuário

O sistema possui um contexto explícito de usuário utilizado pelos principais
fluxos da aplicação.

Esse contexto permite que operações de leitura e escrita sejam vinculadas ao
usuário autenticado.

A v1 utiliza contas locais, mas ainda não possui a arquitetura de autenticação e
autorização necessária para exposição pública.

### Persistência

O SQLite é a fonte principal da aplicação.

Existem repositórios específicos para entidades como:

- contas;
- transações;
- perfil;
- metas;
- orçamento.

Os principais registros pessoais utilizam `user_id`.

Transações também distinguem o modo de dados quando necessário, permitindo
separar:

```text
user
demo
```

Perfil e Metas fictícios são mantidos fora das tabelas pessoais quando
apropriado.

### Qualidade

A aplicação utiliza `pytest` para validar regras e fluxos importantes.

A cobertura automatizada inclui, entre outras áreas:

- contas;
- autenticação;
- transações;
- ETL;
- importação;
- duplicatas;
- perfil;
- metas;
- orçamento;
- isolamento por usuário;
- exclusão de dados;
- exclusão de conta;
- cálculos financeiros;
- funções auxiliares da interface.

Testes de persistência utilizam bancos temporários quando apropriado.

---

## Componentes Principais

| Componente | Responsabilidade |
|---|---|
| `src/app.py` | Coordena navegação, contexto e composição das telas principais. |
| `src/account_repository.py` | Gerencia criação, consulta e autenticação das contas locais. |
| `src/user_context.py` | Centraliza o contexto do usuário autenticado. |
| `src/analytics.py` | Centraliza cálculos e indicadores financeiros. |
| `src/components/` | Reúne os componentes visuais por fluxo. |
| `src/transaction_repository.py` | Persiste e consulta transações. |
| `src/goal_repository.py` | Persiste e consulta metas. |
| `src/profile_repository.py` | Persiste as informações do perfil financeiro. |
| `src/components/budget.py` | Compõe o planejamento mensal e suas ações. |
| `src/budget_repository.py` | Persiste e consulta limites por usuário e período. |
| `src/components/data_management.py` | Controla demonstração, reset financeiro e exclusão de conta. |
| `src/data_reset.py` | Centraliza operações coordenadas de remoção de dados. |
| `scripts/etl_transacoes.py` | Implementa o ETL utilizado para demonstração e processamento explícito. |
| `tests/` | Contém a suíte automatizada das regras e fluxos principais. |

Módulos relacionados ao antigo assistente podem continuar presentes
temporariamente como legado técnico, mas não representam funcionalidades atuais
da aplicação.

---

## Decisões Técnicas

### SQLite como fonte principal

O SQLite é simples, gratuito e adequado ao contexto local da v1.

As operações normais da aplicação gravam diretamente no banco, sem exigir uma
execução automática do ETL.

A escolha também reduz infraestrutura durante a fase em que o foco é validar o
produto e suas regras.

### ETL com responsabilidade limitada

O ETL continua válido, mas deixou de ser o centro de toda interação com os
dados.

Sua responsabilidade atual é principalmente:

- demonstração;
- compatibilidade;
- processamento explícito;
- validação de arquivos do pipeline.

### Autenticação local na v1

A v1 passou a possuir contas locais e deixou de depender de um usuário fixo como
experiência principal.

O sistema atual fornece contexto e isolamento suficientes para o cenário local
do projeto.

Isso não significa que a autenticação esteja pronta para exposição pública.

Uma arquitetura web deverá reavaliar:

- gerenciamento de sessão;
- autenticação da API;
- autorização;
- proteção contra tentativas abusivas;
- ciclo de vida das credenciais;
- armazenamento e transporte de segredos;
- políticas de segurança.

### Privacidade e remoção do Gemini

A integração externa de IA foi removida porque o benefício não justificava o
envio potencial de contexto financeiro para um serviço de terceiros.

Essa decisão reduziu a superfície de exposição de dados e manteve a aplicação
coerente com sua proposta local.

### Dados pessoais e demonstração

Dados pessoais e demonstração são tratados como contextos distintos.

A demonstração existe para apresentar o produto sem exigir dados reais e não
deve sobrescrever os registros pessoais do usuário.

### Compatibilidade sem exposição desnecessária

Campos, arquivos ou módulos antigos podem permanecer internamente quando sua
remoção imediata trouxer risco de regressão sem benefício proporcional.

Compatibilidade interna não deve obrigar a manutenção de funcionalidades
obsoletas na interface.

---

## Limitações Atuais

A v1:

- é uma aplicação local;
- não possui deploy público;
- não integra com bancos;
- não utiliza Open Finance;
- não executa operações financeiras;
- não possui autenticação preparada para ambiente público de produção;
- não possui recuperação remota de senha;
- não possui infraestrutura de produção;
- não possui monitoramento operacional;
- não possui pipeline completo de CI/CD;
- não possui testes end-to-end abrangentes em navegador;
- utiliza SQLite, adequado ao contexto local, mas não escolhido como banco de
  produção multiusuário;
- mantém alguns elementos históricos quando sua remoção não justifica o risco de
  regressão.

Essas limitações são compatíveis com o objetivo da v1 e não precisam ser
resolvidas antes do seu fechamento.

---

## Direção Futura

A evolução do FinanTec deve continuar incremental.

A v1 será preservada como um marco funcional antes das mudanças arquiteturais
mais profundas.

O caminho planejado é:

```text
FinanTec v1 local
        ↓
Fechamento e versionamento
        ↓
Revisão de segurança e hardening
        ↓
Fundação da v2
        ↓
Frontend React + API Python
        ↓
Autenticação e autorização para arquitetura web
        ↓
Migração gradual das funcionalidades
        ↓
Infraestrutura e deploy quando justificados
```

### Hardening

Antes da evolução arquitetural, será feita uma revisão específica da v1.

Entre os pontos a verificar estão:

- autenticação;
- armazenamento de credenciais;
- isolamento entre usuários;
- consultas SQLite;
- importação de arquivos;
- manipulação de caminhos e arquivos locais;
- dependências;
- segredos;
- configurações;
- logs;
- exclusão de dados;
- exclusão de conta.

O objetivo não é transformar a v1 em um sistema público de produção.

Problemas relevantes encontrados serão corrigidos. Melhorias que dependam de uma
nova arquitetura poderão ser incorporadas diretamente à v2.

### Versão 2

A direção planejada para a v2 é separar frontend e backend:

```text
React
        ↓ HTTP
API Python
        ↓
Serviços e regras de negócio
        ↓
Persistência
```

A migração deve reaproveitar gradualmente as regras de negócio já validadas.

Não é objetivo descartar toda a v1 e iniciar uma reescrita completa de uma única
vez.

Entre as responsabilidades iniciais da v2 estarão:

- definir contratos da API;
- separar regras de negócio da camada Streamlit;
- implementar autenticação e autorização adequadas à nova arquitetura;
- introduzir testes de backend e frontend;
- automatizar verificações de qualidade;
- incluir verificações de segurança no processo de desenvolvimento;
- estruturar CI desde as etapas iniciais.

### PostgreSQL

PostgreSQL não é necessário para fechar a v1.

O SQLite continua sendo uma escolha adequada enquanto o produto permanecer
local.

Uma migração passa a fazer mais sentido quando surgirem necessidades como:

- múltiplos usuários simultâneos;
- concorrência;
- servidor central;
- deploy público;
- infraestrutura de produção.

Nesse momento, migrations também passam a fazer parte da arquitetura de banco.

### DevOps e deploy

DevOps não será tratado apenas como uma etapa final de publicação.

A intenção é introduzir práticas gradualmente durante a v2, começando por:

- testes automatizados;
- lint;
- análise estática;
- verificação de dependências;
- verificações de segurança;
- CI.

Posteriormente, quando houver uma aplicação preparada para publicação, podem
entrar:

- ambiente de staging;
- deploy;
- gerenciamento de configurações;
- logs;
- monitoramento;
- backups.

---

## Status Atual

A versão 1 local está funcionalmente concluída e passa pelo fechamento
documental e de estabilização.

Os principais fluxos atuais são:

```text
Conta
Visão geral
Transações
Orçamento
Metas
Perfil
Dados e privacidade
```

Foram validados manualmente fluxos importantes como:

- criação, edição e exclusão de transações;
- importação de dados;
- tratamento de possíveis duplicatas;
- orçamento;
- metas;
- perfil;
- alternância entre dados pessoais e demonstração;
- exclusão dos dados financeiros;
- preservação da conta após o reset;
- exclusão definitiva da conta;
- bloqueio de autenticação após exclusão da conta.

A experiência também passou por revisão em:

- desktop;
- notebook;
- mobile;
- tema escuro;
- tema claro.

O antigo assistente financeiro não faz parte da v1 atual.

Após o fechamento documental, testes finais e versionamento da v1, a próxima
etapa planejada é uma revisão de segurança e hardening antes do início da
transição arquitetural para a v2.