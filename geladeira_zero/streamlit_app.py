"""
streamlit_app.py
================
Interface GRÁFICA (web) para o Geladeira Zero, como alternativa ao terminal.

Reaproveita os MESMOS módulos de lógica do projeto (persistencia, inventario,
alertas, ia, impacto) — não reimplementa nenhuma regra. Os dados são os mesmos
arquivos JSON usados pelo main.py, então terminal e web ficam sincronizados.

Novidades desta versão:
- CONSUMO PARCIAL: dá para consumir/descartar só parte da quantidade.
- Mais robusto: erros de leitura/cálculo aparecem como aviso amigável em vez
  de derrubar a tela inteira.

Como rodar (dentro da pasta do projeto, onde estão os outros .py):
    pip install streamlit
    python -m streamlit run streamlit_app.py
"""

from datetime import date

import pandas as pd
import streamlit as st

import config
import persistencia
import inventario as inv
import alertas
import ia
import impacto


# Unidades aceitas pelo converter_para_kg() do impacto.py.
UNIDADES_VALIDAS = ["kg", "g", "l", "ml", "unid"]


# ---------------------------------------------------------------------------
# ESTADO: carregar do disco e salvar de volta
# ---------------------------------------------------------------------------
def carregar_estado():
    """Lê os arquivos JSON e devolve todo o estado (igual ao main.carregar_tudo)."""
    return {
        "base": persistencia.carregar_json(config.ARQ_BASE_ALIMENTOS, {}),
        "inventario": persistencia.carregar_json(config.ARQ_INVENTARIO, []),
        "historico": persistencia.carregar_json(config.ARQ_HISTORICO, []),
        "usuario": persistencia.carregar_json(config.ARQ_USUARIO, {}),
    }


def salvar_estado(estado):
    """Grava inventário, histórico e usuário de volta no disco."""
    persistencia.salvar_json(config.ARQ_INVENTARIO, estado["inventario"])
    persistencia.salvar_json(config.ARQ_HISTORICO, estado["historico"])
    persistencia.salvar_json(config.ARQ_USUARIO, estado["usuario"])


def impacto_seguro(historico, base):
    """Calcula o impacto sem nunca derrubar a página (devolve zeros se falhar)."""
    try:
        return impacto.calcular_impacto(historico, base)
    except Exception as e:
        st.warning(f"Não foi possível calcular o impacto: {e}")
        return 0.0, 0.0, 0.0, 0.0


# Carregamos do disco a cada execução. Protegido para mostrar erro amigável.
try:
    estado = carregar_estado()
except Exception as e:
    st.error(f"Erro ao ler os arquivos de dados: {e}")
    st.stop()


# ---------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA + BARRA LATERAL
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Geladeira Zero", page_icon="🧊", layout="wide")

nome_usuario = estado["usuario"].get("nome") or "visitante"
ativos = len(estado["inventario"])
vencendo = len(alertas.calcular_alertas(estado["inventario"], config.DIAS_ALERTA))
_, _, _, reais_economizados = impacto_seguro(estado["historico"], estado["base"])

with st.sidebar:
    st.title("🧊 Geladeira Zero")
    st.caption(f"Olá, {nome_usuario}!")
    st.metric("Itens ativos", ativos)
    st.metric(f"Vencendo em {config.DIAS_ALERTA} dias", vencendo)
    st.metric("Economia acumulada", f"R$ {reais_economizados:.2f}")
    st.divider()
    pagina = st.radio(
        "Navegação",
        [
            "📊 Painel",
            "📦 Inventário",
            "➕ Adicionar item",
            "⚠️ Alertas",
            "✅ Consumir / Descartar",
            "🍳 Sugerir receita",
            "🌱 Impacto",
            "⚙️ Configurações",
            "💾 Exportar CSV",
        ],
    )


# ---------------------------------------------------------------------------
# PÁGINA: PAINEL
# ---------------------------------------------------------------------------
if pagina == "📊 Painel":
    st.header("Painel geral")
    col1, col2, col3 = st.columns(3)
    col1.metric("Itens no inventário", ativos)
    col2.metric("Vencendo em breve", vencendo)
    col3.metric("Economia (R$)", f"{reais_economizados:.2f}")

    st.subheader("Próximos a vencer")
    lista = alertas.calcular_alertas(estado["inventario"], config.DIAS_ALERTA)
    if not lista:
        st.success("Nenhum item vencendo nos próximos dias. 🎉")
    else:
        for item, dias in lista:
            if dias < 0:
                st.error(f"**{item['nome']}** venceu há {abs(dias)} dia(s).")
            elif dias == 0:
                st.warning(f"**{item['nome']}** vence HOJE.")
            else:
                st.info(f"**{item['nome']}** vence em {dias} dia(s).")


