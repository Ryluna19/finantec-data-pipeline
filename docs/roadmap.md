# Roadmap — FinanTec Data Pipeline

## Visão Geral

Este roadmap organiza as próximas evoluções possíveis do FinanTec Data Pipeline.

O objetivo é evoluir o projeto de forma incremental, sem transformar o escopo em algo grande demais ou difícil de manter.

A versão atual já possui:

- pipeline ETL com Python e pandas;
- leitura de múltiplos arquivos CSV;
- validação e transformação dos dados;
- carga em SQLite;
- dashboard em Streamlit;
- filtro por período;
- simulador de metas financeiras;
- assistente com IA generativa;
- testes automatizados com pytest;
- contrato de dados para arquivos de transações.

---

## Versão Atual

### Status

Protótipo funcional.

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

Demonstrar um fluxo completo e simples de dados financeiros simulados, desde a entrada dos arquivos até a visualização e explicação dos indicadores.

---

## Próximas Evoluções Prioritárias

### 1. Melhorar a entrada de dados

Permitir que o usuário utilize uma planilha-modelo para preencher novas transações.

Possíveis melhorias:

- manter `data/templates/transacoes_template.csv`;
- documentar melhor como preencher o arquivo;
- adicionar validação mais detalhada;
- criar mensagens de erro mais claras no ETL;
- permitir upload manual pelo Streamlit.

Valor da melhoria:

```text
Aproxima o projeto de um uso real, onde alguém fornece seus próprios dados em um formato padronizado.
```

---

### 2. Ler dados diretamente do SQLite no dashboard

A aplicação já prioriza SQLite quando o banco existe, mas essa etapa pode ser expandida.

Possíveis melhorias:

- criar consultas SQL específicas por período;
- evitar carregar a tabela inteira quando o volume crescer;
- criar camada de repositório para consultas;
- documentar queries principais.

Valor da melhoria:

```text
Deixa o projeto mais próximo de aplicações que usam banco como fonte principal de dados.
```

---

### 3. Relatórios financeiros

Gerar relatórios simples a partir dos dados processados.

Possíveis melhorias:

- relatório CSV por período;
- relatório Excel com resumo e categorias;
- exportação de dados filtrados;
- resumo mensal em arquivo separado.

Valor da melhoria:

```text
Adiciona uma saída útil ao pipeline, além do dashboard.
```

---

### 4. Automação de arquivos

Criar uma automação simples para organizar arquivos processados.

Possíveis melhorias:

- mover arquivos processados para uma pasta `data/archive/`;
- registrar arquivos já processados;
- evitar reprocessamento duplicado;
- criar logs mais detalhados;
- executar o pipeline com um único comando.

Valor da melhoria:

```text
Aproxima o projeto de uma automação simples de processos, conectando o projeto a conceitos de RPA.
```

---

## Evoluções Futuras

### PostgreSQL

Adicionar PostgreSQL como alternativa ao SQLite.

Não é prioridade imediata, porque SQLite é suficiente para a versão local e reduz a complexidade de configuração.

Quando fizer sentido, o PostgreSQL pode ser adicionado para demonstrar:

- banco relacional mais próximo de ambiente produtivo;
- queries SQL mais robustas;
- separação entre ambiente local e banco externo;
- possível deploy futuro.

---

### Upload de planilha no Streamlit

Permitir que o usuário envie um CSV pela interface.

Essa melhoria deve vir depois do contrato de dados e da validação estarem mais sólidos.

Fluxo possível:

```text
Usuário baixa planilha-modelo
        ↓
Preenche transações
        ↓
Faz upload no Streamlit
        ↓
Sistema valida
        ↓
Pipeline processa
        ↓
Dashboard atualiza
```

---

### Histórico de conversas

Persistir o histórico do chat em banco.

Hoje o histórico existe apenas durante a sessão do Streamlit.

Uma evolução futura poderia salvar:

- período analisado;
- pergunta;
- resposta;
- data e hora;
- origem dos dados usados.

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

- autenticação de usuários;
- múltiplas contas reais;
- integração com banco real;
- recomendação personalizada de investimentos;
- deploy com custos;
- arquitetura com microsserviços;
- uso de LangChain ou frameworks complexos;
- RAG com embeddings;
- PostgreSQL obrigatório desde o início.

Essas tecnologias podem ser úteis em outros contextos, mas adicioná-las agora poderia deixar o projeto mais complexo sem melhorar sua proposta principal.

---

## Direção Recomendada

A evolução mais estratégica para a próxima etapa é:

```text
Planilha-modelo + validação mais forte + upload futuro
```

Isso transforma o projeto em algo mais próximo de uma ferramenta real:

```text
Usuário fornece dados no padrão esperado
        ↓
Pipeline valida e processa
        ↓
Dashboard apresenta indicadores
        ↓
IA explica os resultados
```

Essa direção mantém o projeto simples, útil e tecnicamente defensável.