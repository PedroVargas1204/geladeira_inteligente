"""
db.py
=====
Define o BANCO DE DADOS do projeto usando SQLAlchemy (ORM).

Por que um banco em vez dos arquivos JSON?
- JSON: cada gravação reescreve o arquivo INTEIRO. Se duas pessoas (ou duas
  abas do navegador) salvarem ao mesmo tempo, uma apaga o trabalho da outra.
- Banco: cada gravação é uma TRANSAÇÃO — ou acontece por completo, ou não
  acontece. É o alicerce para o app virar multi-usuário.

Por que SQLAlchemy + SQLite?
- SQLite é um banco completo dentro de um único arquivo (data/geladeira.db):
  zero instalação, zero servidor.
- SQLAlchemy traduz classes Python <-> tabelas SQL. Quando o app crescer,
  trocar SQLite por PostgreSQL é (quase) só mudar a string de conexão abaixo.

IMPORTANTE para o futuro multi-usuário: todas as tabelas de dados pessoais
(itens, histórico, receitas do livro) já têm a coluna `usuario_id`. Hoje só
existe o usuário 1 (config.USUARIO_PADRAO_ID), mas o terreno está preparado.
"""

from sqlalchemy import ForeignKey, String, create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import JSON

import config


# ---------------------------------------------------------------------------
# BASE DOS MODELOS
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Classe-mãe de todos os modelos. O SQLAlchemy usa-a para registrar
    as tabelas e criar o schema com Base.metadata.create_all()."""


# ---------------------------------------------------------------------------
# TABELAS
# ---------------------------------------------------------------------------
class Usuario(Base):
    """Perfil e preferências (antes: data/usuario.json)."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String, default="")
    # CREDENCIAIS (etapa multi-usuário).
    # `email` é único: é ele que identifica a conta no login.
    # `senha_hash` guarda o resultado do bcrypt — NUNCA a senha em si.
    # Ambos aceitam None por causa do usuário que já existia antes do login.
    email: Mapped[str | None] = mapped_column(String, unique=True, default=None)
    senha_hash: Mapped[str | None] = mapped_column(String, default=None)
    vegetariano: Mapped[bool] = mapped_column(default=False)
    vegano: Mapped[bool] = mapped_column(default=False)
    # Lista de strings gravada como JSON na coluna (ex.: ["amendoim"]).
    alergias: Mapped[list] = mapped_column(JSON, default=list)
    tempo_max_receita: Mapped[int] = mapped_column(default=60)
    # Dados de saúde (usados por saude.py). Podem ficar vazios (None).
    idade: Mapped[int | None] = mapped_column(default=None)
    peso_kg: Mapped[float | None] = mapped_column(default=None)
    altura_cm: Mapped[float | None] = mapped_column(default=None)
    sexo: Mapped[str | None] = mapped_column(String, default=None)
    nivel_atividade: Mapped[str | None] = mapped_column(String, default=None)


class ItemInventario(Base):
    """Um item dentro da geladeira/despensa/freezer (antes: inventario.json)."""

    __tablename__ = "itens_inventario"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    nome: Mapped[str] = mapped_column(String)
    quantidade: Mapped[float]
    unidade: Mapped[str] = mapped_column(String)
    local: Mapped[str] = mapped_column(String)
    # Datas guardadas como TEXTO ISO ("AAAA-MM-DD"), o MESMO formato que o
    # resto do código já usa para comparar e ordenar. Assim a lógica
    # (inventario.py, alertas.py) não precisou mudar NADA.
    data_compra: Mapped[str] = mapped_column(String)
    data_validade: Mapped[str] = mapped_column(String)


class RegistroHistorico(Base):
    """Item que saiu do estoque: consumido ou descartado (antes: historico.json)."""

    __tablename__ = "historico"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    nome: Mapped[str] = mapped_column(String)
    quantidade: Mapped[float]
    unidade: Mapped[str] = mapped_column(String)
    categoria: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String)  # "consumido" | "descartado"
    data: Mapped[str] = mapped_column(String)    # "AAAA-MM-DD"


