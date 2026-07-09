from data_loader import carregar_transacoes
from analytics import (
    listar_meses_disponiveis,
    filtrar_transacoes_por_mes,
    calcular_resumo_financeiro,
    formatar_moeda,
)

transacoes = carregar_transacoes()
meses = listar_meses_disponiveis(transacoes)

print("=== MESES DISPONÍVEIS ===")
for mes in meses:
    print(mes)

print()
print("=== RESUMO POR MÊS ===")

for mes in meses:
    transacoes_mes = filtrar_transacoes_por_mes(transacoes, mes)
    resumo = calcular_resumo_financeiro(transacoes_mes)

    print()
    print(f"Mês: {mes}")
    print(f"Receitas: {formatar_moeda(resumo['receitas_totais'])}")
    print(f"Gasto de consumo no mês: {formatar_moeda(resumo['despesas_do_mes'])}")
    print(f"Valor separado para reserva: {formatar_moeda(resumo['valor_guardado_reserva'])}")
    print(f"Saldo disponível: {formatar_moeda(resumo['saldo_disponivel'])}")
    print(f"Maior categoria: {resumo['maior_categoria']} ({formatar_moeda(resumo['maior_gasto'])})")
