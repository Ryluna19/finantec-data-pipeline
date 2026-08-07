# Validation — FinanTec Data Pipeline

> [!NOTE]
> Este documento descreve a estratégia de validação da versão atual do FinanTec
> e preserva, ao final, um registro resumido da antiga integração com Gemini.
> A aplicação atual não realiza chamadas para serviços externos de IA.
>
> Consulte também:
> [ADR 001 — Remoção da integração externa com Gemini](decisions/001-remove-gemini-integration.md).

## Visão Geral

A validação do FinanTec combina testes automatizados e verificações manuais dos
principais fluxos da aplicação.

A versão 1 é uma aplicação local com:

- contas;
- transações;
- importação e exportação;
- indicadores;
- orçamento;
- metas;
- perfil;
- dados de demonstração;
- gerenciamento e exclusão dos próprios dados.

A estratégia atual considera cinco áreas principais:

1. regras e cálculos financeiros;
2. validação, importação e ETL;
3. persistência e integridade no SQLite;
4. autenticação, contexto e isolamento por usuário;
5. composição e comportamento dos principais fluxos da interface.

O objetivo não é testar cada detalhe interno da implementação.

Os testes priorizam comportamentos cujo erro pode causar:

- cálculo incorreto;
- perda de dados;
- duplicação;
- mistura entre usuários;
- mistura entre demonstração e dados pessoais;
- persistência incorreta;
- exclusão indevida;
- quebra dos fluxos principais.

---

## Estratégia de Validação

O projeto utiliza principalmente:

- testes automatizados com `pytest`;
- bancos SQLite temporários em testes de persistência;
- testes unitários e de integração das regras principais;
- verificações manuais pela interface;
- scripts manuais auxiliares;
- documentação das limitações conhecidas.

A divisão existe porque diferentes partes do projeto exigem tipos diferentes de
validação.

Funções determinísticas e regras de persistência são adequadas para testes
automatizados.

Comportamentos visuais e interações específicas do Streamlit também precisam de
verificação manual, principalmente quando dependem do ciclo de rerun da
interface.

---

## Testes Automatizados

Os testes ficam em:

```text
tests/
```

Para executar a suíte pelo comando principal:

```powershell
python main.py test
```

Também é possível executar diretamente:

```powershell
pytest -q
```

Antes do fechamento da v1, a suíte completa deve ser executada novamente para
confirmar que nenhuma alteração documental ou funcional recente introduziu
regressões.

O número total de testes não é tratado neste documento como contrato fixo, pois
pode mudar conforme testes redundantes são removidos ou novos comportamentos são
adicionados.

---

## Áreas Cobertas Automaticamente

### Analytics

Os testes verificam regras como:

- receitas totais;
- despesas totais;
- gastos de consumo;
- reserva;
- saldo disponível;
- categorias de gasto;
- períodos;
- formatação monetária;
- cálculos utilizados por metas;
- cálculos utilizados pelo orçamento.

Uma regra importante é que a categoria `Reserva` não deve ser interpretada como
gasto de consumo por padrão.

Também existem validações para pequenas variações de texto que não deveriam
alterar essa classificação.

### ETL

O pipeline é validado nas etapas de:

```text
Extract
Transform
Load
```

Entre os comportamentos cobertos estão:

- presença das colunas obrigatórias;
- conversão de datas;
- normalização dos tipos;
- tratamento de textos;
- conversão de valores;
- rejeição de registros inválidos;
- criação de `ano_mes`;
- ordenação;
- separação entre registros válidos e rejeitados.

### Relatório de rejeições

Quando uma linha é inválida, ela pode receber um ou mais motivos de rejeição.

Exemplos:

```text
data invalida ou vazia
tipo invalido
descricao vazia
valor invalido ou vazio
valor menor ou igual a zero
```

Uma mesma linha pode acumular motivos:

```text
data invalida ou vazia; tipo invalido; descricao vazia
```

Quando necessário, o pipeline gera:

```text
data/processed/transacoes_rejeitadas.csv
```

Esse arquivo é local e não é versionado.

### Carga SQLite

Os testes de carga utilizam bancos temporários para evitar modificar a base
local usada pela aplicação.

São verificados comportamentos como:

- criação das estruturas necessárias;
- persistência dos registros;
- tipos e colunas esperados;
- atualização ou substituição da carga quando aplicável.

---

## Contas e Autenticação

A v1 possui contas locais e esse fluxo faz parte da validação atual.

Os testes automatizados cobrem comportamentos relacionados a:

- criação de conta;
- persistência das credenciais;
- autenticação;
- rejeição de credenciais inválidas;
- contexto de usuário;
- isolamento dos registros associados ao usuário;
- exclusão de conta.

A existência desses testes não significa que a autenticação esteja certificada
para uso público.

