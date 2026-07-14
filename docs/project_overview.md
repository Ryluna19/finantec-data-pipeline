# Project Overview — FinanTec

## Visão Geral

O FinanTec é uma aplicação de controle financeiro pessoal desenvolvida com Python, Streamlit, pandas e SQLite.

O projeto começou como um pipeline ETL para processar dados financeiros simulados em arquivos CSV. Com a evolução da aplicação, passou a permitir que o próprio usuário registre, edite, exclua, importe e exporte transações diretamente pela interface.

Atualmente, o SQLite é a principal fonte de dados das transações do usuário. O pipeline ETL continua disponível para os dados de demonstração, validações em lote e compatibilidade com o fluxo original do projeto.

Além do controle financeiro, a aplicação possui:

- dashboard com indicadores financeiros;
- acompanhamento de receitas, despesas, reserva e saldo;
- metas financeiras persistentes;
- perfil financeiro;
- histórico de conversa persistente;
- assistente com IA generativa;
- importação e exportação de planilhas;
- validação e tratamento de possíveis transações duplicadas.

A aplicação ainda funciona localmente, mas sua arquitetura está sendo preparada para evoluir futuramente para um pequeno SaaS com poucos usuários.

---

## Problema

Pessoas que começam a administrar a própria renda frequentemente registram suas finanças em planilhas ou anotações dispersas.

Esse processo apresenta alguns problemas:

- dificuldade para acompanhar receitas e despesas ao longo do tempo;
- ausência de uma visão consolidada do saldo;
- dados preenchidos com formatos inconsistentes;
- risco de importar ou registrar transações duplicadas;
- dificuldade para acompanhar metas financeiras;
- pouca contextualização sobre os indicadores apresentados.

Antes de gerar análises confiáveis, os dados precisam ser validados, padronizados e armazenados de maneira consistente.

---

## Solução

O FinanTec centraliza o registro e a análise de transações financeiras em uma única aplicação.

O usuário pode:

- registrar transações manualmente;
- editar ou excluir transações existentes;
- importar arquivos CSV ou Excel;
- exportar os dados financeiros;
- filtrar informações por período;
- acompanhar indicadores e categorias de gastos;
- criar e simular metas financeiras;
- consultar um assistente sobre os próprios indicadores.

As transações inseridas manualmente ou importadas pela interface são validadas e gravadas diretamente no SQLite.

O projeto também mantém um pipeline ETL separado para processar arquivos de demonstração e fluxos compatíveis com a estrutura original.

---

## Público-Alvo

O projeto possui dois públicos principais.

### Usuário da aplicação

Uma pessoa que deseja controlar suas finanças pessoais em uma ferramenta simples, privada e personalizável.

O uso atual é local e voltado principalmente para o próprio desenvolvedor, familiares ou pessoas próximas.

Em uma evolução futura, o projeto poderá funcionar como um pequeno SaaS para poucos usuários.

### Avaliação técnica e portfólio

Recrutadores, desenvolvedores e avaliadores técnicos que desejam observar a aplicação prática de:

- Python;
- pandas;
- Streamlit;
- SQLite;
- modelagem e persistência de dados;
- validação de arquivos;
- testes automatizados;
- integração com IA generativa;
- evolução incremental de arquitetura.

---

## Escopo Atual

O FinanTec não pretende competir com grandes plataformas bancárias ou aplicações empresariais de gestão financeira.

O foco é oferecer uma aplicação funcional, tecnicamente coerente e adequada para uso pessoal ou para um pequeno grupo de usuários.

Não fazem parte do escopo atual:

- integração direta com bancos;
- Open Finance;
- conciliação bancária oficial;
- recomendação personalizada de investimentos;
- infraestrutura empresarial;
- microsserviços;
- processamento financeiro em grande escala.

---

## Fluxos de Dados

### Transações do usuário

```text
Entrada manual ou arquivo CSV/Excel
        ↓
Validação e padronização
        ↓
Análise de possíveis duplicatas
        ↓
Gravação direta no SQLite
        ↓
Dashboard e indicadores
        ↓
Assistente explicando os resultados
```

### Dados de demonstração e ETL

```text
Arquivos CSV de demonstração
        ↓
Extração e validação
        ↓
Transformação com pandas
        ↓
Separação entre registros válidos e rejeitados
        ↓
Carga no SQLite
        ↓
Dashboard em modo de demonstração
```

