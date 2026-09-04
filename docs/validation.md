# Validation — FinanTec Data Pipeline

## Objetivo

Este documento descreve a estratégia de validação da V1 publicada do FinanTec.
O foco está nos comportamentos cujo erro poderia causar:

- cálculos incorretos;
- perda ou duplicação de dados;
- mistura de registros entre usuários;
- falhas de autenticação;
- importações inconsistentes;
- exclusões incompletas;
- regressões nos fluxos principais.

A validação combina testes automatizados, bancos temporários e verificações
manuais na interface local e publicada.

## Estado atual

A suíte possui **455 testes automatizados** e está passando integralmente.

Comando principal:

```powershell
python -m pytest -q
```

Verificações auxiliares usadas antes dos commits:

```powershell
python -m compileall -q src tests
git diff --check
git status --short
```

`compileall` verifica se os módulos podem ser compilados, mas não substitui os
testes. `git diff --check` detecta problemas como espaços no final das linhas e
marcadores de conflito.

## Estratégia automatizada

Os testes ficam em `tests/` e utilizam `pytest`.

### Isolamento do banco remoto

A configuração global dos testes força o backend SQLite, exceto quando um teste
avalia explicitamente outro backend. Isso impede que variáveis de ambiente da
máquina façam a suíte ler ou alterar o banco Turso por acidente.

Os testes de persistência utilizam diretórios e bancos temporários sempre que
apropriado.

```text
execução do pytest
        ↓
ambiente de teste isolado
        ↓
SQLite temporário
        ↓
nenhuma escrita no Turso de produção
```

### Tipos de teste

A suíte combina:

- testes unitários de regras e funções determinísticas;
- testes de integração entre serviços e repositórios;
- testes de persistência em bancos temporários;
- testes de composição dos componentes Streamlit com objetos simulados;
- testes do pipeline ETL e dos formatos de importação.

O objetivo não é testar cada linha ou detalhe interno. Os testes priorizam
comportamento observável e risco de regressão.

## Cobertura por domínio

| Área | Principais comportamentos validados |
|---|---|
| Analytics | Receitas, despesas, reserva, saldo, categorias e períodos. |
| Contas | Cadastro, autenticação, hashes, rehash, duplicidade e tentativas de login. |
| Contas temporárias | Validade de 24 horas, bloqueio após expiração e tempo restante. |
| Contexto do usuário | Sessão autenticada, `user_id` e expiração preservada. |
| Banco de dados | SQLite, configuração do Turso, interface comum e tradução de erros. |
| Transações | Identidade, CRUD, sincronização, filtros e isolamento. |
| Importação | CSV, Excel, OFX, mapeamento assistido e prévia. |
| Duplicatas | Identificação, opção segura padrão e importação explícita. |
| ETL | Extração, normalização, rejeições, arquivos processados e carga. |
| Perfil | Criação, atualização, persistência e isolamento. |
| Metas | CRUD, progresso, simulação e isolamento. |
| Orçamento | Limites mensais, recorrência, períodos e acompanhamento. |
| Dados e privacidade | Reset financeiro, exclusão de conta e limpeza de contas vencidas. |
| Interface | Navegação, autenticação, estados de ação, temas e componentes principais. |

## Validação das contas

### Cadastro e autenticação

São verificados automaticamente:

- normalização e validação do nome de usuário;
- regras mínimas da senha;
- armazenamento somente do hash;
- geração de hashes distintos para senhas iguais;
- autenticação válida e inválida;
- atualização do hash quando necessário;
- conflito de nomes de usuário;
- bloqueio temporário após falhas consecutivas;
- limpeza do histórico de falhas após autenticação válida.

### Conta temporária

Os testes cobrem:

- cálculo da expiração 24 horas após a criação;
- conta permanente sem `expires_at`;
- preservação de `expires_at` na sessão;
- detecção de validade encerrada;
- rejeição da autenticação após a expiração;
- encerramento de sessão expirada;
- remoção da conta e dos registros associados;
- cadastro público temporário sem código;
- preservação da exigência de código para conta permanente;
- apresentação do aviso de tempo restante somente para conta temporária.

### Isolamento por usuário

As operações sensíveis utilizam o contexto da conta autenticada. Os testes
verificam o isolamento de:

- transações;
- perfil;
- metas;
- orçamento;
- reset financeiro;
- exclusão de conta.

## Validação das transações

### Cadastro e edição

Os testes validam:

- campos obrigatórios;
- datas, tipos, categorias e valores;
- criação de identidade estável;
- persistência;
- edição e exclusão;
- atualização dos dados exibidos após uma operação.

### Importação

Os caminhos de CSV, Excel e OFX compartilham regras do modelo canônico.

São cobertos:

- cabeçalhos obrigatórios;
- normalização de nomes de coluna;
- conversão de datas e valores;
- tipos explícitos ou derivados do sinal;
- colunas separadas de débito e crédito;
- seleção de aba e cabeçalho no Excel;
- categorias opcionais;
- linhas válidas e rejeitadas;
- prévia antes da persistência;
- identificação de possíveis duplicatas;
- confirmação explícita para importar duplicatas.

### Exportação

A exportação é validada quanto ao período selecionado, colunas esperadas e
geração do arquivo Excel.

## Validação do planejamento financeiro

### Visão geral

São verificados cálculos de:

- receitas;
- gastos de consumo;
- reserva;
- saldo;
- agrupamento por categoria;
- transações recentes;
- resumo do orçamento.

### Orçamento

A cobertura inclui criação, edição, exclusão, recorrência e encerramento de
limites. Também são validados gasto real, saldo restante, valor excedido e
isolamento por usuário e período.

### Metas

São testados CRUD, progresso, valor restante, contribuições e simulações que não
alteram automaticamente os registros persistidos.

### Perfil

Os testes cobrem estado vazio, criação, atualização, fontes de renda e
persistência isolada por usuário.

## Validação da exclusão de dados

Existem dois fluxos distintos:

```text
Apagar meus dados
→ remove registros financeiros
→ preserva conta e credenciais

Excluir conta
→ remove registros financeiros
→ remove tentativas de login
→ remove conta e credenciais
```

A limpeza de uma conta temporária expirada utiliza o mesmo fluxo coordenado de
exclusão, reduzindo a chance de deixar registros órfãos.

Os testes verificam cada tabela associada e confirmam que dados de outros
usuários permanecem preservados.

## Validação manual da V1

Os testes automatizados não substituem a avaliação do ciclo de rerun, layout e
interação real do Streamlit.

### Fluxos funcionais

Foram verificados manualmente:

- criação e autenticação de conta permanente;
- criação pública de conta temporária;
- permanência dos dados temporários entre acessos;
- aviso de tempo restante;
- encerramento da sessão após expiração;
- impossibilidade de autenticar uma conta já removida;
- acesso preservado para contas permanentes antigas;
- cadastro, edição e exclusão de transações;
- importação e tratamento de possíveis duplicatas;
- orçamento, metas e perfil;
- exclusão dos dados financeiros;
- exclusão definitiva da conta.

### Aplicação publicada

No ambiente público foram confirmados:

- carregamento da interface;
- conexão com o banco Turso configurado;
- criação de conta temporária sem código;
- exigência de código para conta permanente;
- aviso exclusivo da conta temporária;
- acesso das contas permanentes existentes;
- funcionamento dos fluxos principais.

### Interface

A interface foi revisada em:

- desktop;
- notebook;
- dispositivos móveis;
- tema claro;
- tema escuro.

## Scripts manuais

`manual_tests/` mantém verificações auxiliares para situações específicas:

```powershell
python manual_tests/teste_dados.py
python manual_tests/teste_metas.py
python manual_tests/teste_periodos.py
python manual_tests/teste_sqlite.py
```

Esses scripts não substituem a suíte automatizada.

## Limitações da validação

A V1 ainda não possui:

- suíte end-to-end automatizada em navegador real;
- testes extensivos de carga e concorrência;
- benchmark formal de desempenho;
- pentest;
- auditoria independente de segurança;
- monitoramento automatizado de disponibilidade;
- validação em grande volume de usuários e dados.

Essas limitações impedem classificar o FinanTec como plataforma financeira de
produção, mas não anulam sua utilidade como projeto funcional de portfólio e
demonstração pública controlada.

## Registro histórico da integração com Gemini

A antiga integração externa foi removida e não faz parte da navegação ou da
execução atual. Os testes de componentes históricos que ainda permanecerem no
repositório não significam que o recurso esteja ativo.

Consulte o
[ADR 001 — Remoção da integração externa com Gemini](decisions/001-remove-gemini-integration.md)
para a decisão completa.

## Critério de aprovação da V1

Para considerar a V1 fechada:

- [x] fluxos principais validados manualmente;
- [x] suíte automatizada passando;
- [x] testes isolados do banco remoto;
- [x] demonstração pública funcional;
- [x] contas temporárias e permanentes verificadas;
- [x] `git diff --check` sem erros antes dos commits;
- [x] secrets ausentes dos arquivos versionados;
- [ ] documentação técnica completamente alinhada;
- [ ] referência de versão criada no Git.

## Resultado

A validação atual fornece confiança sobre os principais riscos funcionais da
V1. O trabalho restante está concentrado na documentação e no versionamento da
referência final, não na expansão do produto.