A implementação atual atende ao contexto local da v1.

Uma análise específica de segurança será realizada antes da evolução da
arquitetura web.

---

## Isolamento por Usuário

O isolamento é uma das áreas de maior risco da aplicação.

Os principais repositórios utilizam `user_id` para separar informações
pessoais.

Os testes verificam, conforme a entidade:

- leitura somente dos registros do usuário esperado;
- atualização somente dos registros corretos;
- exclusão somente dos registros corretos;
- preservação dos registros pertencentes a outro usuário.

Esse princípio é aplicado principalmente a:

- transações;
- perfil;
- metas;
- orçamento;
- conta;
- operações de remoção de dados.

---

## Dados Pessoais e Demonstração

A aplicação diferencia dados pessoais e demonstração.

Essa separação é validada para evitar que o contexto fictício:

- substitua dados pessoais;
- seja gravado como perfil pessoal;
- seja confundido com transações pessoais;
- seja removido durante um reset financeiro da conta.

O fluxo esperado é:

```text
Meus dados
    ↓
Demonstração
    ↓
Meus dados
```

Ao retornar ao contexto pessoal, os dados previamente persistidos devem
continuar disponíveis.

---

## Transações

A validação automatizada das transações cobre áreas como:

- identidade dos registros;
- preparação;
- persistência;
- leitura;
- edição;
- exclusão;
- sincronização;
- validação;
- importação;
- duplicatas;
- composição dos dados exibidos pela interface.

A entrada manual e a importação compartilham regras de validação sempre que
possível, reduzindo diferenças de comportamento entre os dois caminhos.

---

## Importação

A importação é uma das áreas com maior diversidade de entradas.

A aplicação atualmente suporta:

- CSV;
- Excel;
- OFX;
- Excel externo com mapeamento assistido.

### CSV e Excel estruturados

Os testes verificam:

- leitura;
- normalização;
- validação;
- transformação para o formato interno;
- rejeição de linhas inválidas.

### OFX

São considerados cenários como:

- arquivos válidos;
- variações de estrutura;
- conteúdo inválido;
- problemas de parsing;
- conversão para o modelo interno da aplicação.

### Importação assistida

O fluxo assistido considera:

- listagem de abas;
- seleção de aba;
- detecção ou seleção de cabeçalho;
- normalização dos nomes das colunas;
- sugestão de mapeamento;
- mapeamento manual;
- prévia dos registros.

A aplicação suporta diferentes estratégias de valor:

```text
valor único
```

ou:

```text
valor + tipo explícito
```

ou:

```text
débito + crédito
```

### Possíveis duplicatas

A detecção de duplicatas utiliza uma estratégia conservadora.

O comportamento padrão é:

```text
possível duplicata
        ↓
não importar
```

O usuário pode optar explicitamente por importar também esses registros.

Esse comportamento reduz o risco de duplicação acidental.

---

## Perfil

A validação do Perfil considera:

- ausência inicial como estado válido;
- criação no primeiro salvamento;
- leitura;
- atualização;
- fontes de renda;
- persistência;
- associação ao usuário;
- isolamento entre usuários;
- compatibilidade necessária com registros antigos.

O Perfil é independente das Metas.

---

## Metas

Os testes relacionados às metas verificam:

- criação;
- leitura;
- edição;
- exclusão;
- persistência;
- isolamento;
- progresso;
- valor restante;
- contribuição mensal;
- comportamento sem metas cadastradas.

O simulador deve calcular cenários sem modificar automaticamente a meta
persistida.

---

## Orçamento

A validação do orçamento inclui:

- criação de limite;
- edição;
- exclusão;
- isolamento por usuário;
- isolamento por categoria e período;
- recorrência;
- divisão da recorrência a partir de um mês;
- validações de sobreposição;
- valor planejado;
- gasto real;
- valor disponível;
- valor ultrapassado;
- percentual utilizado;
- composição do resumo mensal.

A ausência de orçamento também é um estado válido.

---

## Dados e Privacidade

Existem duas operações destrutivas distintas.

### Apagar meus dados

Essa ação deve remover os dados financeiros do usuário mantendo:

- conta;
- credenciais;
- capacidade de autenticação;
- dados de demonstração.

Entre os dados pessoais removidos estão os registros associados às principais
entidades financeiras do usuário.

Os testes automatizados verificam que a operação:

- remove os registros pessoais esperados;
- preserva a conta;
- preserva registros de outros usuários;
- preserva o contexto de demonstração.

### Excluir conta

Essa operação possui responsabilidade diferente.

```text
Apagar meus dados
→ mantém a conta

Excluir conta
→ remove a conta e seus dados associados
```

A exclusão definitiva deve impedir uma nova autenticação com a conta removida.

