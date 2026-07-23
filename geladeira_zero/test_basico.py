"""
test_basico.py
==============
Testes automatizados das funções "puras" do projeto (as que só calculam,
sem mexer em disco nem em tela). Servem de REDE DE SEGURANÇA: toda vez que
você alterar o código, rode estes testes para descobrir na hora se algo
quebrou — exatamente o tipo de coisa que pegaria o bug do co2_total.

COMO RODAR:
    Opção 1 (recomendada): instale o pytest uma vez e rode
        pip install pytest
        pytest -v
    Opção 2 (sem instalar nada): rode direto com o Python
        python test_basico.py

    Em ambos os casos, rode de DENTRO da pasta do projeto (onde estão os
    módulos config.py, impacto.py, etc.), para os imports funcionarem.
"""

from datetime import datetime, timedelta

import config
from regras import impacto
from regras import inventario as inv
from regras import alertas, ia
from banco import persistencia


# ===========================================================================
# impacto.converter_para_kg  — conversão de unidades para kg
# ===========================================================================
def test_kg_fica_igual():
    assert impacto.converter_para_kg(2, "kg") == 2


def test_grama_divide_por_mil():
    assert impacto.converter_para_kg(500, "g") == 0.5


def test_litro_tratado_como_kg():
    assert impacto.converter_para_kg(1.5, "l") == 1.5


def test_mililitro_divide_por_mil():
    assert impacto.converter_para_kg(250, "ml") == 0.25


def test_unidade_usa_peso_medio():
    # config.PESO_UNIDADE_KG vale 0.2; 3 unidades = 0.6 kg.
    esperado = 3 * config.PESO_UNIDADE_KG
    assert impacto.converter_para_kg(3, "unid") == esperado


def test_unidade_aceita_sinonimos():
    # "un" e "unidade" devem se comportar como "unid".
    assert impacto.converter_para_kg(1, "un") == config.PESO_UNIDADE_KG
    assert impacto.converter_para_kg(1, "unidade") == config.PESO_UNIDADE_KG


def test_maiusculas_funcionam():
    # A função faz .lower(), então "KG" deve valer como "kg".
    assert impacto.converter_para_kg(2, "KG") == 2


# ===========================================================================
# impacto.taxa_aproveitamento  — consumidos / (consumidos + descartados)
# ===========================================================================
def test_taxa_historico_vazio_eh_zero():
    # Sem histórico, deve devolver 0.0 (e NÃO quebrar com divisão por zero).
    assert impacto.taxa_aproveitamento([]) == 0.0


def test_taxa_tudo_consumido_eh_um():
    historico = [
        {"status": "consumido"},
        {"status": "consumido"},
    ]
    assert impacto.taxa_aproveitamento(historico) == 1.0


def test_taxa_meio_a_meio():
    historico = [
        {"status": "consumido"},
        {"status": "descartado"},
    ]
    assert impacto.taxa_aproveitamento(historico) == 0.5


# ===========================================================================
# impacto.agregar_por_categoria  — conta consumidos por categoria
# ===========================================================================
def test_agregar_ignora_descartados():
    historico = [
        {"status": "consumido", "categoria": "Frutas"},
        {"status": "consumido", "categoria": "Frutas"},
        {"status": "descartado", "categoria": "Frutas"},  # NÃO deve contar
        {"status": "consumido", "categoria": "Vegetais"},
    ]
    contagem = impacto.agregar_por_categoria(historico)
    assert contagem == {"Frutas": 2, "Vegetais": 1}


def test_agregar_historico_vazio():
    assert impacto.agregar_por_categoria([]) == {}


# ===========================================================================
# impacto.calcular_impacto  — soma de impacto (o que quebrou com o co2_total!)
# ===========================================================================
def test_calcular_impacto_vazio_devolve_zeros():
    # Garante que a função inicializa os totais e não dá UnboundLocalError.
    resultado = impacto.calcular_impacto([], {})
    assert resultado == (0.0, 0.0, 0.0, 0.0)