---

## Principais Funcionalidades

### Controle de transações

- cadastro manual de transações;
- edição de registros existentes;
- exclusão de registros;
- persistência direta no SQLite;
- isolamento por usuário;
- separação entre dados reais e dados de demonstração;
- identificadores internos gerados pela aplicação.

### Importação de arquivos

- suporte a arquivos CSV e Excel;
- planilha-modelo para preenchimento;
- validação de colunas obrigatórias;
- separação entre linhas válidas e inválidas;
- pré-visualização antes da importação;
- detecção de possíveis duplicatas pelo conteúdo;
- escolha entre ignorar ou incluir linhas correspondentes;
- gravação direta no SQLite;
- limpeza do uploader após a conclusão.

### Exportação

- exportação das transações para Excel;
- remoção de campos técnicos do arquivo entregue ao usuário;
- formatação básica da planilha;
- compatibilidade com uma nova importação.

### Dashboard financeiro

- receitas totais;
- despesas do período;
- valor reservado;
- saldo disponível;
- distribuição de gastos por categoria;
- filtros por período;
- diagnóstico financeiro simples.

### Metas financeiras

- criação de metas personalizadas;
- edição e exclusão;
- persistência por usuário;
- simulação de prazo e contribuição;
- metas iniciais geradas a partir do perfil quando necessário.

### Perfil financeiro

- informações persistidas por usuário;
- preferências e dados financeiros básicos;
- uso dessas informações em partes do dashboard e do assistente.

### Assistente com IA

- respostas determinísticas para perguntas financeiras suportadas;
- uso de IA generativa como complemento;
- cálculos realizados pela aplicação, não pela IA;
- histórico persistente;
- separação por usuário, período e modo de dados;
- fallback seguro para perguntas não reconhecidas.

### Gerenciamento de dados

- resumo das fontes e registros existentes;
- reset seguro dos dados do usuário;
- preservação das informações de outros usuários;
- preservação dos dados de demonstração;
- execução manual do pipeline ETL quando necessário.

---

## Contrato das Transações

As informações principais de uma transação são:

```text
data
tipo
descricao
categoria
valor
```

Essas colunas permitem calcular os indicadores atuais e manter a planilha simples para o usuário.

Campos técnicos como identificadores, usuário, origem e modo de dados são controlados internamente pela aplicação e não precisam ser preenchidos na planilha.

---

## Detecção de Possíveis Duplicatas

Arquivos importados não precisam possuir um identificador técnico.

Antes da gravação, o FinanTec compara as informações financeiras da transação, como:

- data;
- tipo;
- descrição;
- categoria;
- valor.

Quando uma ou mais correspondências são encontradas, o usuário precisa escolher explicitamente entre:

- ignorar linhas que já existem;
- importar todas as linhas, incluindo possíveis duplicatas.

Essa abordagem reduz importações acidentais sem impedir que duas transações legítimas possuam os mesmos dados.

---

## Arquitetura Atual

### Interface

- Streamlit;
- componentes separados por responsabilidade;
- CSS personalizado;
- estado de sessão para interações temporárias.

### Aplicação e regras de negócio

- Python;
- pandas;
- serviços específicos para persistência e sincronização;
- funções de análise financeira separadas da interface.

### Persistência

- SQLite para o ambiente local;
- dados isolados por `user_id`;
- separação por modo de dados;
- repositórios para acesso às principais entidades.

### Inteligência artificial

- Google GenAI;
- contexto preparado pela aplicação;
- respostas baseadas nos indicadores calculados;
- regras determinísticas para perguntas suportadas.

### Qualidade

- pytest;
- bancos temporários durante os testes;
- testes de persistência;
- testes de isolamento entre usuários;
- testes de validação e regras financeiras;
- testes dos fluxos de importação;
- validações manuais da interface.

---

## Principais Componentes

