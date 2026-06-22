"""
main.py
=======
PONTO DE ENTRADA do programa (RF01). Amarra tudo:
- carrega os 5 JSON do disco;
- mostra o menu num laço;
- roteia cada opção para a função certa;
- salva o estado a cada ação (RNF04).

Baixo acoplamento: main só CHAMA funções dos módulos, sem conhecer seus
detalhes internos.

Responsável (slides): Pessoa A
"""

from datetime import datetime

import config
import persistencia
import interface
import inventario as inv
import alertas
import ia
import impacto


# ---------------------------------------------------------------------------
# CARREGAR / SALVAR TODO O ESTADO
# ---------------------------------------------------------------------------
def carregar_tudo():
    """Lê os arquivos JSON e devolve um dicionário com todo o estado."""
    return {
        "base": persistencia.carregar_json(config.ARQ_BASE_ALIMENTOS, {}),
        "inventario": persistencia.carregar_json(config.ARQ_INVENTARIO, []),
        "historico": persistencia.carregar_json(config.ARQ_HISTORICO, []),
        "usuario": persistencia.carregar_json(config.ARQ_USUARIO, {}),
    }


def salvar_tudo(estado):
    """Grava o estado de volta no disco (chamado a cada ação)."""
    persistencia.salvar_json(config.ARQ_INVENTARIO, estado["inventario"])
    persistencia.salvar_json(config.ARQ_HISTORICO, estado["historico"])
    persistencia.salvar_json(config.ARQ_USUARIO, estado["usuario"])


# ---------------------------------------------------------------------------
# AÇÕES DO MENU (uma função por opção)
# ---------------------------------------------------------------------------
def acao_adicionar(estado):
    interface.desenhar_titulo("Adicionar item")
    nome = interface.ler_texto("Nome do alimento: ")
    chave, dados = inv.buscar_alimento_por_nome(nome, estado["base"])

    if dados is None:
        print("  ! Alimento não está no catálogo. Cadastre um conhecido.")
        interface.pausar()
        return

    quantidade = interface.ler_float("Quantidade: ", minimo=0.01)
    unidade = interface.ler_texto("Unidade (kg/g/l/ml/unid): ").lower()
    print(f"Locais válidos: {', '.join(config.LOCAIS_VALIDOS)}")
    local = interface.ler_opcao("Local: ", config.LOCAIS_VALIDOS)
    data_compra = interface.ler_data("Data de compra")

    validade = inv.sugerir_validade(data_compra, dados, local)
    item = {
        "nome": chave,
        "quantidade": quantidade,
        "unidade": unidade,
        "local": local,
        "data_compra": data_compra,
        "data_validade": validade,
    }
    inv.adicionar_item(estado["inventario"], item)
    salvar_tudo(estado)
    print(f"  + Adicionado! Validade sugerida: {validade}")
    interface.pausar()


def acao_ver_inventario(estado):
    interface.desenhar_titulo("Inventário (por validade)")
    ordenado = inv.listar_ordenado(estado["inventario"])
    if not ordenado:
        interface.linha("(inventário vazio)")
    for item in ordenado:
        dias = alertas.dias_para_vencer(item["data_validade"])
        marca = "VENCIDO" if dias < 0 else f"{dias}d"
        texto = (f"{item['nome']:<12} {item['quantidade']}{item['unidade']:<6}"
                 f" {item['local']:<10} vence {item['data_validade']} ({marca})")
        interface.linha(texto)
    interface.borda()
    interface.pausar()


def acao_ver_alertas(estado):
    interface.desenhar_titulo("Alertas de vencimento")
    lista = alertas.calcular_alertas(estado["inventario"])
    if not lista:
        interface.linha("Nenhum item vencendo nos próximos dias. :)")
    for item, dias in lista:
        if dias < 0:
            estado_txt = f"VENCEU há {abs(dias)} dia(s)"
        elif dias == 0:
            estado_txt = "VENCE HOJE"
        else:
            estado_txt = f"vence em {dias} dia(s)"
        interface.linha(f"{item['nome']:<14} {estado_txt}")
    interface.borda()
    interface.pausar()