def test_calcular_impacto_soma_consumido():
    base = {
        "tomate": {"co2_kg": 2.0, "agua_litros_kg": 200, "preco_kg": 5.0,
                   "categoria": "Vegetais"},
    }
    historico = [
        {"nome": "tomate", "quantidade": 1, "unidade": "kg",
         "status": "consumido"},
    ]
    kg, co2, agua, reais = impacto.calcular_impacto(historico, base)
    assert kg == 1.0
    assert co2 == 2.0
    assert agua == 200
    assert reais == 5.0


def test_calcular_impacto_ignora_descartado():
    base = {
        "tomate": {"co2_kg": 2.0, "agua_litros_kg": 200, "preco_kg": 5.0,
                   "categoria": "Vegetais"},
    }
    historico = [
        {"nome": "tomate", "quantidade": 1, "unidade": "kg",
         "status": "descartado"},  # descartado não entra na economia
    ]
    assert impacto.calcular_impacto(historico, base) == (0.0, 0.0, 0.0, 0.0)


# ===========================================================================
# alertas.dias_para_vencer  — diferença de dias entre hoje e a validade
# ===========================================================================
def test_dias_para_vencer_futuro():
    # Uma data 5 dias à frente deve devolver 5 (usamos um "hoje" fixo).
    hoje = datetime(2026, 1, 1)
    validade = (hoje + timedelta(days=5)).strftime("%Y-%m-%d")
    assert alertas.dias_para_vencer(validade, hoje) == 5


def test_dias_para_vencer_passado_eh_negativo():
    hoje = datetime(2026, 1, 10)
    validade = (hoje - timedelta(days=3)).strftime("%Y-%m-%d")
    assert alertas.dias_para_vencer(validade, hoje) == -3


# ===========================================================================
# alertas.calcular_alertas  — só itens que vencem em DIAS_ALERTA ou menos
# ===========================================================================
def test_alertas_filtra_e_ordena():
    hoje = datetime(2026, 1, 1)
    inventario = [
        {"nome": "longe",  "data_validade": (hoje + timedelta(days=30)).strftime("%Y-%m-%d")},
        {"nome": "urgente","data_validade": (hoje + timedelta(days=1)).strftime("%Y-%m-%d")},
        {"nome": "hoje",   "data_validade": hoje.strftime("%Y-%m-%d")},
    ]
    resultado = alertas.calcular_alertas(inventario, config.DIAS_ALERTA, hoje)
    # "longe" (30 dias) não entra; sobram 2, ordenados por urgência.
    nomes = [item["nome"] for (item, dias) in resultado]
    assert nomes == ["hoje", "urgente"]


# ===========================================================================
# inventario.sugerir_validade  — data_compra + durabilidade do local
# ===========================================================================
def test_sugerir_validade_soma_dias_do_local():
    dados = {"validade_dias": {"geladeira": 7, "despensa": 30, "freezer": 90}}
    # Compra em 01/01/2026, na geladeira (7 dias) -> vence em 08/01/2026.
    assert inv.sugerir_validade("2026-01-01", dados, "geladeira") == "2026-01-08"


def test_sugerir_validade_local_desconhecido_zero_dias():
    # Local sem durabilidade cadastrada usa 0 -> vence no mesmo dia.
    dados = {"validade_dias": {"geladeira": 7}}
    assert inv.sugerir_validade("2026-01-01", dados, "freezer") == "2026-01-01"


# ===========================================================================
# inventario.buscar_alimento_por_nome  — busca tolerante no catálogo
# ===========================================================================
def test_busca_exata():
    base = {"tomate": {"categoria": "Vegetais"}}
    chave, dados = inv.buscar_alimento_por_nome("tomate", base)
    assert chave == "tomate"
    assert dados is not None


