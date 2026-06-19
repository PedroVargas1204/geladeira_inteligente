# Roteiro de Estudos — Projeto **Geladeira Zero**
### Aprendendo o projeto inteiro do zero, código por código

> Este guia foi feito para quem **não sabe nada** ainda. Ele te ensina os
> conceitos de Python conforme eles aparecem, monta o projeto inteiro na
> ordem certa e explica **cada arquivo bloco a bloco**. No fim, você consegue
> reescrever tudo sozinho e entender cada linha.
>
> **Regra de ouro do projeto (vinda dos slides):** *ninguém faz commit sem
> entender linha a linha.* Este roteiro existe para você cumprir exatamente isso.

---

## Como usar este roteiro

1. Leia a **Parte 0** (visão geral + conceitos) com calma. Não pule.
2. Crie a pasta do projeto e os arquivos **na ordem das partes 2 a 9**. A ordem
   é proposital: cada módulo só usa o que já foi criado antes dele.
3. Para cada arquivo: **copie, leia a explicação, rode o teste sugerido.**
4. Sempre que travar num conceito, volte na **Parte 0.4 (glossário)**.

Você vai precisar só de **Python 3** instalado. A IA é opcional (o programa
funciona offline graças ao "plano B").

---
---

# PARTE 0 — Fundamentos antes do código

## 0.1 O que é o Geladeira Zero (em uma frase)

Um **aplicativo de terminal** (sem janelas, só texto) escrito em **Python**
que combate o desperdício de comida: você cadastra o que tem na geladeira, ele
calcula a validade de cada item, avisa o que está perto de vencer, sugere
receitas (com IA, ou um plano B offline) e mostra quanto você economizou de
dinheiro, CO₂ e água. Os dados ficam salvos em **arquivos JSON** entre uma
sessão e outra.

O menu que o usuário vê:

```
[1] Adicionar item ao inventário
[2] Ver inventário (ordenado por validade)
[3] Ver alertas de vencimento
[4] Sugerir receita com o que tenho
[5] Marcar consumido / descartado
[6] Ver impacto e economia
[7] Configurações (preferências)
[8] Exportar histórico (CSV)
[0] Sair
```

## 0.2 A grande ideia: dividir para conquistar

Em vez de um arquivo gigante com tudo, o projeto é dividido em **8 módulos**
(arquivos `.py`) + um arquivo de **configuração**. Cada módulo tem **uma
responsabilidade só**. Isso se chama *separação de responsabilidades* e é o que
torna o código possível de entender.

| Arquivo | Responsabilidade |
|---|---|
| `config.py` | Guardar todas as constantes e caminhos num lugar só |
| `persistencia.py` | Ler/gravar arquivos (JSON e CSV). A "fundação" |
| `interface.py` | Desenhar telas e validar tudo que o usuário digita |
| `inventario.py` | Estoque: cadastrar, listar, validade, mover ao histórico |
| `alertas.py` | Descobrir o que está vencendo |
| `ia.py` | Gerar receita com IA + plano B se a IA falhar |
| `impacto.py` | Calcular economia (kg, CO₂, água, R$) |
| `main.py` | O "maestro": junta tudo e mostra o menu |

## 0.3 A arquitetura: quem depende de quem

Pense numa **fila** onde cada caixa só conhece as que estão à sua **esquerda**.
Ninguém olha para a direita. Isso se chama **baixo acoplamento** e é o segredo
para o código não virar um espaguete:

```
config + persistencia   →   inventario · alertas   →   ia   →   impacto   →   main · interface
    (a base de tudo)          (estoque e prazos)     (receitas)  (cálculos)     (amarra tudo)
```

Lendo da esquerda para a direita: `config` e `persistencia` não dependem de
ninguém. `inventario` usa `config` e `persistencia`. `ia` usa `alertas`. E o
`main` lá no fim usa todo mundo, mas ninguém usa o `main`. Por isso a gente
**constrói da esquerda para a direita** neste roteiro.

A pasta `data/` guarda os 5 arquivos JSON (a "memória" do programa):

- `base_alimentos.json` — catálogo: validade, preço, CO₂ e água de cada alimento
- `inventario.json` — itens ativos na geladeira/despensa
- `historico.json` — itens já consumidos ou descartados
- `usuario.json` — nome e preferências (vegetariano, alergias…)
- `receitas_cache.json` — receitas já geradas, para funcionar offline

## 0.4 Glossário mínimo de Python (volte aqui quando travar)

**Variável** — um nome que guarda um valor. `dias = 3`.

**String** — texto entre aspas. `"tomate"`. Um **f-string** é uma string que
permite encaixar valores com `{}`: `f"Faltam {dias} dias"` vira
`"Faltam 3 dias"`.

**Lista** `[]` — uma sequência ordenada de valores.
`frutas = ["maca", "banana"]`. Acessa pela posição: `frutas[0]` é `"maca"`.

**Dicionário** `{}` — pares **chave: valor**, como uma agenda.
`item = {"nome": "ovo", "qtd": 12}`. Acessa pela chave: `item["nome"]`.

**Tupla** `()` — como uma lista, mas **fixa**. Muito usada para devolver
**vários valores de uma vez** de uma função: `return kg, co2, agua`.

**Função** — um bloco de código com nome, que recebe entradas (parâmetros) e
pode **devolver** (`return`) um resultado. Define-se com `def`.

**Módulo** — um arquivo `.py`. Você usa o de outro arquivo com `import`.

**Condicional** `if / elif / else` — executa um trecho **se** uma condição for
verdadeira.

**Laço** (loop):
- `for x in lista:` — repete uma vez para cada item da lista.
- `while condição:` — repete **enquanto** a condição for verdadeira.

**Exceção** — um erro em tempo de execução. `try / except` permite **tentar**
algo arriscado e **tratar** o erro em vez de o programa quebrar.

**JSON** — um formato de texto para guardar listas e dicionários em arquivo.
É praticamente igual à sintaxe de Python.

Guarde esses sete conceitos. O projeto inteiro é feito de combinações deles.

---
---

# PARTE 1 — Preparando o terreno

Crie esta estrutura de pastas e arquivos (ainda vazios; vamos preenchê-los):

```
geladeira_zero/
├── config.py
├── persistencia.py
├── interface.py
├── inventario.py
├── alertas.py
├── ia.py
├── impacto.py
├── main.py
└── data/
    ├── base_alimentos.json
    ├── inventario.json
    ├── historico.json
    ├── usuario.json
    └── receitas_cache.json
```

No terminal:

```bash
mkdir -p geladeira_zero/data
cd geladeira_zero
```

Vamos começar pela **esquerda** da arquitetura: a fundação.