def acao_sugerir_receita(estado):
    interface.desenhar_titulo("Receita com o que tenho")
    if not estado["inventario"]:
        interface.linha("Adicione itens primeiro.")
        interface.borda()
        interface.pausar()
        return

    print("Buscando receita...")
    receita, origem = ia.sugerir_receita(estado["inventario"], estado["usuario"])
    rotulo = {"ia": "IA", "cache": "cache local", "generica": "receita base"}
    print(f"\n[{rotulo.get(origem, origem)}]  {receita['titulo']}\n")
    print("Ingredientes:")
    for ing in receita["ingredientes"]:
        print(f"  - {ing}")
    print("\nModo de preparo:")
    for i, passo in enumerate(receita["modo_preparo"], start=1):
        print(f"  {i}. {passo}")
    interface.pausar()


def acao_marcar(estado):
    interface.desenhar_titulo("Marcar consumido / descartado")
    ordenado = inv.listar_ordenado(estado["inventario"])
    if not ordenado:
        interface.linha("(inventário vazio)")
        interface.borda()
        interface.pausar()
        return

    # Mostra também a quantidade, para o usuário decidir o consumo parcial.
    for i, item in enumerate(ordenado):
        interface.linha(f"[{i}] {item['nome']} - {item['quantidade']}"
                        f"{item['unidade']} - vence {item['data_validade']}")
    interface.borda()

    indice = interface.ler_inteiro("Número do item: ", minimo=0,
                                   maximo=len(ordenado) - 1)
    item_escolhido = ordenado[indice]
    # Acha a posição real do item na lista original (a ordenada é uma cópia).
    real = estado["inventario"].index(item_escolhido)
    qtd_atual = item_escolhido["quantidade"]
    unidade = item_escolhido["unidade"]

    print("[1] Consumido   [2] Descartado")
    escolha = interface.ler_opcao("Opção: ", ["1", "2"])

    # Pergunta QUANTO. ENTER (vazio) = tudo. Nunca aceita mais do que existe.
    print(f"Quantidade disponível: {qtd_atual}{unidade}")
    qtd = interface.ler_float(
        f"Quanto? (máx {qtd_atual}, ENTER = tudo): ",
        minimo=0.01, maximo=qtd_atual, padrao=qtd_atual,
    )
    parcial = qtd < qtd_atual
    resto = round(qtd_atual - qtd, 4)

    if escolha == "1":
        inv.marcar_consumido(estado["inventario"], estado["historico"], real,
                             estado["base"], qtd)
        if parcial:
            print(f"  + Consumido {qtd}{unidade}. Restam {resto}{unidade} "
                  f"no inventário.")
        else:
            print("  + Item totalmente consumido (entrou na economia).")
    else:
        inv.marcar_descartado(estado["inventario"], estado["historico"], real,
                              estado["base"], qtd)
        if parcial:
            print(f"  - Descartado {qtd}{unidade}. Restam {resto}{unidade} "
                  f"no inventário.")
        else:
            print("  - Item totalmente descartado.")

    salvar_tudo(estado)
    interface.pausar()


def acao_impacto(estado):
    interface.desenhar_titulo("Impacto e economia")
    kg, co2, agua, reais = impacto.calcular_impacto(estado["historico"],
                                                    estado["base"])
    taxa = impacto.taxa_aproveitamento(estado["historico"])
    interface.linha(f"Alimento salvo:  {kg:.2f} kg")
    interface.linha(f"CO2 evitado:     {co2:.2f} kg")
    interface.linha(f"Água economizada:{agua:.0f} L")
    interface.linha(f"Dinheiro salvo:  R$ {reais:.2f}")
    interface.linha(f"Aproveitamento:  {taxa*100:.0f}%")
    interface.linha("")
    interface.linha("Por categoria:")
    contagem = impacto.agregar_por_categoria(estado["historico"])
    for linha_grafico in impacto.grafico_barras(contagem):
        interface.linha(linha_grafico)
    interface.borda()
    interface.pausar()


