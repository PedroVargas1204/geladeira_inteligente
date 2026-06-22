"""
test_basico.py
==============
Testes automatizados das funções "puras" do projeto (as que só calculam,
sem mexer em disco nem em tela). Servem de REDE DE SEGURANÇA: toda vez que
você alterar o código, rode estes testes para descobrir na hora se algo
quebrou — exatamente o tipo de coisa que pegaria o bug do co2_total.

COMO RODAR:
    Opção 1 (recomendada): instale o pytest uma vez e rode
        pip install pytest
        pytest -v
    Opção 2 (sem instalar nada): rode direto com o Python
        python test_basico.py

    Em ambos os casos, rode de DENTRO da pasta do projeto (onde estão os
    módulos config.py, impacto.py, etc.), para os imports funcionarem.
"""

from datetime import datetime, timedelta

import config
import impacto
import inventario as inv
import alertas
import ia
import persistencia


# ===========================================================================
# impacto.converter_para_kg  — conversão de unidades para kg
# ===========================================================================
def test_kg_fica_igual():
    assert impacto.converter_para_kg(2, "kg") == 2


def test_grama_divide_por_mil():
    assert impacto.converter_para_kg(500, "g") == 0.5


def test_litro_tratado_como_kg():
    assert impacto.converter_para_kg(1.5, "l") == 1.5


def test_mililitro_divide_por_mil():
    assert impacto.converter_para_kg(250, "ml") == 0.25


def test_unidade_usa_peso_medio():
    # config.PESO_UNIDADE_KG vale 0.2; 3 unidades = 0.6 kg.
    esperado = 3 * config.PESO_UNIDADE_KG
    assert impacto.converter_para_kg(3, "unid") == esperado


def test_unidade_aceita_sinonimos():
    # "un" e "unidade" devem se comportar como "unid".
    assert impacto.converter_para_kg(1, "un") == config.PESO_UNIDADE_KG
    assert impacto.converter_para_kg(1, "unidade") == config.PESO_UNIDADE_KG


def test_maiusculas_funcionam():
    # A função faz .lower(), então "KG" deve valer como "kg".
    assert impacto.converter_para_kg(2, "KG") == 2


# ===========================================================================
# impacto.taxa_aproveitamento  — consumidos / (consumidos + descartados)
# ===========================================================================
def test_taxa_historico_vazio_eh_zero():
    # Sem histórico, deve devolver 0.0 (e NÃO quebrar com divisão por zero).
    assert impacto.taxa_aproveitamento([]) == 0.0


def test_taxa_tudo_consumido_eh_um():
    historico = [
        {"status": "consumido"},
        {"status": "consumido"},
    ]
    assert impacto.taxa_aproveitamento(historico) == 1.0


def test_taxa_meio_a_meio():
    historico = [
        {"status": "consumido"},
        {"status": "descartado"},
    ]
    assert impacto.taxa_aproveitamento(historico) == 0.5


# ===========================================================================
# impacto.agregar_por_categoria  — conta consumidos por categoria
# ===========================================================================
def test_agregar_ignora_descartados():
    historico = [
        {"status": "consumido", "categoria": "Frutas"},
        {"status": "consumido", "categoria": "Frutas"},
        {"status": "descartado", "categoria": "Frutas"},  # NÃO deve contar
        {"status": "consumido", "categoria": "Vegetais"},
    ]
    contagem = impacto.agregar_por_categoria(historico)
    assert contagem == {"Frutas": 2, "Vegetais": 1}


def test_agregar_historico_vazio():
    assert impacto.agregar_por_categoria([]) == {}


# ===========================================================================
# impacto.calcular_impacto  — soma de impacto (o que quebrou com o co2_total!)
# ===========================================================================
def test_calcular_impacto_vazio_devolve_zeros():
    # Garante que a função inicializa os totais e não dá UnboundLocalError.
    resultado = impacto.calcular_impacto([], {})
    assert resultado == (0.0, 0.0, 0.0, 0.0)


def test_calcular_impacto_soma_consumido():
    base = {
        "tomate": {"co2_kg": 2.0, "agua_litros_kg": 200, "preco_kg": 5.0,
                   "categoria": "Vegetais"},
    }
    historico = [
        {"nome": "tomate", "quantidade": 1, "unidade": "kg",
         "status": "consumido"},
    ]
    kg, co2, agua, reais = impacto.calcular_impacto(historico, base)
    assert kg == 1.0
    assert co2 == 2.0
    assert agua == 200
    assert reais == 5.0


def test_calcular_impacto_ignora_descartado():
    base = {
        "tomate": {"co2_kg": 2.0, "agua_litros_kg": 200, "preco_kg": 5.0,
                   "categoria": "Vegetais"},
    }
    historico = [
        {"nome": "tomate", "quantidade": 1, "unidade": "kg",
         "status": "descartado"},  # descartado não entra na economia
    ]
    assert impacto.calcular_impacto(historico, base) == (0.0, 0.0, 0.0, 0.0)