---
---

# PARTE 2 — A fundação: `config.py`

**Responsável nos slides: Pessoa D.**

### Por que existe

Imagine que o número "3 dias de alerta" aparece em 5 arquivos. Se um dia você
quiser mudar para 5 dias, teria que caçar os 5 lugares. O `config.py` resolve
isso: **todo número e caminho de arquivo mora aqui**. Os slides chamam isso de
*evitar "números mágicos" espalhados pelo código*.

### O código

```python
import os

# CAMINHOS
PASTA_BASE = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA_BASE, "data")

ARQ_BASE_ALIMENTOS = os.path.join(PASTA_DADOS, "base_alimentos.json")
ARQ_INVENTARIO     = os.path.join(PASTA_DADOS, "inventario.json")
ARQ_HISTORICO      = os.path.join(PASTA_DADOS, "historico.json")
ARQ_USUARIO        = os.path.join(PASTA_DADOS, "usuario.json")
ARQ_RECEITAS_CACHE = os.path.join(PASTA_DADOS, "receitas_cache.json")
ARQ_EXPORT_CSV     = os.path.join(PASTA_DADOS, "historico_export.csv")

# REGRAS DE NEGÓCIO
DIAS_ALERTA = 3
DIAS_ALERTA_AMPLO = 7
TIMEOUT_IA = 20
PESO_UNIDADE_KG = 0.2
PERIODO_IMPACTO_DIAS = 30
LOCAIS_VALIDOS = ["geladeira", "despensa", "freezer"]

# CONFIGURAÇÃO DA IA
IA_API_URL = "https://api.anthropic.com/v1/messages"
IA_MODEL   = "claude-sonnet-4-6"
IA_NOME_VARIAVEL_CHAVE = "IA_API_KEY"
```

### Explicando bloco a bloco

**`import os`** — `os` é um módulo da biblioteca padrão do Python para falar com
o sistema operacional (arquivos, pastas, etc.). Já vem com o Python.

**`__file__`** — uma variável mágica que o Python preenche com o caminho do
arquivo atual (aqui, o próprio `config.py`).

**`os.path.abspath(__file__)`** transforma isso num caminho **absoluto**
completo (ex.: `/home/voce/geladeira_zero/config.py`).

**`os.path.dirname(...)`** corta o nome do arquivo e deixa só a **pasta**
(`/home/voce/geladeira_zero`). Resultado: `PASTA_BASE` é a pasta do projeto.

Por que esse malabarismo? Para que o programa **ache os dados rodando de
qualquer lugar** (slide 4). Se usássemos só `"data/..."`, o programa só acharia
os arquivos se você estivesse exatamente na pasta certa ao rodar.

**`os.path.join(a, b)`** junta pedaços de caminho com a barra certa do sistema
(`/` no Linux/Mac, `\` no Windows). Nunca escreva caminhos com `+` e barras na
mão; use `os.path.join`.

**As constantes de regra** (`DIAS_ALERTA = 3`, etc.) são só variáveis. O truque
é a **disciplina**: como combinamos que TODA constante mora aqui, qualquer
outro arquivo vai escrever `config.DIAS_ALERTA` em vez de cravar o número `3`.

**A chave da IA NÃO está aqui.** Só o *nome* da variável de ambiente
(`IA_API_KEY`). Senha nunca vai no código — você verá o porquê no módulo `ia.py`.

> **Conceito de APC desta parte:** variáveis, listas, strings, e a ideia de
> *constantes centralizadas*.

---
---

# PARTE 3 — Os dados em disco: a pasta `data/`

Antes de escrever quem lê os arquivos, precisamos dos arquivos. JSON é só texto
com a mesma cara de listas e dicionários do Python.

### `base_alimentos.json` — o catálogo

Cada alimento é uma **chave** (o nome) apontando para um **dicionário** com suas
informações. Exemplo de uma entrada:

```json
{
  "tomate": {
    "categoria": "Legumes",
    "sinonimos": ["tomate italiano", "tomate cereja", "tomates"],
    "validade_dias": { "geladeira": 7, "despensa": 3, "freezer": 60 },
    "preco_kg": 8.0,
    "co2_kg": 1.4,
    "agua_litros_kg": 214
  }
}
```

Leia assim: o tomate é da categoria *Legumes*; pode ser chamado de outras
formas (*sinônimos*); dura 7 dias na geladeira, 3 na despensa, 60 no freezer;
custa R$ 8/kg; produzir 1 kg emite 1,4 kg de CO₂ e gasta 214 L de água. São
esses números que alimentam os cálculos de validade e de impacto.

> O arquivo completo (com 10 alimentos) está nos arquivos do projeto que
> acompanham este roteiro. Você pode adicionar mais seguindo o mesmo formato.

### Os outros quatro arquivos começam "vazios"

São a memória que o programa vai preenchendo. No começo:

```jsonc
// inventario.json
[]

// historico.json
[]

// receitas_cache.json
{}

// usuario.json
{
  "nome": "",
  "vegetariano": false,
  "vegano": false,
  "alergias": [],
  "tempo_max_receita": 60
}
```

`[]` é uma **lista vazia** (ainda não há itens). `{}` é um **dicionário vazio**.
`false` é o "falso" do JSON (em Python vira `False`).

> **Conceito de APC desta parte:** estrutura de dados em JSON (listas e
> dicionários aninhados) — exatamente o que o Python carrega para a memória.

---
---

# PARTE 4 — A fundação que toca o disco: `persistencia.py`

**Responsável: Pessoa D.** É o **único** módulo que abre arquivos. Todos os
outros pedem dados a ele. Se um dia trocarmos JSON por um banco de dados, só
este arquivo muda.

### Função 1 — `carregar_json`: ler sem quebrar

```python
import json
import csv
import config

def carregar_json(caminho, padrao):
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao
```

Linha a linha:

- **`import json`** — módulo padrão que converte entre texto JSON e
  listas/dicionários Python.
- **`def carregar_json(caminho, padrao):`** — define a função. Recebe o
  `caminho` do arquivo e um valor `padrao` para devolver se algo der errado.
- **`try:`** — "tente fazer isto, que pode falhar".
- **`with open(caminho, "r", encoding="utf-8") as arquivo:`** — abre o arquivo
  para **leitura** (`"r"`). O `encoding="utf-8"` garante acentos corretos. O
  `with` é importante: ele **fecha o arquivo sozinho** ao terminar, mesmo se
  der erro.
- **`return json.load(arquivo)`** — lê o texto e transforma em lista/dicionário
  Python, devolvendo o resultado.
- **`except (FileNotFoundError, json.JSONDecodeError):`** — se o arquivo **não
  existe** (primeira execução do programa) **ou** está **corrompido**, em vez
  de quebrar, caímos aqui.
- **`return padrao`** — devolvemos o valor seguro (ex.: `[]` ou `{}`).

Isso é o que o slide 4 chama de **defensivo**: a primeira execução e arquivos
estragados **não derrubam** o programa. É um dos pontos mais importantes do
projeto.

### Função 2 — `salvar_json`: gravar bonito e com acentos

```python
def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=2, ensure_ascii=False)
```

- **`"w"`** — abre para **escrita** (write); apaga o conteúdo antigo e grava o
  novo.
- **`json.dump(dados, arquivo, ...)`** — escreve `dados` (lista/dicionário) como
  texto JSON dentro do arquivo.
- **`indent=2`** — formata com 2 espaços de recuo: o arquivo fica **legível**
  por humanos.
- **`ensure_ascii=False`** — **preserva acentos**. Sem isso, "Maçã" viraria
  `"Ma\u00e7\u00e3"` no arquivo (slide 4).

### Função 3 — `buscar_alimento_na_base`: fonte única de consulta

```python
def buscar_alimento_na_base(nome, base):
    chave = nome.strip().lower()
    return base.get(chave)
