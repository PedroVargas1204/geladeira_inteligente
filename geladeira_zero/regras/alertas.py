"""
alertas.py
==========
Gera os alertas de vencimento (RF05, slide 6). Olha o inventário e descobre
quais itens vencem em DIAS_ALERTA dias ou menos.


"""

from datetime import datetime

import config


def _normalizar_data(referencia):
    """Devolve `referencia` como date, sem a hora; None vira a data de hoje.

    datetime é subclasse de date, por isso é verificado primeiro.
    """
    if referencia is None:
        return config.hoje()
    if isinstance(referencia, datetime):
        return referencia.date()
    return referencia


def dias_para_vencer(data_validade, hoje=None):
    """Dias até a validade: 0 = vence hoje, 1 = amanhã, negativo = vencido.

    Compara só datas de calendário; se `hoje` for datetime, a hora é ignorada.
    """
    hoje = _normalizar_data(hoje)
    validade = datetime.strptime(data_validade, "%Y-%m-%d").date()
    return (validade - hoje).days


def calcular_alertas(inventario, dias_alerta=config.DIAS_ALERTA, hoje=None):
    """
    Retorna uma lista de tuplas (item, dias) dos itens que vencem em
    `dias_alerta` dias ou menos — inclusive os já vencidos.

    A lista é ordenada por urgência: quem vence antes aparece primeiro
    (slide 6). sort + lambda na chave `dias`.
    """
    hoje = _normalizar_data(hoje)

    alertas = []
    for item in inventario:
        dias = dias_para_vencer(item["data_validade"], hoje)
        if dias <= dias_alerta:
            alertas.append((item, dias))  # guarda a TUPLA (item, dias)

    alertas.sort(key=lambda par: par[1])  # par[1] é o número de dias
    return alertas
