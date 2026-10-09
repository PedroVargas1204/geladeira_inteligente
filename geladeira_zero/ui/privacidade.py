"""
privacidade.py
==============
Aviso de privacidade da versão de teste, em linguagem simples.
"""

import streamlit as st

import config

TITULO = "Como cuido dos seus dados"


def texto_privacidade():
    """Devolve o aviso de privacidade em Markdown."""
    return f"""
**Antes de tudo, meu bem: aqui ninguém mexe nos seus dados sem você saber.**

**Quem cuida dos dados.** {config.RESPONSAVEL_DADOS}, estudante da UnB e criador
do Geladeira Zero, nesta versão de teste. Contato: {config.CONTATO_PRIVACIDADE}.

**O que guardamos.** Seu nome (se você informar), e-mail e senha (guardada
embaralhada, nunca como você digitou); os alimentos que você cadastra; o
histórico do que foi consumido ou descartado; as receitas que você gerou; e as
preferências de receita (vegetariano, vegano e tempo de preparo). Nesta versão
não pedimos nenhum dado de saúde.

**Para quê.** Fazer o app funcionar (avisar o que está vencendo, sugerir
receitas e mostrar o seu impacto) e, no fim do teste, entender como o app foi
usado. Não vendemos seus dados nem os usamos para propaganda.

**Com quem compartilhamos.**
- **Google (Gemini):** quando você pede uma receita, enviamos só os
  ingredientes escolhidos, se a receita deve ser vegetariana ou vegana e o
  tempo máximo. Seu nome e seu e-mail não vão. Nesta versão usamos o plano
  gratuito, em que o Google pode usar esse conteúdo para melhorar os produtos
  dele.
- **Streamlit Community Cloud**, onde o app roda, e **Neon**, onde fica o
  banco de dados.
- Esses serviços podem guardar ou processar dados em servidores fora do Brasil.
- Uma receita gerada pode ser reaproveitada para outra pessoa que escolha os
  mesmos ingredientes, sem nada que identifique você.

**Por quanto tempo.** Até {config.PRAZO_GUARDA_DIAS} dias depois do fim do
teste. Depois disso, apagamos todas as contas.

**Seus direitos.** Você pode ver e corrigir suas preferências em Configurações,
baixar seu histórico em Exportar CSV e apagar a conta com todos os dados em
Configurações → Excluir minha conta. Para qualquer outro pedido ou dúvida,
escreva para {config.CONTATO_PRIVACIDADE}.

**Importante.** O app é só para maiores de 18 anos. As receitas são sugestões
automáticas e podem errar: confira os ingredientes, principalmente se você
tiver alergia. Nada aqui substitui nutricionista ou médico.

*Versão de {config.VERSAO_PRIVACIDADE}.*
"""


def mostrar_aviso():
    """Mostra o aviso dentro de um expander, fechado por padrão."""
    with st.expander(TITULO):
        st.markdown(texto_privacidade())
