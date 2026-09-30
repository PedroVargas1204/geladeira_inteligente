"""
operacoes.py
============
As AÇÕES do app, cada uma gravando no banco de forma pontual e atômica.

Por que este módulo existe
--------------------------
Até aqui, salvar era assim: carregava tudo para a memória, mexia nas listas
e chamava salvar_estado(), que apagava todas as linhas do usuário e as
regravava. Isso imitava o comportamento antigo dos arquivos JSON e funciona
bem para uma pessoa por vez — mas tem um furo sério:

    Aba A carrega o inventário  ......... [tomate]
    Aba B carrega o inventário  ......... [tomate]
    Aba A adiciona leite e salva ........ [tomate, leite]
    Aba B adiciona ovo e salva .......... [tomate, ovo]   ← o leite sumiu!

A aba B gravou a lista que ELA tinha na memória, que já estava velha. É o
problema clássico de "ler, modificar, gravar tudo de novo".

Aqui a lógica muda: em vez de regravar o estado inteiro, cada ação altera
apenas as linhas que ela realmente mexe — um INSERT do leite, um UPDATE
naquele item específico, um DELETE daquela linha. As duas abas passam a
conviver sem se apagarem.

Cada função abre UMA sessão e faz tudo dentro dela, então a operação é
atômica: consumir um item grava o registro no histórico E reduz a
quantidade juntos, ou nada acontece. Nunca pela metade.

Camadas (quem pode importar quem)
---------------------------------
    db.py            tabelas
    persistencia.py  leitura e gravação
    inventario.py    regras puras (não sabem o que é banco)
    operacoes.py     ← aqui: junta regra + gravação, em transação
    streamlit_app.py / main.py   interfaces
"""

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

import config
from banco import db
from regras import inventario as inv


class ItemNaoEncontrado(Exception):
    """
    O item não existe mais (ou não pertence a este usuário).

    Acontece de verdade: você abre duas abas, consome o item na primeira e
    clica em consumir na segunda. A interface deve mostrar um aviso amigável
    e recarregar, não quebrar.
    """


class ReceitaNaoEncontrada(Exception):
    """A receita não está mais no livro (ou não pertence a este usuário)."""


# ---------------------------------------------------------------------------
# BUSCA INTERNA — sempre filtrando pelo dono
# ---------------------------------------------------------------------------
def _buscar_item(sessao, usuario_id, item_id):
    """
    Carrega um item GARANTINDO que ele pertence a `usuario_id`.

    O filtro por usuario_id não é decoração: sem ele, bastaria alguém
    chamar a função com o id de um item alheio para apagar o item de outra
    pessoa. Toda operação pontual filtra pelo dono.
    """
    item = sessao.scalars(
        select(db.ItemInventario).where(
            db.ItemInventario.id == item_id,
            db.ItemInventario.usuario_id == usuario_id,
        )
    ).first()
    if item is None:
        raise ItemNaoEncontrado(
            "Este item não está mais no seu inventário. Atualize a página."
        )
    return item


# ---------------------------------------------------------------------------
# ADICIONAR
# ---------------------------------------------------------------------------
def adicionar_item(usuario_id, item):
    """
    Insere UM item no inventário e devolve o id gerado.

    Um único INSERT: não toca em nenhuma outra linha, então nada que outra
    aba tenha adicionado no meio-tempo é perdido.
    """
    with db.abrir_sessao() as sessao:
        linha = db.ItemInventario(
            usuario_id=usuario_id,
            nome=item["nome"],
            quantidade=float(item["quantidade"]),
            unidade=item["unidade"],
            local=item["local"],
            data_compra=item.get("data_compra", ""),
            data_validade=item.get("data_validade", ""),
        )
        sessao.add(linha)
        sessao.commit()
        return linha.id


# ---------------------------------------------------------------------------
# CONSUMIR / DESCARTAR
# ---------------------------------------------------------------------------
def _mover_para_historico(usuario_id, item_id, status, base, quantidade=None):
    """
    Tira (tudo ou parte de) um item do inventário e registra no histórico.

    Tudo em uma transação só:
      1. lê o item (conferindo o dono);
      2. calcula quanto sai, usando a MESMA regra da versão em memória;
      3. insere a linha no histórico;
      4. apaga o item (se saiu tudo) ou reduz a quantidade (se foi parcial).

    Devolve (quantidade_movida, mover_tudo, resto) para a interface montar
    a mensagem ("restam 200g no inventário").
    """
    with db.abrir_sessao() as sessao:
        item = _buscar_item(sessao, usuario_id, item_id)

        # Regra única, compartilhada com inventario._mover_para_historico.
        movida, mover_tudo, resto = inv.calcular_movimento(
            item.quantidade, quantidade
        )

        # Categoria vem do catálogo, para o impacto agregar corretamente.
        _, dados = inv.buscar_alimento_por_nome(item.nome, base)
        categoria = dados["categoria"] if dados else "Outros"

        sessao.add(db.RegistroHistorico(
            usuario_id=usuario_id,
            nome=item.nome,
            quantidade=movida,
            unidade=item.unidade,
            categoria=categoria,
            status=status,
            data=config.hoje().strftime("%Y-%m-%d"),
        ))

        if mover_tudo:
            sessao.delete(item)
        else:
            item.quantidade = resto

        # Um único commit: o registro no histórico e a baixa no inventário
        # acontecem juntos. Sem chance de registrar o consumo e o item
        # continuar cheio, ou vice-versa.
        sessao.commit()
        return movida, mover_tudo, resto