def test_busca_ignora_maiusculas_e_espacos():
    base = {"tomate": {"categoria": "Vegetais"}}
    chave, dados = inv.buscar_alimento_por_nome("  Tomate  ", base)
    assert chave == "tomate"


def test_busca_por_substring():
    base = {"tomate": {"categoria": "Vegetais"}}
    # "tomate cereja" contém "tomate" -> deve encontrar.
    chave, dados = inv.buscar_alimento_por_nome("tomate cereja", base)
    assert chave == "tomate"


def test_busca_nao_encontrada_devolve_none():
    base = {"tomate": {"categoria": "Vegetais"}}
    chave, dados = inv.buscar_alimento_por_nome("abacaxi", base)
    assert chave is None
    assert dados is None


# ===========================================================================
# ia.chave_cache  — chave estável independente da ordem dos ingredientes
# ===========================================================================
def test_chave_cache_independe_da_ordem():
    # "ovo+tomate" e "tomate+ovo" devem gerar a MESMA chave.
    a = ia.chave_cache(["ovo", "tomate"])
    b = ia.chave_cache(["tomate", "ovo"])
    assert a == b


def test_chave_cache_normaliza_maiusculas():
    assert ia.chave_cache(["Tomate"]) == ia.chave_cache(["tomate"])


# ===========================================================================
# persistencia + banco — ida e volta: o que salvo é o que carrego
# ===========================================================================
def test_estado_ida_e_volta_no_banco():
    # Usa um banco TEMPORÁRIO para não tocar no data/geladeira.db real.
    import os
    import tempfile

    from banco import db 

    with tempfile.TemporaryDirectory() as pasta:
        engine_teste = db.criar_engine(os.path.join(pasta, "teste.db"))
        db.usar_engine(engine_teste)
        try:
            estado = {
                "inventario": [{
                    "nome": "tomate", "quantidade": 2.0, "unidade": "unid",
                    "local": "geladeira", "data_compra": "2026-07-01",
                    "data_validade": "2026-07-08",
                }],
                "historico": [{
                    "nome": "leite", "quantidade": 1.0, "unidade": "l",
                    "categoria": "Laticínios", "status": "consumido",
                    "data": "2026-07-02",
                }],
                "usuario": {"nome": "Teste", "vegetariano": True,
                            "alergias": ["amendoim"]},
            }
            persistencia.salvar_estado(estado)
            lido = persistencia.carregar_estado()
            assert lido["inventario"][0]["nome"] == "tomate"
            assert lido["inventario"][0]["data_validade"] == "2026-07-08"
            assert lido["historico"][0]["status"] == "consumido"
            assert lido["usuario"]["vegetariano"] is True
            assert lido["usuario"]["alergias"] == ["amendoim"]
        finally:
            # Fecha as conexões (no Windows, arquivo aberto não pode ser
            # apagado) e zera o engine global: o próximo uso recria o real.
            engine_teste.dispose()
            db.usar_engine(None)


# ===========================================================================
# auth — cadastro, login e proteção da senha
# ===========================================================================
def test_autenticacao_cadastro_e_login():
    import os
    import tempfile

    from banco import auth
    from banco import db

    with tempfile.TemporaryDirectory() as pasta:
        engine_teste = db.criar_engine(os.path.join(pasta, "auth.db"))
        db.usar_engine(engine_teste)
        try:
            # E-mail é normalizado (maiúsculas e espaços não criam outra conta).
            uid = auth.cadastrar(" Pedro@Email.com ", "senhaforte123", "Pedro")
            assert auth.autenticar("pedro@email.com", "senhaforte123") == uid

            # A senha NUNCA fica legível no banco.
            with db.abrir_sessao() as sessao:
                guardado = sessao.get(db.Usuario, uid).senha_hash
            assert "senhaforte123" not in guardado

            # O sal do bcrypt faz a mesma senha gerar hashes diferentes.
            assert auth.gerar_hash("igual") != auth.gerar_hash("igual")

            # Senha errada e e-mail inexistente devolvem a MESMA mensagem,
            # para não revelar quais e-mails estão cadastrados.
            erros = []
            for email, senha in [("pedro@email.com", "errada"),
                                 ("ninguem@email.com", "senhaforte123")]:
                try:
                    auth.autenticar(email, senha)
                    raise AssertionError("deixou entrar sem credencial válida")
                except auth.ErroAutenticacao as erro:
                    erros.append(str(erro))
            assert erros[0] == erros[1]

            # E-mail repetido é recusado.
            try:
                auth.cadastrar("pedro@email.com", "outrasenha123")
                raise AssertionError("aceitou e-mail duplicado")
            except auth.ErroAutenticacao:
                pass
        finally:
            engine_teste.dispose()
            db.usar_engine(None)


