"""
migrar_json_para_db.py
======================
Script de USO ÚNICO: importa os dados dos antigos arquivos JSON
(data/inventario.json, historico.json, usuario.json, livro_receitas.json,
receitas_cache.json) para o novo banco data/geladeira.db.

Como usar (dentro da pasta geladeira_zero):
    python migrar_json_para_db.py

É seguro rodar mais de uma vez: se o banco já tiver dados, o script pergunta
antes de sobrescrever. Os arquivos JSON NÃO são apagados — ficam como backup
(e fora do git, por causa do .gitignore).
"""

import json
import os

import config
from banco import db
from banco import persistencia


def ler_json(caminho, padrao):
    """Lê um JSON antigo; devolve `padrao` se não existir/estiver corrompido."""
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def main():
    pasta = config.PASTA_DADOS
    arq_inventario = os.path.join(pasta, "inventario.json")
    arq_historico = os.path.join(pasta, "historico.json")
    arq_usuario = os.path.join(pasta, "usuario.json")
    arq_livro = os.path.join(pasta, "livro_receitas.json")
    arq_cache = os.path.join(pasta, "receitas_cache.json")

    estado = {
        "inventario": ler_json(arq_inventario, []),
        "historico": ler_json(arq_historico, []),
        "usuario": ler_json(arq_usuario, {}),
    }
    livro = ler_json(arq_livro, [])
    cache = ler_json(arq_cache, {})

    print("Encontrado nos JSONs antigos:")
    print(f"  - {len(estado['inventario'])} itens no inventário")
    print(f"  - {len(estado['historico'])} registros no histórico")
    print(f"  - perfil do usuário: {'sim' if estado['usuario'] else 'não'}")
    print(f"  - {len(livro)} receitas no livro")
    print(f"  - {len(cache)} receitas no cache")

    # Se o banco já tem dados, confirma antes de sobrescrever.
    ja_existe = persistencia.carregar_estado()
    if ja_existe["inventario"] or ja_existe["historico"] or ja_existe["usuario"]:
        resposta = input(
            "\nO banco já contém dados. Sobrescrever com os JSONs? [s/N] "
        ).strip().lower()
        if resposta != "s":
            print("Nada foi alterado.")
            return

    persistencia.salvar_estado(estado)
    persistencia.salvar_livro(livro)
    persistencia.salvar_cache(cache)

    print(f"\nMigração concluída -> {config.ARQ_BANCO}")
    print("Os arquivos JSON antigos foram mantidos como backup (fora do git).")


if __name__ == "__main__":
    main()
