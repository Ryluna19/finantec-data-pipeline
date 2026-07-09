from data_loader import (
    carregar_conceitos_financeiros,
    carregar_historico_atendimento,
    carregar_perfil_usuario,
    carregar_produtos_financeiros,
    carregar_transacoes,
)
from analytics import calcular_gastos_por_categoria, calcular_resumo_financeiro
from prompts import montar_contexto
from agent import gerar_resposta_finantec


perfil_usuario = carregar_perfil_usuario()
transacoes = carregar_transacoes()
historico_atendimento = carregar_historico_atendimento()
conceitos_financeiros = carregar_conceitos_financeiros()
produtos_financeiros = carregar_produtos_financeiros()

resumo_financeiro = calcular_resumo_financeiro(transacoes)
gastos_por_categoria = calcular_gastos_por_categoria(transacoes)

contexto = montar_contexto(
    perfil_usuario=perfil_usuario,
    resumo_financeiro=resumo_financeiro,
    gastos_por_categoria=gastos_por_categoria,
    historico_atendimento=historico_atendimento,
    conceitos_financeiros=conceitos_financeiros,
    produtos_financeiros=produtos_financeiros,
)

pergunta = "Em qual categoria eu mais gastei este mês e o que posso observar sobre isso?"

print("Pergunta enviada ao FinanTec:")
print(pergunta)
print()
print("Resposta:")
print(gerar_resposta_finantec(pergunta, contexto))