def consumir(usuario_id, item_id, base, quantidade=None):
    """Marca como consumido. Sem `quantidade`, consome o item inteiro."""
    return _mover_para_historico(usuario_id, item_id, "consumido", base,
                                 quantidade)


def descartar(usuario_id, item_id, base, quantidade=None):
    """Marca como descartado. Sem `quantidade`, descarta o item inteiro."""
    return _mover_para_historico(usuario_id, item_id, "descartado", base,
                                 quantidade)


# ---------------------------------------------------------------------------
# LIVRO DE RECEITAS
# ---------------------------------------------------------------------------
def registrar_receita(usuario_id, registro):
    """Guarda a receita no livro e devolve o id.

    Se o usuário já tem a mesma receita (mesmo título e mesma `chave`),
    só soma uma visualização. O incremento é feito pelo próprio banco
    (vezes = vezes + 1), então duas abas ao mesmo tempo não perdem contagem.
    """
    with db.abrir_sessao() as sessao:
        existente = sessao.scalars(
            select(db.ReceitaLivro.id).where(
                db.ReceitaLivro.usuario_id == usuario_id,
                db.ReceitaLivro.titulo == registro["titulo"],
                db.ReceitaLivro.chave == registro["chave"],
            )
        ).first()

        if existente is not None:
            sessao.execute(
                update(db.ReceitaLivro)
                .where(db.ReceitaLivro.id == existente)
                .values(vezes=db.ReceitaLivro.vezes + 1,
                        visto_em=registro["visto_em"])
            )
            sessao.commit()
            return existente

        linha = db.ReceitaLivro(
            usuario_id=usuario_id,
            titulo=registro["titulo"],
            ingredientes=list(registro["ingredientes"]),
            modo_preparo=list(registro["modo_preparo"]),
            ingredientes_usados=list(registro["ingredientes_usados"]),
            chave=registro["chave"],
            origem=registro["origem"],
            criada_em=registro["criada_em"],
            visto_em=registro["visto_em"],
            vezes=1,
        )
        sessao.add(linha)
        sessao.commit()
        return linha.id


def remover_receita(usuario_id, receita_id):
    """Apaga uma receita do livro, conferindo o dono."""
    with db.abrir_sessao() as sessao:
        resultado = sessao.execute(
            delete(db.ReceitaLivro).where(
                db.ReceitaLivro.id == receita_id,
                db.ReceitaLivro.usuario_id == usuario_id,
            )
        )
        sessao.commit()

    if resultado.rowcount == 0:
        raise ReceitaNaoEncontrada(
            "Esta receita não está mais no seu livro. Atualize a página."
        )


# ---------------------------------------------------------------------------
# CACHE DE RECEITAS (global, sem dono: não é dado pessoal)
# ---------------------------------------------------------------------------
def salvar_no_cache(chave, receita):
    """Grava ou atualiza UMA entrada do cache, sem tocar nas outras.

    Se duas pessoas criarem a mesma chave no mesmo instante, o banco recusa
    a segunda inserção; como é só um cache, fica valendo a primeira.
    """
    with db.abrir_sessao() as sessao:
        sessao.merge(db.ReceitaCache(chave=chave, dados=receita))
        try:
            sessao.commit()
        except IntegrityError:
            sessao.rollback()


# ---------------------------------------------------------------------------
# PERFIL
# ---------------------------------------------------------------------------
def salvar_perfil(usuario_id, dados):
    """
    Grava só o perfil do usuário, sem tocar em inventário nem histórico.

    Antes, salvar uma preferência regravava o inventário inteiro junto —
    o que podia apagar itens adicionados em outra aba. Agora é um UPDATE
    em uma linha.

    Campos ausentes em `dados` são ignorados (não viram None por engano):
    a tela de configurações edita preferências, e a de saúde edita peso e
    altura, cada uma mandando só o que conhece.
    """
    campos = ("nome", "vegetariano", "vegano", "alergias", "tempo_max_receita",
              "idade", "peso_kg", "altura_cm", "sexo", "nivel_atividade")

    with db.abrir_sessao() as sessao:
        usuario = sessao.get(db.Usuario, usuario_id)
        if usuario is None:
            usuario = db.Usuario(id=usuario_id)
            sessao.add(usuario)

        for campo in campos:
            if campo in dados:
                valor = dados[campo]
                if campo == "alergias":
                    valor = list(valor or [])
                setattr(usuario, campo, valor)

        sessao.commit()