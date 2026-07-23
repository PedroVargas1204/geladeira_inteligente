# 🧊 Geladeira Zero

Sistema de gestão inteligente de alimentos para reduzir o desperdício doméstico. Controle o que está na sua geladeira, receba alertas de validade, gere receitas com IA usando os ingredientes prestes a vencer e acompanhe o impacto ambiental e financeiro do que você deixou de jogar fora.

Feito 100% em Python, com duas interfaces: **terminal** (CLI) e **web** (Streamlit).

---

## ✨ Funcionalidades

- **Contas de usuário** — cadastro e login com senha protegida por bcrypt. Cada pessoa tem a sua geladeira: inventário, histórico, preferências e livro de receitas são isolados por conta.
- **Inventário de alimentos** — cadastre itens com quantidade, unidade e local de armazenamento (geladeira, freezer ou despensa). A validade é sugerida automaticamente a partir de um catálogo de alimentos.
- **Alertas de validade** — veja o que vence nos próximos dias antes que seja tarde.
- **Receitas com IA** — o sistema seleciona os ingredientes mais urgentes e pede uma receita à API do Gemini. Sem internet ou sem chave de API? Um plano B offline garante que você sempre receba uma sugestão.
- **Consumo e descarte** — marque itens como consumidos ou descartados (total ou parcialmente) e alimente o histórico.
- **Impacto ambiental** — calcule quanto alimento você salvou (kg), CO₂ evitado, água economizada e dinheiro poupado (R$), com equivalências do dia a dia (km de carro, banhos de chuveiro).
- **Perfil de saúde** — estimativa de taxa metabólica basal (TMB) e gasto energético diário (TDEE) pela equação de Mifflin-St Jeor.
- **Exportação em CSV** — leve seu histórico para planilhas.
- **Persistência em banco de dados** — os dados ficam em um banco SQLite (via SQLAlchemy). Cada ação grava apenas o que mudou, em uma transação atômica, de modo que várias abas ou usuários simultâneos não sobrescrevem o trabalho uns dos outros.

## 🖥️ Interfaces

| Interface | Arquivo | Descrição |
|-----------|---------|-----------|
| Terminal (CLI) | `main.py` | Menu interativo com todas as funcionalidades |
| Web (Streamlit) | `streamlit_app.py` | Painel visual com login, cards, busca, filtros e notificações |

> A CLI opera sempre sobre a conta padrão local e não pede login — ela é uma ferramenta de uso pessoal na própria máquina. O acesso multi-usuário acontece pela interface web.

## 🚀 Como executar

### Pré-requisitos

- Python 3.10+
- pip

### Instalação

```bash
git clone https://github.com/PedroVargas1204/geladeira_inteligente.git
cd geladeira_inteligente
pip install -r requirements.txt
```

### Primeira execução

O projeto usa um banco SQLite criado automaticamente em `geladeira_zero/data/geladeira.db` — não é preciso instalar nem configurar nenhum servidor de banco de dados. O schema também se atualiza sozinho: ao abrir, o app verifica se faltam colunas novas na tabela e as adiciona.

Ao abrir a interface web pela primeira vez, crie a sua conta na aba **Criar conta**. Se você já usava o projeto antes do login existir, o app detecta os dados que estavam ali e oferece uma tela para definir e-mail e senha mantendo todo o inventário.

Se você vem de uma versão bem antiga (que guardava tudo em arquivos JSON), rode uma única vez o script de migração para importar seus dados:

```bash
cd geladeira_zero
python migrar_json_para_db.py
```

### Rodando no terminal

```bash
cd geladeira_zero
python main.py
```

### Rodando a interface web

```bash
cd geladeira_zero
python -m streamlit run streamlit_app.py
```

O app abre automaticamente no navegador (por padrão em `http://localhost:8501`).

## 🤖 Configurando a IA (opcional)

As receitas por IA usam a API do **Google Gemini**. A chave nunca fica no código — ela é lida da variável de ambiente `IA_API_KEY`:

**Linux / macOS**
```bash
export IA_API_KEY="sua-chave-aqui"
```

**Windows (PowerShell)**
```powershell
$env:IA_API_KEY = "sua-chave-aqui"
```