---

## Validação Manual Final da v1

Além da suíte automatizada, os principais fluxos foram testados diretamente na
interface antes do fechamento da v1.

### Transações

Foi validado o ciclo:

```text
criar
↓
editar
↓
consultar
↓
trocar período
↓
exportar
↓
excluir
```

O fluxo funcionou conforme esperado.

### Importação

Foram verificados:

- importação válida;
- identificação de possíveis duplicatas;
- comportamento padrão de ignorar duplicatas;
- opção explícita de importar possíveis duplicatas;
- bloqueio de arquivo inválido;
- importação assistida de Excel.

Os fluxos funcionaram conforme esperado.

### Orçamento

Foi validado:

- criação de limite;
- persistência;
- edição;
- atualização dos valores exibidos;
- categoria acima do limite;
- troca de período;
- retorno ao período;
- exclusão.

Durante a validação, o Streamlit exibiu temporariamente um card antigo após uma
edição.

A consulta direta ao SQLite confirmou que existia apenas um registro
persistido. Após novo rerender da interface, o elemento antigo desapareceu.

O caso foi classificado como um artefato temporário de renderização da interface
e não como duplicação de dados no banco.

### Metas

Foi validado:

- criação;
- edição;
- recálculo dos indicadores;
- persistência;
- navegação para outra área e retorno;
- exclusão;
- separação entre simulador e dados persistidos.

### Perfil

Foi validado:

- edição de informações;
- alteração de fonte de renda;
- persistência;
- saída da tela;
- retorno à tela;
- restauração dos dados utilizados no teste.

### Demonstração

Foi validado:

```text
Meus dados
↓
Demonstração
↓
Meus dados
```

A demonstração foi carregada corretamente.

Ao retornar aos dados pessoais, o contexto original permaneceu disponível.

### Exclusão dos dados financeiros

Foi realizado um teste real do fluxo:

```text
Zona de risco
↓
confirmação APAGAR
↓
Apagar meus dados
```

O resultado esperado foi confirmado:

- dados financeiros removidos;
- conta preservada;
- autenticação da mesma conta ainda possível.

Durante essa etapa foi identificado um problema de interação no Streamlit.

O fluxo utilizava um campo de confirmação e um botão independentes, sujeitos aos
reruns da interface.

A ação foi alterada para utilizar um formulário, agrupando confirmação e envio
em uma única submissão.

Depois da alteração, a exclusão funcionou corretamente.

### Exclusão de conta

Foi utilizada uma conta descartável para validar a exclusão definitiva.

Depois da confirmação:

- a conta foi removida;
- os dados associados deixaram de existir;
- a aplicação retornou ao fluxo de autenticação;
- uma nova tentativa de login com a conta excluída foi recusada.

### Responsividade

A interface foi revisada manualmente em diferentes tamanhos.

Foram verificados principalmente:

- desktop;
- notebook;
- aproximadamente 1366 × 768;
- mobile próximo de 412 × 915.

Não foram identificadas quebras funcionais ou rolagem horizontal global nos
fluxos principais.

Alguns ajustes responsivos são intencionais, como redução de informações
secundárias no cabeçalho mobile.

### Temas

Foram revisados:

```text
tema escuro
tema claro
```

No tema claro foram ajustados principalmente:

- contraste de textos secundários;
- bordas;
- hierarquia dos cards;
- separação visual de Perfil;
- separação visual das ações em Dados e privacidade.

### Data editor

O componente `st.data_editor` possui comportamento visual parcialmente
controlado internamente pelo Streamlit.

Tentativas de forçar completamente o mesmo tema da aplicação não produziram um
resultado consistente.

Como o componente permanece legível e funcional, esse comportamento foi aceito
como limitação visual da v1.

Ele não é tratado como bloqueador funcional.

---

## Scripts Manuais

A pasta:

```text
manual_tests/
```

contém scripts auxiliares utilizados durante o desenvolvimento.

Entre os arquivos existentes estão:

| Arquivo | Finalidade |
|---|---|
| `manual_tests/teste_dados.py` | Inspeção de dados e resumo financeiro. |
| `manual_tests/teste_metas.py` | Verificação auxiliar de cálculos de metas. |
| `manual_tests/teste_periodos.py` | Verificação dos períodos disponíveis. |
| `manual_tests/teste_sqlite.py` | Consulta auxiliar ao SQLite. |
| `manual_tests/README.md` | Documentação dos scripts manuais. |

Exemplos de execução:

```powershell
python manual_tests/teste_dados.py
python manual_tests/teste_metas.py
python manual_tests/teste_periodos.py
python manual_tests/teste_sqlite.py
```

Esses scripts não substituem a suíte automatizada nem a validação funcional
pela interface.

---

