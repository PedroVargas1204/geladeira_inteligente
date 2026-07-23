"""
migrar_sqlite_para_postgres.py
==============================
Copia TODOS os dados do banco SQLite local (data/geladeira.db) para o
PostgreSQL hospedado — o passo que leva o que você já tem para o app
publicado na internet.

Como usar (dentro da pasta geladeira_zero):

    Windows (PowerShell):
        $env:DATABASE_URL = "postgresql://usuario:senha@ep-xxx.neon.tech/neondb"
        python migrar_sqlite_para_postgres.py

    Linux / macOS:
        export DATABASE_URL="postgresql://usuario:senha@ep-xxx.neon.tech/neondb"
        python migrar_sqlite_para_postgres.py

O script é conservador: se o PostgreSQL já tiver usuários cadastrados, ele
pergunta antes de continuar. O SQLite local não é alterado em momento
algum — ele é só lido.

Sobre os ids: as linhas são recriadas com os MESMOS ids do SQLite, para
que os vínculos entre usuário, itens e histórico continuem batendo. Ao
final, os contadores de id do PostgreSQL são reposicionados, senão o
próximo cadastro tentaria usar um id já ocupado.
"""

import os
import sys

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

import config
import db


# Tabelas na ordem em que devem ser copiadas: usuários primeiro, porque as
# outras apontam para eles.
TABELAS = [
    (db.Usuario, "usuarios"),
    (db.ItemInventario, "itens_inventario"),
    (db.RegistroHistorico, "historico"),
    (db.ReceitaLivro, "livro_receitas"),
    (db.ReceitaCache, "receitas_cache"),
]


def copiar_linha(modelo, linha):
    """Copia os valores de uma linha para um objeto novo, campo a campo."""
    valores = {
        coluna.name: getattr(linha, coluna.name)
        for coluna in modelo.__table__.columns
    }
    return modelo(**valores)


def main():
    url_destino = config.url_do_banco()

    if url_destino.startswith("sqlite"):
        print("ERRO: DATABASE_URL não está definida.")
        print("Defina a variável com a string de conexão do PostgreSQL")
        print("antes de rodar este script (veja o topo do arquivo).")
        sys.exit(1)

    if not os.path.exists(config.ARQ_BANCO):
        print(f"ERRO: não encontrei o banco local em {config.ARQ_BANCO}")
        sys.exit(1)

    origem = create_engine(f"sqlite:///{config.ARQ_BANCO}")
    destino = db.criar_engine(url_destino)  # já cria as tabelas lá

    # Confere se o destino está vazio antes de escrever qualquer coisa.
    with Session(destino) as sessao:
        ja_tem = sessao.scalars(select(db.Usuario)).first() is not None
    if ja_tem:
        resposta = input(
            "O banco de destino JÁ tem usuários. Continuar mesmo assim "
            "pode duplicar dados. Continuar? [s/N] "
        ).strip().lower()
        if resposta != "s":
            print("Nada foi alterado.")
            return

    total_geral = 0
    with Session(origem) as ler, Session(destino) as gravar:
        for modelo, nome in TABELAS:
            linhas = ler.scalars(select(modelo)).all()
            for linha in linhas:
                gravar.add(copiar_linha(modelo, linha))
            gravar.flush()  # erros aparecem por tabela, não só no fim
            print(f"  {nome:<20} {len(linhas):>4} linha(s)")
            total_geral += len(linhas)
        gravar.commit()

    # Reposiciona os contadores de id do PostgreSQL. Sem isso, o próximo
    # cadastro tentaria o id 1 — que já existe — e daria erro de chave
    # duplicada. (O SQLite não precisa disso; o PostgreSQL sim.)
    if url_destino.startswith("postgresql"):
        with destino.begin() as conexao:
            for modelo, nome in TABELAS:
                if "id" not in modelo.__table__.columns:
                    continue  # receitas_cache usa a chave como id
                conexao.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{nome}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {nome}), 1))"
                ))
        print("  contadores de id ajustados")

    origem.dispose()
    destino.dispose()
    print(f"\nMigração concluída: {total_geral} linha(s) copiadas.")
    print("O banco SQLite local não foi alterado.")


if __name__ == "__main__":
    main()