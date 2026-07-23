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
from datetime import datetime

import config
from banco import persistencia
from regras import alertas

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
    urgentes = alertas.calcular_alertas(inventario, config.DIAS_ALERTA)
    if not urgentes:
        urgentes = alertas.calcular_alertas(inventario, config.DIAS_ALERTA_AMPLO)
    if urgentes:
        return [item["nome"] for (item, dias) in urgentes]
    # Nada perto de vencer: usa tudo que tem na geladeira.
    return [item["nome"] for item in inventario]


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
    itens_txt = ", ".join(ingredientes) if ingredientes else "o que houver"

    return (
        "Você é um chef que evita desperdício de alimentos. "
        f"Tenho estes alimentos precisando ser usados logo: {itens_txt}. "
        "Crie UMA receita simples e prática que aproveite o máximo deles "
        "(pode assumir itens básicos de despensa como sal, azeite e temperos). "
        f"Restrições alimentares: {texto_restricoes}. "
        f"Tempo máximo de preparo: {tempo} minutos. "
        "Responda APENAS com um objeto JSON válido, sem nenhum texto antes "
        'ou depois, no formato: {"titulo": string, '
        '"ingredientes": [lista de strings com as quantidades], '
        '"modo_preparo": [lista de strings, um passo por item]}.'
    )


# ---------------------------------------------------------------------------
# 3) CHAMAR A IA (com segurança)
# ---------------------------------------------------------------------------
def consultar_ia(prompt):
    """
    Chama a API do Gemini. A chave vem da variável de ambiente IA_API_KEY.
    Levanta exceção se algo falhar — quem chama trata e cai no fallback.
    """
    chave = os.environ.get(config.IA_NOME_VARIAVEL_CHAVE)
    if not chave:
        raise RuntimeError("Sem chave de API (IA_API_KEY não definida).")
    if not TEM_REQUESTS:
        raise RuntimeError("Biblioteca 'requests' não instalada.")

    cabecalhos = {
        "x-goog-api-key": chave,
        "content-type": "application/json",
    }
    corpo = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 800,
            "responseMimeType": "application/json",  # resposta em JSON puro
        },
    }

    resposta = requests.post(
        config.IA_API_URL,
        headers=cabecalhos,
        json=corpo,
        timeout=config.TIMEOUT_IA,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    texto = dados["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(texto)


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
# 5) LIVRO DE RECEITAS — histórico permanente do que já foi visualizado
# ---------------------------------------------------------------------------
def registrar_no_livro(receita, origem, ingredientes, usuario_id=config.USUARIO_PADRAO_ID):
    """
    Guarda a receita no livro (data/livro_receitas.json) — um histórico
    PERMANENTE de tudo que o usuário já visualizou, para poder refazer.
    Diferente do cache, que existe só para o modo offline e sobrescreve
    por combinação de ingredientes.

    Se a mesma receita (mesmo título + mesma combinação) já estiver no
    livro, só incrementa o contador e atualiza a data da última vez.
    Nunca levanta exceção: um problema aqui não pode impedir a receita
    de chegar ao usuário.
    """
    try:
        livro = persistencia.carregar_livro(usuario_id)
        chave = chave_cache(ingredientes)
        agora = datetime.now().strftime("%Y-%m-%d %H:%M")

        for registro in livro:
            if (registro.get("titulo") == receita.get("titulo")
                    and registro.get("chave") == chave):
                registro["vezes"] = registro.get("vezes", 1) + 1
                registro["visto_em"] = agora
                persistencia.salvar_livro(livro, usuario_id)
                return

        livro.append({
            "titulo": receita.get("titulo", "Receita sem título"),
            "ingredientes": receita.get("ingredientes", []),
            "modo_preparo": receita.get("modo_preparo", []),
            "ingredientes_usados": list(ingredientes),
            "chave": chave,
            "origem": origem,
            "criada_em": agora,
            "visto_em": agora,
            "vezes": 1,
        })
        persistencia.salvar_livro(livro, usuario_id)
    except Exception as erro:
        print(f"[DEBUG] Falha ao registrar no livro: {repr(erro)}")


def listar_livro(usuario_id=config.USUARIO_PADRAO_ID):
    """Devolve todas as receitas do livro DESTE usuário (lista de dicionários)."""
    return persistencia.carregar_livro(usuario_id)


def remover_do_livro(indice, usuario_id=config.USUARIO_PADRAO_ID):
    """Remove a receita na posição `indice` do livro deste usuário e salva."""
    livro = persistencia.carregar_livro(usuario_id)
    if 0 <= indice < len(livro):
        livro.pop(indice)
        persistencia.salvar_livro(livro, usuario_id)


# ---------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL DO MÓDULO — orquestra tudo com fallback
# ---------------------------------------------------------------------------
def sugerir_receita(inventario, usuario, ingredientes=None, usuario_id=config.USUARIO_PADRAO_ID):
    """
    Devolve (receita, origem). origem indica de onde veio: "ia", "cache"
    ou "generica". O programa NUNCA trava: try/except garante o plano B.

    `ingredientes` é opcional: se vier uma lista (ex.: escolhida pelo
    usuário na interface), ela é usada como está; se vier None, mantém o
    comportamento automático de priorizar o que está perto de vencer.
    """
    if ingredientes is None:
        ingredientes = selecionar_ingredientes(inventario)
    cache = persistencia.carregar_cache()
    chave = chave_cache(ingredientes)

    # Tenta a IA primeiro.
    try:
        prompt = montar_prompt(ingredientes, usuario)
        receita = consultar_ia(prompt)
        # Deu certo: guarda no cache para uso offline futuro.
        cache[chave] = receita
        persistencia.salvar_cache(cache)
        registrar_no_livro(receita, "ia", ingredientes, usuario_id)
        return receita, "ia"
    except Exception as erro:
        # Qualquer falha (sem chave, sem internet, timeout, erro HTTP...)
        # cai aqui. O print abaixo mostra a causa no TERMINAL para ajudar
        # a depurar. (Pode remover depois que tudo estiver funcionando.)
        print(f"[DEBUG] Falha na IA: {repr(erro)}")
        # Plano B:
        if chave in cache:
            registrar_no_livro(cache[chave], "cache", ingredientes, usuario_id)
            return cache[chave], "cache"
        receita = receita_generica(ingredientes)
        registrar_no_livro(receita, "generica", ingredientes, usuario_id)
        return receita, "generica"