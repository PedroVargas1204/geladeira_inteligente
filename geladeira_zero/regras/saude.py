"""
saude.py
========
Cálculos de saúde/energia do usuário: taxa metabólica basal (TMB) e gasto
energético diário estimado, considerando o nível de atividade física.

Usa a equação de Mifflin-St Jeor (1990), a mais recomendada atualmente
para estimar a TMB de adultos:

    Homens:   TMB = 10*peso(kg) + 6,25*altura(cm) - 5*idade(anos) + 5
    Mulheres: TMB = 10*peso(kg) + 6,25*altura(cm) - 5*idade(anos) - 161

O gasto total (TDEE) multiplica a TMB pelo fator do nível de atividade.

IMPORTANTE: são ESTIMATIVAS populacionais, para fins informativos —
não substituem avaliação de um profissional de saúde ou nutricionista.
"""

# Fatores de atividade física (multiplicadores clássicos de Harris/McArdle).
# A ordem importa: é a ordem exibida na interface.
NIVEIS_ATIVIDADE = {
    "sedentario": {
        "rotulo": "Sedentário (pouco ou nenhum exercício)",
        "fator": 1.2,
    },
    "leve": {
        "rotulo": "Leve (exercício 1-3x por semana)",
        "fator": 1.375,
    },
    "moderado": {
        "rotulo": "Moderado (exercício 3-5x por semana)",
        "fator": 1.55,
    },
    "intenso": {
        "rotulo": "Intenso (exercício 6-7x por semana)",
        "fator": 1.725,
    },
    "muito_intenso": {
        "rotulo": "Muito intenso (treino pesado diário ou trabalho físico)",
        "fator": 1.9,
    },
}

SEXOS_VALIDOS = ("feminino", "masculino")


def calcular_tmb(peso_kg, altura_cm, idade, sexo):
    """
    Taxa Metabólica Basal (kcal/dia) pela equação de Mifflin-St Jeor:
    a energia mínima que o corpo gasta em repouso absoluto.

    Devolve None se algum dado estiver faltando ou inválido — quem chama
    decide o que mostrar (ex.: "preencha seus dados").
    """
    try:
        peso_kg = float(peso_kg)
        altura_cm = float(altura_cm)
        idade = int(idade)
    except (TypeError, ValueError):
        return None

    if peso_kg <= 0 or altura_cm <= 0 or idade <= 0:
        return None
    if sexo not in SEXOS_VALIDOS:
        return None

    base = 10 * peso_kg + 6.25 * altura_cm - 5 * idade
    ajuste = 5 if sexo == "masculino" else -161
    return round(base + ajuste)


def calcular_gasto_diario(tmb, nivel_atividade):
    """
    Gasto energético diário estimado (kcal/dia): TMB x fator de atividade.
    Devolve None se a TMB for None ou o nível for desconhecido.
    """
    if tmb is None:
        return None
    nivel = NIVEIS_ATIVIDADE.get(nivel_atividade)
    if nivel is None:
        return None
    return round(tmb * nivel["fator"])


def resumo_energetico(usuario):
    """
    Atalho: recebe o dicionário do usuário (usuario.json) e devolve
    (tmb, gasto_diario) — qualquer um pode ser None se faltar dado.
    """
    tmb = calcular_tmb(
        usuario.get("peso_kg"),
        usuario.get("altura_cm"),
        usuario.get("idade"),
        usuario.get("sexo"),
    )
    gasto = calcular_gasto_diario(tmb, usuario.get("nivel_atividade"))
    return tmb, gasto