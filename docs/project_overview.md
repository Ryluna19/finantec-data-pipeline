# Project Overview — FinanTec

## Visão Geral

O FinanTec é uma aplicação local de organização financeira desenvolvida com
Python, Streamlit, pandas e SQLite.

O projeto começou como um pipeline ETL para processar transações simuladas em
CSV. Com sua evolução, passou a permitir cadastro, edição, exclusão, importação
e exportação diretamente pela interface. O SQLite tornou-se a principal fonte
dos dados, enquanto o ETL foi mantido para demonstração, compatibilidade e
processamento explícito de arquivos.

O objetivo do produto é fazer o básico de um controlador financeiro pessoal
parecer completo e confiável, valorizando:

- regras de negócio claras;
- persistência e isolamento de dados;
- importação e validação;
- testes automatizados;
- privacidade;
- interface funcional e responsiva;
- decisões técnicas documentadas.

O FinanTec não pretende ser banco digital, sistema empresarial ou plataforma de
investimentos.

---

## Problema e Solução

Quem começa a organizar a própria renda frequentemente usa planilhas ou
anotações dispersas. Isso dificulta consolidar receitas, despesas, reservas,
saldo e metas, além de aumentar o risco de formatos inválidos e registros
duplicados.

O FinanTec centraliza esses fluxos em uma aplicação local:

- registra e consulta transações;
- importa arquivos CSV e Excel;
- valida e sinaliza rejeições;
- identifica possíveis duplicatas;
- calcula indicadores por período;
- acompanha metas persistentes;
- separa dados pessoais e demonstração;
- permite apagar somente as transações pessoais.

---

## Público e Escopo

O uso atual é pessoal e local. O projeto também serve como portfólio técnico
para demonstrar Python, pandas, Streamlit, SQLite, modelagem de dados, testes e
evolução incremental de arquitetura.

Não fazem parte do escopo atual:

- integração bancária e Open Finance;
- autenticação real e múltiplos usuários finais;
- recomendação personalizada de investimentos;
- infraestrutura empresarial;
- microsserviços;
- processamento financeiro em grande escala.

---

## Fluxos de Dados

### Dados pessoais

```text
Entrada manual ou arquivo CSV/Excel
        ↓
Validação e padronização
        ↓
Análise de possíveis duplicatas
        ↓
Gravação direta no SQLite
        ↓
Consulta, indicadores e metas
```

### Demonstração e compatibilidade

```text
Arquivos CSV de demonstração
        ↓
ETL com pandas
        ↓
Registros válidos e rejeitados
        ↓
Carga da partição de demonstração no SQLite
        ↓
Dashboard em modo de demonstração
```

---

## Funcionalidades Atuais

### Visão geral

- receitas, despesas, reserva e saldo disponível;
- gastos por categoria;
- diagnóstico financeiro simples;
- filtros por período;
- transações recentes.

### Transações

- consulta e filtros como conteúdo principal;
- cadastro manual sob demanda;
- importação de CSV e Excel sob demanda;
- exportação limitada ao período selecionado;
- edição e exclusão de registros persistidos;
- confirmação antes de excluir;
- validação e relatório expansível de rejeições.

### Metas

- visualizações separadas para metas salvas e simulador;
- criação e edição sob demanda;
- progresso, valor atual, restante e contribuição mensal;
- estado de conclusão;
- confirmação antes da exclusão;
- persistência isolada por usuário.

### Perfil

- resumo antes do formulário de edição;
- fontes de renda editáveis;
- renda mensal calculada pela soma das fontes;
- preservação interna de campos antigos por compatibilidade.

### Dados e privacidade

- alternância entre dados pessoais e demonstração;
- resumo dos dados armazenados localmente;
- exclusão somente das transações pessoais e arquivos relacionados;
- preservação de perfil, metas, conversas, demonstração e banco SQLite.

### Insights congelados

O projeto preserva classificação local de intenções, respostas determinísticas
e histórico de conversa. Esse recurso não utiliza serviço externo e foi retirado
da navegação principal para não competir com os fluxos financeiros centrais.

