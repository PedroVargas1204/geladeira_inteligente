# Limpeza do repo + migração JSON → banco de dados

## O que mudou

**Novos arquivos**
- `.gitignore` — ignora `__pycache__/`, ambientes virtuais, `.env` e os dados
  pessoais em `data/` (só `base_alimentos.json` continua versionado).
- `geladeira_zero/db.py` — modelos SQLAlchemy (tabelas) e conexão SQLite.
- `geladeira_zero/migrar_json_para_db.py` — importa seus JSONs antigos
  para o banco (uso único).

**Alterados**
- `geladeira_zero/persistencia.py` — reescrita sobre o banco. A interface de
  dicionários foi mantida: os módulos de lógica não mudaram nada.
- `geladeira_zero/config.py` — ganhou `ARQ_BANCO` e `USUARIO_PADRAO_ID`.
- `geladeira_zero/main.py`, `streamlit_app.py`, `ia.py` — trocaram
  `carregar_json/salvar_json` pelas novas funções de domínio
  (`carregar_estado`, `salvar_estado`, `carregar_livro`, `carregar_cache`...).
- `geladeira_zero/test_basico.py` — o teste de JSON virou um teste de
  ida-e-volta no banco (usando banco temporário).
- `requirements.txt` — versões fixadas + SQLAlchemy.

## Como aplicar no seu repositório

1. Copie os arquivos deste pacote por cima do seu repo (mesma estrutura).

2. Tire do controle de versão o que agora é ignorado (os arquivos continuam
   no seu disco, só saem do git):

   ```
   git rm -r --cached geladeira_zero/__pycache__
   git rm --cached geladeira_zero/data/inventario.json \
                   geladeira_zero/data/historico.json \
                   geladeira_zero/data/usuario.json \
                   geladeira_zero/data/livro_receitas.json \
                   geladeira_zero/data/receitas_cache.json \
                   geladeira_zero/data/historico_export.csv
   ```

   > Atenção: seu `usuario.json` com nome/peso/idade continuará visível no
   > HISTÓRICO do git. Se quiser apagar de verdade do histórico público,
   > pesquise por `git filter-repo` (passo opcional e mais avançado).

3. Instale as dependências e migre seus dados:

   ```
   pip install -r requirements.txt
   cd geladeira_zero
   python migrar_json_para_db.py
   ```

4. Confirme que está tudo funcionando:

   ```
   python test_basico.py          # 27 testes devem passar
   python main.py                 # versão terminal
   python -m streamlit run streamlit_app.py   # versão web
   ```

5. Commit:

   ```
   git add -A
   git commit -m "Migra persistência de JSON para SQLite (SQLAlchemy) e limpa o repo"
   git push
   ```

## Por que assim (e o próximo passo)

- As tabelas de dados pessoais já têm `usuario_id` — o terreno do
  multi-usuário está pronto; hoje tudo pertence ao usuário 1.
- `salvar_estado()` grava tudo em UMA transação: acabou o risco de arquivo
  meio-escrito do JSON.
- A gravação ainda é "espelho" (apaga e regrava as linhas do usuário),
  imitando a semântica antiga. O próximo passo natural, antes do login,
  é trocar isso por operações pontuais (inserir/alterar/remover item a item)
  — aí sim dois usuários simultâneos não se atrapalham em nada.
- Para PostgreSQL no futuro: muda-se a string de conexão em `db.py`
  (e instala-se o driver `psycopg`). Os modelos ficam iguais.
