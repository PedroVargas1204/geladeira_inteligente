# 🧊 Geladeira Zero

Sistema de gestão inteligente de alimentos para reduzir o desperdício doméstico. Controle o que está na sua geladeira, receba alertas de validade, gere receitas com IA usando os ingredientes prestes a vencer e acompanhe o impacto ambiental e financeiro do que você deixou de jogar fora.

Feito 100% em Python, com duas interfaces: **terminal** (CLI) e **web** (Streamlit).

---

## ✨ Funcionalidades

- **Inventário de alimentos** — cadastre itens com quantidade, unidade e local de armazenamento (geladeira, freezer ou despensa). A validade é sugerida automaticamente a partir de um catálogo de alimentos.
- **Alertas de validade** — veja o que vence nos próximos dias antes que seja tarde.
- **Receitas com IA** — o sistema seleciona os ingredientes mais urgentes e pede uma receita à API do Gemini. Sem internet ou sem chave de API? Um plano B offline garante que você sempre receba uma sugestão.
- **Consumo e descarte** — marque itens como consumidos ou descartados (total ou parcialmente) e alimente o histórico.
- **Impacto ambiental** — calcule quanto alimento você salvou (kg), CO₂ evitado, água economizada e dinheiro poupado (R$), com equivalências do dia a dia (km de carro, banhos de chuveiro).
- **Perfil de saúde** — estimativa de taxa metabólica basal (TMB) e gasto energético diário (TDEE) pela equação de Mifflin-St Jeor.
- **Exportação em CSV** — leve seu histórico para planilhas.
- **Persistência automática** — tudo é salvo em arquivos JSON a cada ação; terminal e interface web compartilham os mesmos dados.

## 🖥️ Interfaces

| Interface | Arquivo | Descrição |
|-----------|---------|-----------|
| Terminal (CLI) | `main.py` | Menu interativo com todas as funcionalidades |
| Web (Streamlit) | `streamlit_app.py` | Painel visual com cards, busca, filtros e notificações |

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
├── main.py            # Ponto de entrada da CLI (menu e roteamento)
├── streamlit_app.py   # Interface web (reusa os mesmos módulos de lógica)
├── config.py          # Constantes e caminhos centralizados
├── persistencia.py    # Leitura/gravação dos arquivos JSON
├── inventario.py      # Regras do inventário e catálogo de alimentos
├── alertas.py         # Cálculo de itens próximos do vencimento
├── ia.py              # Chamada à API do Gemini + fallback offline
├── impacto.py         # Métricas de impacto (kg, CO₂, água, R$)
├── saude.py           # TMB e gasto energético (Mifflin-St Jeor)
├── interface.py       # Utilitários de entrada/saída do terminal
├── test_basico.py     # Testes automatizados das funções puras
└── data/              # Arquivos JSON (inventário, histórico, catálogo...)
```

O projeto segue **baixo acoplamento**: `main.py` e `streamlit_app.py` são apenas camadas de apresentação — toda a regra de negócio vive nos módulos, que são compartilhados entre as duas interfaces.

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

Os testes cobrem as funções puras do projeto: conversão de unidades, taxa de aproveitamento e cálculos de impacto.

## 🛠️ Tecnologias

- [Python](https://www.python.org/) — linguagem principal
- [Streamlit](https://streamlit.io/) — interface web
- [Pandas](https://pandas.pydata.org/) — manipulação de dados na interface
- [Requests](https://requests.readthedocs.io/) — chamadas HTTP à API de IA
- [Google Gemini](https://ai.google.dev/) — geração de receitas

## ⚠️ Aviso

Os cálculos de saúde (TMB/TDEE) são **estimativas populacionais para fins informativos** e não substituem a avaliação de um profissional de saúde ou nutricionista.

## 👤 Autor

**Pedro Vargas dos Santos e Silva** — [@PedroVargas1204](https://github.com/PedroVargas1204)