A integração anterior com Gemini foi removida por uma decisão preventiva de
privacidade, documentada em
[ADR 001](decisions/001-remove-gemini-integration.md).

---

## Arquitetura Atual

### Interface

- Streamlit;
- componentes separados por responsabilidade;
- CSS personalizado e responsivo;
- estado de sessão para interações temporárias.

### Regras e serviços

- Python e pandas;
- cálculos financeiros fora da interface;
- serviços específicos para cadastro, importação e sincronização;
- validação compartilhada entre entrada manual e arquivos.

### Persistência

- SQLite como fonte principal;
- repositórios para transações, perfil, metas e conversas;
- isolamento interno por `user_id`;
- separação entre dados pessoais e demonstração;
- identificadores estáveis gerados pela aplicação.

### Qualidade

- pytest;
- bancos temporários nos testes de persistência;
- testes de CRUD, isolamento e reset;
- testes de importação, duplicatas e identidade;
- testes de cálculos e composição dos principais fluxos.

---

## Componentes Principais

| Componente | Responsabilidade |
|---|---|
| `src/app.py` | Coordena navegação, período e composição das telas principais. |
| `src/analytics.py` | Centraliza cálculos e indicadores financeiros. |
| `src/components/` | Reúne componentes visuais por fluxo. |
| `src/transaction_repository.py` | Persiste e consulta transações. |
| `src/goal_repository.py` | Persiste e consulta metas. |
| `src/profile_repository.py` | Persiste o perfil e suas fontes de renda. |
| `src/chat_repository.py` | Preserva localmente o histórico do recurso congelado. |
| `src/financial_intents.py` | Classificação determinística preservada. |
| `src/financial_responses.py` | Respostas financeiras locais preservadas. |
| `scripts/etl_transacoes.py` | ETL de demonstração e compatibilidade. |
| `tests/` | Testes automatizados das regras e fluxos principais. |

---

## Decisões Técnicas

### SQLite como fonte principal

O SQLite é simples, gratuito e suficiente para o uso local. As transações são
gravadas diretamente no banco, sem depender de uma execução automática do ETL.

### ETL com responsabilidade limitada

O ETL continua válido para dados de demonstração, compatibilidade com arquivos
antigos e processamento explícito. Ele não é mais pré-requisito para o uso
normal da aplicação.

### Privacidade e remoção do Gemini

A integração externa poderia enviar perguntas, histórico recente e contexto
financeiro para processamento por terceiros. Não houve violação comprovada,
mas o risco potencial não era proporcional ao benefício de uma API gratuita em
um aplicativo pessoal e local.

Por isso, a integração foi removida preventivamente. As consultas suportadas
passaram a depender apenas de regras locais e o recurso foi posteriormente
congelado fora da navegação principal.

### Isolamento antes da autenticação

As principais entidades já usam `user_id`, embora o projeto possua apenas um
usuário local fixo e não ofereça autenticação real.

### Compatibilidade sem exposição na interface

Campos e módulos antigos podem permanecer internamente quando sua remoção
imediata trouxer risco de migração. Eles não precisam continuar visíveis para a
pessoa usuária.

---

## Limitações Atuais

- não possui autenticação real;
- não possui deploy público;
- não integra com bancos;
- não executa operações financeiras;
- não possui exclusão coordenada de todos os dados locais;
- não possui testes end-to-end completos no navegador;
- mantém partes históricas do ETL e do antigo recurso de IA por compatibilidade.

---

## Direção Futura

A evolução deve continuar incremental:

```text
fluxos locais estáveis
        ↓
revisão global de UX e responsividade
        ↓
documentação alinhada
        ↓
deploy e mudanças estruturais somente se ainda fizerem sentido
```

PostgreSQL, autenticação e multiusuário não são consequências obrigatórias. O
SQLite pode permanecer como escolha legítima enquanto o produto continuar
pessoal e local.

---

## Status Atual

O FinanTec possui os principais fluxos financeiros estabilizados, navegação
focada em Visão geral, Transações e Metas, persistência local em SQLite e suíte
automatizada cobrindo as regras de maior risco.

O foco atual é consolidar a documentação e realizar uma revisão global da
experiência antes de considerar deploy ou expansão de arquitetura.