def test_senha_curta_e_email_invalido_sao_recusados():
    import os
    import tempfile

    from banco import auth
    from banco import db

    with tempfile.TemporaryDirectory() as pasta:
        engine_teste = db.criar_engine(os.path.join(pasta, "auth2.db"))
        db.usar_engine(engine_teste)
        try:
            for email, senha in [("semarroba", "senhaforte123"),
                                 ("a@b.com", "curta")]:
                try:
                    auth.cadastrar(email, senha)
                    raise AssertionError(f"aceitou cadastro inválido: {email}")
                except auth.ErroAutenticacao:
                    pass
        finally:
            engine_teste.dispose()
            db.usar_engine(None)


# ===========================================================================
# multi-usuário — cada conta enxerga apenas os próprios dados
# ===========================================================================
def test_dados_isolados_entre_usuarios():
    import os
    import tempfile

    from banco import auth
    from banco import db

    with tempfile.TemporaryDirectory() as pasta:
        engine_teste = db.criar_engine(os.path.join(pasta, "multi.db"))
        db.usar_engine(engine_teste)
        try:
            ana = auth.cadastrar("ana@email.com", "senhaforte123", "Ana")
            bob = auth.cadastrar("bob@email.com", "senhaforte456", "Bob")

            persistencia.salvar_estado({
                "inventario": [{"nome": "tomate", "quantidade": 3.0,
                                "unidade": "unid", "local": "geladeira",
                                "data_compra": "2026-07-01",
                                "data_validade": "2026-07-10"}],
                "historico": [], "usuario": {"nome": "Ana"},
            }, ana)
            persistencia.salvar_estado({
                "inventario": [{"nome": "camarão", "quantidade": 500.0,
                                "unidade": "g", "local": "freezer",
                                "data_compra": "2026-07-05",
                                "data_validade": "2026-12-01"}],
                "historico": [], "usuario": {"nome": "Bob"},
            }, bob)

            nomes_ana = [i["nome"] for i in persistencia.carregar_estado(ana)["inventario"]]
            nomes_bob = [i["nome"] for i in persistencia.carregar_estado(bob)["inventario"]]
            assert nomes_ana == ["tomate"]
            assert nomes_bob == ["camarão"]
            assert persistencia.carregar_estado(ana)["usuario"]["nome"] == "Ana"

            # Gravar na conta de um não pode alterar a do outro.
            estado_bob = persistencia.carregar_estado(bob)
            estado_bob["inventario"].append({
                "nome": "ovo", "quantidade": 6.0, "unidade": "unid",
                "local": "geladeira", "data_compra": "2026-07-06",
                "data_validade": "2026-08-01"})
            persistencia.salvar_estado(estado_bob, bob)
            assert len(persistencia.carregar_estado(ana)["inventario"]) == 1
            assert len(persistencia.carregar_estado(bob)["inventario"]) == 2
        finally:
            engine_teste.dispose()
            db.usar_engine(None)