```

- **`nome.strip().lower()`** — `.strip()` remove espaços nas pontas; `.lower()`
  deixa tudo minúsculo. Assim `" Tomate "` vira `"tomate"`.
- **`base.get(chave)`** — `base` é o dicionário do catálogo. `.get(chave)`
  devolve o valor da chave, **ou `None`** se a chave não existir (diferente de
  `base[chave]`, que quebraria com erro). Devolver `None` é mais seguro.

O slide 4 chama isso de **fonte única**: a regra de "como consultar o catálogo"
mora em um lugar só, sem ser repetida pelo projeto.

### Função 4 — `exportar_csv`: o histórico em planilha (RF11)

```python
def exportar_csv(historico, caminho=config.ARQ_EXPORT_CSV):
    colunas = ["nome", "quantidade", "unidade", "categoria", "status", "data"]
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        for item in historico:
            linha = {coluna: item.get(coluna, "") for coluna in colunas}
            escritor.writerow(linha)
    return caminho
```

- **`csv.DictWriter`** — sabe transformar **dicionários** em linhas de CSV. Você
  diz a ordem das colunas com `fieldnames`.
- **`escritor.writeheader()`** — escreve a primeira linha com os nomes das
  colunas.
- **O `for`** percorre cada item do histórico. Para cada um, monta uma `linha`
  pegando só as colunas que queremos. O `{... for ...}` é uma **dict
  comprehension** (jeito compacto de montar dicionário). O `item.get(coluna, "")`
  usa `""` se a coluna faltar — nunca quebra.
- **`escritor.writerow(linha)`** grava aquela linha no arquivo.

Resultado: **uma linha por item do histórico** — exatamente o RF11.

### Teste rápido deste módulo

```python
import persistencia
base = persistencia.carregar_json("data/base_alimentos.json", {})
print(persistencia.buscar_alimento_na_base("Tomate", base))  # acha mesmo com maiúscula
print(persistencia.carregar_json("data/nao_existe.json", []))  # devolve []  (defensivo)
```

> **Conceitos de APC desta parte:** arquivos (JSON/CSV), tratamento de exceções
> (`try/except`), dicionários, `dict.get`, e *dict comprehension*.

---
---

# PARTE 5 — A casca e os porteiros: `interface.py`

**Responsável: Pessoa A.** Dois trabalhos: **desenhar as telas** e **validar
tudo que o usuário digita** (RNF03). Nenhum dado inválido pode entrar.

### Desenhando telas com alinhamento

```python
import os
from datetime import datetime

LARGURA = 60

def desenhar_titulo(texto):
    print("+" + "-" * (LARGURA + 2) + "+")
    print(f"| {texto.upper():<{LARGURA}} |")
    print("+" + "-" * (LARGURA + 2) + "+")
```

A mágica está no **f-string** `{texto.upper():<{LARGURA}}`:

- `texto.upper()` deixa o título em MAIÚSCULAS.
- `:<` significa **alinhar à esquerda e preencher com espaços**.
- `{LARGURA}` diz **quantas colunas** ocupar (60).

Então qualquer título, curto ou longo, ocupa sempre 60 colunas — e a borda `|`
da direita **sempre cai no mesmo lugar**. É assim que o slide 5 descreve as
"molduras com bordas alinhadas em colunas fixas". O `"-" * (LARGURA+2)` repete o
traço para formar a linha de cima/baixo.

```python
def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")
```

`os.name` é `"nt"` no Windows e `"posix"` no Linux/Mac. O comando de limpar tela
é diferente em cada um (`cls` vs `clear`), então escolhemos na hora — funciona
em todos (slide 5).

### Os "porteiros": leitores que só aceitam dado válido

Esta é a ideia central do arquivo. **Cada leitor é um `while True`** (laço
infinito) que **só termina com `return`** quando o dado é válido. Se for
inválido, avisa e pergunta de novo.

```python
def ler_inteiro(prompt, minimo=None, maximo=None):
    while True:
        bruto = input(prompt).strip()
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
```

Passo a passo:

- **`while True:`** — repete para sempre… até um `return` nos tirar de dentro.
- **`input(prompt)`** — mostra a pergunta e lê o que a pessoa digitar (sempre
  como texto).
- **`int(bruto)`** — tenta converter o texto em número inteiro. Se a pessoa
  digitou "abc", isso dá `ValueError`, e o `except` mostra o erro e
  **`continue`** (volta ao topo do laço, perguntando de novo).
- Os dois `if` checam limites mínimo/máximo, quando informados.
- **`return valor`** só é alcançado quando o número passou em **todas** as
  checagens. É a saída do laço.

Esse padrão se repete em todos os leitores. Veja dois detalhes especiais:

```python
def ler_float(prompt, minimo=0.0):
    while True:
        bruto = input(prompt).strip().replace(",", ".")
        try:
            valor = float(bruto)
        except ValueError:
            print("  ! Digite um número válido (ex.: 1,5).")
            continue
        if valor < minimo:
            print(f"  ! O valor mínimo é {minimo}.")
            continue
        return valor
```

O `.replace(",", ".")` aceita **vírgula OU ponto**: o brasileiro digita "1,5" e
o programa entende 1.5 (slide 5).

```python
def ler_data(prompt):
    while True:
        bruto = input(prompt + " (DD/MM/AAAA): ").strip()
        try:
            data = datetime.strptime(bruto, "%d/%m/%Y")
            return data.strftime("%Y-%m-%d")
        except ValueError:
            print("  ! Data inválida. Use DD/MM/AAAA (ex.: 25/12/2026).")
