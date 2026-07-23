# Deploy: PostgreSQL (Neon) + Streamlit Community Cloud

## Arquivos deste pacote

| Arquivo | Situação |
|---|---|
| `geladeira_zero/config.py` | alterado — descobre a qual banco conectar |
| `geladeira_zero/db.py` | alterado — engine e migração compatíveis com Postgres |
| `geladeira_zero/migrar_sqlite_para_postgres.py` | **novo** — leva seus dados para o Neon |
| `requirements.txt` | alterado — driver `psycopg` |

Nenhum outro módulo mudou. `auth.py`, `operacoes.py`, `persistencia.py` e as
interfaces continuam iguais: a troca de banco acontece toda na camada de baixo.

---

## 1. Instalar o driver

```bash
pip install -r requirements.txt
```

## 2. Pegar a string de conexão no Neon

No painel do projeto, em **Connection string**, copie algo como:

```
postgresql://usuario:senha@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

> Essa string contém a senha do banco. Nunca coloque no código nem no git.

## 3. Levar seus dados para lá

**Windows (PowerShell):**
```powershell
cd geladeira_zero
$env:DATABASE_URL = "postgresql://...cole aqui..."
python migrar_sqlite_para_postgres.py
```

**Linux / macOS:**
```bash
cd geladeira_zero
export DATABASE_URL="postgresql://...cole aqui..."
python migrar_sqlite_para_postgres.py
```

O script mostra quantas linhas copiou por tabela. Ele apenas LÊ o SQLite
local — seus dados na máquina continuam intactos como backup.

## 4. Testar apontando para o Neon

Na mesma janela do terminal (com a variável ainda definida):

```bash
python -m streamlit run streamlit_app.py
```

Faça login e confira se o inventário aparece. Se aparecer, o app está
conversando com o banco na nuvem.

> Feche o terminal para "esquecer" a variável e voltar ao SQLite local.
> Sem `DATABASE_URL` definida, o app usa o banco do seu computador — é
> assim que você continua desenvolvendo sem mexer nos dados de produção.

## 5. Publicar no Streamlit Community Cloud

1. Faça commit e push de tudo para o GitHub.
2. Em share.streamlit.io, conecte sua conta do GitHub.
3. Crie o app apontando para:
   - repositório: `PedroVargas1204/geladeira_inteligente`
   - branch: `main`
   - arquivo principal: `geladeira_zero/streamlit_app.py`
4. Em **Advanced settings → Secrets**, cole:

```toml
DATABASE_URL = "postgresql://...sua string do Neon..."
IA_API_KEY = "...sua chave do Gemini..."
```

5. Deploy. Sai um link do tipo `seu-app.streamlit.app`.

---

## Cuidados

- **O app fica público.** Qualquer pessoa com o link pode criar conta.
  Se preferir uma demonstração fechada, avalie criar uma conta de exemplo
  e não divulgar o link amplamente.
- **A chave da IA passa a ser usada por estranhos.** Confira se há limite
  de gasto configurado na sua conta do Google AI Studio.
- **Primeira visita pode demorar alguns segundos.** O Neon desliga o banco
  quando ninguém usa e acorda na primeira consulta. É esperado.
- **Backup.** O plano gratuito não tem backup automático. Seu SQLite local
  é uma cópia do estado no momento da migração — guarde-o.
