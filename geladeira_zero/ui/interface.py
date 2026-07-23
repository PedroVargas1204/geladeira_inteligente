"""
interface.py
============
A "casca" do programa em modo texto (CLI). Duas responsabilidades:
1. Desenhar as telas (molduras, títulos, menus).
2. Validar TODA entrada do usuário, para que nenhum dado inválido entre no
   programa (RNF03). Cada leitor é um laço que só termina com dado válido.

Além disso, os leitores entendem a tecla ESC: apertá-la em qualquer campo
aborta a operação atual e volta ao menu (capturado lá no main.py).

Responsável (slides): Pessoa A
"""

import os
import sys
from datetime import datetime

LARGURA = 60  # largura fixa das molduras, em caracteres


class OperacaoCancelada(Exception):
    """Usuário apertou ESC para abortar a operação e voltar ao menu."""
    pass


# ---------------------------------------------------------------------------
# LEITURA DE TECLADO COM SUPORTE A ESC (cross-platform)
# ---------------------------------------------------------------------------
def _ler_linha(prompt):
    """
    Lê uma linha do teclado caractere a caractere, para conseguir detectar
    a tecla ESC (que o input() comum não captura). Se ESC for pressionado,
    levanta OperacaoCancelada. Senão, devolve o texto digitado.
    Funciona em Windows e Linux/Mac.
    """
    print(prompt, end="", flush=True)
    return _ler_windows() if os.name == "nt" else _ler_unix()


def _ler_windows():
    import msvcrt
    buffer = []
    while True:
        ch = msvcrt.getwch()
        if ch == "\x1b":                 # ESC
            print()
            raise OperacaoCancelada()
        if ch in ("\r", "\n"):           # ENTER
            print()
            return "".join(buffer)
        if ch == "\x03":                 # Ctrl+C
            raise KeyboardInterrupt
        if ch == "\x08":                 # Backspace
            if buffer:
                buffer.pop()
                print("\b \b", end="", flush=True)
            continue
        if ch in ("\x00", "\xe0"):       # setas/F1.. : descarta o 2º código
            msvcrt.getwch()
            continue
        print(ch, end="", flush=True)    # ecoa e guarda
        buffer.append(ch)


def _ler_unix():
    import tty, termios, select
    fd = sys.stdin.fileno()
    antigo = termios.tcgetattr(fd)
    buffer = []
    try:
        tty.setcbreak(fd)                # desliga modo de linha e echo; mantém Ctrl+C
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":             # ESC (ou início de seta)
                # Se há mais bytes esperando, é uma seta -> ignora.
                tem_mais, _, _ = select.select([sys.stdin], [], [], 0.0005)
                if tem_mais:
                    sys.stdin.read(2)    # descarta o resto da sequência (ex.: "[A")
                    continue
                print()
                raise OperacaoCancelada()
            if ch in ("\r", "\n"):       # ENTER
                print()
                return "".join(buffer)
            if ch in ("\x7f", "\x08"):   # Backspace
                if buffer:
                    buffer.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            if ch == "\x03":             # Ctrl+C
                raise KeyboardInterrupt
            sys.stdout.write(ch)         # ecoa e guarda
            sys.stdout.flush()
            buffer.append(ch)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, antigo)


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
    while True:
        valor = _ler_linha(prompt).strip()
        if valor or not obrigatorio:
            return valor
        print("  ! Este campo não pode ficar vazio.")


def ler_inteiro(prompt, minimo=None, maximo=None):
    while True:
        bruto = _ler_linha(prompt).strip()
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


def ler_float(prompt, minimo=0.0, maximo=None, padrao=None):
    """
    Lê um número decimal. Aceita vírgula OU ponto (slide 5): "1,5" e "1.5"
    são lidos como 1.5.

    Parâmetros novos (usados pelo consumo parcial):
      maximo : se informado, recusa valores acima desse limite.
      padrao : se informado e o usuário só apertar ENTER (campo vazio),
               devolve esse valor. Permite "ENTER = tudo".
    """
    while True:
        bruto = _ler_linha(prompt).strip().replace(",", ".")
        if bruto == "" and padrao is not None:
            return padrao
        try:
            valor = float(bruto)
        except ValueError:
            print("  ! Digite um número válido (ex.: 1,5).")
            continue
        if valor < minimo:
            print(f"  ! O valor mínimo é {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"  ! O valor máximo é {maximo}.")
            continue
        return valor


def ler_opcao(prompt, opcoes_validas, cancelavel=True):
    # No menu principal passamos cancelavel=False: lá não há o que cancelar,
    # então usamos o input() comum e ESC não dispara nada.
    leitor = _ler_linha if cancelavel else (lambda p: input(p))
    while True:
        valor = leitor(prompt).strip()
        if valor in opcoes_validas:
            return valor
        print(f"  ! Opção inválida. Escolha entre: {', '.join(opcoes_validas)}")


def ler_data(prompt):
    while True:
        bruto = _ler_linha(prompt + " (DD/MM/AAAA): ").strip()
        try:
            data = datetime.strptime(bruto, "%d/%m/%Y")
            return data.strftime("%Y-%m-%d")
        except ValueError:
            print("  ! Data inválida. Use o formato DD/MM/AAAA (ex.: 25/12/2026).")


def ler_sim_nao(prompt):
    while True:
        valor = _ler_linha(prompt + " (s/n): ").strip().lower()
        if valor in ("s", "sim"):
            return True
        if valor in ("n", "nao", "não"):
            return False
        print("  ! Responda com 's' ou 'n'.")