## Registro Histórico — Gemini e Assistente Financeiro

O FinanTec já utilizou uma integração externa com Gemini.

Essa fase possuía testes específicos porque dependia de fatores externos como:

- chave da API;
- internet;
- disponibilidade do serviço;
- limites da API;
- variação das respostas do modelo.

O princípio utilizado naquela implementação era manter os cálculos financeiros
em Python.

A IA recebia indicadores já calculados e deveria apenas explicá-los.

Entre os cenários históricos estavam perguntas sobre:

- maior categoria de gasto;
- saldo do período;
- contribuição mensal necessária para uma meta;
- ausência de acesso a taxas bancárias em tempo real;
- recusa de recomendações personalizadas de investimento.

A integração externa foi posteriormente removida por uma decisão preventiva de
privacidade.

O assistente financeiro, o histórico de conversas e o antigo mecanismo de
Insights não fazem parte das funcionalidades atuais da aplicação.

Referências remanescentes em testes, módulos ou documentação são consideradas
legado técnico ou registro histórico.

---

## Problemas Históricos Relevantes

### IA tentando recalcular valores

Em versões antigas, havia risco de a IA tentar interpretar ou recalcular
valores financeiros.

A arquitetura foi alterada para que os cálculos fossem produzidos previamente
em Python.

Esse problema deixou de ser aplicável à execução atual depois da remoção da
integração externa.

### Formatação de moeda no antigo chat

Respostas contendo `R$` podiam ser interpretadas incorretamente pelo Markdown
utilizado na interface do antigo assistente.

Uma etapa de tratamento foi adicionada naquela fase.

O caso permanece apenas como registro histórico.

### Histórico de conversa entre períodos

Durante a fase com assistente, houve necessidade de separar conversas por
contexto e período.

O recurso de conversa não faz parte da v1 atual.

### Rejeições do ETL

Inicialmente, registros inválidos eram descartados sem explicação suficiente.

O pipeline passou a gerar o relatório de rejeições com os respectivos motivos.

Esse comportamento continua relevante e faz parte da validação atual.

---

## Limitações da Validação Atual

Apesar da cobertura existente, a v1 ainda não possui:

- suíte end-to-end abrangente executada em navegador real;
- testes extensivos com grandes volumes de dados;
- benchmark de performance;
- testes de carga;
- auditoria formal de segurança;
- pentest;
- validação da autenticação em ambiente público;
- testes de concorrência para múltiplos usuários simultâneos;
- pipeline completo de CI/CD.

Essas ausências não impedem o fechamento da aplicação local.

Elas definem limites claros para o que pode ser afirmado sobre a versão.

---

## Próxima Validação — Hardening

Depois do fechamento da v1 será realizada uma etapa específica de segurança e
hardening.

Essa revisão deverá avaliar principalmente:

- armazenamento de senhas;
- parâmetros e algoritmo de hash;
- autenticação;
- sessão;
- isolamento por usuário;
- autorização das operações;
- SQL;
- integridade das operações destrutivas;
- importação de arquivos;
- caminhos locais;
- dependências;
- secrets;
- configurações;
- logs;
- resíduos de dados após exclusão.

Problemas encontrados serão classificados entre:

```text
corrigir na v1
corrigir na fundação da v2
não prioritário para o contexto atual
```

---

## Critério de Aprovação da v1

Para considerar a v1 fechada, os seguintes pontos devem estar atendidos:

- principais fluxos funcionais validados manualmente;
- suíte automatizada passando;
- `git diff --check` sem erros;
- documentação alinhada ao comportamento atual;
- ausência de alterações não intencionais;
- repositório limpo;
- commit final;
- referência de versão criada no Git.

A auditoria de segurança aprofundada não é requisito para declarar a v1 local
funcionalmente concluída.

Ela é a etapa imediatamente posterior ao fechamento.

---

## Resultado Atual

A validação atual cobre os principais riscos funcionais da aplicação local:

- cálculos financeiros;
- ETL;
- rejeições;
- SQLite;
- contas;
- autenticação local;
- isolamento por usuário;
- transações;
- importação de CSV;
- importação de Excel;
- importação de OFX;
- importação assistida;
- duplicatas;
- perfil;
- metas;
- orçamento;
- demonstração;
- reset dos dados financeiros;
- preservação da conta;
- exclusão definitiva da conta;
- principais estados e componentes da interface.

A validação manual final complementou a cobertura automatizada nos fluxos em que
o comportamento do Streamlit e a experiência real de uso são relevantes.

Com isso, a v1 possui evidência suficiente para ser tratada como uma aplicação
local funcionalmente estabilizada.

A próxima etapa não é adicionar novas funcionalidades à v1, mas concluir seu
versionamento e iniciar a revisão de segurança planejada.