def test_conta_antiga_ganha_login_sem_perder_dados():
    # Cenário real da migração: quem já usava o app quando ele era de um
    # usuário só define e-mail/senha e continua com o mesmo inventário.
    import os
    import tempfile

    from banco import auth
    from banco import db

    with tempfile.TemporaryDirectory() as pasta:
        engine_teste = db.criar_engine(os.path.join(pasta, "legado.db"))
        db.usar_engine(engine_teste)
        try:
            # Conta antiga: tem dados, mas nenhum e-mail.
            with db.abrir_sessao() as sessao:
                sessao.add(db.Usuario(id=1, nome="Pedro"))
                sessao.commit()
            persistencia.salvar_estado({
                "inventario": [{"nome": "camarão", "quantidade": 500.0,
                                "unidade": "g", "local": "freezer",
                                "data_compra": "2026-06-29",
                                "data_validade": "2026-12-26"}],
                "historico": [], "usuario": {"nome": "Pedro"},
            }, 1)

            assert auth.existe_alguma_conta() is False
            assert auth.conta_legada_id() == 1

            auth.definir_credenciais(1, "pedro@email.com", "senhaforte123")
            assert auth.autenticar("pedro@email.com", "senhaforte123") == 1

            # O que mais importa: os dados continuam lá.
            estado = persistencia.carregar_estado(1)
            assert estado["inventario"][0]["nome"] == "camarão"

            # E a tela de ativação não deve aparecer de novo.
            assert auth.conta_legada_id() is None
        finally:
            engine_teste.dispose()
            db.usar_engine(None)


# ===========================================================================
# operacoes — gravações pontuais (o que permite duas abas ao mesmo tempo)
# ===========================================================================
def _banco_temporario(pasta, nome):
    """Prepara um banco vazio e devolve (engine, base_de_alimentos)."""
    from banco import db

    engine = db.criar_engine(f"{pasta}/{nome}")
    db.usar_engine(engine)
    return engine


def _item_teste(nome, quantidade=1.0, unidade="unid"):
    return {"nome": nome, "quantidade": quantidade, "unidade": unidade,
            "local": "geladeira", "data_compra": "2026-07-01",
            "data_validade": "2026-08-01"}


def test_duas_gravacoes_simultaneas_nao_se_apagam():
    # O cenário que a gravação em massa perdia: duas abas carregam o mesmo
    # inventário e cada uma adiciona um item. Com escrita pontual, os dois
    # itens sobrevivem.
    import tempfile

    from banco import auth
    from banco import db
    from banco import operacoes

    with tempfile.TemporaryDirectory() as pasta:
        engine_teste = _banco_temporario(pasta, "conc.db")
        try:
            uid = auth.cadastrar("pedro@email.com", "senhaforte123")
            operacoes.adicionar_item(uid, _item_teste("tomate", 3.0))

            persistencia.carregar_estado(uid)  # "aba A" tira sua foto
            persistencia.carregar_estado(uid)  # "aba B" tira a mesma foto
            operacoes.adicionar_item(uid, _item_teste("leite", 1.0, "l"))
            operacoes.adicionar_item(uid, _item_teste("ovo", 6.0))

            nomes = sorted(i["nome"] for i
                           in persistencia.carregar_estado(uid)["inventario"])
            assert nomes == ["leite", "ovo", "tomate"]
        finally:
            engine_teste.dispose()
            db.usar_engine(None)