# ===========================================================================
# alertas.dias_para_vencer  — diferença de dias entre hoje e a validade
# ===========================================================================
def test_dias_para_vencer_futuro():
    # Uma data 5 dias à frente deve devolver 5 (usamos um "hoje" fixo).
    hoje = datetime(2026, 1, 1)
    validade = (hoje + timedelta(days=5)).strftime("%Y-%m-%d")
    assert alertas.dias_para_vencer(validade, hoje) == 5


def test_dias_para_vencer_passado_eh_negativo():
    hoje = datetime(2026, 1, 10)
    validade = (hoje - timedelta(days=3)).strftime("%Y-%m-%d")
    assert alertas.dias_para_vencer(validade, hoje) == -3


# ===========================================================================
# alertas.calcular_alertas  — só itens que vencem em DIAS_ALERTA ou menos
# ===========================================================================
def test_alertas_filtra_e_ordena():
    hoje = datetime(2026, 1, 1)
    inventario = [
        {"nome": "longe",  "data_validade": (hoje + timedelta(days=30)).strftime("%Y-%m-%d")},
        {"nome": "urgente","data_validade": (hoje + timedelta(days=1)).strftime("%Y-%m-%d")},
        {"nome": "hoje",   "data_validade": hoje.strftime("%Y-%m-%d")},
    ]
    resultado = alertas.calcular_alertas(inventario, config.DIAS_ALERTA, hoje)
    # "longe" (30 dias) não entra; sobram 2, ordenados por urgência.
    nomes = [item["nome"] for (item, dias) in resultado]
    assert nomes == ["hoje", "urgente"]


# ===========================================================================
# inventario.sugerir_validade  — data_compra + durabilidade do local
# ===========================================================================
def test_sugerir_validade_soma_dias_do_local():
    dados = {"validade_dias": {"geladeira": 7, "despensa": 30, "freezer": 90}}
    # Compra em 01/01/2026, na geladeira (7 dias) -> vence em 08/01/2026.
    assert inv.sugerir_validade("2026-01-01", dados, "geladeira") == "2026-01-08"


def test_sugerir_validade_local_desconhecido_zero_dias():
    # Local sem durabilidade cadastrada usa 0 -> vence no mesmo dia.
    dados = {"validade_dias": {"geladeira": 7}}
    assert inv.sugerir_validade("2026-01-01", dados, "freezer") == "2026-01-01"


# ===========================================================================
# inventario.buscar_alimento_por_nome  — busca tolerante no catálogo
# ===========================================================================
def test_busca_exata():
    base = {"tomate": {"categoria": "Vegetais"}}
    chave, dados = inv.buscar_alimento_por_nome("tomate", base)
    assert chave == "tomate"
    assert dados is not None


def test_busca_ignora_maiusculas_e_espacos():
    base = {"tomate": {"categoria": "Vegetais"}}
    chave, dados = inv.buscar_alimento_por_nome("  Tomate  ", base)
    assert chave == "tomate"


def test_busca_por_substring():
    base = {"tomate": {"categoria": "Vegetais"}}
    # "tomate cereja" contém "tomate" -> deve encontrar.
    chave, dados = inv.buscar_alimento_por_nome("tomate cereja", base)
    assert chave == "tomate"


def test_busca_nao_encontrada_devolve_none():
    base = {"tomate": {"categoria": "Vegetais"}}
    chave, dados = inv.buscar_alimento_por_nome("abacaxi", base)
    assert chave is None
    assert dados is None


# ===========================================================================
# ia.chave_cache  — chave estável independente da ordem dos ingredientes
# ===========================================================================
def test_chave_cache_independe_da_ordem():
    # "ovo+tomate" e "tomate+ovo" devem gerar a MESMA chave.
    a = ia.chave_cache(["ovo", "tomate"])
    b = ia.chave_cache(["tomate", "ovo"])
    assert a == b


def test_chave_cache_normaliza_maiusculas():
    assert ia.chave_cache(["Tomate"]) == ia.chave_cache(["tomate"])


# ===========================================================================
# persistencia.carregar_json  — defensiva: arquivo inexistente devolve padrão
# ===========================================================================
def test_carregar_json_inexistente_devolve_padrao():
    # Um caminho que não existe deve devolver o padrão, sem quebrar.
    assert persistencia.carregar_json("nao_existe_xyz.json", []) == []
    assert persistencia.carregar_json("nao_existe_xyz.json", {}) == {}


# ===========================================================================
# EXECUÇÃO SEM PYTEST: roda tudo com asserts e conta os resultados.
# (Permite "python test_basico.py" mesmo sem o pytest instalado.)
# ===========================================================================
if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passou = 0
    falhou = 0
    for teste in testes:
        try:
            teste()
            print(f"  ok   {teste.__name__}")
            passou += 1
        except AssertionError as e:
            print(f"  FALHOU {teste.__name__}  -> {e}")
            falhou += 1
        except Exception as e:
            print(f"  ERRO   {teste.__name__}  -> {type(e).__name__}: {e}")
            falhou += 1
    print("-" * 50)
    print(f"{passou} passaram, {falhou} falharam, de {len(testes)} testes.")