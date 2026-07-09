# Roadmap — FinanTec Data Pipeline

## Visão Geral

Este roadmap organiza as próximas evoluções possíveis do FinanTec Data Pipeline.

O objetivo é evoluir o projeto de forma incremental, sem transformar o escopo em algo grande demais ou difícil de manter.

A direção futura mais coerente é transformar o projeto em uma ferramenta local de controle financeiro pessoal, mantendo o foco em dados, validação, SQLite, dashboard e IA explicando indicadores.

A proposta não é criar, neste momento, um sistema multiusuário com login, autenticação, permissões ou integração bancária real.

---

## Versão Atual

### Status

Protótipo funcional em evolução.

### A versão atual já possui

- pipeline ETL com Python e pandas;
- leitura de múltiplos arquivos CSV;
- validação e transformação dos dados;
- separação entre transações válidas e rejeitadas;
- relatório de rejeições com motivo;
- carga em SQLite;
- dashboard em Streamlit;
- filtro por período;
- resumo financeiro;
- gráfico de gastos por categoria;
- simulador de metas financeiras;
- assistente com IA generativa;
- histórico de conversa separado por período;
- testes automatizados com pytest;
- testes manuais documentados;
- contrato de dados para arquivos de transações;
- comando principal com `main.py`.

### Fluxo atual

```text
CSV bruto
   ↓
ETL com pandas
   ↓
CSV processado
   ↓
SQLite
   ↓
Dashboard Streamlit
   ↓
IA explicando indicadores
```

### Objetivo da versão atual

Demonstrar um fluxo completo e simples de dados financeiros simulados, desde a entrada dos arquivos até a validação, persistência, visualização e explicação dos indicadores.

---

## Próximas Evoluções Prioritárias

### 1. Evoluir entrada de dados para controle financeiro local

Permitir que a pessoa registre ou edite transações em uma experiência parecida com uma planilha simples de gastos.

A ideia não é criar um sistema de usuários, mas sim uma ferramenta local/pessoal baseada em um único perfil financeiro simulado.

Possíveis melhorias:

- criar uma tela de cadastro/edição de transações no Streamlit;
- usar `st.data_editor` para editar transações em formato de tabela;
- salvar novas transações em CSV local ou SQLite;
- reaproveitar o contrato de dados atual;
- validar entradas antes de processar;
- mostrar erros de validação de forma clara;
- permitir baixar ou visualizar a planilha-modelo.

Valor da melhoria:

```text
Transforma o projeto em algo mais próximo de uma ferramenta real de gestão financeira pessoal, sem aumentar demais o escopo com autenticação ou infraestrutura complexa.
```

Fluxo possível:

```text
Pessoa registra gastos na interface
        ↓
Sistema salva os dados localmente
        ↓
Pipeline valida e organiza
        ↓
SQLite armazena os dados
        ↓
Dashboard mostra os indicadores
        ↓
IA ajuda a interpretar os resultados
```

---

### 2. Melhorar a entrada via planilha-modelo

Permitir que a pessoa utilize uma planilha-modelo para preencher novas transações e importar os dados para o projeto.

Possíveis melhorias:

- manter `data/templates/transacoes_template.csv`;
- documentar melhor como preencher o arquivo;
- adicionar exemplos válidos e inválidos;
- exibir instruções no dashboard;
- permitir upload manual pelo Streamlit;
- validar o arquivo enviado antes de processar;
- mostrar relatório de rejeições após o upload.

Valor da melhoria:

```text
Aproxima o projeto de um uso real, onde alguém fornece seus próprios dados em um formato padronizado.
```

---

### 3. Ler dados com consultas mais específicas ao SQLite

A aplicação já prioriza SQLite quando o banco existe, mas essa etapa pode ser expandida.

Possíveis melhorias:

- criar consultas SQL específicas por período;
- evitar carregar a tabela inteira quando o volume crescer;
- criar uma camada simples de repositório para consultas;
- documentar queries principais;
- usar SQLite como fonte principal do dashboard de forma mais explícita.

