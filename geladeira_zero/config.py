"""
config.py
=========
Centraliza TODAS as constantes do projeto (os "números mágicos") e os
caminhos dos arquivos de dados. Nenhum outro módulo deve inventar esses
valores: todos importam daqui. Assim, mudar uma regra é mudar UM lugar só.

Responsável (slides): Pessoa D
"""

import os

# ---------------------------------------------------------------------------
# CAMINHOS (paths)
# ---------------------------------------------------------------------------
# __file__ é o caminho deste próprio arquivo (config.py).
# os.path.dirname() pega só a PASTA onde ele está.
# Resultado: PASTA_BASE aponta para a pasta do projeto, não importa de onde
# o programa for executado. (Slide 4: "PASTA_DADOS é relativa ao próprio arquivo")
PASTA_BASE = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA_BASE, "data")

# Caminho completo de cada um dos 5 arquivos JSON.
ARQ_BASE_ALIMENTOS = os.path.join(PASTA_DADOS, "base_alimentos.json")
ARQ_INVENTARIO     = os.path.join(PASTA_DADOS, "inventario.json")
ARQ_HISTORICO      = os.path.join(PASTA_DADOS, "historico.json")
ARQ_USUARIO        = os.path.join(PASTA_DADOS, "usuario.json")
ARQ_RECEITAS_CACHE = os.path.join(PASTA_DADOS, "receitas_cache.json")
ARQ_EXPORT_CSV     = os.path.join(PASTA_DADOS, "historico_export.csv")
ARQ_LIVRO_RECEITAS = os.path.join(PASTA_DADOS, "livro_receitas.json")

# ---------------------------------------------------------------------------
# REGRAS DE NEGÓCIO (constantes)
# ---------------------------------------------------------------------------
# Quantos dias antes de vencer um item entra na lista de alertas.
DIAS_ALERTA = 3

# Janela usada quando NÃO há itens urgentes (a IA amplia a busca).
DIAS_ALERTA_AMPLO = 7

# Quantos segundos esperar pela IA antes de desistir e usar o plano B.
TIMEOUT_IA = 20

# Unidades válidas para nao quebrar
UNIDADES_VALIDAS = ["kg","g","l","ml","unid"]
# Quando o item é contado em "unid" (unidade), quanto pesa em kg cada um.
# Usado para converter tudo para kg antes de somar o impacto.
PESO_UNIDADE_KG = 0.2

# Período (em dias) considerado no resumo de impacto do mês.
PERIODO_IMPACTO_DIAS = 30

# Locais de armazenamento válidos.
LOCAIS_VALIDOS = ["geladeira", "despensa", "freezer"]

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO DA IA
# ---------------------------------------------------------------------------
# Endpoint e modelo. A CHAVE não fica aqui: vem da variável de ambiente
# IA_API_KEY (senha fora do código). Veja ia.py.
IA_MODEL   = "gemini-2.5-flash"
IA_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{IA_MODEL}:generateContent"
)
IA_NOME_VARIAVEL_CHAVE = "IA_API_KEY"
