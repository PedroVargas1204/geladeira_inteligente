"""
login_ui.py
===========
As telas de login e cadastro do Streamlit, isoladas do resto da interface.

Por que um módulo separado? Porque o streamlit_app.py já é grande, e o
login tem uma responsabilidade bem delimitada: descobrir QUEM está usando
o app. Depois que ele responde essa pergunta, o resto da interface segue
igual — só passando o usuario_id adiante.

Como a sessão funciona no Streamlit: o script inteiro roda de novo a cada
clique. O que sobrevive entre execuções é o `st.session_state`, um
dicionário por aba do navegador. É lá que guardamos o usuario_id de quem
entrou. Fechar a aba encerra a sessão.
"""

import streamlit as st

import auth


# Chave usada no st.session_state. Constante para não errar de digitação.
CHAVE_SESSAO = "usuario_id"


# ---------------------------------------------------------------------------
# ESTADO DA SESSÃO
# ---------------------------------------------------------------------------
def usuario_logado():
    """Devolve o id de quem está logado nesta sessão, ou None."""
    return st.session_state.get(CHAVE_SESSAO)


def entrar(usuario_id):
    """Marca a sessão como autenticada e recarrega a página."""
    st.session_state[CHAVE_SESSAO] = usuario_id
    st.rerun()


def sair():
    """
    Encerra a sessão.

    Limpa TUDO do session_state, não só o usuario_id: coisas como a última
    receita gerada ou a página aberta pertencem ao usuário anterior e não
    podem vazar para quem entrar depois na mesma aba.
    """
    st.session_state.clear()
    st.rerun()


# ---------------------------------------------------------------------------
# TELA DE ENTRADA
# ---------------------------------------------------------------------------
def exigir_login():
    """
    Porteiro do app.

    Se já houver alguém logado, devolve o usuario_id e o app segue normal.
    Se não, desenha a tela de login/cadastro e INTERROMPE a execução com
    st.stop() — assim nenhuma parte do app protegido chega a rodar.
    """
    usuario_id = usuario_logado()
    if usuario_id is not None:
        return usuario_id

    _desenhar_tela()
    st.stop()


def _desenhar_tela():
    """Desenha o formulário de entrada centralizado na página."""
    # Três colunas: a do meio segura o formulário, as laterais são margem.
    _, meio, _ = st.columns([1, 2, 1])

    with meio:
        st.title("🧊 Geladeira Zero")
        st.caption("Entre na sua conta para ver a sua geladeira.")

        legada = auth.conta_legada_id() if not auth.existe_alguma_conta() else None
        if legada is not None:
            # Primeira vez com login: existe um inventário antigo esperando dono.
            _aba_ativar_conta(legada)
            return

        aba_entrar, aba_criar = st.tabs(["Entrar", "Criar conta"])
        with aba_entrar:
            _formulario_entrar()
        with aba_criar:
            _formulario_criar()


def _formulario_entrar():
    """Formulário de login de quem já tem conta."""
    # st.form agrupa os campos: nada é reprocessado até clicar no botão,
    # e o Enter dentro do campo já envia.
    with st.form("form_entrar"):
        email = st.text_input("E-mail", placeholder="voce@email.com")
        senha = st.text_input("Senha", type="password")
        enviou = st.form_submit_button("Entrar", use_container_width=True)

    if enviou:
        try:
            entrar(auth.autenticar(email, senha))
        except auth.ErroAutenticacao as erro:
            st.error(str(erro))


def _formulario_criar():
    """Formulário de cadastro de uma conta nova (geladeira vazia)."""
    with st.form("form_criar"):
        nome = st.text_input("Como quer ser chamado?", placeholder="Seu nome")
        email = st.text_input("E-mail", placeholder="voce@email.com")
        senha = st.text_input(
            "Senha", type="password",
            help=f"Mínimo de {auth.SENHA_MINIMA} caracteres.",
        )
        repetir = st.text_input("Repita a senha", type="password")
        enviou = st.form_submit_button("Criar conta", use_container_width=True)

    if enviou:
        if senha != repetir:
            st.error("As senhas não são iguais.")
            return
        try:
            usuario_id = auth.cadastrar(email, senha, nome)
        except auth.ErroAutenticacao as erro:
            st.error(str(erro))
            return
        st.session_state["flash"] = ("Conta criada. Bem-vindo!", "🎉")
        entrar(usuario_id)


def _aba_ativar_conta(usuario_id):
    """
    Tela mostrada UMA única vez: quando o app ganha login mas já existe
    um inventário do tempo em que ele era de usuário único.
    """
    st.info(
        "Encontramos os dados que você já usava neste computador. "
        "Defina um e-mail e uma senha para continuar com eles."
    )

    with st.form("form_ativar"):
        nome = st.text_input("Como quer ser chamado?", placeholder="Seu nome")
        email = st.text_input("E-mail", placeholder="voce@email.com")
        senha = st.text_input(
            "Senha", type="password",
            help=f"Mínimo de {auth.SENHA_MINIMA} caracteres.",
        )
        repetir = st.text_input("Repita a senha", type="password")
        enviou = st.form_submit_button(
            "Ativar minha conta", use_container_width=True
        )

    if enviou:
        if senha != repetir:
            st.error("As senhas não são iguais.")
            return
        try:
            auth.definir_credenciais(usuario_id, email, senha, nome)
        except auth.ErroAutenticacao as erro:
            st.error(str(erro))
            return
        st.session_state["flash"] = ("Conta ativada. Seus dados continuam aqui!", "✅")
        entrar(usuario_id)


# ---------------------------------------------------------------------------
# BLOCO DA BARRA LATERAL
# ---------------------------------------------------------------------------
def bloco_conta(usuario_id):
    """
    Mostra quem está logado e o botão de sair. Chamar dentro do
    `with st.sidebar:` do app.
    """
    conta = auth.dados_da_conta(usuario_id) or {}
    st.caption(conta.get("email", ""))
    if st.button("Sair", use_container_width=True):
        sair()