def test_consumo_parcial_e_total_pelo_banco():
    import tempfile

    from banco import auth
    from banco import db
    from banco import operacoes

    with tempfile.TemporaryDirectory() as pasta:
        engine_teste = _banco_temporario(pasta, "consumo.db")
        try:
            base = persistencia.carregar_base()
            uid = auth.cadastrar("pedro@email.com", "senhaforte123")
            item_id = operacoes.adicionar_item(uid, _item_teste("tomate", 3.0))

            # Parcial: sobra no inventário e entra 1 registro no histórico.
            movida, tudo, resto = operacoes.consumir(uid, item_id, base, 1.0)
            assert (movida, tudo, resto) == (1.0, False, 2.0)
            estado = persistencia.carregar_estado(uid)
            assert estado["inventario"][0]["quantidade"] == 2.0
            assert len(estado["historico"]) == 1
            assert estado["historico"][0]["status"] == "consumido"

            # Total: o item sai do inventário.
            operacoes.consumir(uid, item_id, base)
            estado = persistencia.carregar_estado(uid)
            assert estado["inventario"] == []
            assert len(estado["historico"]) == 2

            # Consumir de novo (item já foi, como em outra aba) é erro tratado.
            try:
                operacoes.consumir(uid, item_id, base)
                raise AssertionError("consumiu um item que não existe mais")
            except operacoes.ItemNaoEncontrado:
                pass
        finally:
            engine_teste.dispose()
            db.usar_engine(None)


def test_usuario_nao_altera_item_de_outro():
    # Proteção importante: passar o id de um item alheio não pode funcionar.
    import tempfile

    from banco import auth
    from banco import db
    from banco import operacoes

    with tempfile.TemporaryDirectory() as pasta:
        engine_teste = _banco_temporario(pasta, "seguranca.db")
        try:
            base = persistencia.carregar_base()
            ana = auth.cadastrar("ana@email.com", "senhaforte123", "Ana")
            bob = auth.cadastrar("bob@email.com", "senhaforte456", "Bob")
            item_da_ana = operacoes.adicionar_item(ana, _item_teste("tomate", 3.0))

            for acao in (operacoes.consumir, operacoes.descartar):
                try:
                    acao(bob, item_da_ana, base)
                    raise AssertionError("Bob alterou um item da Ana")
                except operacoes.ItemNaoEncontrado:
                    pass

            estado_ana = persistencia.carregar_estado(ana)
            assert len(estado_ana["inventario"]) == 1
            assert estado_ana["historico"] == []
        finally:
            engine_teste.dispose()
            db.usar_engine(None)


def test_salvar_perfil_nao_toca_no_inventario():
    import tempfile

    from banco import auth
    from banco import db
    from banco import operacoes

    with tempfile.TemporaryDirectory() as pasta:
        engine_teste = _banco_temporario(pasta, "perfil.db")
        try:
            uid = auth.cadastrar("pedro@email.com", "senhaforte123", "Pedro")
            operacoes.adicionar_item(uid, _item_teste("tomate", 3.0))

            operacoes.salvar_perfil(uid, {"nome": "Pedro V",
                                          "tempo_max_receita": 90})
            estado = persistencia.carregar_estado(uid)
            assert len(estado["inventario"]) == 1
            assert estado["usuario"]["nome"] == "Pedro V"

            # Mandar só um campo não apaga os outros.
            operacoes.salvar_perfil(uid, {"peso_kg": 76.0})
            estado = persistencia.carregar_estado(uid)
            assert estado["usuario"]["nome"] == "Pedro V"
            assert estado["usuario"]["peso_kg"] == 76.0
        finally:
            engine_teste.dispose()
            db.usar_engine(None)


# ===========================================================================
# EXECUÇÃO SEM PYTEST: roda tudo com asserts e conta os resultados.
# (Permite "python test_basico.py" mesmo sem o pytest instalado.)
# ===========================================================================
if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passou = 0
    falhou = 0
    for teste in testes:
        try:
            teste()
            print(f"  ok   {teste.__name__}")
            passou += 1
        except AssertionError as e:
            print(f"  FALHOU {teste.__name__}  -> {e}")
            falhou += 1
        except Exception as e:
            print(f"  ERRO   {teste.__name__}  -> {type(e).__name__}: {e}")
            falhou += 1
    print("-" * 50)
    print(f"{passou} passaram, {falhou} falharam, de {len(testes)} testes.")