class ReceitaLivro(Base):
    """Receita guardada no livro do usuário (antes: livro_receitas.json)."""

    __tablename__ = "livro_receitas"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    titulo: Mapped[str] = mapped_column(String)
    ingredientes: Mapped[list] = mapped_column(JSON, default=list)
    modo_preparo: Mapped[list] = mapped_column(JSON, default=list)
    ingredientes_usados: Mapped[list] = mapped_column(JSON, default=list)
    chave: Mapped[str] = mapped_column(String, default="")
    origem: Mapped[str] = mapped_column(String, default="")  # ia|cache|generica
    criada_em: Mapped[str] = mapped_column(String, default="")
    visto_em: Mapped[str] = mapped_column(String, default="")
    vezes: Mapped[int] = mapped_column(default=1)


class ReceitaCache(Base):
    """
    Cache offline: combinação de ingredientes -> última receita gerada
    (antes: receitas_cache.json). É GLOBAL (sem usuario_id de propósito):
    se alguém já gerou receita para "tomate+ovo", qualquer usuário offline
    pode reaproveitá-la — é só um cache, não dado pessoal.
    """

    __tablename__ = "receitas_cache"

    chave: Mapped[str] = mapped_column(String, primary_key=True)
    dados: Mapped[dict] = mapped_column(JSON)


# ---------------------------------------------------------------------------
# ENGINE (conexão) E SESSÕES
# ---------------------------------------------------------------------------
# O engine é criado uma única vez quando o módulo é importado.
# Para PostgreSQL no futuro: "postgresql+psycopg://usuario:senha@host/banco".
_engine = None


def obter_engine():
    """Devolve o engine global, criando-o (e as tabelas) na primeira vez."""
    global _engine
    if _engine is None:
        _engine = criar_engine(config.url_do_banco())
    return _engine


def criar_engine(destino):
    """
    Cria o engine e garante que todas as tabelas existem.

    `destino` aceita duas formas:
      - uma URL do SQLAlchemy ("postgresql+psycopg://..." ou "sqlite:///...");
      - um caminho de arquivo, que vira SQLite (usado pelos TESTES, que
        trabalham com um banco temporário para não tocar no banco real).
    """
    url = destino if "://" in str(destino) else f"sqlite:///{destino}"

    # pool_pre_ping testa a conexão antes de usá-la. É indispensável com o
    # Neon: ele desliga o banco quando ninguém acessa, e sem esse teste a
    # primeira consulta depois da soneca falharia com "connection closed".
    engine = create_engine(url, pool_pre_ping=True)

    Base.metadata.create_all(engine)
    _migrar_colunas_novas(engine)
    return engine


def _migrar_colunas_novas(engine):
    """
    Migração leve de schema.

    ATENÇÃO ao detalhe que pega todo mundo: `create_all()` só cria tabelas
    que AINDA NÃO existem — ele nunca altera uma tabela já criada. Então,
    para quem já tinha um banco antes do login existir, a tabela `usuarios`
    ficaria sem as colunas `email` e `senha_hash`, e o app quebraria com
    "no such column".

    Esta função compara as colunas que existem no banco com as que o modelo
    espera e adiciona as que faltam com ALTER TABLE. É segura para rodar
    sempre: se não falta nada, não faz nada.

    Funciona tanto no SQLite quanto no PostgreSQL: a lista de colunas vem
    do `inspect()` do SQLAlchemy, que fala a língua de cada banco, em vez
    de um comando específico como o PRAGMA do SQLite.
    """
    novas = {
        "usuarios": {
            "email": "VARCHAR",
            "senha_hash": "VARCHAR",
        },
    }

    inspetor = inspect(engine)

    with engine.begin() as conexao:
        for tabela, colunas in novas.items():
            if not inspetor.has_table(tabela):
                continue  # create_all() já criou completa; nada a migrar.
            existentes = {c["name"] for c in inspetor.get_columns(tabela)}
            for coluna, tipo in colunas.items():
                if coluna not in existentes:
                    conexao.exec_driver_sql(
                        f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}"
                    )

        # ADD COLUMN não aceita UNIQUE embutido, então a unicidade do e-mail
        # é garantida por um índice à parte. A sintaxe abaixo é aceita pelos
        # dois bancos.
        conexao.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_usuarios_email "
            "ON usuarios (email)"
        )


def usar_engine(engine):
    """Substitui o engine global (usado pelos testes)."""
    global _engine
    _engine = engine


def abrir_sessao():
    """
    Abre uma sessão de trabalho com o banco. Use sempre com `with`:

        with db.abrir_sessao() as sessao:
            ...consultas e gravações...
            sessao.commit()

    O `with` garante que a conexão é fechada mesmo se algo der errado.
    """
    return Session(obter_engine())