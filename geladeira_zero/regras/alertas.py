"""
alertas.py
==========
Gera os alertas de vencimento (RF05, slide 6). Olha o inventário e descobre
quais itens vencem em DIAS_ALERTA dias ou menos.

Responsável (slides): Pessoa B
"""

from datetime import datetime

import config


def dias_para_vencer(data_validade, hoje=None):
    """
    Quantos dias faltam até a validade. Pode ser negativo (já venceu).
    Subtração de datas devolve um timedelta; .days pega o número de dias.
    """
    if hoje is None:
        hoje = datetime.now()
    validade = datetime.strptime(data_validade, "%Y-%m-%d")
    return (validade - hoje).days


def calcular_alertas(inventario, dias_alerta=config.DIAS_ALERTA, hoje=None):
    """
    Retorna uma lista de tuplas (item, dias) dos itens que vencem em
    `dias_alerta` dias ou menos — inclusive os já vencidos.

    A lista é ordenada por urgência: quem vence antes aparece primeiro
    (slide 6). sort + lambda na chave `dias`.
    """
    if hoje is None:
        hoje = datetime.now()

    alertas = []
    for item in inventario:
        dias = dias_para_vencer(item["data_validade"], hoje)
        if dias <= dias_alerta:
            alertas.append((item, dias))  # guarda a TUPLA (item, dias)

    alertas.sort(key=lambda par: par[1])  # par[1] é o número de dias
    return alertas