# ---------------------------------------------------------------------------
# PÁGINA: INVENTÁRIO
# ---------------------------------------------------------------------------
elif pagina == "📦 Inventário":
    st.header("Inventário (ordenado por validade)")
    ordenado = inv.listar_ordenado(estado["inventario"])
    if not ordenado:
        st.info("Inventário vazio. Adicione itens na aba ➕.")
    else:
        linhas = []
        for item in ordenado:
            dias = alertas.dias_para_vencer(item["data_validade"])
            if dias < 0:
                situacao = f"🔴 Vencido há {abs(dias)}d"
            elif dias <= config.DIAS_ALERTA:
                situacao = f"🟡 Vence em {dias}d"
            else:
                situacao = f"🟢 {dias}d"
            linhas.append({
                "Alimento": item["nome"],
                "Qtd": f"{item['quantidade']} {item['unidade']}",
                "Local": item["local"],
                "Validade": item["data_validade"],
                "Situação": situacao,
            })
        st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# PÁGINA: ADICIONAR ITEM
# ---------------------------------------------------------------------------
elif pagina == "➕ Adicionar item":
    st.header("Adicionar item ao inventário")
    if not estado["base"]:
        st.error("O catálogo de alimentos (base_alimentos.json) está vazio.")
    else:
        catalogo = sorted(estado["base"].keys())
        with st.form("form_adicionar"):
            nome = st.selectbox("Alimento (do catálogo)", catalogo)
            col1, col2 = st.columns(2)
            quantidade = col1.number_input("Quantidade", min_value=0.01,
                                           value=1.0, step=0.1)
            unidade = col2.selectbox("Unidade", UNIDADES_VALIDAS)
            local = st.selectbox("Local de armazenamento", config.LOCAIS_VALIDOS)
            data_compra = st.date_input("Data de compra", value=date.today())
            enviar = st.form_submit_button("Adicionar")

        if enviar:
            data_iso = data_compra.strftime("%Y-%m-%d")
            dados = estado["base"][nome]
            validade = inv.sugerir_validade(data_iso, dados, local)
            item = {
                "nome": nome,
                "quantidade": quantidade,
                "unidade": unidade,
                "local": local,
                "data_compra": data_iso,
                "data_validade": validade,
            }
            inv.adicionar_item(estado["inventario"], item)
            salvar_estado(estado)
            st.success(f"Adicionado! Validade sugerida: {validade}")
            st.rerun()


# ---------------------------------------------------------------------------
# PÁGINA: ALERTAS
# ---------------------------------------------------------------------------
elif pagina == "⚠️ Alertas":
    st.header("Alertas de vencimento")
    lista = alertas.calcular_alertas(estado["inventario"])
    if not lista:
        st.success("Nenhum item vencendo nos próximos dias. 🙂")
    else:
        for item, dias in lista:
            if dias < 0:
                st.error(f"**{item['nome']}** — venceu há {abs(dias)} dia(s)")
            elif dias == 0:
                st.warning(f"**{item['nome']}** — vence HOJE")
            else:
                st.info(f"**{item['nome']}** — vence em {dias} dia(s)")


# ---------------------------------------------------------------------------
# PÁGINA: CONSUMIR / DESCARTAR  (com consumo parcial)
# ---------------------------------------------------------------------------
elif pagina == "✅ Consumir / Descartar":
    st.header("Marcar item como consumido ou descartado")
    ordenado = inv.listar_ordenado(estado["inventario"])
    if not ordenado:
        st.info("Inventário vazio.")
    else:
        # Mapeia o rótulo mostrado -> posição real na lista original.
        rotulos = {
            f"{item['nome']} — {item['quantidade']}{item['unidade']} "
            f"(vence {item['data_validade']})": estado["inventario"].index(item)
            for item in ordenado
        }
        escolha = st.selectbox("Escolha o item", list(rotulos.keys()))
        indice = rotulos[escolha]
        item_sel = estado["inventario"][indice]
        qtd_max = float(item_sel["quantidade"])
        unidade = item_sel["unidade"]

        # Campo de quantidade: começa cheio (= consumir tudo). Reduza para
        # fazer consumo parcial — o resto continua no inventário.
        qtd = st.number_input(
            f"Quantidade a registrar ({unidade})",
            min_value=0.01,
            max_value=qtd_max,
            value=qtd_max,
            step=0.1,
        )
        if qtd < qtd_max:
            st.caption(f"Consumo parcial: restarão "
                       f"{round(qtd_max - qtd, 4)}{unidade} no inventário.")
        else:
            st.caption("Quantidade total: o item sairá do inventário.")

        col1, col2 = st.columns(2)
        if col1.button("✅ Consumido", use_container_width=True):
            inv.marcar_consumido(estado["inventario"], estado["historico"],
                                 indice, estado["base"], qtd)
            salvar_estado(estado)
            st.success(f"Registrado: {qtd}{unidade} consumido(s).")
            st.rerun()
        if col2.button("🗑️ Descartado", use_container_width=True):
            inv.marcar_descartado(estado["inventario"], estado["historico"],
                                  indice, estado["base"], qtd)
            salvar_estado(estado)
            st.warning(f"Registrado: {qtd}{unidade} descartado(s).")
            st.rerun()