```

- **`datetime.strptime(texto, formato)`** transforma texto em data **e valida
  de verdade**: "31/02/2026" é recusado, porque fevereiro não tem dia 31
  (slide 5). Datas impossíveis caem no `except`.
- **`data.strftime("%Y-%m-%d")`** devolve a data no formato **AAAA-MM-DD**.
  Usamos esse formato internamente porque, como texto, ele **ordena
  corretamente** (2026-06-09 vem antes de 2026-06-10) e é fácil de comparar.

Os outros leitores (`ler_texto`, `ler_opcao`, `ler_sim_nao`) seguem o mesmo
molde. `ler_opcao` recebe a lista de opções válidas e só aceita uma delas;
`ler_sim_nao` devolve `True`/`False`.

> **Conceitos de APC desta parte:** `while True` + `return` como padrão de
> validação, `try/except`, conversão de tipos (`int`, `float`), f-strings com
> alinhamento, e `datetime.strptime/strftime`.

---
---

# PARTE 6 — O miolo do estoque: `inventario.py`

**Responsável: Pessoa B.** Aqui mora a lógica do produto: encontrar alimentos,
calcular validade, listar e mover itens para o histórico. Ele **usa** `config`
e `persistencia` (que já existem).

### Busca tolerante: aceitar o jeito que a pessoa escreve

```python
from datetime import datetime, timedelta
import config
import persistencia

def buscar_alimento_por_nome(nome, base):
    consulta = nome.strip().lower()
    dados = persistencia.buscar_alimento_na_base(consulta, base)
    if dados is not None:
        return consulta, dados
    for chave, dados in base.items():
        sinonimos = dados.get("sinonimos", [])
        if consulta in [s.lower() for s in sinonimos]:
            return chave, dados
        if chave in consulta or consulta in chave:
            return chave, dados
    return None, None
```

A pessoa pode escrever "Tomate", "tomate italiano" ou "tomate cereja maduro".
A busca tenta, **em ordem** (slide 6):

1. **Chave exata** — reaproveita `persistencia.buscar_alimento_na_base`. Se
   achou, devolve.
2. **Sinônimos** — percorre o catálogo (`base.items()` dá pares
   chave/valor) e vê se a consulta bate com algum sinônimo.
3. **Substring** — `chave in consulta` é `True` se "tomate" estiver *dentro de*
   "tomate cereja maduro". `in` em texto verifica se um pedaço aparece no outro.

Repare que a função **devolve dois valores**: a `chave` oficial e os `dados`.
Quem chama recebe `chave, dados = buscar_alimento_por_nome(...)`. Se não achou,
devolve `None, None`.

### Calcular a validade: aritmética com datas (RF03)

```python
def sugerir_validade(data_compra, dados_alimento, local):
    dias = dados_alimento["validade_dias"].get(local, 0)
    data = datetime.strptime(data_compra, "%Y-%m-%d")
    validade = data + timedelta(days=dias)
    return validade.strftime("%Y-%m-%d")
```

- `dados_alimento["validade_dias"]` é o dicionário tipo
  `{"geladeira": 7, "despensa": 3, "freezer": 60}`. `.get(local, 0)` pega os
  dias **daquele local** (0 se o local não existir).
- `datetime.strptime(...)` transforma a data de compra (texto) em data de
  verdade.
- **`data + timedelta(days=dias)`** — esta é a chave. Um `timedelta` é uma
  *duração*. Somar uma data com uma duração dá uma **nova data** no futuro. Se
  comprei tomate dia 10 e ele dura 7 dias na geladeira, a validade é dia 17.
  É exatamente o que o slide 6 chama de "datetime + timedelta".
- Devolve a validade como texto `AAAA-MM-DD`.

### Listar ordenado por validade (RF04)

```python
def listar_ordenado(inventario):
    return sorted(inventario, key=lambda item: item["data_validade"])
```

- **`sorted(lista, key=...)`** devolve uma **nova** lista ordenada.
- **`key=lambda item: item["data_validade"]`** diz *por qual critério* ordenar.
  Um **lambda** é uma mini-função sem nome: aqui, "dado um item, use a data de
  validade dele para ordenar". Como as datas estão em `AAAA-MM-DD`, ordenar as
  strings já coloca quem vence primeiro no topo (slide 6).

> Esse par **`sort` + `lambda`** é um dos conceitos que os slides destacam.
> Memorize o formato: `sorted(lista, key=lambda x: x[algo])`.

### Mover para o histórico ao consumir/descartar

```python
def _mover_para_historico(inventario, historico, indice, status, base):
    item = inventario.pop(indice)
    _, dados = buscar_alimento_por_nome(item["nome"], base)
    categoria = dados["categoria"] if dados else "Outros"
    registro = {
        "nome": item["nome"],
        "quantidade": item["quantidade"],
        "unidade": item["unidade"],
        "categoria": categoria,
        "status": status,
        "data": datetime.now().strftime("%Y-%m-%d"),
    }
    historico.append(registro)
    return inventario, historico

def marcar_consumido(inventario, historico, indice, base):
    return _mover_para_historico(inventario, historico, indice, "consumido", base)

def marcar_descartado(inventario, historico, indice, base):
    return _mover_para_historico(inventario, historico, indice, "descartado", base)
```

- **`inventario.pop(indice)`** faz duas coisas ao mesmo tempo: **remove** o item
  daquela posição da lista **e devolve** o item removido, que guardamos em
  `item`.
- Buscamos a `categoria` no catálogo (para o módulo de impacto agrupar depois).
  O `dados["categoria"] if dados else "Outros"` é um **if em uma linha**: usa a
  categoria se achou os dados, senão "Outros".
- **`datetime.now()`** é a data/hora de agora; `.strftime("%Y-%m-%d")` guarda só
  a data.
- **`historico.append(registro)`** adiciona o registro ao fim da lista de
  histórico.

O `_` no começo de `_mover_para_historico` é uma convenção que significa "função
interna, de uso privado do módulo". `marcar_consumido` e `marcar_descartado` são
só atalhos que chamam ela com o `status` certo — assim não repetimos código.

> **Conceitos de APC desta parte:** `datetime`/`timedelta`, `sort` + `lambda`,
> `in` em strings/listas, `list.pop`/`list.append`, retorno de múltiplos valores
> (tupla), e funções auxiliares para não repetir código.

---
---

# PARTE 7 — O que está vencendo: `alertas.py`

**Responsável: Pessoa B.** Pequeno e focado: descobrir o que vence logo (RF05).
Usa `config`.

```python
from datetime import datetime
import config

