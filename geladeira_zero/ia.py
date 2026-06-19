"""
ia.py
=====
A camada criativa (RF06) + plano B (RNF05). Pega o que está para vencer,
monta um pedido para a IA, chama a API com segurança e SEMPRE devolve uma
receita — mesmo sem internet ou sem chave de API.

Responsável (slides): Pessoa C
"""

import os
import json

import config
import persistencia
import alertas

# requests é uma biblioteca externa (HTTP). Importamos com try para o
# programa não quebrar caso ela não esteja instalada — cairíamos no fallback.
try:
    import requests
    TEM_REQUESTS = True
except ImportError:
    TEM_REQUESTS = False


# ---------------------------------------------------------------------------
# 1) ESCOLHER OS INGREDIENTES
# ---------------------------------------------------------------------------
def selecionar_ingredientes(inventario):
    """
    Escolhe quais ingredientes usar na receita (slide 7).

    Reaproveita calcular_alertas() para pegar primeiro o que vence antes.
    Se não houver itens urgentes, amplia a janela (DIAS_ALERTA_AMPLO).
    """
    urgentes = alertas.calcular_alertas(inventario, config.DIAS_ALERTA)
    if not urgentes:
        urgentes = alertas.calcular_alertas(inventario, config.DIAS_ALERTA_AMPLO)

    # Pega só os nomes dos itens (descartando o número de dias da tupla).
    return [item["nome"] for (item, dias) in urgentes]


# ---------------------------------------------------------------------------
# 2) MONTAR O PEDIDO (PROMPT)
# ---------------------------------------------------------------------------
def montar_prompt(ingredientes, usuario):
    """
    Monta o texto enviado à IA: ingredientes + restrições do usuário
    (vegetariano, vegano, alergias, tempo máximo). (slide 7)
    """
    restricoes = []
    if usuario.get("vegetariano"):
        restricoes.append("vegetariana")
    if usuario.get("vegano"):
        restricoes.append("vegana")
    if usuario.get("alergias"):
        restricoes.append("sem " + ", sem ".join(usuario["alergias"]))

    texto_restricoes = "; ".join(restricoes) if restricoes else "nenhuma"
    tempo = usuario.get("tempo_max_receita", 60)

    return (
        "Você é um chef que evita desperdício. Crie UMA receita simples usando "
        f"prioritariamente estes ingredientes: {', '.join(ingredientes)}. "
        f"Restrições: {texto_restricoes}. Tempo máximo: {tempo} minutos. "
        "Responda em JSON com as chaves: titulo (string), "
        "ingredientes (lista de strings) e modo_preparo (lista de strings)."
    )


# ---------------------------------------------------------------------------
# 3) CHAMAR A IA (com segurança)
# ---------------------------------------------------------------------------
def consultar_ia(prompt):
    """
    Chama a API da IA. A chave vem da variável de ambiente IA_API_KEY
    (senha FORA do código). Tem timeout para não travar para sempre.

    Levanta uma exceção se algo falhar — quem chama trata e cai no fallback.
    """
    chave = os.environ.get(config.IA_NOME_VARIAVEL_CHAVE)
    if not chave:
        raise RuntimeError("Sem chave de API (IA_API_KEY não definida).")
    if not TEM_REQUESTS:
        raise RuntimeError("Biblioteca 'requests' não instalada.")

    cabecalhos = {
        "x-api-key": chave,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    corpo = {
        "model": config.IA_MODEL,
        "max_tokens": 800,
        "messages": [{"role": "user", "content": prompt}],
    }

    resposta = requests.post(
        config.IA_API_URL,
        headers=cabecalhos,
        json=corpo,
        timeout=config.TIMEOUT_IA,  # desiste após N segundos
    )
    resposta.raise_for_status()             # erro HTTP vira exceção
    dados = resposta.json()
    texto = dados["content"][0]["text"]     # extrai o texto da resposta
    return json.loads(texto)                # converte o JSON da receita


# ---------------------------------------------------------------------------
# 4) PLANO B (FALLBACK) — cache local ou receita genérica
# ---------------------------------------------------------------------------
def chave_cache(ingredientes):
    """
    Gera uma chave estável para o cache. Ordena os ingredientes para que
    "ovo+tomate" e "tomate+ovo" virem a MESMA chave (slide 7).
    """
    return "+".join(sorted(i.lower() for i in ingredientes))


def receita_generica(ingredientes):
    """Último recurso: uma receita que sempre funciona, sem depender de nada."""
    lista = ingredientes if ingredientes else ["o que você tiver"]
    return {
        "titulo": "Refogado de aproveitamento",
        "ingredientes": lista + ["sal", "azeite", "temperos a gosto"],
        "modo_preparo": [
            "Lave e corte os ingredientes em pedaços pequenos.",
            "Aqueça um fio de azeite em uma panela.",
            "Refogue os ingredientes começando pelos mais firmes.",
            "Tempere com sal e seus temperos preferidos.",
            "Cozinhe até ficar macio e sirva.",
        ],
    }


# ---------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL DO MÓDULO — orquestra tudo com fallback
# ---------------------------------------------------------------------------
def sugerir_receita(inventario, usuario):
    """
    Devolve (receita, origem). origem indica de onde veio: "ia", "cache"
    ou "generica". O programa NUNCA trava: try/except garante o plano B.
    """
    ingredientes = selecionar_ingredientes(inventario)
    cache = persistencia.carregar_json(config.ARQ_RECEITAS_CACHE, {})
    chave = chave_cache(ingredientes)

    # Tenta a IA primeiro.
    try:
        prompt = montar_prompt(ingredientes, usuario)
        receita = consultar_ia(prompt)
        # Deu certo: guarda no cache para uso offline futuro.
        cache[chave] = receita
        persistencia.salvar_json(config.ARQ_RECEITAS_CACHE, cache)
        return receita, "ia"
    except Exception:
        # Qualquer falha (sem chave, sem internet, timeout, erro HTTP...)
        # cai aqui. Plano B:
        if chave in cache:
            return cache[chave], "cache"
        return receita_generica(ingredientes), "generica"
