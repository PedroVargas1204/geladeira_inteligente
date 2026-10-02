"""
config.py
=========
Centraliza TODAS as constantes do projeto (os "números mágicos") e os
caminhos dos arquivos de dados. Nenhum outro módulo deve inventar esses
valores: todos importam daqui. Assim, mudar uma regra é mudar UM lugar só.


"""

import os
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# CAMINHOS (paths)
# ---------------------------------------------------------------------------
# __file__ é o caminho deste próprio arquivo (config.py).
# os.path.dirname() pega só a PASTA onde ele está.
# Resultado: PASTA_BASE aponta para a pasta do projeto, não importa de onde
# o programa for executado. (Slide 4: "PASTA_DADOS é relativa ao próprio arquivo")
PASTA_BASE = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA_BASE, "data")

# O BANCO DE DADOS (SQLite): um único arquivo com todas as tabelas.
ARQ_BANCO = os.path.join(PASTA_DADOS, "geladeira.db")


def url_do_banco():
    """
    Descobre a QUAL banco conectar.

    - Se a variável de ambiente DATABASE_URL existir, usa ela: é assim que
      o app em produção aponta para o PostgreSQL hospedado (Neon).
    - Se não existir, cai no SQLite local. Assim, desenvolver na sua
      máquina continua funcionando sem configurar nada.

    A senha do banco NUNCA fica no código: vive na variável de ambiente
    (ou nos "secrets" do Streamlit Cloud), fora do controle de versão.
    """
    url = os.environ.get("DATABASE_URL", "").strip()

    if not url:
        # No Streamlit Cloud os segredos também chegam por st.secrets.
        # O try protege quem roda pela CLI, sem Streamlit carregado.
        try:
            import streamlit as st

            url = str(st.secrets.get("DATABASE_URL", "")).strip()
        except Exception:
            url = ""

    if not url:
        return f"sqlite:///{ARQ_BANCO}"

    # O Neon entrega a string começando com "postgresql://". O SQLAlchemy
    # precisa saber QUAL driver usar, por isso trocamos para o psycopg 3.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)

    return url

def codigo_convite():
    """Código exigido no cadastro (CODIGO_CONVITE). Vazio = cadastro fechado."""
    codigo = os.environ.get("CODIGO_CONVITE", "").strip()
    if not codigo:
        try:
            import streamlit as st

            codigo = str(st.secrets.get("CODIGO_CONVITE", "")).strip()
        except Exception:
            codigo = ""
    return codigo

# Enquanto o app não tem login, todo dado pertence a este usuário.
# Quando o multi-usuário chegar, este valor virá da sessão de login.
USUARIO_PADRAO_ID = 1

# Catálogo do sistema (só leitura) — continua em JSON, versionado no git.
ARQ_BASE_ALIMENTOS = os.path.join(PASTA_DADOS, "base_alimentos.json")

# Caminhos dos ANTIGOS arquivos JSON de dados. Só são usados pelo script
# migrar_json_para_db.py (importação única). Depois de migrar, podem sumir.
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

# Unidades aceitas por impacto.converter_para_kg, na ordem exibida nas telas.
UNIDADES_VALIDAS = ["unid", "kg", "g", "l", "ml"]
# Quando o item é contado em "unid" (unidade), quanto pesa em kg cada um.
# Usado para converter tudo para kg antes de somar o impacto.
PESO_UNIDADE_KG = 0.2

# Período (em dias) considerado no resumo de impacto do mês.
PERIODO_IMPACTO_DIAS = 30

# Locais de armazenamento válidos.
LOCAIS_VALIDOS = ["geladeira", "despensa", "freezer"]

# Alergias são dado de saúde: desligadas na versão de teste (sem campo na
# tela e sem envio à IA). Voltam com consentimento no app de celular.
ALERGIAS_ATIVAS = False

# ---------------------------------------------------------------------------
# DATA E HORA
# ---------------------------------------------------------------------------
# Horário de Brasília (UTC−3), sem horário de verão desde 2019. Fixo porque o
# teste atual é no DF; no app de celular, o fuso passa a ser por usuário.
FUSO_BRASILIA = timezone(timedelta(hours=-3), "Brasília")


def agora():
    """Data e hora atuais em Brasília, independente do fuso do servidor."""
    return datetime.now(FUSO_BRASILIA)


def hoje():
    """Data de hoje em Brasília."""
    return agora().date()


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

# ---------------------------------------------------------------------------
# TEXTOS FIXOS
# ---------------------------------------------------------------------------
# Aparece em toda receita e no livro: a sugestão automática pode errar.
AVISO_RECEITA = ("Meu bem, essa receita é uma sugestão automática e pode errar. "
                 "Tem alergia ou restrição? Confere cada ingrediente antes de cozinhar.")

# Aparece na tela de entrada logo depois de a pessoa excluir a conta.
AVISO_CONTA_EXCLUIDA = ("Pronto, meu bem. Sua conta e todos os seus dados foram "
                        "apagados. Se quiser voltar, é só criar uma conta nova.")