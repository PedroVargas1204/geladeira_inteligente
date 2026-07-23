"""
inventario.py
=============
O miolo do produto. Cuida do estoque:
- busca tolerante de alimentos no catálogo;
- cálculo da validade de cada item;
- cadastro e listagem (ordenada por validade);
- mover itens para o histórico quando consumidos ou descartados,
  agora com suporte a CONSUMO PARCIAL (consumir só parte da quantidade).

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
# CONSUMIR / DESCARTAR  -> move para o histórico (com consumo parcial)
# ---------------------------------------------------------------------------
def calcular_movimento(quantidade_item, quantidade_pedida):
    """
    Decide se um consumo/descarte é TOTAL ou PARCIAL. Função pura: não toca
    em listas nem no banco, só faz a conta.

    Devolve (quantidade_movida, mover_tudo, resto).

    Existe para que a regra do consumo parcial fique em UM lugar só, usada
    tanto pela versão em memória (_mover_para_historico) quanto pelas
    gravações pontuais no banco (operacoes.py).
    """
    if quantidade_pedida is None or quantidade_pedida >= quantidade_item:
        return quantidade_item, True, 0.0
    # round evita sobras feias de float (ex.: 0.30000000000000004).
    return quantidade_pedida, False, round(quantidade_item - quantidade_pedida, 4)


def _mover_para_historico(inventario, historico, indice, status, base,
                          quantidade=None):
    """
    Move (total ou parcialmente) o item da posição `indice` para o histórico.

    - Se `quantidade` for None ou >= a quantidade do item: move o item INTEIRO
      e o remove do inventário (comportamento antigo).
    - Se `quantidade` for menor: registra no histórico apenas a parte usada
      e REDUZ a quantidade do item, que continua no inventário (consumo parcial).

    O histórico guarda sempre a quantidade efetivamente movida, então o cálculo
    de impacto continua correto automaticamente.
    """
    item = inventario[indice]
    qtd_total = item["quantidade"]

    # Decide se é movimento total ou parcial (regra única, ver acima).
    quantidade_movida, mover_tudo, resto = calcular_movimento(
        qtd_total, quantidade
    )

    # Descobre a categoria pelo catálogo (para o impacto agregar depois).
    _, dados = buscar_alimento_por_nome(item["nome"], base)
    categoria = dados["categoria"] if dados else "Outros"

    registro = {
        "nome": item["nome"],
        "quantidade": quantidade_movida,
        "unidade": item["unidade"],
        "categoria": categoria,
        "status": status,
        "data": datetime.now().strftime("%Y-%m-%d"),
    }
    historico.append(registro)

    if mover_tudo:
        inventario.pop(indice)  # remove o item inteiro
    else:
        item["quantidade"] = resto

    return inventario, historico


def marcar_consumido(inventario, historico, indice, base, quantidade=None):
    """Marca como consumido. Se `quantidade` vier, consome só essa parte."""
    return _mover_para_historico(inventario, historico, indice, "consumido",
                                 base, quantidade)


def marcar_descartado(inventario, historico, indice, base, quantidade=None):
    """Marca como descartado. Se `quantidade` vier, descarta só essa parte."""
    return _mover_para_historico(inventario, historico, indice, "descartado",
                                 base, quantidade)