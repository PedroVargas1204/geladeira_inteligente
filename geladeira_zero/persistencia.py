"""
persistencia.py
===============
A FUNDAÇÃO do projeto. É a única camada que toca o disco:
- lê e grava todos os arquivos JSON;
- exporta o histórico em CSV;
- consulta o catálogo de alimentos (base).

Todos os outros módulos dependem dela. Se um dia trocarmos JSON por banco
de dados, só este arquivo muda.

Responsável (slides): Pessoa D
"""

import json
import csv

import config


# ---------------------------------------------------------------------------
# LEITURA / GRAVAÇÃO DE JSON
# ---------------------------------------------------------------------------
def carregar_json(caminho, padrao):
    """
    Lê um arquivo JSON e devolve seu conteúdo.

    É DEFENSIVA (slide 4): se o arquivo não existir (1ª execução) ou estiver
    corrompido, em vez de quebrar o programa ela devolve `padrao` (ex.: [] ou {}).

    Parâmetros:
        caminho (str): caminho do arquivo .json
        padrao        : o que devolver se algo der errado (ex.: [], {})
    """
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        # FileNotFoundError -> arquivo ainda não existe
        # JSONDecodeError   -> arquivo existe mas está corrompido/vazio
        return padrao


def salvar_json(caminho, dados):
    """
    Grava `dados` (lista ou dicionário Python) em um arquivo JSON.

    indent=2          -> formata bonito, legível por humanos
    ensure_ascii=False -> preserva acentos: salva "Maçã", não "Ma\\u00e7\\u00e3"
    """
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CONSULTA AO CATÁLOGO DE ALIMENTOS
# ---------------------------------------------------------------------------
def buscar_alimento_na_base(nome, base):
    """
    FONTE ÚNICA de consulta ao catálogo (slide 4: "sem repetir a regra").

    Procura `nome` na base de forma direta (chave normalizada para minúsculas
    e sem espaços nas pontas). Devolve o dicionário do alimento, ou None.

    A busca TOLERANTE (sinônimos, substring) fica em inventario.py, que chama
    esta função como base.
    """
    chave = nome.strip().lower()
    return base.get(chave)  # dict.get devolve None se a chave não existir


# ---------------------------------------------------------------------------
# EXPORTAÇÃO CSV (RF11)
# ---------------------------------------------------------------------------
def exportar_csv(historico, caminho=config.ARQ_EXPORT_CSV):
    """
    Exporta o histórico para CSV — uma linha por item (slide 4, RF11).

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