def dias_para_vencer(data_validade, hoje=None):
    if hoje is None:
        hoje = datetime.now()
    validade = datetime.strptime(data_validade, "%Y-%m-%d")
    return (validade - hoje).days

def calcular_alertas(inventario, dias_alerta=config.DIAS_ALERTA, hoje=None):
    if hoje is None:
        hoje = datetime.now()
    alertas = []
    for item in inventario:
        dias = dias_para_vencer(item["data_validade"], hoje)
        if dias <= dias_alerta:
            alertas.append((item, dias))
    alertas.sort(key=lambda par: par[1])
    return alertas
```

### `dias_para_vencer`

- **`(validade - hoje)`** — subtrair uma data de outra dá um `timedelta` (uma
  duração). **`.days`** pega o número de dias dessa duração.
- O resultado pode ser **negativo** (se já venceu), `0` (vence hoje) ou positivo
  (faltam X dias). Esse sinal será usado para escrever "VENCIDO", "VENCE HOJE" ou
  "vence em X dias".
- O parâmetro `hoje=None` com `if hoje is None: hoje = datetime.now()` é um
  truque útil: por padrão usa a data real, mas permite **passar uma data fixa
  nos testes** (para o teste não depender do dia em que você roda).

### `calcular_alertas`

- Percorre o inventário; para cada item calcula quantos dias faltam.
- **`if dias <= dias_alerta:`** seleciona quem vence em `DIAS_ALERTA` (3) dias
  **ou menos** — inclusive os já vencidos (dias negativos).
- **`alertas.append((item, dias))`** — guarda uma **tupla** `(item, dias)`. Os
  slides destacam isso: o alerta carrega *o item* e *quantos dias faltam* juntos.
- **`alertas.sort(key=lambda par: par[1])`** — ordena por urgência. Em cada tupla
  `par`, `par[0]` é o item e `par[1]` é o número de dias; ordenamos por `par[1]`,
  então quem vence antes (menor número) aparece primeiro.

Repare que `ia.py` vai **reaproveitar** esta função para escolher ingredientes —
é por isso que `alertas` vem antes de `ia` na arquitetura.

> **Conceitos de APC desta parte:** subtração de datas, tuplas, `for`,
> condicional, `sort` + `lambda` indexando a tupla.

---
---

# PARTE 8 — O diferencial: `ia.py` (com plano B que nunca trava)

**Responsável: Pessoa C.** A parte mais "esperta": pede uma receita à IA usando
o que está vencendo — mas **garante uma receita mesmo sem IA** (RNF05). Usa
`config`, `persistencia` e `alertas`.

### Import defensivo do `requests`

```python
import os
import json
import config
import persistencia
import alertas

try:
    import requests
    TEM_REQUESTS = True
except ImportError:
    TEM_REQUESTS = False
```

`requests` é uma biblioteca **externa** (faz chamadas HTTP pela internet). Pode
não estar instalada. Em vez de deixar o programa quebrar no `import`, tentamos
importar e guardamos um sinalizador `TEM_REQUESTS`. Se faltar, o programa segue
e cai no plano B. Robustez desde a primeira linha.

### Passo 1 — escolher ingredientes (reaproveitando alertas)

```python
def selecionar_ingredientes(inventario):
    urgentes = alertas.calcular_alertas(inventario, config.DIAS_ALERTA)
    if not urgentes:
        urgentes = alertas.calcular_alertas(inventario, config.DIAS_ALERTA_AMPLO)
    return [item["nome"] for (item, dias) in urgentes]
```

- Pega primeiro o que vence em 3 dias. **`if not urgentes:`** ("se a lista
  estiver vazia") amplia a janela para 7 dias (slide 7).
- **`[item["nome"] for (item, dias) in urgentes]`** é uma **list comprehension**:
  percorre as tuplas `(item, dias)` e monta uma lista só com os **nomes**. O
  `dias` é ignorado aqui.

### Passo 2 — montar o pedido (prompt)

```python
def montar_prompt(ingredientes, usuario):
    restricoes = []
    if usuario.get("vegetariano"):
        restricoes.append("vegetariana")
    if usuario.get("vegano"):
        restricoes.append("vegana")
    if usuario.get("alergias"):
        restricoes.append("sem " + ", sem ".join(usuario["alergias"]))
    texto_restricoes = "; ".join(restricoes) if restricoes else "nenhuma"
    tempo = usuario.get("tempo_max_receita", 60)
    return (
        "Você é um chef que evita desperdício. Crie UMA receita simples usando "
        f"prioritariamente estes ingredientes: {', '.join(ingredientes)}. "
        f"Restrições: {texto_restricoes}. Tempo máximo: {tempo} minutos. "
        "Responda em JSON com as chaves: titulo (string), "
        "ingredientes (lista de strings) e modo_preparo (lista de strings)."
    )