# ---------------------------------------------------------------------------
# PÁGINA: SUGERIR RECEITA
# ---------------------------------------------------------------------------
elif pagina == "🍳 Sugerir receita":
    st.header("Receita com o que você tem")
    if not estado["inventario"]:
        st.info("Adicione itens primeiro.")
    else:
        if st.button("Gerar receita"):
            with st.spinner("Buscando receita..."):
                try:
                    receita, origem = ia.sugerir_receita(estado["inventario"],
                                                          estado["usuario"])
                except Exception as e:
                    st.error(f"Falha ao gerar receita: {e}")
                    receita, origem = None, None
            if receita:
                rotulo = {"ia": "IA", "cache": "cache local",
                          "generica": "receita base"}
                st.caption(f"Origem: {rotulo.get(origem, origem)}")
                st.subheader(receita["titulo"])
                st.markdown("**Ingredientes:**")
                for ing in receita["ingredientes"]:
                    st.markdown(f"- {ing}")
                st.markdown("**Modo de preparo:**")
                for i, passo in enumerate(receita["modo_preparo"], start=1):
                    st.markdown(f"{i}. {passo}")


# ---------------------------------------------------------------------------
# PÁGINA: IMPACTO
# ---------------------------------------------------------------------------
elif pagina == "🌱 Impacto":
    st.header("Impacto e economia")
    kg, co2, agua, reais = impacto_seguro(estado["historico"], estado["base"])
    taxa = impacto.taxa_aproveitamento(estado["historico"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Alimento salvo", f"{kg:.2f} kg")
    col2.metric("CO₂ evitado", f"{co2:.2f} kg")
    col3.metric("Água economizada", f"{agua:.0f} L")
    col4, col5 = st.columns(2)
    col4.metric("Dinheiro salvo", f"R$ {reais:.2f}")
    col5.metric("Aproveitamento", f"{taxa*100:.0f}%")

    st.subheader("Itens consumidos por categoria")
    contagem = impacto.agregar_por_categoria(estado["historico"])
    if not contagem:
        st.info("Sem dados ainda. Marque itens como consumidos para ver o gráfico.")
    else:
        df = pd.DataFrame(
            {"Categoria": list(contagem.keys()), "Itens": list(contagem.values())}
        ).set_index("Categoria")
        st.bar_chart(df)


# ---------------------------------------------------------------------------
# PÁGINA: CONFIGURAÇÕES
# ---------------------------------------------------------------------------
elif pagina == "⚙️ Configurações":
    st.header("Preferências do usuário")
    u = estado["usuario"]
    with st.form("form_config"):
        nome = st.text_input("Seu nome", value=u.get("nome", ""))
        col1, col2 = st.columns(2)
        vegetariano = col1.checkbox("Vegetariano", value=u.get("vegetariano", False))
        vegano = col2.checkbox("Vegano", value=u.get("vegano", False))
        alergias_txt = st.text_input(
            "Alergias (separadas por vírgula)",
            value=", ".join(u.get("alergias", [])),
        )
        tempo = st.slider("Tempo máx. de receita (min)", 5, 240,
                          value=u.get("tempo_max_receita", 60))
        salvar = st.form_submit_button("Salvar preferências")

    if salvar:
        u["nome"] = nome
        u["vegetariano"] = vegetariano
        u["vegano"] = vegano
        u["alergias"] = [a.strip() for a in alergias_txt.split(",") if a.strip()]
        u["tempo_max_receita"] = tempo
        salvar_estado(estado)
        st.success("Preferências salvas.")
        st.rerun()


# ---------------------------------------------------------------------------
# PÁGINA: EXPORTAR CSV
# ---------------------------------------------------------------------------
elif pagina == "💾 Exportar CSV":
    st.header("Exportar histórico")
    if not estado["historico"]:
        st.info("Histórico vazio. Nada para exportar ainda.")
    else:
        caminho = persistencia.exportar_csv(estado["historico"])
        st.success(f"Arquivo gerado em: {caminho}")
        with open(caminho, "r", encoding="utf-8") as arquivo:
            conteudo = arquivo.read()
        st.download_button(
            "Baixar historico_export.csv",
            data=conteudo,
            file_name="historico_export.csv",
            mime="text/csv",
        )
        st.dataframe(pd.DataFrame(estado["historico"]),
                     use_container_width=True, hide_index=True)