"""
auth.py
=======
Cadastro e login de usuários.

REGRA DE OURO: a senha do usuário NUNCA é guardada. O que vai para o banco
é um "hash" produzido pelo bcrypt — um resultado do qual é inviável voltar
para a senha original. No login, em vez de comparar senhas, o bcrypt refaz
a conta e compara os hashes.

Por que bcrypt e não algo como SHA-256? Porque bcrypt é PROPOSITALMENTE
lento e embute um "sal" (um valor aleatório por senha). Isso torna inúteis
as tabelas prontas de senhas comuns e deixa a força bruta cara. Duas
pessoas com a mesma senha geram hashes diferentes.

Este módulo NÃO conhece Streamlit nem terminal: só fala com o banco.
Assim ele serve às duas interfaces (e a uma API, no futuro).
"""

import bcrypt
from sqlalchemy import func, select

from banco import db


# ---------------------------------------------------------------------------
# ERRO DE NEGÓCIO
# ---------------------------------------------------------------------------
class ErroAutenticacao(Exception):
    """
    Erro previsto de cadastro/login (e-mail repetido, senha curta...).

    Existe para a interface poder mostrar a mensagem ao usuário com
    tranquilidade, sem confundir com um bug de verdade do programa.
    """


# ---------------------------------------------------------------------------
# SENHAS
# ---------------------------------------------------------------------------
# Tamanho mínimo exigido no cadastro.
SENHA_MINIMA = 8


def gerar_hash(senha):
    """Transforma a senha em um hash bcrypt (texto) pronto para o banco."""
    # bcrypt trabalha com bytes, por isso o encode/decode.
    # gensalt() cria o sal aleatório — é o que faz cada hash ser único.
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def conferir_senha(senha, senha_hash):
    """Devolve True se `senha` corresponde ao `senha_hash` guardado."""
    if not senha_hash:
        return False
    try:
        return bcrypt.checkpw(
            senha.encode("utf-8"), senha_hash.encode("utf-8")
        )
    except ValueError:
        # Hash malformado no banco: trata como senha errada, sem quebrar.
        return False


# ---------------------------------------------------------------------------
# NORMALIZAÇÃO
# ---------------------------------------------------------------------------
def normalizar_email(email):
    """
    Deixa o e-mail em minúsculas e sem espaços nas pontas.

    Sem isso, "Pedro@Email.com" e "pedro@email.com " viram duas contas
    diferentes — e o usuário jura que já se cadastrou.
    """
    return (email or "").strip().lower()


# ---------------------------------------------------------------------------
# CADASTRO
# ---------------------------------------------------------------------------
def cadastrar(email, senha, nome=""):
    """
    Cria uma conta nova e devolve o `usuario_id`.

    Levanta ErroAutenticacao se o e-mail for inválido, já estiver em uso,
    ou se a senha for curta demais.
    """
    email = normalizar_email(email)

    if "@" not in email or "." not in email:
        raise ErroAutenticacao("Informe um e-mail válido.")
    if len(senha or "") < SENHA_MINIMA:
        raise ErroAutenticacao(
            f"A senha precisa ter pelo menos {SENHA_MINIMA} caracteres."
        )

    with db.abrir_sessao() as sessao:
        if _buscar_por_email(sessao, email) is not None:
            raise ErroAutenticacao("Já existe uma conta com esse e-mail.")

        usuario = db.Usuario(
            nome=(nome or "").strip(),
            email=email,
            senha_hash=gerar_hash(senha),
        )
        sessao.add(usuario)
        sessao.commit()
        # Depois do commit o banco já atribuiu o id automático.
        return usuario.id


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------
def autenticar(email, senha):
    """
    Confere as credenciais e devolve o `usuario_id` de quem entrou.

    Levanta ErroAutenticacao se o e-mail não existir ou a senha não bater.
    A mensagem é a MESMA nos dois casos, de propósito: dizer "este e-mail
    não existe" entregaria a estranhos quais e-mails estão cadastrados.
    """
    email = normalizar_email(email)
    generico = "E-mail ou senha incorretos."

    with db.abrir_sessao() as sessao:
        usuario = _buscar_por_email(sessao, email)
        if usuario is None or not conferir_senha(senha, usuario.senha_hash):
            raise ErroAutenticacao(generico)
        return usuario.id