| Componente | Responsabilidade |
|---|---|
| `src/app.py` | Coordena a interface principal e os diferentes módulos da aplicação. |
| `src/analytics.py` | Centraliza os cálculos e indicadores financeiros. |
| `src/transaction_repository.py` | Realiza operações de persistência das transações. |
| `src/transaction_editor.py` | Gerencia a entrada manual e a edição de transações. |
| `src/import_transaction_database_service.py` | Prepara e salva importações diretamente no SQLite. |
| `src/transaction_sync_service.py` | Sincroniza alterações durante a transição entre fontes antigas e o banco. |
| `src/transaction_files.py` | Leitura, exportação, validação e comparação de arquivos. |
| `src/components/file_transfer.py` | Interface de importação e exportação. |
| `src/components/data_management.py` | Resumo, reset e execução dos fluxos de gerenciamento de dados. |
| `src/agent.py` | Integração com a IA generativa. |
| `src/prompts.py` | Regras e contexto enviados ao assistente. |
| `scripts/etl_transacoes.py` | Pipeline ETL usado por dados de demonstração e fluxos compatíveis. |
| `tests/` | Testes automatizados das regras, persistência e fluxos principais. |
| `docs/` | Documentação técnica e decisões do projeto. |
| `main.py` | Entrada simplificada para execução do projeto. |

---

## Decisões Técnicas

### SQLite como fonte principal local

O SQLite foi escolhido por ser simples, gratuito e suficiente para o estágio atual.

As transações do usuário são gravadas diretamente no banco, sem necessidade de executar o ETL após cada alteração.

O PostgreSQL poderá substituir o SQLite quando autenticação, deploy e múltiplos usuários reais forem implementados.

### ETL mantido com responsabilidade limitada

O pipeline ETL continua sendo uma parte válida do projeto, mas deixou de ser o único caminho para inserir dados.

Atualmente, ele é utilizado principalmente para:

- dados de demonstração;
- processamento de arquivos antigos;
- validações em lote;
- preservação da proposta original de engenharia de dados.

### Cálculos fora da IA

Receitas, despesas, saldo, percentuais e demais indicadores são calculados em Python.

A IA recebe os resultados prontos e atua principalmente na interpretação e explicação.

Essa decisão reduz o risco de números inventados ou cálculos inconsistentes.

### Identificadores internos

Cada transação persistida recebe um identificador interno.

O usuário não precisa informar esse identificador em planilhas ou formulários.

### Isolamento por usuário

As principais entidades utilizam `user_id` para separar os dados.

A autenticação real ainda não foi implementada, mas a estrutura interna já evita que registros de usuários diferentes sejam misturados.

### Uma conta representa um perfil financeiro

Na versão inicial, cada conta de usuário representa um único perfil financeiro.

Contas bancárias, cartões e carteiras separadas poderão ser adicionadas futuramente caso tragam valor real para o produto.

---

## Limitações Atuais

O projeto ainda não possui:

- autenticação real;
- cadastro e login de usuários;
- recuperação de senha;
- banco PostgreSQL;
- deploy público;
- múltiplas contas financeiras por usuário;
- aplicativo mobile;
- integração bancária;
- sincronização automática com instituições financeiras;
- testes end-to-end completos da interface;
- avaliação automatizada ampla das respostas da IA.

A interface ainda possui áreas que precisarão de uma revisão visual dedicada, mas a prioridade atual é concluir as funcionalidades e estabilizar a arquitetura.

---

## Direção Futura

A evolução planejada é transformar o FinanTec em um pequeno SaaS financeiro, mantendo o escopo controlado.

O caminho principal é:

```text
SQLite como fonte local confiável
        ↓
Revisão dos módulos transacionais
        ↓
Autenticação
        ↓
PostgreSQL
        ↓
Deploy
        ↓
Melhorias incrementais de produto
```

Possíveis melhorias posteriores incluem:

- múltiplas contas financeiras;
- filtros e relatórios adicionais;
- evolução da detecção de intenção do assistente;
- acesso responsivo por dispositivos móveis;
- refinamento visual;
- notificações e lembretes;
- importações mais flexíveis.

---

## Status Atual

O FinanTec já possui:

- pipeline ETL funcional;
- dashboard financeiro;
- dados de demonstração;
- entrada manual de transações;
- edição e exclusão;
- importação de CSV e Excel;
- exportação para Excel;
- detecção de possíveis duplicatas;
- persistência direta no SQLite;
- isolamento por usuário;
- perfil financeiro persistente;
- metas financeiras persistentes;
- chat persistente;
- assistente com IA generativa;
- reset seguro dos dados;
- testes automatizados;
- documentação técnica.

O foco atual é finalizar a centralização dos dados transacionais no SQLite e revisar os módulos relacionados antes de iniciar autenticação e PostgreSQL.