Valor da melhoria:

```text
Deixa o projeto mais próximo de aplicações que usam banco como fonte principal de dados.
```

---

### 4. Relatórios financeiros

Gerar relatórios simples a partir dos dados processados.

Possíveis melhorias:

- relatório CSV por período;
- relatório Excel com resumo e categorias;
- exportação de dados filtrados;
- resumo mensal em arquivo separado;
- relatório de transações rejeitadas mais amigável;
- botão de download no Streamlit.

Valor da melhoria:

```text
Adiciona uma saída útil ao pipeline, além do dashboard.
```

---

### 5. Automação de arquivos

Criar uma automação simples para organizar arquivos processados.

Possíveis melhorias:

- mover arquivos processados para uma pasta `data/archive/`;
- registrar arquivos já processados;
- evitar reprocessamento duplicado;
- criar logs mais detalhados;
- gerar resumo da execução do ETL;
- executar o pipeline com um único comando.

Valor da melhoria:

```text
Aproxima o projeto de uma automação simples de processos, conectando o projeto a conceitos de RPA sem tornar o escopo pesado.
```

---

## Evoluções Futuras

### Histórico de conversas em banco

Persistir o histórico do chat em SQLite.

Hoje o histórico existe apenas durante a sessão do Streamlit.

Uma evolução futura poderia salvar:

- período analisado;
- pergunta;
- resposta;
- data e hora;
- origem dos dados usados.

Essa melhoria faria sentido depois que o projeto estiver mais consolidado como ferramenta local.

---

### PostgreSQL

Adicionar PostgreSQL como alternativa ao SQLite.

Não é prioridade imediata, porque SQLite é suficiente para a versão local e reduz a complexidade de configuração.

Quando fizer sentido, o PostgreSQL pode ser adicionado para demonstrar:

- banco relacional mais próximo de ambiente produtivo;
- queries SQL mais robustas;
- separação entre ambiente local e banco externo;
- possível deploy futuro.

---

### Testes da interface

Adicionar testes para componentes da aplicação Streamlit.

Essa melhoria não é prioridade agora, porque o maior risco técnico do projeto está no pipeline de dados e nos cálculos financeiros, que já possuem testes automatizados.

---

### Avaliação automatizada da IA

Criar um processo para avaliar respostas da IA de forma mais estruturada.

Possibilidades:

- conjunto fixo de perguntas;
- respostas esperadas;
- avaliação manual registrada;
- comparação semântica futura;
- uso de rubricas de segurança e coerência.

---

## O que não é prioridade agora

Algumas ideias poderiam aumentar o escopo sem trazer retorno proporcional neste momento.

Não são prioridade:

- login e autenticação;
- múltiplos usuários;
- controle de permissões;
- múltiplas contas reais;
- integração com bancos reais;
- recomendação personalizada de investimentos;
- deploy com custos;
- arquitetura com microsserviços;
- uso de LangChain ou frameworks complexos;
- RAG com embeddings;
- PostgreSQL obrigatório desde o início;
- integração com Open Finance;
- aplicativo mobile.

Essas tecnologias podem ser úteis em outros contextos, mas adicioná-las agora poderia deixar o projeto mais complexo sem melhorar sua proposta principal.

---

## Direção Recomendada

A evolução mais estratégica para a próxima etapa é:

```text
Controle financeiro local + validação forte + SQLite + dashboard
```

Na prática, isso significa evoluir de:

```text
CSV bruto → ETL → SQLite → dashboard → IA
```

para:

```text
Pessoa registra ou importa transações
        ↓
Sistema valida os dados
        ↓
SQLite armazena a base
        ↓
Dashboard apresenta indicadores
        ↓
IA explica os resultados
```

Essa direção mantém o projeto simples, útil e tecnicamente defensável.

Ela também deixa o projeto mais interessante para portfólio, porque mostra evolução de um pipeline de dados para uma ferramenta local de gestão financeira pessoal.