"""
interface.py
============
A "casca" do programa em modo texto (CLI). Duas responsabilidades:
1. Desenhar as telas (molduras, títulos, menus).
2. Validar TODA entrada do usuário, para que nenhum dado inválido entre no
   programa (RNF03). Cada leitor é um laço que só termina com dado válido.

Responsável (slides): Pessoa A
"""

import os
from datetime import datetime

LARGURA = 60  # largura fixa das molduras, em caracteres


# ---------------------------------------------------------------------------
# DESENHO DE TELAS
# ---------------------------------------------------------------------------
def limpar_tela():
    """Limpa o terminal. Funciona em Windows, Linux e Mac (slide 5)."""
    # os.name é "nt" no Windows e "posix" no Linux/Mac.
    os.system("cls" if os.name == "nt" else "clear")


def desenhar_titulo(texto):
    """
    Desenha um título dentro de uma moldura com bordas alinhadas.

    A mágica do alinhamento é o f-string {texto:<LARGURA}:
    "<" alinha à esquerda e completa com espaços até ter LARGURA colunas.
    Por isso a borda direita "|" sempre cai no mesmo lugar.
    """
    print("+" + "-" * (LARGURA + 2) + "+")
    print(f"| {texto.upper():<{LARGURA}} |")
    print("+" + "-" * (LARGURA + 2) + "+")


def linha(texto=""):
    """Imprime uma linha de conteúdo dentro da moldura, alinhada à esquerda."""
    print(f"| {texto:<{LARGURA}} |")


def borda():
    print("+" + "-" * (LARGURA + 2) + "+")


def pausar():
    input("\nPressione ENTER para continuar...")


# ---------------------------------------------------------------------------
# LEITORES VALIDADOS (cada um é um while True que só sai com dado válido)
# ---------------------------------------------------------------------------
def ler_texto(prompt, obrigatorio=True):
    """Lê um texto. Se obrigatorio, não aceita vazio."""
    while True:
        valor = input(prompt).strip()
        if valor or not obrigatorio:
            return valor
        print("  ! Este campo não pode ficar vazio.")


def ler_inteiro(prompt, minimo=None, maximo=None):
    """Lê um número inteiro dentro de [minimo, maximo] (quando informados)."""
    while True:
        bruto = input(prompt).strip()
        try:
            valor = int(bruto)
        except ValueError:
            print("  ! Digite um número inteiro válido.")
            continue
        if minimo is not None and valor < minimo:
            print(f"  ! O valor mínimo é {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"  ! O valor máximo é {maximo}.")
            continue
        return valor


def ler_float(prompt, minimo=0.0):
    """
    Lê um número decimal. Aceita vírgula OU ponto (slide 5): "1,5" e "1.5"
    são lidos como 1.5.
    """
    while True:
        bruto = input(prompt).strip().replace(",", ".")
        try:
            valor = float(bruto)
        except ValueError:
            print("  ! Digite um número válido (ex.: 1,5).")
            continue
        if valor < minimo:
            print(f"  ! O valor mínimo é {minimo}.")
            continue
        return valor


def ler_opcao(prompt, opcoes_validas):
    """
    Lê a opção do menu. `opcoes_validas` é uma lista de strings, ex.: ["0","1",...].
    Só retorna quando a entrada está na lista.
    """
    while True:
        valor = input(prompt).strip()
        if valor in opcoes_validas:
            return valor
        print(f"  ! Opção inválida. Escolha entre: {', '.join(opcoes_validas)}")


def ler_data(prompt):
    """
    Lê uma data no formato DD/MM/AAAA e devolve no formato AAAA-MM-DD
    (formato ISO, que ordena bem e é fácil de comparar).

    strptime valida de verdade: 31/02/2026 é recusado, porque fevereiro
    não tem dia 31 (slide 5).
    """
    while True:
        bruto = input(prompt + " (DD/MM/AAAA): ").strip()
        try:
            data = datetime.strptime(bruto, "%d/%m/%Y")
            return data.strftime("%Y-%m-%d")
        except ValueError:
            print("  ! Data inválida. Use o formato DD/MM/AAAA (ex.: 25/12/2026).")


def ler_sim_nao(prompt):
    """Lê uma resposta sim/não e devolve True/False."""
    while True:
        valor = input(prompt + " (s/n): ").strip().lower()
        if valor in ("s", "sim"):
            return True
        if valor in ("n", "nao", "não"):
            return False
        print("  ! Responda com 's' ou 'n'.")