```

- Junta **ingredientes + restrições** do usuário (slide 7). `", ".join(lista)`
  cola os itens de uma lista num texto separado por vírgula.
- Pedimos explicitamente a resposta **em JSON** com chaves conhecidas. Isso é
  importante: assim conseguimos converter a resposta da IA num dicionário Python
  previsível.

### Passo 3 — chamar a IA com segurança

```python
def consultar_ia(prompt):
    chave = os.environ.get(config.IA_NOME_VARIAVEL_CHAVE)
    if not chave:
        raise RuntimeError("Sem chave de API (IA_API_KEY não definida).")
    if not TEM_REQUESTS:
        raise RuntimeError("Biblioteca 'requests' não instalada.")
    cabecalhos = {
        "x-api-key": chave,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    corpo = {
        "model": config.IA_MODEL,
        "max_tokens": 800,
        "messages": [{"role": "user", "content": prompt}],
    }
    resposta = requests.post(config.IA_API_URL, headers=cabecalhos,
                             json=corpo, timeout=config.TIMEOUT_IA)
    resposta.raise_for_status()
    dados = resposta.json()
    texto = dados["content"][0]["text"]
    return json.loads(texto)
```

Os pontos que os slides destacam:

- **`os.environ.get("IA_API_KEY")`** — a chave (senha) vem de uma **variável de
  ambiente**, **não do código**. Você a define fora do programa
  (`export IA_API_KEY=...`). Se alguém vir seu código, não vê sua senha.
- **`raise RuntimeError(...)`** — se não há chave ou `requests`, **lançamos uma
  exceção de propósito**. Lembre disso: lá no `sugerir_receita`, essa exceção
  será capturada e nos levará ao plano B.
- **`requests.post(..., timeout=config.TIMEOUT_IA)`** — o **timeout** é crucial:
  se a internet travar, desistimos após 20 segundos em vez de congelar para
  sempre (slide 7).
- **`resposta.raise_for_status()`** — se o servidor respondeu com erro (ex.: 401,
  500), isso vira exceção.
- As últimas linhas extraem o texto da resposta e **`json.loads(texto)`** o
  converte no dicionário da receita.

### Passo 4 — o plano B (fallback)

```python
def chave_cache(ingredientes):
    return "+".join(sorted(i.lower() for i in ingredientes))

def receita_generica(ingredientes):
    lista = ingredientes if ingredientes else ["o que você tiver"]
    return {
        "titulo": "Refogado de aproveitamento",
        "ingredientes": lista + ["sal", "azeite", "temperos a gosto"],
        "modo_preparo": [
            "Lave e corte os ingredientes em pedaços pequenos.",
            "Aqueça um fio de azeite em uma panela.",
            "Refogue os ingredientes começando pelos mais firmes.",
            "Tempere com sal e seus temperos preferidos.",
            "Cozinhe até ficar macio e sirva.",
        ],
    }
```

**`chave_cache`** resolve um detalhe esperto (slide 7): `sorted(...)` ordena os
ingredientes antes de juntar, então `["ovo","tomate"]` e `["tomate","ovo"]`
geram **a mesma chave** `"ovo+tomate"`. Sem isso, guardaríamos a mesma receita
duas vezes com nomes diferentes.

**`receita_generica`** é a última rede de segurança: uma receita que sempre
funciona, sem depender de nada.

### A função que orquestra tudo com `try/except`

```python
def sugerir_receita(inventario, usuario):
    ingredientes = selecionar_ingredientes(inventario)
    cache = persistencia.carregar_json(config.ARQ_RECEITAS_CACHE, {})
    chave = chave_cache(ingredientes)
    try:
        prompt = montar_prompt(ingredientes, usuario)
        receita = consultar_ia(prompt)
        cache[chave] = receita
        persistencia.salvar_json(config.ARQ_RECEITAS_CACHE, cache)
        return receita, "ia"
    except Exception:
        if chave in cache:
            return cache[chave], "cache"
        return receita_generica(ingredientes), "generica"
```

Esta é a peça que faz o programa **nunca travar** (slide 7). A lógica:

1. **Tenta a IA** dentro do `try`. Se der certo, guarda a receita no cache (para
   uso offline futuro) e devolve `(receita, "ia")`.
2. **Se qualquer coisa falhar** — sem chave, sem internet, timeout, erro HTTP —
   o `except Exception:` captura **tudo** e vamos ao plano B:
   - se já temos essa combinação no **cache**, devolvemos ela (`"cache"`);
   - senão, devolvemos a **receita genérica** (`"generica"`).

Repare que a função devolve **uma tupla** `(receita, origem)`. O `origem` deixa a
interface mostrar de onde veio a receita ("IA", "cache local" ou "receita base").

> É por isso que o slide diz: *sem chave ou sem internet → fallback automático,
> ótimo para demonstrar offline.* Você consegue apresentar o trabalho sem
> depender da internet da sala.

> **Conceitos de APC desta parte:** variáveis de ambiente, `requests` + timeout
> (HTTP), `try/except` para controle de fluxo, `json.loads`, list comprehension,
> `sorted`, e retorno em tupla.

---
---

# PARTE 9 — A conta que motiva: `impacto.py`

**Responsável: Pessoa D.** A partir do histórico de itens **consumidos** (os que
você aproveitou a tempo), soma o quanto foi salvo (RF08 + RF09). Usa `config` e
`persistencia`.

### Uniformizar unidades antes de somar

```python
import config
import persistencia

def converter_para_kg(quantidade, unidade):
    unidade = unidade.lower()
    if unidade == "kg":
        return quantidade
    if unidade == "g":
        return quantidade / 1000
    if unidade == "l":
        return quantidade
    if unidade == "ml":
        return quantidade / 1000
    if unidade in ("unid", "unidade", "un"):
        return quantidade * config.PESO_UNIDADE_KG
    return quantidade
```

Você não pode somar "2 kg" com "500 g" diretamente. Esta função coloca **tudo em
kg** (slide 8): gramas viram kg dividindo por 1000; "unid" usa um peso médio por
unidade vindo do `config.PESO_UNIDADE_KG`. Só depois disso somamos.

### O cálculo principal: retorno múltiplo (tupla)

```python
def calcular_impacto(historico, base):
    kg_total = co2_total = agua_total = reais_total = 0.0
    for registro in historico:
        if registro.get("status") != "consumido":
            continue
        kg = converter_para_kg(registro["quantidade"], registro["unidade"])
        dados = persistencia.buscar_alimento_na_base(registro["nome"], base)
        if dados is None:
            continue
        kg_total    += kg
        co2_total   += kg * dados["co2_kg"]
        agua_total  += kg * dados["agua_litros_kg"]
        reais_total += kg * dados["preco_kg"]
    return kg_total, co2_total, agua_total, reais_total
```

- Começamos os quatro totais em zero.
- **`if registro.get("status") != "consumido": continue`** — só itens
  **consumidos** contam como economia (descartados não). `continue` pula para o
  próximo item do laço.
- Convertemos a quantidade para kg, buscamos os fatores do alimento no catálogo
  e **acumulamos**: cada kg salvo multiplica o CO₂, a água e o preço por kg
  daquele alimento. `+=` significa "some isto ao total".
- **`return kg_total, co2_total, agua_total, reais_total`** — devolve **quatro
  valores de uma vez**. Isso é o **retorno múltiplo** via tupla que os slides
  destacam. Quem chama faz:
  `kg, co2, agua, reais = calcular_impacto(historico, base)`.

### Agregar por categoria: o padrão `dict.get(cat, 0) + 1`

```python
def agregar_por_categoria(historico):
    contagem = {}
    for registro in historico:
        if registro.get("status") != "consumido":
            continue
        cat = registro.get("categoria", "Outros")
        contagem[cat] = contagem.get(cat, 0) + 1
    return contagem
```

Este é um padrão clássico de contagem (slide 8). **`contagem.get(cat, 0)`**
devolve o total atual daquela categoria, ou `0` se for a primeira vez. Somamos 1
e guardamos. No fim, `contagem` é algo como `{"Legumes": 3, "Frutas": 2}`.

### Taxa de aproveitamento (sem dividir por zero)

```python
def taxa_aproveitamento(historico):
    consumidos  = sum(1 for r in historico if r.get("status") == "consumido")
    descartados = sum(1 for r in historico if r.get("status") == "descartado")
    total = consumidos + descartados
    if total == 0:
        return 0.0
    return consumidos / total
```

- **`sum(1 for r in historico if ...)`** conta quantos registros batem na
  condição (soma 1 para cada um). É um jeito compacto de contar.
- **`if total == 0: return 0.0`** evita a **divisão por zero** quando o histórico
  ainda está vazio. Sempre proteja divisões assim.
- Senão, devolve a fração `consumidos / total` (ex.: 0.8 = 80% aproveitado).

### "Gráfico" de barras em texto

```python
def grafico_barras(contagem):
    if not contagem:
        return ["(sem dados ainda)"]
    itens = sorted(contagem.items(), key=lambda par: par[1], reverse=True)
    linhas = []
    for categoria, qtd in itens:
        barra = "#" * qtd
        linhas.append(f"{categoria:<14} {barra} {qtd}")
    return linhas
```

- **`sorted(..., reverse=True)`** ordena do **maior para o menor** (slide 8).
- **`"#" * qtd`** repete o caractere `#` `qtd` vezes — a "barra" do gráfico.
- O f-string `{categoria:<14}` alinha os rótulos à esquerda em 14 colunas, igual
  às molduras da interface. O resultado é uma lista de linhas prontas para
  imprimir, tipo:

```
Legumes        ### 3
Frutas         ## 2
```

> **Conceitos de APC desta parte:** `for` com `continue`, acumuladores (`+=`),
> retorno múltiplo (tupla), `dict.get(cat,0)+1`, `sum(...)`, proteção de divisão
> por zero, `sorted(reverse=True)` e repetição de string.

---
---

# PARTE 10 — O maestro: `main.py`

**Responsável: Pessoa A.** O **ponto de entrada** (RF01). Carrega os dados,
mostra o menu num laço, manda cada opção para a função certa e salva a cada
ação. Ele **usa todo mundo**, mas, graças ao baixo acoplamento, **só chama
funções** — não conhece os detalhes internos dos módulos.

### Carregar e salvar todo o estado

```python
import config, persistencia, interface
import inventario as inv
import alertas, ia, impacto
from datetime import datetime

def carregar_tudo():
    return {
        "base": persistencia.carregar_json(config.ARQ_BASE_ALIMENTOS, {}),
        "inventario": persistencia.carregar_json(config.ARQ_INVENTARIO, []),
        "historico": persistencia.carregar_json(config.ARQ_HISTORICO, []),
        "usuario": persistencia.carregar_json(config.ARQ_USUARIO, {}),
    }

def salvar_tudo(estado):
    persistencia.salvar_json(config.ARQ_INVENTARIO, estado["inventario"])
    persistencia.salvar_json(config.ARQ_HISTORICO, estado["historico"])
    persistencia.salvar_json(config.ARQ_USUARIO, estado["usuario"])
```

- **`import inventario as inv`** — dá um apelido curto ao módulo, só para
  escrever menos depois.
- **`carregar_tudo`** lê os arquivos JSON e devolve **um único dicionário
  `estado`** com tudo dentro: base, inventário, histórico e usuário. Carregar o
  estado num só lugar facilita passá-lo adiante.
- **`salvar_tudo`** grava de volta. Note que não salvamos a `base` (o catálogo
  não muda durante o uso). É isto que será chamado **a cada ação** para nada se
  perder (RNF04).

### Uma função por opção do menu

Cada item do menu tem uma função `acao_...`. Exemplo, adicionar um item:

```python
def acao_adicionar(estado):
    interface.desenhar_titulo("Adicionar item")
    nome = interface.ler_texto("Nome do alimento: ")
    chave, dados = inv.buscar_alimento_por_nome(nome, estado["base"])
    if dados is None:
        print("  ! Alimento não está no catálogo.")
        interface.pausar()
        return
    quantidade = interface.ler_float("Quantidade: ", minimo=0.01)
    unidade = interface.ler_texto("Unidade (kg/g/l/ml/unid): ").lower()
    print(f"Locais válidos: {', '.join(config.LOCAIS_VALIDOS)}")
    local = interface.ler_opcao("Local: ", config.LOCAIS_VALIDOS)
    data_compra = interface.ler_data("Data de compra")
    validade = inv.sugerir_validade(data_compra, dados, local)
    item = {
        "nome": chave, "quantidade": quantidade, "unidade": unidade,
        "local": local, "data_compra": data_compra, "data_validade": validade,
    }
    inv.adicionar_item(estado["inventario"], item)
    salvar_tudo(estado)
    print(f"  + Adicionado! Validade sugerida: {validade}")
    interface.pausar()
```

Veja como **tudo se encaixa**: a `interface` faz a leitura validada, o
`inventario` calcula a validade e guarda o item, e o `main` chama `salvar_tudo`
no fim. O `main` não sabe *como* a validade é calculada — só pede. **Isso é baixo
acoplamento na prática.**

As outras ações (`acao_ver_inventario`, `acao_ver_alertas`,
`acao_sugerir_receita`, `acao_marcar`, `acao_impacto`, `acao_configuracoes`,
`acao_exportar_csv`) seguem a mesma receita: desenham um título, chamam funções
dos módulos, mostram o resultado e (quando alteram dados) chamam `salvar_tudo`.

### O cabeçalho dinâmico

```python
def desenhar_cabecalho(estado):
    ativos = len(estado["inventario"])
    vencendo = len(alertas.calcular_alertas(estado["inventario"], config.DIAS_ALERTA))
    _, _, _, reais = impacto.calcular_impacto(estado["historico"], estado["base"])
    nome = estado["usuario"].get("nome") or "visitante"
    interface.desenhar_titulo("Geladeira Zero")
    interface.linha(f"Olá, {nome}!")
    interface.linha(f"Itens ativos: {ativos} | Vencendo em "
                    f"{config.DIAS_ALERTA}d: {vencendo} | Economia: R$ {reais:.2f}")
    interface.borda()
```

A cada volta do menu, mostramos um resumo: quantos itens ativos, quantos vencem
em 3 dias e a economia acumulada (slide 9). Repare no
**`_, _, _, reais = impacto.calcular_impacto(...)`**: como aquela função devolve
quatro valores, usamos `_` para **ignorar** os três que não precisamos aqui e
ficar só com `reais`.

### O laço principal

```python
def main():
    estado = carregar_tudo()
    acoes = {
        "1": acao_adicionar, "2": acao_ver_inventario, "3": acao_ver_alertas,
        "4": acao_sugerir_receita, "5": acao_marcar, "6": acao_impacto,
        "7": acao_configuracoes, "8": acao_exportar_csv,
    }
    while True:
        interface.limpar_tela()
        desenhar_cabecalho(estado)
        print("\n[1] Adicionar item   [2] Ver inventário")
        # ... (resto do menu) ...
        print("[0] Sair")
        opcao = interface.ler_opcao("\nEscolha: ",
                                    ["0","1","2","3","4","5","6","7","8"])
        if opcao == "0":
            print("Até logo! Menos desperdício. :)")
            break
        acoes[opcao](estado)

if __name__ == "__main__":
    main()
```

Dois pontos finos e importantes:

**1. O dicionário `acoes` substitui um `if/elif` gigante.** Em vez de
`if opcao == "1": ... elif opcao == "2": ...`, guardamos um mapa
**opção → função**. Aí `acoes[opcao](estado)` pega a função certa e a executa.
(Os slides mencionam o roteamento com `if/elif`; este dicionário é a versão
elegante da mesma ideia — use a que seu grupo entender melhor.)

**2. `if __name__ == "__main__":`** — esta linha mágica significa "só rode
`main()` se este arquivo for executado **diretamente** (`python main.py`)". Se
outro arquivo *importar* `main`, o menu **não** dispara sozinho. É o padrão
correto para o ponto de entrada de um programa Python.

O `while True` repete o menu para sempre; só o `break` (na opção 0) encerra.

> **Conceitos de APC desta parte:** dicionário como roteador, `while True` +
> `break`, desempacotar tupla ignorando valores com `_`, `len`, e o idioma
> `if __name__ == "__main__"`.

---
---

# PARTE 11 — Como rodar e testar

Com Python instalado, dentro da pasta `geladeira_zero/`:

```bash
python main.py
```

Você verá o menu. Fluxo sugerido para testar tudo:

1. **[7] Configurações** — coloque seu nome e preferências.
2. **[1] Adicionar item** — adicione "tomate", 1, "kg", "geladeira", e uma data
   de compra de alguns dias atrás (para ele já aparecer nos alertas).
3. **[2] Ver inventário** — confira a validade calculada e a ordenação.
4. **[3] Ver alertas** — veja o que está perto de vencer.
5. **[4] Sugerir receita** — sem internet/chave, vem o plano B (receita base).
   É o comportamento esperado e ótimo para demonstrar offline.
6. **[5] Marcar consumido** — marque o tomate como consumido.
7. **[6] Ver impacto** — veja kg, CO₂, água, R$ e o gráfico por categoria.
8. **[8] Exportar CSV** — gera `data/historico_export.csv`.
9. **[0] Sair** e rode de novo: seus dados continuam lá (persistência).

### Para ligar a IA de verdade (opcional)

```bash
pip install requests
export IA_API_KEY="sua-chave-aqui"   # no Windows: set IA_API_KEY=sua-chave
python main.py
```

Sem esses passos, o programa **continua funcionando** pelo plano B — esse é o
ponto inteiro do RNF05.

---
---

# PARTE 12 — Mapa final: requisitos × código × matéria de APC

### Requisitos atendidos (slide 10)

| Req. | O que é | Onde mora |
|---|---|---|
| RF01 | Menu principal | `main` + `interface` |
| RF02 | Cadastrar item | `inventario` (via `acao_adicionar`) |
| RF03 | Sugerir validade | `inventario.sugerir_validade` |
| RF04 | Listar por validade | `inventario.listar_ordenado` |
| RF05 | Alertas de vencimento | `alertas.calcular_alertas` |
| RF06 | Receita com IA | `ia.sugerir_receita` |
| RF08 | Impacto ambiental | `impacto.calcular_impacto` |
| RF09 | Economia (R$) | `impacto.calcular_impacto` |
| RF10 | Preferências do usuário | `main.acao_configuracoes` |
| RF11 | Exportar histórico CSV | `persistencia.exportar_csv` |
| RNF03 | Validação total de entradas | `interface` (todos os leitores) |
| RNF04 | Salva a cada ação | `main.salvar_tudo` |
| RNF05 | Fallback da IA | `ia.sugerir_receita` (try/except) |

### Conteúdos de APC demonstrados (slide 11)

Listas & dicionários · laços `while`/`for` · condicionais `if/elif` · funções &
módulos · strings & f-strings · `datetime` & `timedelta` · tuplas (retorno
múltiplo) · arquivos JSON/CSV · tratamento de exceções · `sort` + `lambda` ·
variáveis de ambiente · `requests` (HTTP) + timeout.

Cada um desses tem um lugar concreto no código que você acabou de entender. Se
souber explicar **onde** cada conceito aparece e **por que**, você domina o
projeto.

---
---

# PARTE 13 — Ordem de estudo recomendada (checklist)

Estude e reescreva nesta ordem. Só passe adiante quando souber explicar o atual
**sem olhar**:

- [ ] **0.** Ler a Parte 0 inteira (visão geral + glossário).
- [ ] **1.** `config.py` — entender `__file__`, `os.path.join`, constantes.
- [ ] **2.** Os JSON em `data/` — formato de listas e dicionários.
- [ ] **3.** `persistencia.py` — `try/except`, `json.load/dump`, `csv.DictWriter`.
- [ ] **4.** `interface.py` — o padrão `while True` + `return` de validação.
- [ ] **5.** `inventario.py` — `datetime + timedelta`, `sort` + `lambda`.
- [ ] **6.** `alertas.py` — tuplas `(item, dias)` e ordenação por urgência.
- [ ] **7.** `ia.py` — variável de ambiente, `requests` + timeout, fallback.
- [ ] **8.** `impacto.py` — retorno múltiplo, `dict.get(cat,0)+1`, divisão segura.
- [ ] **9.** `main.py` — `carregar/salvar_tudo`, roteamento, `__main__`.
- [ ] **10.** Rodar o programa inteiro e percorrer todas as 8 opções.

**Teste para si mesmo:** abra qualquer função e tente explicar em voz alta o que
cada linha faz e por quê. Se travar, volte na parte correspondente deste guia.

Quando conseguir fazer isso com as 9 funções "estrela" abaixo, você está pronto:

1. `persistencia.carregar_json` (o defensivo)
2. `interface.ler_inteiro` (o padrão de validação)
3. `interface.ler_data` (validação real de datas)
4. `inventario.sugerir_validade` (datetime + timedelta)
5. `inventario.listar_ordenado` (sort + lambda)
6. `alertas.calcular_alertas` (tuplas + urgência)
7. `ia.sugerir_receita` (try/except + fallback)
8. `impacto.calcular_impacto` (retorno múltiplo)
9. `main.main` (o laço e o roteamento)

Bom estudo — e lembre da regra de ouro: **ninguém faz commit sem entender linha
a linha.**
