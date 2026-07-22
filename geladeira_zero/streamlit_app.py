"""
streamlit_app.py
================
Interface GRÁFICA (web) para o Geladeira Zero, como alternativa ao terminal.

Reaproveita os MESMOS módulos de lógica do projeto (persistencia, inventario,
alertas, ia, impacto) — não reimplementa nenhuma regra. Os dados são os mesmos
arquivos JSON usados pelo main.py, então terminal e web ficam sincronizados.

Novidades desta versão (redesign de UX):
- Tema visual próprio (veja .streamlit/config.toml na mesma pasta).
- Painel com saudação, cards e atalho direto para gerar receita.
- Adicionar item mostra a validade prevista ANTES de confirmar, e avisa
  quando o local escolhido não é recomendado para aquele alimento.
- Inventário com busca e filtro por local de armazenamento.
- Receita fica na tela (não some ao interagir) e tem layout em colunas.
- Impacto com equivalências do dia a dia (km de carro, banhos de chuveiro).
- Notificações (toasts) que sobrevivem ao recarregamento da página.

Como rodar (dentro da pasta do projeto, onde estão os outros .py):
    pip install streamlit pandas
    python -m streamlit run streamlit_app.py
"""

from datetime import date, datetime

import pandas as pd
import streamlit as st

import config
import login_ui
import persistencia
import inventario as inv
import alertas
import ia
import impacto
import saude


# Unidades aceitas pelo converter_para_kg() do impacto.py.
UNIDADES_VALIDAS = ["kg", "g", "l", "ml", "unid"]

EMOJI_LOCAL = {"geladeira": "🧊", "despensa": "🗄️", "freezer": "❄️"}

# Rótulos amigáveis para as unidades (o valor salvo continua sendo a sigla).
ROTULO_UNIDADE = {
    "unid": "unidades",
    "kg": "quilos (kg)",
    "g": "gramas (g)",
    "l": "litros (L)",
    "ml": "mililitros (mL)",
}


def data_br(data_iso):
    """
    Converte 'AAAA-MM-DD' (formato dos arquivos JSON) para 'DD/MM/AAAA'
    (exibição). Os arquivos continuam em ISO porque a ordenação por
    validade depende disso — só a TELA muda para o padrão brasileiro.
    """
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return data_iso


def data_hora_br(texto_iso):
    """Converte 'AAAA-MM-DD HH:MM' para 'DD/MM/AAAA às HH:MM' (exibição)."""
    try:
        momento = datetime.strptime(texto_iso, "%Y-%m-%d %H:%M")
        return momento.strftime("%d/%m/%Y às %H:%M")
    except (ValueError, TypeError):
        return texto_iso


# ---------------------------------------------------------------------------
# ESTADO: carregar do disco e salvar de volta
# ---------------------------------------------------------------------------
def carregar_estado(usuario_id):
    """Lê o banco e devolve todo o estado DESTE usuário."""
    return persistencia.carregar_estado(usuario_id)


def salvar_estado(estado, usuario_id):
    """Grava inventário, histórico e perfil DESTE usuário, em uma transação."""
    persistencia.salvar_estado(estado, usuario_id)


def impacto_seguro(historico, base):
    """Calcula o impacto sem nunca derrubar a página (devolve zeros se falhar)."""
    try:
        return impacto.calcular_impacto(historico, base)
    except Exception as e:
        st.warning(f"Não foi possível calcular o impacto: {e}")
        return 0.0, 0.0, 0.0, 0.0


def avisar(mensagem, icone="✅"):
    """
    Agenda um toast para DEPOIS do st.rerun(). Toasts disparados logo antes
    de recarregar a página se perdem; guardando em session_state, o aviso
    aparece na próxima execução.
    """
    st.session_state["flash"] = (mensagem, icone)


# ---------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------------------------------
# Precisa ser o PRIMEIRO comando Streamlit da execução — inclusive antes de
# qualquer st.error() —, senão o Streamlit reclama.
st.set_page_config(page_title="Geladeira Zero", page_icon="🧊", layout="wide")

# ---------------------------------------------------------------------------
# LOGIN: o porteiro do app
# ---------------------------------------------------------------------------
# Se ninguém estiver logado nesta sessão, exigir_login() desenha a tela de
# entrada e interrompe a execução aqui — nada abaixo chega a rodar.
USUARIO_ID = login_ui.exigir_login()

# Daqui para baixo, TODOS os dados são lidos e gravados no escopo de
# USUARIO_ID: cada conta enxerga apenas a própria geladeira.
try:
    estado = carregar_estado(USUARIO_ID)