def trocar_senha(usuario_id, senha_atual, senha_nova):
    """Troca a senha, exigindo a atual como confirmação."""
    if len(senha_nova or "") < SENHA_MINIMA:
        raise ErroAutenticacao(
            f"A senha precisa ter pelo menos {SENHA_MINIMA} caracteres."
        )

    with db.abrir_sessao() as sessao:
        usuario = sessao.get(db.Usuario, usuario_id)
        if usuario is None or not conferir_senha(senha_atual, usuario.senha_hash):
            raise ErroAutenticacao("Senha atual incorreta.")
        usuario.senha_hash = gerar_hash(senha_nova)
        sessao.commit()


# ---------------------------------------------------------------------------
# CONSULTAS AUXILIARES
# ---------------------------------------------------------------------------
def _buscar_por_email(sessao, email):
    """Busca o usuário pelo e-mail (já normalizado). Uso interno."""
    return sessao.scalars(
        select(db.Usuario).where(db.Usuario.email == email)
    ).first()


def dados_da_conta(usuario_id):
    """Devolve {"id", "nome", "email"} de quem está logado, ou None."""
    with db.abrir_sessao() as sessao:
        usuario = sessao.get(db.Usuario, usuario_id)
        if usuario is None:
            return None
        return {"id": usuario.id, "nome": usuario.nome, "email": usuario.email}


def conta_legada_id():
    """
    Devolve o id da conta ANTIGA (a que existia antes do login), ou None.

    Contexto: até agora o app era de um usuário só, gravando tudo no id 1
    sem e-mail nem senha. Quando o login entra em cena, esses dados ficariam
    órfãos — ninguém conseguiria acessá-los. Esta função encontra essa conta
    para que a interface possa oferecer: "defina um e-mail e uma senha e
    continue com o seu inventário de sempre".

    Só considera contas sem e-mail (ou seja, sem login configurado).
    """
    with db.abrir_sessao() as sessao:
        usuario = sessao.scalars(
            select(db.Usuario)
            .where(db.Usuario.email.is_(None))
            .order_by(db.Usuario.id)
        ).first()
        return usuario.id if usuario else None


def definir_credenciais(usuario_id, email, senha, nome=""):
    """
    Dá e-mail e senha a uma conta que ainda não tinha login, preservando
    todos os dados dela (inventário, histórico, receitas).

    Recusa se a conta já tiver credenciais — trocar senha é trabalho do
    trocar_senha(), que exige a senha atual.
    """
    email = normalizar_email(email)

    if "@" not in email or "." not in email:
        raise ErroAutenticacao("Informe um e-mail válido.")
    if len(senha or "") < SENHA_MINIMA:
        raise ErroAutenticacao(
            f"A senha precisa ter pelo menos {SENHA_MINIMA} caracteres."
        )

    with db.abrir_sessao() as sessao:
        usuario = sessao.get(db.Usuario, usuario_id)
        if usuario is None:
            raise ErroAutenticacao("Conta não encontrada.")
        if usuario.email:
            raise ErroAutenticacao("Esta conta já tem login configurado.")
        if _buscar_por_email(sessao, email) is not None:
            raise ErroAutenticacao("Já existe uma conta com esse e-mail.")

        usuario.email = email
        usuario.senha_hash = gerar_hash(senha)
        if nome.strip():
            usuario.nome = nome.strip()
        sessao.commit()
        return usuario.id


def existe_alguma_conta():
    """
    Diz se já existe pelo menos uma conta COM login (e-mail preenchido).

    Serve para a interface saber se mostra a tela de login ou convida a
    criar a primeira conta.
    """
    with db.abrir_sessao() as sessao:
        total = sessao.scalar(
            select(func.count())
            .select_from(db.Usuario)
            .where(db.Usuario.email.is_not(None))
        )
        return bool(total)