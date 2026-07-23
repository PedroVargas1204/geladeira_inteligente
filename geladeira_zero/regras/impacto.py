"""
impacto.py
==========
A partir do histórico de itens CONSUMIDOS (aproveitados no prazo), calcula:
- quanto alimento foi salvo (kg);
- CO₂ evitado;
- água economizada;
- dinheiro poupado (R$).
Também agrega por categoria e calcula a taxa de aproveitamento. (RF08 + RF09)

Responsável (slides): Pessoa D
"""

import config
from banco import persistencia


# ---------------------------------------------------------------------------
# CONVERSÃO DE UNIDADES
# ---------------------------------------------------------------------------
def converter_para_kg(quantidade, unidade):
    """
    Uniformiza tudo para kg antes de somar (slide 8).
      kg   -> já está
      g    -> divide por 1000
      l/ml -> tratamos como ~kg (1 litro ≈ 1 kg, simplificação)
      unid -> multiplica pelo peso médio (config.PESO_UNIDADE_KG)
    """
    unidade = unidade.lower()
    if unidade == "kg":
        return quantidade
    if unidade == "g":
        return quantidade / 1000
    if unidade == "l":
        return quantidade
    if unidade == "ml":
        return quantidade / 1000
    if unidade in ("unid", "unidade", "un"):
        return quantidade * config.PESO_UNIDADE_KG
    return quantidade  # desconhecida: assume kg


# ---------------------------------------------------------------------------
# CÁLCULO PRINCIPAL — retorno múltiplo (tupla)
# ---------------------------------------------------------------------------
def calcular_impacto(historico, base):
    """
    Soma o impacto dos itens CONSUMIDOS. Devolve uma TUPLA com 4 valores:
        (kg_total, co2_total, agua_total, reais_total)
    """
    kg_total = 0.0
    co2_total = 0.0
    agua_total = 0.0
    reais_total = 0.0

    for registro in historico:
        if registro.get("status") != "consumido":
            continue

        kg = converter_para_kg(registro["quantidade"], registro["unidade"])
        dados = persistencia.buscar_alimento_na_base(registro["nome"], base)
        if dados is None:
            continue

        kg_total    += kg
        co2_total   += kg * dados.get("co2_kg", 0)
        agua_total  += kg * dados.get("agua_litros_kg", 0)
        reais_total += kg * dados.get("preco_kg", 0)

    return kg_total, co2_total, agua_total, reais_total


# ---------------------------------------------------------------------------
# AGREGAÇÃO POR CATEGORIA  — padrão dict.get(cat, 0) + 1
# ---------------------------------------------------------------------------
def agregar_por_categoria(historico):
    """
    Conta quantos itens consumidos há por categoria (slide 8).
    Usa o padrão clássico: contagem[cat] = contagem.get(cat, 0) + 1
    """
    contagem = {}
    for registro in historico:
        if registro.get("status") != "consumido":
            continue
        cat = registro.get("categoria", "Outros")
        contagem[cat] = contagem.get(cat, 0) + 1
    return contagem


def taxa_aproveitamento(historico):
    """
    Fração aproveitada: consumidos / (consumidos + descartados).
    Devolve 0.0 se ainda não houver histórico (evita divisão por zero).
    """
    consumidos  = sum(1 for r in historico if r.get("status") == "consumido")
    descartados = sum(1 for r in historico if r.get("status") == "descartado")
    total = consumidos + descartados
    if total == 0:
        return 0.0
    return consumidos / total


# ---------------------------------------------------------------------------
# "GRÁFICO" DE BARRAS EM TEXTO
# ---------------------------------------------------------------------------
def grafico_barras(contagem):
    """
    Monta linhas de um gráfico de barras com '#', do maior para o menor
    (slide 8). Devolve uma lista de strings para a interface imprimir.
    """
    if not contagem:
        return ["(sem dados ainda)"]

    # Ordena por valor (decrescente). sorted + lambda + reverse.
    itens = sorted(contagem.items(), key=lambda par: par[1], reverse=True)

    linhas = []
    for categoria, qtd in itens:
        barra = "#" * qtd
        linhas.append(f"{categoria:<14} {barra} {qtd}")
    return linhas
