"""
inventario.py
=============
O miolo do produto. Cuida do estoque:
- busca tolerante de alimentos no catálogo;
- cálculo da validade de cada item;
- cadastro e listagem (ordenada por validade);
- mover itens para o histórico quando consumidos ou descartados.

Responsável (slides): Pessoa B
"""

from datetime import datetime, timedelta

import config
import persistencia


# ---------------------------------------------------------------------------
# BUSCA TOLERANTE NO CATÁLOGO
# ---------------------------------------------------------------------------
def buscar_alimento_por_nome(nome, base):
    """
    Busca TOLERANTE (slide 6): encontra o alimento mesmo que o usuário escreva
    diferente. Tenta, em ordem:
      1) chave exata ("tomate")
      2) sinônimos ("tomate italiano" -> tomate)
      3) substring ("tomate cereja maduro" contém "tomate")

    Devolve (chave, dados) ou (None, None) se não achar.
    """
    consulta = nome.strip().lower()

    # 1) tentativa direta usando a fonte única de persistencia
    dados = persistencia.buscar_alimento_na_base(consulta, base)
    if dados is not None:
        return consulta, dados

    # 2) e 3) percorre o catálogo procurando sinônimo ou substring
    for chave, dados in base.items():
        sinonimos = dados.get("sinonimos", [])
        if consulta in [s.lower() for s in sinonimos]:
            return chave, dados
        if chave in consulta or consulta in chave:
            return chave, dados

    return None, None


# ---------------------------------------------------------------------------
# CÁLCULO DE VALIDADE
# ---------------------------------------------------------------------------
def sugerir_validade(data_compra, dados_alimento, local):
    """
    Sugere a data de validade (RF03, slide 6).

    Soma à data de compra os dias de durabilidade do alimento NAQUELE local
    de armazenamento. Aritmética de datas: datetime + timedelta.

        validade = data_compra + timedelta(dias)
    """
    dias = dados_alimento["validade_dias"].get(local, 0)
    data = datetime.strptime(data_compra, "%Y-%m-%d")
    validade = data + timedelta(days=dias)
    return validade.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# CADASTRO E LISTAGEM
# ---------------------------------------------------------------------------
def adicionar_item(inventario, item):
    """Adiciona um item (dicionário) à lista do inventário."""
    inventario.append(item)
    return inventario


def listar_ordenado(inventario):
    """
    Devolve o inventário ordenado por data de validade (RF04, slide 6).
    A chave de ordenação é a própria data em texto ISO (AAAA-MM-DD), que
    ordena corretamente como string. sort + lambda.
    """
    return sorted(inventario, key=lambda item: item["data_validade"])


# ---------------------------------------------------------------------------
# CONSUMIR / DESCARTAR  -> move para o histórico
# ---------------------------------------------------------------------------
def _mover_para_historico(inventario, historico, indice, status, base):
    """
    Tira o item da posição `indice` do inventário e o adiciona ao histórico
    com o `status` ("consumido" ou "descartado") e a data de hoje.
    """
    item = inventario.pop(indice)  # remove do inventário e guarda numa variável

    # Descobre a categoria pelo catálogo (para o impacto agregar depois).
    _, dados = buscar_alimento_por_nome(item["nome"], base)
    categoria = dados["categoria"] if dados else "Outros"

    registro = {
        "nome": item["nome"],
        "quantidade": item["quantidade"],
        "unidade": item["unidade"],
        "categoria": categoria,
        "status": status,
        "data": datetime.now().strftime("%Y-%m-%d"),
    }
    historico.append(registro)
    return inventario, historico


def marcar_consumido(inventario, historico, indice, base):
    return _mover_para_historico(inventario, historico, indice, "consumido", base)


def marcar_descartado(inventario, historico, indice, base):
    return _mover_para_historico(inventario, historico, indice, "descartado", base)