def acao_configuracoes(estado):
    """Preferências do usuário (RF10).

    Lê TODOS os campos em variáveis locais primeiro. Se o usuário apertar ESC
    no meio, a OperacaoCancelada sobe sem ter alterado nada no estado. Só
    quando todos os campos foram preenchidos é que gravamos de uma vez.
    """
    interface.desenhar_titulo("Configurações")
    u = estado["usuario"]

    nome = interface.ler_texto("Seu nome: ", obrigatorio=False) or u.get("nome", "")
    vegetariano = interface.ler_sim_nao("Vegetariano?")
    vegano = interface.ler_sim_nao("Vegano?")
    alergias_txt = interface.ler_texto("Alergias (separadas por vírgula): ",
                                       obrigatorio=False)
    tempo = interface.ler_inteiro("Tempo máx. de receita (min): ",
                                  minimo=5, maximo=240)

    # Chegou aqui: tudo válido e ninguém cancelou. Grava de uma vez.
    u["nome"] = nome
    u["vegetariano"] = vegetariano
    u["vegano"] = vegano
    u["alergias"] = [a.strip() for a in alergias_txt.split(",") if a.strip()]
    u["tempo_max_receita"] = tempo
    salvar_tudo(estado)
    print("  + Preferências salvas.")
    interface.pausar()


def acao_exportar_csv(estado):
    interface.desenhar_titulo("Exportar histórico (CSV)")
    caminho = persistencia.exportar_csv(estado["historico"])
    print(f"  + Exportado para: {caminho}")
    interface.pausar()


# ---------------------------------------------------------------------------
# CABEÇALHO DINÂMICO
# ---------------------------------------------------------------------------
def desenhar_cabecalho(estado):
    """Mostra, a cada volta do menu, um resumo do estado atual (slide 9)."""
    ativos = len(estado["inventario"])
    vencendo = len(alertas.calcular_alertas(estado["inventario"],
                                            config.DIAS_ALERTA))
    _, _, _, reais = impacto.calcular_impacto(estado["historico"],
                                              estado["base"])
    nome = estado["usuario"].get("nome") or "visitante"
    interface.desenhar_titulo("Geladeira Zero")
    interface.linha(f"Olá, {nome}!")
    interface.linha(f"Itens ativos: {ativos}  |  Vencendo em "
                    f"{config.DIAS_ALERTA}d: {vencendo}  |  Economia: R$ {reais:.2f}")
    interface.borda()


# ---------------------------------------------------------------------------
# LAÇO PRINCIPAL
# ---------------------------------------------------------------------------
def main():
    estado = carregar_tudo()

    # Mapa: opção -> função. Alternativa elegante ao if/elif gigante.
    acoes = {
        "1": acao_adicionar,
        "2": acao_ver_inventario,
        "3": acao_ver_alertas,
        "4": acao_sugerir_receita,
        "5": acao_marcar,
        "6": acao_impacto,
        "7": acao_configuracoes,
        "8": acao_exportar_csv,
    }

    while True:
        interface.limpar_tela()
        desenhar_cabecalho(estado)
        print("\n[1] Adicionar item        [2] Ver inventário")
        print("[3] Ver alertas           [4] Sugerir receita")
        print("[5] Marcar consumido/desc.[6] Ver impacto")
        print("[7] Configurações         [8] Exportar CSV")
        print("[0] Sair")
        print("\n(dica: aperte ESC em qualquer campo para voltar ao menu)")

        opcao = interface.ler_opcao(
            "\nEscolha: ",
            ["0", "1", "2", "3", "4", "5", "6", "7", "8"],
            cancelavel=False,   # no menu, ESC não faz sentido
        )
        if opcao == "0":
            print("Até logo! Menos desperdício. :)")
            break

        try:
            acoes[opcao](estado)  # roteia para a função certa
        except interface.OperacaoCancelada:
            print("\n  Operação cancelada. Nenhuma alteração foi salva.")
            interface.pausar()


# Só executa main() se este arquivo for rodado direto (python main.py),
# e não quando for importado por outro módulo.
if __name__ == "__main__":
    main()