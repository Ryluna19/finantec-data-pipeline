# Testes Manuais

Esta pasta contém scripts auxiliares usados durante o desenvolvimento do FinanTec Data Pipeline.

Esses scripts servem para validar manualmente partes específicas do projeto, como leitura de dados, montagem de contexto, conexão com SQLite e integração com IA.

Eles não substituem os testes automatizados da pasta `tests/`.

## Scripts disponíveis

| Arquivo | Finalidade |
|---|---|
| `teste_contexto.py` | Verifica a montagem do contexto enviado para a IA. |
| `teste_dados.py` | Verifica a leitura e preparação dos dados. |
| `teste_ia.py` | Testa manualmente a chamada para a IA generativa. |
| `teste_metas.py` | Verifica simulações de metas financeiras. |
| `teste_periodos.py` | Lista e valida os períodos disponíveis na base. |
| `teste_sqlite.py` | Verifica leitura de dados a partir do SQLite. |

## Observação

Para rodar os scripts, execute os comandos a partir da raiz do projeto.

Exemplo:

```bash
python manual_tests/teste_periodos.py