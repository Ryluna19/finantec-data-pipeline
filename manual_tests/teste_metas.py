import _path_setup
from data_loader import carregar_perfil_usuario
from analytics import calcular_meta_mensal, formatar_moeda

perfil = carregar_perfil_usuario()

print("=== SIMULAÇÃO DE METAS ===")

for meta in perfil["objetivos_financeiros"]:
    nome = meta["nome"]
    valor_meta = float(meta["valor_meta"])
    valor_atual = float(meta["valor_atual"])
    prazo_meses = int(meta["prazo_meses"])

    simulacao = calcular_meta_mensal(
        valor_meta=valor_meta,
        prazo_meses=prazo_meses,
        valor_ja_reservado=valor_atual
    )

    print()
    print(f"Meta: {nome}")
    print(f"Valor da meta: {formatar_moeda(valor_meta)}")
    print(f"Valor atual: {formatar_moeda(valor_atual)}")
    print(f"Valor restante: {formatar_moeda(simulacao['valor_restante'])}")
    print(f"Prazo: {prazo_meses} meses")
    print(f"Valor mensal necessário: {formatar_moeda(simulacao['valor_mensal_necessario'])}")