except Exception as e:
    st.error(f"Erro ao ler os dados: {e}")
    st.stop()
# ---------------------------------------------------------------------------
# CORES CUSTOMIZADAS (sidebar e bordas dos inputs)
# ---------------------------------------------------------------------------
COR_SIDEBAR = "#34362F"         # ← FUNDO da barra lateral
COR_TEXTO_SIDEBAR = "#EDF8F2"   # ← TEXTO da barra lateral
COR_BORDA = "#B8C4A9"           # borda dos inputs

# ← CORES DO BOTÃO "SAIR" (barra lateral). Mexa só aqui para trocar o visual.
BTN_FUNDO = "#3F4438"           # fundo normal
BTN_TEXTO = "#EDF8F2"           # texto normal
BTN_BORDA = "#6B7A5C"           # borda normal
BTN_FUNDO_HOVER = "#557A46"     # fundo ao passar o mouse
BTN_TEXTO_HOVER = "#ACC092"     # texto ao passar o mouse
BTN_BORDA_HOVER = "#E7F3E0"     # borda ao passar o mouse

st.markdown(
    f"""
    <style>
    /* fundo da barra lateral */
    section[data-testid="stSidebar"] > div {{
        background-color: {COR_SIDEBAR};
    }}
    /* texto da barra lateral */
    section[data-testid="stSidebar"] * {{
        color: {COR_TEXTO_SIDEBAR} !important;
    }}
    /* bordas dos inputs (texto, número, select, data) */
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"],
    [data-baseweb="input"] > div,
    .stNumberInput div[data-baseweb],
    .stDateInput div[data-baseweb],
    .stTextInput div[data-baseweb] {{
        border-color: {COR_BORDA} !important;
    }}
    /* borda verde ao focar/passar o mouse */
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"] > div:hover {{
        border-color: #557A46 !important;
    }}

    /* ----- BOTÃO "SAIR" (e qualquer botão da barra lateral) ----- */
    /* Os dois seletores cobrem versões diferentes do Streamlit. */
    section[data-testid="stSidebar"] .stButton > button,
    section[data-testid="stSidebar"] button[data-testid^="stBaseButton"] {{
        background-color: {BTN_FUNDO} !important;
        color: {BTN_TEXTO} !important;
        border: 1px solid {BTN_BORDA} !important;
        border-radius: 8px;
        font-weight: 500;
        /* transition = a mudança acontece suave, não em um salto seco */
        transition: background-color .18s ease, border-color .18s ease,
                    color .18s ease, transform .18s ease;
    }}

    /* :hover = enquanto o mouse está em cima */
    section[data-testid="stSidebar"] .stButton > button:hover,
    section[data-testid="stSidebar"] button[data-testid^="stBaseButton"]:hover {{
        background-color: {BTN_FUNDO_HOVER} !important;
        color: {BTN_TEXTO_HOVER} !important;
        border-color: {BTN_BORDA_HOVER} !important;
        transform: translateY(-1px);   /* sobe 1px: dá sensação de relevo */
    }}

    /* :active = no instante do clique (afunda de volta) */
    section[data-testid="stSidebar"] .stButton > button:active,
    section[data-testid="stSidebar"] button[data-testid^="stBaseButton"]:active {{
        transform: translateY(0);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Mostra o toast agendado na execução anterior (se houver).
if "flash" in st.session_state:
    mensagem, icone = st.session_state.pop("flash")
    st.toast(mensagem, icon=icone)

nome_usuario = estado["usuario"].get("nome") or "visitante"
ativos = len(estado["inventario"])

# Separa os alertas em duas listas: já vencidos (dias < 0) e
# vencendo nos próximos DIAS_ALERTA dias (0 <= dias <= DIAS_ALERTA).
todos_alertas = alertas.calcular_alertas(estado["inventario"], config.DIAS_ALERTA)
itens_vencidos = [(item, dias) for (item, dias) in todos_alertas if dias < 0]
itens_vencendo = [(item, dias) for (item, dias) in todos_alertas if dias >= 0]
vencendo = len(itens_vencendo)
vencidos = len(itens_vencidos)
_, _, _, reais_economizados = impacto_seguro(estado["historico"], estado["base"])

PAGINAS = [
    "📊 Painel",
    "📦 Inventário",
    "➕ Adicionar item",
    "⚠️ Alertas",
    "✅ Consumir / Descartar",
    "🍳 Sugerir receita",
    "📖 Livro de receitas",
    "🌱 Impacto",
    "⚙️ Configurações",
    "💾 Exportar CSV",
]

# Navegação programática: se algum botão pediu para trocar de página,
# aplicamos ANTES de criar o widget de rádio (regra do Streamlit).
if "ir_para" in st.session_state:
    st.session_state["nav"] = st.session_state.pop("ir_para")

with st.sidebar:
    st.title("Geladeira Zero")
    st.caption(f"Olá, {nome_usuario}!")

    col_a, col_b = st.columns(2)
    col_a.metric("Itens ativos", ativos)
    col_b.metric("Economia", f"R$ {reais_economizados:.0f}")
    col_c, col_d = st.columns(2)
    col_c.metric(f"Vencem em {config.DIAS_ALERTA}d", vencendo)
    col_d.metric("Vencidos", vencidos)

    st.divider()
    pagina = st.radio("Navegação", PAGINAS, key="nav", label_visibility="collapsed")
    st.divider()
    login_ui.bloco_conta(USUARIO_ID)
    st.caption("♻️ Menos desperdício, mais sabor.")


# ---------------------------------------------------------------------------
# PÁGINA: PAINEL
# ---------------------------------------------------------------------------
if pagina == "📊 Painel":
    hora = datetime.now().hour
    saudacao = "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"
    st.header(f"{saudacao}, {nome_usuario}!")

    # Uma frase de resumo diz mais que quatro números soltos.
    if vencidos:
        st.caption(f"⚠️ Você tem {vencidos} item(ns) vencido(s) e "
                   f"{vencendo} vencendo em breve. Bora resolver?")
    elif vencendo:
        st.caption(f"⏳ {vencendo} item(ns) vencendo nos próximos "
                   f"{config.DIAS_ALERTA} dias — que tal uma receita?")
    else:
        st.caption("✨ Tudo sob controle na sua geladeira.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 No inventário", ativos)
    col2.metric(f"⏳ Vencendo em {config.DIAS_ALERTA} dias", vencendo)
    col3.metric("🔴 Vencidos", vencidos)
    col4.metric("💰 Economia", f"R$ {reais_economizados:.2f}")

    st.divider()
    col_esq, col_dir = st.columns(2, gap="large")

    with col_esq:
        st.subheader("⏳ Precisam de atenção")
        if not itens_vencidos and not itens_vencendo:
            st.success("Nenhum item vencido ou vencendo. 🎉")
        else:
            for item, dias in itens_vencidos:
                st.error(f"**{item['nome']}** venceu há {abs(dias)} dia(s).")
            for item, dias in itens_vencendo:
                if dias == 0:
                    st.error(f"**{item['nome']}** vence **HOJE**.")
                else:
                    st.info(f"**{item['nome']}** vence em {dias} dia(s).")

    with col_dir:
        st.subheader("⚡ Ações rápidas")
        with st.container(border=True):
            if itens_vencendo or itens_vencidos:
                st.write("Tem coisa vencendo — a IA monta uma receita "
                         "para aproveitar tudo antes que estrague.")
            else:
                st.write("Gere uma receita com o que você tem em casa.")
            if st.button("🍳 Gerar receita agora", type="primary",
                         width="stretch"):
                st.session_state["ir_para"] = "🍳 Sugerir receita"
                st.session_state["gerar_ao_abrir"] = True
                st.rerun()
        with st.container(border=True):
            st.write("Acabou de fazer compras?")
            if st.button("➕ Adicionar itens", width="stretch"):
                st.session_state["ir_para"] = "➕ Adicionar item"
                st.rerun()


# ---------------------------------------------------------------------------
# PÁGINA: INVENTÁRIO
# ---------------------------------------------------------------------------
elif pagina == "📦 Inventário":
    st.header("📦 Inventário")
    st.caption("Ordenado por validade: o que vence primeiro aparece no topo.")
    ordenado = inv.listar_ordenado(estado["inventario"])

    if not ordenado:
        st.info("Inventário vazio. Adicione itens na aba ➕ Adicionar item.")
    else:
        # Busca + filtro deixam a tabela útil mesmo com muitos itens.
        col_busca, col_filtro = st.columns([2, 1])
        busca = col_busca.text_input("🔎 Buscar alimento",
                                     placeholder="ex.: tomate")
        filtro_local = col_filtro.selectbox(
            "Local", ["todos"] + list(config.LOCAIS_VALIDOS))

        linhas = []
        for item in ordenado:
            if busca and busca.strip().lower() not in item["nome"].lower():
                continue
            if filtro_local != "todos" and item["local"] != filtro_local:
                continue
            dias = alertas.dias_para_vencer(item["data_validade"])
            if dias < 0:
                situacao = f"🔴 Vencido há {abs(dias)}d"
            elif dias <= config.DIAS_ALERTA:
                situacao = f"🟡 Vence em {dias}d"
            else:
                situacao = f"🟢 Vence em {dias}d"
            local = item["local"]
            linhas.append({
                "Alimento": item["nome"],
                "Qtd": f"{item['quantidade']} {item['unidade']}",
                "Local": f"{EMOJI_LOCAL.get(local, '')} {local}",
                "Comprado em": data_br(item.get("data_compra", "—")),
                "Validade": data_br(item["data_validade"]),
                "Situação": situacao,
            })

        if not linhas:
            st.info("Nenhum item encontrado com esses filtros.")
        else:
            st.dataframe(pd.DataFrame(linhas), width="stretch",
                         hide_index=True)
            st.caption(f"{len(linhas)} item(ns) exibido(s).")


# ---------------------------------------------------------------------------
# PÁGINA: ADICIONAR ITEM
# ---------------------------------------------------------------------------
elif pagina == "➕ Adicionar item":
    st.header("➕ Adicionar item")
    if not estado["base"]:
        st.error("O catálogo de alimentos (base_alimentos.json) está vazio.")
    else:
        catalogo = sorted(estado["base"].keys())

        # Sem st.form de propósito: assim a prévia da validade atualiza
        # em tempo real conforme o usuário troca alimento/local/data.
        nome = st.selectbox("Alimento (do catálogo)", catalogo)
        # A unidade vem PRIMEIRO, em botões horizontais — e o campo de
        # quantidade se adapta a ela: unidades inteiras sobem de 1 em 1,
        # gramas de 50 em 50, quilos de 0,25 em 0,25. Menos digitação.
        unidade = st.radio(
            "Como você mede esse item?",
            ["unid", "kg", "g", "l", "ml"],
            horizontal=True,
            format_func=lambda u: ROTULO_UNIDADE.get(u, u),
        )

        col_qtd, col_local = st.columns(2)
        if unidade == "unid":
            quantidade = float(col_qtd.number_input(
                "Quantidade", min_value=1, value=1, step=1))
        elif unidade in ("g", "ml"):
            quantidade = float(col_qtd.number_input(
                f"Quantidade ({unidade})", min_value=10, value=500, step=50))
        else:  # kg ou l
            quantidade = float(col_qtd.number_input(
                f"Quantidade ({unidade})", min_value=0.1, value=1.0,
                step=0.25, format="%.2f"))

        local = col_local.selectbox(
            "Local de armazenamento",
            config.LOCAIS_VALIDOS,
            format_func=lambda l: f"{EMOJI_LOCAL.get(l, '')} {l}",
        )
        data_compra = st.date_input("Data de compra", value=date.today(),
                                    format="DD/MM/YYYY")

        # PRÉVIA: mostra quanto o alimento dura em cada local e a data
        # de validade que será sugerida — antes de o usuário confirmar.
        dados = estado["base"][nome]
        duracoes = dados["validade_dias"]
        st.caption("Durabilidade típica — " + " · ".join(
            f"{EMOJI_LOCAL.get(l, '')} {l}: {duracoes.get(l, 0)}d"
            for l in config.LOCAIS_VALIDOS
        ))

        data_iso = data_compra.strftime("%Y-%m-%d")
        validade_prevista = inv.sugerir_validade(data_iso, dados, local)
        if duracoes.get(local, 0) == 0:
            st.warning(f"⚠️ **{local}** não é recomendado para "
                       f"**{nome}** — a validade cairia em hoje mesmo. "
                       "Considere outro local.")
        else:
            st.info(f"📅 Você vai adicionar **{quantidade:g} {unidade} de "
                    f"{nome}** — validade prevista: "
                    f"**{data_br(validade_prevista)}**")

        if st.button("Adicionar ao inventário", type="primary",
                     width="stretch"):
            item = {
                "nome": nome,
                "quantidade": quantidade,
                "unidade": unidade,
                "local": local,
                "data_compra": data_iso,
                "data_validade": validade_prevista,
            }
            inv.adicionar_item(estado["inventario"], item)
            salvar_estado(estado, USUARIO_ID)
            avisar(f"{nome} adicionado! Vence em "
                   f"{data_br(validade_prevista)}.", "🧊")
            st.rerun()


# ---------------------------------------------------------------------------
# PÁGINA: ALERTAS
# ---------------------------------------------------------------------------
elif pagina == "⚠️ Alertas":
    st.header("⚠️ Alertas de vencimento")
    lista = alertas.calcular_alertas(estado["inventario"])
    if not lista:
        st.success("Nenhum item vencendo nos próximos dias. 🙂")
    else:
        st.caption(f"{len(lista)} item(ns) precisando de atenção, "
                   "do mais urgente para o menos urgente.")
        for item, dias in lista:
            if dias < 0:
                st.error(f"**{item['nome']}** — venceu há {abs(dias)} dia(s)")
            elif dias == 0:
                st.error(f"**{item['nome']}** — vence **HOJE**")
            else:
                st.info(f"**{item['nome']}** — vence em {dias} dia(s)")

        st.divider()
        if st.button("🍳 Aproveitar em uma receita", type="primary"):
            st.session_state["ir_para"] = "🍳 Sugerir receita"
            st.session_state["gerar_ao_abrir"] = True
            st.rerun()


# ---------------------------------------------------------------------------
# PÁGINA: CONSUMIR / DESCARTAR  (com consumo parcial)
# ---------------------------------------------------------------------------
elif pagina == "✅ Consumir / Descartar":
    st.header("✅ Consumir ou descartar")
    st.caption("Registrar o destino dos alimentos alimenta as métricas "
               "de impacto — consumo conta como desperdício evitado.")

    if not estado["inventario"]:
        st.info("Inventário vazio.")
    else:
        # enumerate ANTES de ordenar preserva a posição real de cada item
        # na lista original (dois itens iguais não se confundem).
        pares = sorted(enumerate(estado["inventario"]),
                       key=lambda par: par[1]["data_validade"])
        rotulos = {}
        for posicao, item in pares:
            rotulo = (f"{item['nome']} — {item['quantidade']}"
                      f"{item['unidade']} "
                      f"(vence {data_br(item['data_validade'])})")
            rotulos[rotulo] = posicao

        escolha = st.selectbox("Escolha o item", list(rotulos.keys()))
        indice = rotulos[escolha]
        item_sel = estado["inventario"][indice]
        qtd_max = float(item_sel["quantidade"])
        unidade = item_sel["unidade"]

        # Campo de quantidade: começa cheio (= consumir tudo). Reduza para
        # fazer consumo parcial — o resto continua no inventário.
        # O passo acompanha a unidade (1 unid, 50 g/ml, 0,25 kg/l).
        passo = {"unid": 1.0, "g": 50.0, "ml": 50.0}.get(unidade, 0.25)
        qtd = st.number_input(
            f"Quantidade a registrar ({unidade})",
            min_value=0.01,
            max_value=qtd_max,
            value=qtd_max,
            step=passo,
        )
        if qtd < qtd_max:
            st.caption(f"Consumo parcial: restarão "
                       f"{round(qtd_max - qtd, 4)}{unidade} no inventário.")
        else:
            st.caption("Quantidade total: o item sairá do inventário.")

        col1, col2 = st.columns(2)
        if col1.button("✅ Consumido", type="primary", width="stretch"):
            inv.marcar_consumido(estado["inventario"], estado["historico"],
                                 indice, estado["base"], qtd)
            salvar_estado(estado, USUARIO_ID)
            avisar(f"{qtd}{unidade} de {item_sel['nome']} consumido(s). "
                   "Desperdício evitado! 🌱", "✅")
            st.rerun()
        if col2.button("🗑️ Descartado", width="stretch"):
            inv.marcar_descartado(estado["inventario"], estado["historico"],
                                  indice, estado["base"], qtd)
            salvar_estado(estado, USUARIO_ID)
            avisar(f"{qtd}{unidade} de {item_sel['nome']} descartado(s).", "🗑️")
            st.rerun()


# ---------------------------------------------------------------------------
# PÁGINA: SUGERIR RECEITA
# ---------------------------------------------------------------------------
elif pagina == "🍳 Sugerir receita":
    st.header("🍳 Receita com o que você tem")

    if not estado["inventario"]:
        st.info("Adicione itens primeiro.")
    else:
        # Cada item do inventário vira uma opção com as informações que
        # importam na decisão: quantidade, situação e validade. Os que
        # estão perto de vencer (a sugestão automática) já vêm marcados.
        sugeridos = set(ia.selecionar_ingredientes(estado["inventario"]))
        opcoes = {}   # rótulo mostrado -> nome do alimento
        padrao = []   # rótulos pré-selecionados
        for item in inv.listar_ordenado(estado["inventario"]):
            dias = alertas.dias_para_vencer(item["data_validade"])
            if dias < 0:
                status = f"🔴 vencido há {abs(dias)}d"
            elif dias <= config.DIAS_ALERTA:
                status = f"🟡 vence em {dias}d"
            else:
                status = f"🟢 vence em {dias}d"
            rotulo = (f"{item['nome']} · {item['quantidade']}"
                      f"{item['unidade']} · {status} "
                      f"({data_br(item['data_validade'])})")
            if rotulo not in opcoes:
                opcoes[rotulo] = item["nome"]
                if item["nome"] in sugeridos:
                    padrao.append(rotulo)

        st.caption("Monte a receita do seu jeito: os itens perto de vencer "
                   "já vêm marcados, mas você pode tirar e pôr o que quiser.")
        escolhidos = st.multiselect(
            "Ingredientes do inventário",
            list(opcoes.keys()),
            default=padrao,
            placeholder="Escolha um ou mais ingredientes...",
        )
        # set() elimina nomes repetidos (dois pacotes do mesmo alimento).
        ingredientes = sorted({opcoes[r] for r in escolhidos})

        if ingredientes:
            st.caption("A receita vai usar: **" +
                       ", ".join(ingredientes) + "**")

        gerar = st.button("✨ Gerar receita", type="primary",
                          disabled=not ingredientes)
        if not ingredientes:
            st.info("Selecione pelo menos um ingrediente para gerar.")

        # O painel/alertas podem pedir para já gerar ao abrir a página
        # (usa a pré-seleção automática).
        if st.session_state.pop("gerar_ao_abrir", False) and ingredientes:
            gerar = True

        if gerar:
            with st.spinner("Consultando o chef..."):
                try:
                    receita, origem = ia.sugerir_receita(
                        estado["inventario"], estado["usuario"],
                        ingredientes=ingredientes, usuario_id=USUARIO_ID)
                    # Guardamos na sessão: a receita continua na tela
                    # mesmo depois de outros cliques/reruns.
                    st.session_state["ultima_receita"] = (receita, origem)
                except Exception as e:
                    st.error(f"Falha ao gerar receita: {e}")

        if "ultima_receita" in st.session_state:
            receita, origem = st.session_state["ultima_receita"]
            rotulo = {"ia": "🤖 gerada pela IA agora",
                      "cache": "💾 do cache local (offline)",
                      "generica": "📖 receita base (plano B)"}

            st.divider()
            st.subheader(receita["titulo"])
            st.caption(f"Origem: {rotulo.get(origem, origem)}")

            col_ing, col_prep = st.columns([1, 2], gap="large")
            with col_ing:
                st.markdown("##### 🧺 Ingredientes")
                with st.container(border=True):
                    for ing in receita["ingredientes"]:
                        st.markdown(f"- {ing}")
            with col_prep:
                st.markdown("##### 👨‍🍳 Modo de preparo")
                for i, passo in enumerate(receita["modo_preparo"], start=1):
                    st.markdown(f"**{i}.** {passo}")

            st.divider()
            st.caption("Não curtiu? Clique em ✨ Gerar receita de novo. "
                       "Toda receita gerada fica guardada no "
                       "📖 Livro de receitas para você refazer quando quiser.")


# ---------------------------------------------------------------------------
# PÁGINA: LIVRO DE RECEITAS
# ---------------------------------------------------------------------------
elif pagina == "📖 Livro de receitas":
    st.header("📖 Livro de receitas")
    st.caption("Todas as receitas que você já visualizou, guardadas para "
               "refazer quando bater a fome de novo.")

    livro = ia.listar_livro(USUARIO_ID)
    if not livro:
        st.info("Seu livro ainda está vazio. Gere uma receita em "
                "🍳 Sugerir receita e ela aparece aqui automaticamente.")
    else:
        busca = st.text_input("🔎 Buscar por título ou ingrediente",
                              placeholder="ex.: camarão")
        consulta = busca.strip().lower()

        ORIGENS = {"ia": "🤖 IA", "cache": "💾 cache local",
                   "generica": "receita base"}

        # Percorre do fim para o começo (mais recentes primeiro), levando
        # junto o índice REAL na lista salva — é ele que o botão de
        # remover usa, então a exclusão nunca pega a receita errada.
        exibidas = 0
        for indice in range(len(livro) - 1, -1, -1):
            rec = livro[indice]
            texto_busca = (rec.get("titulo", "") + " " +
                           " ".join(rec.get("ingredientes_usados", []))
                           ).lower()
            if consulta and consulta not in texto_busca:
                continue
            exibidas += 1

            usados = ", ".join(rec.get("ingredientes_usados", []))
            with st.expander(f"{rec.get('titulo', 'Sem título')}  ·  {usados}"):
                vezes = rec.get("vezes", 1)
                st.caption(
                    f"Origem: {ORIGENS.get(rec.get('origem'), rec.get('origem'))} · "
                    f"gerada em {data_hora_br(rec.get('criada_em', '?'))} · "
                    f"vista {vezes} vez(es)"
                )
                col_ing, col_prep = st.columns([1, 2], gap="large")
                with col_ing:
                    st.markdown("**Ingredientes**")
                    for ing in rec.get("ingredientes", []):
                        st.markdown(f"- {ing}")
                with col_prep:
                    st.markdown("**Modo de preparo**")
                    for i, passo in enumerate(rec.get("modo_preparo", []),
                                              start=1):
                        st.markdown(f"**{i}.** {passo}")

                if st.button("🗑️ Remover do livro", key=f"remover_{indice}"):
                    ia.remover_do_livro(indice, USUARIO_ID)
                    avisar("Receita removida do livro.", "🗑️")
                    st.rerun()

        if exibidas == 0:
            st.info("Nenhuma receita encontrada com essa busca.")
        else:
            st.caption(f"{exibidas} de {len(livro)} receita(s).")


# ---------------------------------------------------------------------------
# PÁGINA: IMPACTO
# ---------------------------------------------------------------------------
elif pagina == "🌱 Impacto":
    st.header("🌱 Impacto e economia")
    st.caption("Tudo que você consumiu (em vez de jogar fora) vira "
               "desperdício evitado — e a conta aparece aqui.")

    kg, co2, agua, reais = impacto_seguro(estado["historico"], estado["base"])
    taxa = impacto.taxa_aproveitamento(estado["historico"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🥗 Alimento salvo", f"{kg:.2f} kg")
    col2.metric("💨 CO₂ evitado", f"{co2:.2f} kg")
    col3.metric("💧 Água economizada", f"{agua:.0f} L")
    col4.metric("💰 Dinheiro salvo", f"R$ {reais:.2f}")

    # Equivalências tornam os números abstratos palpáveis.
    if co2 > 0 or agua > 0:
        km_carro = co2 / 0.12       # ~0,12 kg CO₂ por km de carro popular
        banhos = agua / 80          # ~80 L por banho de 8 minutos
        st.caption(f"Isso equivale a ≈ **{km_carro:.0f} km** de carro não "
                   f"rodados e ≈ **{banhos:.0f} banhos** de chuveiro. 🚿🚗")

    st.divider()
    st.subheader("Taxa de aproveitamento")
    st.progress(min(taxa, 1.0),
                text=f"{taxa*100:.0f}% do que saiu do inventário foi "
                     "consumido (e não descartado)")

    st.subheader("Itens consumidos por categoria")
    contagem = impacto.agregar_por_categoria(estado["historico"])
    if not contagem:
        st.info("Sem dados ainda. Marque itens como consumidos para ver o gráfico.")
    else:
        df = pd.DataFrame(
            {"Categoria": list(contagem.keys()), "Itens": list(contagem.values())}
        ).set_index("Categoria")
        st.bar_chart(df, color="#4ECDC4")


# ---------------------------------------------------------------------------
# PÁGINA: CONFIGURAÇÕES
# ---------------------------------------------------------------------------
elif pagina == "⚙️ Configurações":
    st.header("⚙️ Preferências")
    st.caption("A IA usa essas preferências ao criar receitas: restrições "
               "alimentares, alergias e tempo máximo de preparo.")
    u = estado["usuario"]

    # Opções fixas do formulário (rótulos amigáveis -> valor salvo).
    OPCOES_SEXO = {
        "Prefiro não informar": None,
        "Feminino": "feminino",
        "Masculino": "masculino",
    }
    niveis_chaves = list(saude.NIVEIS_ATIVIDADE.keys())

    with st.form("form_config"):
        st.markdown("##### Perfil")
        nome = st.text_input("Seu nome", value=u.get("nome", ""))

        st.markdown("##### Sobre você")
        st.caption("Usado para estimar sua taxa metabólica e gasto "
                   "energético diário (em breve, no painel).")
        col1, col2, col3 = st.columns(3)
        idade = col1.number_input("Idade (anos)", min_value=0, max_value=120,
                                  value=int(u.get("idade") or 0), step=1)
        peso = col2.number_input("Peso (kg)", min_value=0.0, max_value=400.0,
                                 value=float(u.get("peso_kg") or 0.0),
                                 step=0.5, format="%.1f")
        altura = col3.number_input("Altura (cm)", min_value=0, max_value=250,
                                   value=int(u.get("altura_cm") or 0), step=1)

        col4, col5 = st.columns(2)
        rotulos_sexo = list(OPCOES_SEXO.keys())
        sexo_atual = u.get("sexo")
        indice_sexo = 0
        for i, (rotulo_s, valor_s) in enumerate(OPCOES_SEXO.items()):
            if valor_s == sexo_atual:
                indice_sexo = i
        sexo_rotulo = col4.selectbox("Sexo (usado só no cálculo)",
                                     rotulos_sexo, index=indice_sexo)

        nivel_atual = u.get("nivel_atividade", "sedentario")
        indice_nivel = (niveis_chaves.index(nivel_atual)
                        if nivel_atual in niveis_chaves else 0)
        nivel = col5.selectbox(
            "Nível de atividade física",
            niveis_chaves,
            index=indice_nivel,
            format_func=lambda n: saude.NIVEIS_ATIVIDADE[n]["rotulo"],
        )

        st.markdown("##### Preferências de receita")
        col6, col7 = st.columns(2)
        vegetariano = col6.checkbox("🥦 Vegetariano",
                                    value=u.get("vegetariano", False))
        vegano = col7.checkbox("🌱 Vegano", value=u.get("vegano", False))
        alergias_txt = st.text_input(
            "Alergias (separadas por vírgula)",
            value=", ".join(u.get("alergias", [])),
            placeholder="ex.: amendoim, camarão, lactose",
        )
        tempo = st.slider("⏱️ Tempo máx. de receita (min)", 5, 240,
                          value=u.get("tempo_max_receita", 60))
        salvar = st.form_submit_button("Salvar preferências", type="primary")

    if salvar:
        u["nome"] = nome
        u["idade"] = int(idade) or None
        u["peso_kg"] = float(peso) or None
        u["altura_cm"] = int(altura) or None
        u["sexo"] = OPCOES_SEXO[sexo_rotulo]
        u["nivel_atividade"] = nivel
        u["vegetariano"] = vegetariano
        u["vegano"] = vegano
        u["alergias"] = [a.strip() for a in alergias_txt.split(",") if a.strip()]
        u["tempo_max_receita"] = tempo
        salvar_estado(estado, USUARIO_ID)
        avisar("Preferências salvas!", "⚙️")
        st.rerun()

    # PRÉVIA ENERGÉTICA: aparece quando os dados estão completos.
    tmb, gasto = saude.resumo_energetico(u)
    if tmb is not None:
        st.divider()
        st.subheader("Sua estimativa energética")
        col_tmb, col_gasto = st.columns(2)
        col_tmb.metric("Taxa metabólica basal",
                       f"{tmb} kcal/dia",
                       help="Energia mínima que seu corpo gasta em repouso "
                            "(equação de Mifflin-St Jeor).")
        if gasto is not None:
            col_gasto.metric("Gasto diário estimado",
                             f"{gasto} kcal/dia",
                             help="TMB multiplicada pelo seu nível de "
                                  "atividade física.")
        st.caption("Estimativas populacionais, apenas informativas — "
                   "não substituem a avaliação de um profissional de "
                   "saúde ou nutricionista.")
    elif any([u.get("idade"), u.get("peso_kg"), u.get("altura_cm")]):
        st.caption("Preencha idade, peso, altura e sexo para ver sua "
                   "estimativa energética.")


# ---------------------------------------------------------------------------
# PÁGINA: EXPORTAR CSV
# ---------------------------------------------------------------------------
elif pagina == "💾 Exportar CSV":
    st.header("💾 Exportar histórico")
    if not estado["historico"]:
        st.info("Histórico vazio. Nada para exportar ainda.")
    else:
        caminho = persistencia.exportar_csv(estado["historico"])
        st.success(f"Arquivo gerado em: {caminho}")
        with open(caminho, "r", encoding="utf-8") as arquivo:
            conteudo = arquivo.read()
        st.download_button(
            "⬇️ Baixar historico_export.csv",
            data=conteudo,
            file_name="historico_export.csv",
            mime="text/csv",
            type="primary",
        )
        df_hist = pd.DataFrame(estado["historico"])
        if "data" in df_hist.columns:
            df_hist["data"] = df_hist["data"].map(data_br)
        st.dataframe(df_hist, width="stretch", hide_index=True)