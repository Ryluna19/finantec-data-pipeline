from data_loader import carregar_transacoes
from analytics import calcular_resumo_financeiro, calcular_gastos_por_categoria, formatar_moeda

transacoes = carregar_transacoes()

resumo = calcular_resumo_financeiro(transacoes)
gastos_por_categoria = calcular_gastos_por_categoria(transacoes)

print("=== RESUMO FINANCEIRO ===")
print(f"Receitas: {formatar_moeda(resumo['receitas_totais'])}")
print(f"Gasto de consumo no mês: {formatar_moeda(resumo['despesas_do_mes'])}")
print(f"Valor separado para reserva: {formatar_moeda(resumo['valor_guardado_reserva'])}")
print(f"Saldo disponível: {formatar_moeda(resumo['saldo_disponivel'])}")
print(f"Maior categoria de consumo: {resumo['maior_categoria']} ({formatar_moeda(resumo['maior_gasto'])})")

print()
print("=== GASTOS DE CONSUMO POR CATEGORIA ===")

for categoria, valor in gastos_por_categoria.items():
    print(f"{categoria}: {formatar_moeda(valor)}")
