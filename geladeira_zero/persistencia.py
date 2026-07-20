"""
persistencia.py
===============
A FUNDAÇÃO do projeto. Continua sendo a ÚNICA camada que guarda dados —
mas agora em um BANCO DE DADOS (SQLite via SQLAlchemy, ver db.py) em vez
de arquivos JSON.

A promessa antiga se cumpriu: "se um dia trocarmos JSON por banco de dados,
só este arquivo muda". Os módulos de lógica (inventario, alertas, ia,
impacto, saude) continuam trabalhando com LISTAS e DICIONÁRIOS comuns —
esta camada converte de/para as tabelas do banco.

O que ainda vive em arquivo:
- base_alimentos.json  -> catálogo do SISTEMA (só leitura), versionado no git;
- historico_export.csv -> exportação gerada sob demanda (RF11).
"""

import csv
import json

from sqlalchemy import delete, select

import config
import db


# ---------------------------------------------------------------------------
# CATÁLOGO DE ALIMENTOS (arquivo, só leitura)
# ---------------------------------------------------------------------------
def carregar_base():
    """
    Lê o catálogo base_alimentos.json e devolve o dicionário
    {nome: dados}. Defensiva: se o arquivo faltar ou estiver corrompido,
    devolve {} em vez de quebrar o programa.
    """
    try:
        with open(config.ARQ_BASE_ALIMENTOS, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def buscar_alimento_na_base(nome, base):
    """
    FONTE ÚNICA de consulta ao catálogo (sem repetir a regra).

    Procura `nome` na base de forma direta (chave normalizada para minúsculas
    e sem espaços nas pontas). Devolve o dicionário do alimento, ou None.

    A busca TOLERANTE (sinônimos, substring) fica em inventario.py, que chama
    esta função como base.
    """
    chave = nome.strip().lower()
    return base.get(chave)  # dict.get devolve None se a chave não existir


# ---------------------------------------------------------------------------
# CONVERSÃO: linha do banco <-> dicionário
# ---------------------------------------------------------------------------
# O resto do código trabalha com dicionários (item["nome"], item["local"]...).
# Estas funções fazem a ponte, para a lógica não precisar conhecer o banco.

def _item_para_dict(item):
    return {
        "nome": item.nome,
        "quantidade": item.quantidade,
        "unidade": item.unidade,
        "local": item.local,
        "data_compra": item.data_compra,
        "data_validade": item.data_validade,
    }


def _registro_para_dict(reg):
    return {
        "nome": reg.nome,
        "quantidade": reg.quantidade,
        "unidade": reg.unidade,
        "categoria": reg.categoria,
        "status": reg.status,
        "data": reg.data,
    }


def _usuario_para_dict(u):
    if u is None:
        return {}
    return {
        "nome": u.nome,
        "vegetariano": u.vegetariano,
        "vegano": u.vegano,
        "alergias": list(u.alergias or []),
        "tempo_max_receita": u.tempo_max_receita,
        "idade": u.idade,
        "peso_kg": u.peso_kg,
        "altura_cm": u.altura_cm,
        "sexo": u.sexo,
        "nivel_atividade": u.nivel_atividade,
    }


def _receita_para_dict(r):
    return {
        "titulo": r.titulo,
        "ingredientes": list(r.ingredientes or []),
        "modo_preparo": list(r.modo_preparo or []),
        "ingredientes_usados": list(r.ingredientes_usados or []),
        "chave": r.chave,
        "origem": r.origem,
        "criada_em": r.criada_em,
        "visto_em": r.visto_em,
        "vezes": r.vezes,
    }


# ---------------------------------------------------------------------------
# ESTADO PRINCIPAL: base + inventário + histórico + usuário
# ---------------------------------------------------------------------------
def carregar_estado(usuario_id=config.USUARIO_PADRAO_ID):
    """
    Carrega TODO o estado do app para a memória, no mesmo formato de antes:
    {"base": {...}, "inventario": [...], "historico": [...], "usuario": {...}}

    `usuario_id` já existe pensando no multi-usuário: hoje é sempre 1.
    """
    with db.abrir_sessao() as sessao:
        itens = sessao.scalars(
            select(db.ItemInventario)
            .where(db.ItemInventario.usuario_id == usuario_id)
        ).all()
        registros = sessao.scalars(
            select(db.RegistroHistorico)
            .where(db.RegistroHistorico.usuario_id == usuario_id)
        ).all()
        usuario = sessao.get(db.Usuario, usuario_id)

        return {
            "base": carregar_base(),
            "inventario": [_item_para_dict(i) for i in itens],
            "historico": [_registro_para_dict(r) for r in registros],
            "usuario": _usuario_para_dict(usuario),
        }


def salvar_estado(estado, usuario_id=config.USUARIO_PADRAO_ID):
    """
    Grava inventário, histórico e usuário de volta no banco, em UMA
    transação: ou salva tudo, ou nada (se algo falhar no meio, o banco
    fica como estava — impossível "meio salvo", que era o risco do JSON).

    Estratégia (espelho): apaga as linhas do usuário e regrava a partir
    das listas em memória — exatamente a semântica que o app já tinha com
    JSON. Quando o app for multi-usuário de verdade, o passo seguinte é
    trocar isto por operações pontuais (inserir/alterar item a item).
    """
    with db.abrir_sessao() as sessao:
        # Perfil: atualiza se existe, cria se não existe.
        usuario = sessao.get(db.Usuario, usuario_id)
        if usuario is None:
            usuario = db.Usuario(id=usuario_id)
            sessao.add(usuario)
        dados_usuario = estado.get("usuario", {})
        usuario.nome = dados_usuario.get("nome", "")
        usuario.vegetariano = bool(dados_usuario.get("vegetariano", False))
        usuario.vegano = bool(dados_usuario.get("vegano", False))
        usuario.alergias = list(dados_usuario.get("alergias", []))
        usuario.tempo_max_receita = int(dados_usuario.get("tempo_max_receita", 60))
        usuario.idade = dados_usuario.get("idade")
        usuario.peso_kg = dados_usuario.get("peso_kg")
        usuario.altura_cm = dados_usuario.get("altura_cm")
        usuario.sexo = dados_usuario.get("sexo")
        usuario.nivel_atividade = dados_usuario.get("nivel_atividade")

        # Inventário: espelha a lista em memória.
        sessao.execute(
            delete(db.ItemInventario)
            .where(db.ItemInventario.usuario_id == usuario_id)
        )
        for item in estado.get("inventario", []):
            sessao.add(db.ItemInventario(
                usuario_id=usuario_id,
                nome=item.get("nome", ""),
                quantidade=float(item.get("quantidade", 0)),
                unidade=item.get("unidade", "unid"),
                local=item.get("local", "geladeira"),
                data_compra=item.get("data_compra", ""),
                data_validade=item.get("data_validade", ""),
            ))

        # Histórico: idem.
        sessao.execute(
            delete(db.RegistroHistorico)
            .where(db.RegistroHistorico.usuario_id == usuario_id)
        )
        for reg in estado.get("historico", []):
            sessao.add(db.RegistroHistorico(
                usuario_id=usuario_id,
                nome=reg.get("nome", ""),
                quantidade=float(reg.get("quantidade", 0)),
                unidade=reg.get("unidade", "unid"),
                categoria=reg.get("categoria", ""),
                status=reg.get("status", ""),
                data=reg.get("data", ""),
            ))

        sessao.commit()


# ---------------------------------------------------------------------------
# LIVRO DE RECEITAS (usado por ia.py)
# ---------------------------------------------------------------------------
def carregar_livro(usuario_id=config.USUARIO_PADRAO_ID):
    """Devolve todas as receitas do livro como lista de dicionários."""
    with db.abrir_sessao() as sessao:
        receitas = sessao.scalars(
            select(db.ReceitaLivro)
            .where(db.ReceitaLivro.usuario_id == usuario_id)
            .order_by(db.ReceitaLivro.id)
        ).all()
        return [_receita_para_dict(r) for r in receitas]


def salvar_livro(livro, usuario_id=config.USUARIO_PADRAO_ID):
    """Espelha a lista `livro` (dicionários) na tabela livro_receitas."""
    with db.abrir_sessao() as sessao:
        sessao.execute(
            delete(db.ReceitaLivro)
            .where(db.ReceitaLivro.usuario_id == usuario_id)
        )
        for r in livro:
            sessao.add(db.ReceitaLivro(
                usuario_id=usuario_id,
                titulo=r.get("titulo", "Receita sem título"),
                ingredientes=list(r.get("ingredientes", [])),
                modo_preparo=list(r.get("modo_preparo", [])),
                ingredientes_usados=list(r.get("ingredientes_usados", [])),
                chave=r.get("chave", ""),
                origem=r.get("origem", ""),
                criada_em=r.get("criada_em", ""),
                visto_em=r.get("visto_em", ""),
                vezes=int(r.get("vezes", 1)),
            ))
        sessao.commit()


# ---------------------------------------------------------------------------
# CACHE DE RECEITAS OFFLINE (usado por ia.py) — global, sem usuario_id
# ---------------------------------------------------------------------------
def carregar_cache():
    """Devolve o cache como dicionário {chave: receita}."""
    with db.abrir_sessao() as sessao:
        linhas = sessao.scalars(select(db.ReceitaCache)).all()
        return {linha.chave: linha.dados for linha in linhas}


def salvar_cache(cache):
    """Espelha o dicionário `cache` na tabela receitas_cache."""
    with db.abrir_sessao() as sessao:
        sessao.execute(delete(db.ReceitaCache))
        for chave, dados in cache.items():
            sessao.add(db.ReceitaCache(chave=chave, dados=dados))
        sessao.commit()


# ---------------------------------------------------------------------------
# EXPORTAÇÃO CSV (RF11) — continua em arquivo, é o objetivo dela
# ---------------------------------------------------------------------------
def exportar_csv(historico, caminho=config.ARQ_EXPORT_CSV):
    """
    Exporta o histórico para CSV — uma linha por item (RF11).

    Usa csv.DictWriter: cada item do histórico é um dicionário, e o writer
    transforma cada dicionário em uma linha do CSV, na ordem das colunas.
    """
    colunas = ["nome", "quantidade", "unidade", "categoria", "status", "data"]

    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()                # primeira linha: nomes das colunas
        for item in historico:
            # Monta uma linha só com as colunas que queremos, na ordem certa.
            linha = {coluna: item.get(coluna, "") for coluna in colunas}
            escritor.writerow(linha)

    return caminho