> Sem a chave (ou sem internet), o sistema usa automaticamente um **fallback offline** com receitas do livro local — nada quebra.

## 📁 Estrutura do projeto

```
geladeira_zero/
├── main.py                   # Ponto de entrada da CLI (menu e roteamento)
├── streamlit_app.py          # Interface web (reusa os mesmos módulos de lógica)
├── login_ui.py               # Telas de login/cadastro e sessão do Streamlit
├── auth.py                   # Cadastro, login e hash de senhas (bcrypt)
├── config.py                 # Constantes e caminhos centralizados
├── db.py                     # Modelos SQLAlchemy, conexão e migração de schema
├── persistencia.py           # Leitura dos dados e exportação CSV
├── operacoes.py              # Ações do app: gravações pontuais e atômicas
├── migrar_json_para_db.py    # Importa os dados dos JSONs antigos para o banco
├── inventario.py             # Regras do inventário e catálogo de alimentos
├── alertas.py                # Cálculo de itens próximos do vencimento
├── ia.py                     # Chamada à API do Gemini + fallback offline
├── impacto.py                # Métricas de impacto (kg, CO₂, água, R$)
├── saude.py                  # TMB e gasto energético (Mifflin-St Jeor)
├── interface.py              # Utilitários de entrada/saída do terminal
├── test_basico.py            # Testes automatizados
└── data/                     # Banco SQLite + catálogo de alimentos (JSON)
```

O projeto segue **baixo acoplamento**, em camadas bem definidas:

```
db.py                              tabelas e conexão
persistencia.py                    leitura dos dados
inventario.py / alertas.py / ...   regras puras (não sabem o que é banco)
operacoes.py                       junta regra + gravação, em transação
main.py / streamlit_app.py         apresentação
```

Foi esse isolamento que permitiu migrar de arquivos JSON para SQLite sem alterar uma linha de `inventario.py`, `alertas.py`, `impacto.py` ou `saude.py`.

## 🔐 Segurança

- Senhas nunca são armazenadas: o banco guarda apenas o hash **bcrypt**, que embute um sal aleatório por senha e é propositalmente lento contra força bruta.
- Login com credencial inválida devolve sempre a mesma mensagem, sem revelar se o e-mail existe.
- Toda operação de escrita filtra pelo dono do registro, de forma que uma conta não consegue alterar itens de outra nem informando o identificador diretamente.
- A chave da API de IA vive em variável de ambiente, fora do código e fora do controle de versão.

## 🧪 Testes

```bash
cd geladeira_zero
pip install pytest
pytest -v
```

Ou, sem instalar nada:

```bash
python test_basico.py
```

São 35 testes cobrindo as funções puras do projeto (conversão de unidades, taxa de aproveitamento, cálculos de impacto, busca no catálogo), a autenticação, o isolamento de dados entre contas e as gravações concorrentes. Os testes que tocam o banco usam um arquivo temporário, sem risco para os seus dados reais.

## 🛠️ Tecnologias

- [Python](https://www.python.org/) — linguagem principal
- [Streamlit](https://streamlit.io/) — interface web
- [Pandas](https://pandas.pydata.org/) — manipulação de dados na interface
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM e camada de acesso ao banco
- [SQLite](https://www.sqlite.org/) — banco de dados embutido (um único arquivo, sem servidor)
- [bcrypt](https://github.com/pyca/bcrypt/) — hash de senhas
- [Requests](https://requests.readthedocs.io/) — chamadas HTTP à API de IA
- [Google Gemini](https://ai.google.dev/) — geração de receitas

## 🗺️ Próximos passos

- [x] Autenticação e contas de usuário (cada pessoa com sua geladeira)
- [ ] Geladeira compartilhada entre membros de uma mesma casa
- [ ] Deploy com banco PostgreSQL hospedado

## ⚠️ Aviso

Os cálculos de saúde (TMB/TDEE) são **estimativas populacionais para fins informativos** e não substituem a avaliação de um profissional de saúde ou nutricionista.

## 👤 Autor

**Pedro Vargas dos Santos e Silva** — [@PedroVargas1204](https://github.com/PedroVargas1204)