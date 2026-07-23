# Guia de Estudo Python — usando o projeto `geladeira_zero`

Repositório: https://github.com/PedroVargas1204/geladeira_inteligente/tree/main/geladeira_zero

Todos os trechos abaixo são **código real do projeto** (arquivo e linha indicados), exceto as duas seções marcadas como "extra", que eu escrevi no mesmo estilo porque o repositório não tinha um exemplo pronto desses tópicos (Recursividade e Matrizes).

---

## 1. Funções

O projeto inteiro é organizado em funções pequenas, cada uma com uma responsabilidade. Exemplo simples, com valor padrão de parâmetro:

```python
# inventario.py, linha 54
def sugerir_validade(data_compra, dados_alimento, local):
    """Soma a data de compra aos dias de durabilidade daquele local."""
    dias = dados_alimento["validade_dias"].get(local, 0)
    data = datetime.strptime(data_compra, "%Y-%m-%d")
    validade = data + timedelta(days=dias)
    return validade.strftime("%Y-%m-%d")
```

Repare em:
- **parâmetros nomeados** (`data_compra`, `dados_alimento`, `local`);
- **retorno único** de valor;
- **docstring** explicando o que a função faz.

Função que **retorna múltiplos valores** (na prática, uma tupla — ver seção 8):

```python
# impacto.py, linha 46
def calcular_impacto(historico, base):
    kg_total = 0.0
    co2_total = 0.0
    agua_total = 0.0
    reais_total = 0.0
    for registro in historico:
        ...
    return kg_total, co2_total, agua_total, reais_total
```

E uso de **parâmetros com valor padrão** (`minimo`, `maximo`, `padrao` só são usados se o chamador não passar nada):

```python
# interface.py, linha 164
def ler_float(prompt, minimo=0.0, maximo=None, padrao=None):
    ...
```

**Estude também:** `main.py` mostra como funções podem ser guardadas num **dicionário** e chamadas dinamicamente (function dispatch), evitando um `if/elif` gigante:

```python
# main.py, linha 270
acoes = {
    "1": acao_adicionar,
    "2": acao_ver_inventario,
    ...
}
acoes[opcao](estado)  # chama a função certa conforme a opção escolhida
```

---

## 2. Recursividade *(extra — não existe no repositório original)*

O projeto não usa recursão em nenhum lugar (o padrão do código é usar laços `for`/`while`). Para você estudar o conceito no mesmo "universo" do projeto, aqui vai um exemplo recursivo equivalente a algo que o projeto faz de forma iterativa — somar a quantidade total de um alimento no inventário:

```python
def soma_quantidade_recursiva(inventario, nome_alimento, indice=0):
    """
    Versão recursiva de "somar quantidade de um alimento no inventário".
    Caso base: chegou ao fim da lista -> devolve 0.
    Caso recursivo: soma o item atual (se for o alimento certo) com o
    resultado da chamada para o resto da lista.
    """
    if indice == len(inventario):          # caso base
        return 0

    item = inventario[indice]
    quantidade_atual = item["quantidade"] if item["nome"] == nome_alimento else 0

    # chamada recursiva para o restante da lista
    return quantidade_atual + soma_quantidade_recursiva(inventario, nome_alimento, indice + 1)
```

Compare com a versão iterativa que o projeto realmente usaria (mais próxima do estilo do código-fonte):

```python
def soma_quantidade_iterativa(inventario, nome_alimento):
    total = 0
    for item in inventario:
        if item["nome"] == nome_alimento:
            total += item["quantidade"]
    return total
```

**Ponto de estudo:** toda função recursiva precisa de um **caso base** (que para a recursão) e um **caso recursivo** (que caminha em direção ao caso base). Sem caso base, você cai em `RecursionError`.

---

## 3. Laços de repetição (`for` e `while`)

**`while True` com saída controlada** — padrão usado em todos os leitores de entrada validada:

```python
# interface.py, linha 147
def ler_inteiro(prompt, minimo=None, maximo=None):
    while True:
        bruto = _ler_linha(prompt).strip()
        try:
            valor = int(bruto)
        except ValueError:
            print("  ! Digite um número inteiro válido.")
            continue
        if minimo is not None and valor < minimo:
            print(f"  ! O valor mínimo é {minimo}.")
            continue
        return valor
```
O laço só termina (`return`) quando o dado digitado é válido — ótimo exemplo de "laço de validação".

**`while True` como loop principal do programa** (menu):

```python
# main.py, linha 281
while True:
    interface.limpar_tela()
    desenhar_cabecalho(estado)
    ...
    opcao = interface.ler_opcao(...)
    if opcao == "0":
        print("Até logo! Menos desperdício. :)")
        break
```

**`for` percorrendo lista de dicionários:**

```python
# main.py, linha 86
for item in ordenado:
    dias = alertas.dias_para_vencer(item["data_validade"])
    marca = "VENCIDO" if dias < 0 else f"{dias}d"
    ...
```

**`for` com `enumerate`** (pega índice e valor ao mesmo tempo):

```python
# main.py, linha 129
for i, passo in enumerate(receita["modo_preparo"], start=1):
    print(f"  {i}. {passo}")
```

**`for` acumulando num dicionário** (padrão clássico de contagem):

```python
# impacto.py, linha 76
def agregar_por_categoria(historico):
    contagem = {}
    for registro in historico:
        if registro.get("status") != "consumido":
            continue
        cat = registro.get("categoria", "Outros")
        contagem[cat] = contagem.get(cat, 0) + 1
    return contagem
```

---

## 4. Condicionais (`if` / `elif` / `else`)

**Cadeia de `if` retornando cedo** (evita `elif` desnecessário):

```python
# impacto.py, linha 21
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
    return quantidade  # desconhecida: assume kg
```

**Operador ternário** (`x if condição else y`), muito usado no projeto:

```python
# main.py, linha 88
marca = "VENCIDO" if dias < 0 else f"{dias}d"
```

```python
# inventario.py, linha 107
if quantidade is None or quantidade >= qtd_total:
    quantidade_movida = qtd_total
    mover_tudo = True
else:
    quantidade_movida = quantidade
    mover_tudo = False
```

**`if/elif/else` de três ramos:**

```python
# main.py, linha 102
if dias < 0:
    estado_txt = f"VENCEU há {abs(dias)} dia(s)"
elif dias == 0:
    estado_txt = "VENCE HOJE"
else:
    estado_txt = f"vence em {dias} dia(s)"
```

---

## 5. Strings

**Formatação com f-strings e alinhamento** (muito rico neste projeto):

```python
# interface.py, linha 110
def desenhar_titulo(texto):
    print("+" + "-" * (LARGURA + 2) + "+")
    print(f"| {texto.upper():<{LARGURA}} |")   # :< alinha à esquerda, largura dinâmica
    print("+" + "-" * (LARGURA + 2) + "+")
```

**Métodos de string** — `.strip()`, `.lower()`, `.upper()`, `.replace()`, `.split()`:

```python
# ia.py, linha 120
def chave_cache(ingredientes):
    return "+".join(sorted(i.lower() for i in ingredientes))
```

```python
# interface.py, linha 175 (aceita "1,5" ou "1.5" como decimal)
bruto = _ler_linha(prompt).strip().replace(",", ".")
```

```python
# main.py, linha 231
u["alergias"] = [a.strip() for a in alergias_txt.split(",") if a.strip()]
```

**Concatenação e `join`:**

```python
# main.py, linha 62
print(f"Locais válidos: {', '.join(config.LOCAIS_VALIDOS)}")
```

**Comparação tolerante de strings (case-insensitive, substring):**

```python
# inventario.py, linha 33
consulta = nome.strip().lower()
...
if chave in consulta or consulta in chave:
    return chave, dados
```

---

## 6. Listas

**Criação e manipulação:**

```python
# inventario.py, linha 72
def adicionar_item(inventario, item):
    inventario.append(item)      # adiciona ao fim
    return inventario
```

```python
# inventario.py, linha 129
inventario.pop(indice)           # remove pelo índice
```

**`sorted()` com `key` e `lambda`:**

```python
# inventario.py, linha 78
def listar_ordenado(inventario):
    return sorted(inventario, key=lambda item: item["data_validade"])
```

```python
# impacto.py, linha 115
itens = sorted(contagem.items(), key=lambda par: par[1], reverse=True)
```

**List comprehension** (criar lista nova filtrando/transformando outra):

```python
# ia.py, linha 42
return [item["nome"] for (item, dias) in urgentes]
```

```python
# main.py, linha 231
u["alergias"] = [a.strip() for a in alergias_txt.split(",") if a.strip()]
```

**Concatenar listas com `+`:**

```python
# ia.py, linha 128
lista = ingredientes if ingredientes else ["o que você tiver"]
return {
    "titulo": "Refogado de aproveitamento",
    "ingredientes": lista + ["sal", "azeite", "temperos a gosto"],
    ...
}
```

**`sum()` com generator expression** (soma condicional dentro de uma lista):

```python
# impacto.py, linha 95
consumidos  = sum(1 for r in historico if r.get("status") == "consumido")
descartados = sum(1 for r in historico if r.get("status") == "descartado")
```

---

## 7. Dicionários

O projeto usa dicionários pra **tudo**: itens do inventário, catálogo de alimentos, registros de histórico, preferências do usuário. É o tópico mais rico do repositório.

**Dicionário aninhado** — o catálogo de alimentos (`data/base_alimentos.json`):

```json
"tomate": {
  "categoria": "Legumes",
  "sinonimos": ["tomate italiano", "tomate cereja", "tomates"],
  "validade_dias": { "geladeira": 7, "despensa": 3, "freezer": 60 },
  "preco_kg": 8.0,
  "co2_kg": 1.4,
  "agua_litros_kg": 214
}
```
Repare que `validade_dias` é **um dicionário dentro de outro dicionário** — acessado assim:

```python
# inventario.py, linha 63
dias = dados_alimento["validade_dias"].get(local, 0)
```

**`dict.get()` com valor padrão** — evita `KeyError` e é usado o tempo todo:

```python
# persistencia.py, linha 69
return base.get(chave)  # devolve None se a chave não existir
```

```python
# impacto.py, linha 86
contagem[cat] = contagem.get(cat, 0) + 1   # padrão clássico de contador
```

**Montar um dicionário do zero (registro):**

```python
# main.py, linha 67
item = {
    "nome": chave,
    "quantidade": quantidade,
    "unidade": unidade,
    "local": local,
    "data_compra": data_compra,
    "data_validade": validade,
}
```

**Percorrer um dicionário com `.items()`:**

```python
# inventario.py, linha 41
for chave, dados in base.items():
    sinonimos = dados.get("sinonimos", [])
    ...
```

**Dict comprehension:**

```python
# persistencia.py, linha 89
linha = {coluna: item.get(coluna, "") for coluna in colunas}
```

---

## 8. Tuplas

**Retorno múltiplo de função** (na verdade uma tupla, mesmo sem parênteses):

```python
# impacto.py, linha 70
return kg_total, co2_total, agua_total, reais_total
```
Chamado assim, com **desempacotamento**:

```python
# main.py, linha 192
kg, co2, agua, reais = impacto.calcular_impacto(estado["historico"], estado["base"])
```

**Lista de tuplas** — cada alerta é o par `(item, dias)`:

```python
# alertas.py, linha 37
alertas = []
for item in inventario:
    dias = dias_para_vencer(item["data_validade"], hoje)
    if dias <= dias_alerta:
        alertas.append((item, dias))     # tupla (item, dias)

alertas.sort(key=lambda par: par[1])     # ordena pela posição 1 da tupla
return alertas
```

E desempacotada depois:

```python
# main.py, linha 101
for item, dias in lista:
    ...
```

**Por que tupla e não lista aqui?** Porque `(item, dias)` é um par de dados que **não deve mudar de tamanho** — é a estrutura certa para "um registro fixo de dois valores", diferente de uma lista que cresce/encolhe.

---

## 9. Matrizes (listas de listas) *(extra — não existe no repositório original)*

O projeto não usa matrizes porque os dados são melhor representados como lista de dicionários. Mas dá pra montar um exemplo no mesmo domínio: uma matriz simples mostrando quantidade de cada categoria de alimento em cada local de armazenamento (linhas = categorias, colunas = locais):

```python
locais = ["geladeira", "despensa", "freezer"]
categorias = ["Frutas", "Legumes", "Verduras"]

# matriz 3x3 inicializada com zeros
matriz = [[0 for _ in locais] for _ in categorias]

def registrar(matriz, categoria, local, quantidade=1):
    linha = categorias.index(categoria)
    coluna = locais.index(local)
    matriz[linha][coluna] += quantidade

registrar(matriz, "Frutas", "geladeira")
registrar(matriz, "Frutas", "freezer")
registrar(matriz, "Legumes", "geladeira")

# percorrendo a matriz com dois laços aninhados
for i, categoria in enumerate(categorias):
    for j, local in enumerate(locais):
        if matriz[i][j] > 0:
            print(f"{categoria} em {local}: {matriz[i][j]}")
```

**Ponto de estudo:** uma matriz é só uma **lista cujos elementos também são listas**. `matriz[linha][coluna]` acessa uma célula. Cuidado com `[[0]*n]*m` — isso cria `m` referências para a **mesma** lista interna; o jeito certo de zerar é com list comprehension, como acima.

---

## 10. Conversão de tipos

**`int()`, `float()`, `str()` explícitos com tratamento de erro:**

```python
# interface.py, linha 147
try:
    valor = int(bruto)
except ValueError:
    print("  ! Digite um número inteiro válido.")
    continue
```

```python
# interface.py, linha 178
try:
    valor = float(bruto)
except ValueError:
    print("  ! Digite um número válido (ex.: 1,5).")
    continue
```

**Conversão de data (string) para objeto `datetime` e de volta pra string:**

```python
# inventario.py, linha 64
data = datetime.strptime(data_compra, "%Y-%m-%d")   # string -> datetime
validade = data + timedelta(days=dias)
return validade.strftime("%Y-%m-%d")                 # datetime -> string
```

**Conversão implícita/matemática de tipos** (int vira float na divisão):

```python
# impacto.py, linha 33
return quantidade / 1000   # int ou float dividido -> sempre float em Python 3
```

**`round()` para arredondar depois de operações com float:**

```python
# inventario.py, linha 132
item["quantidade"] = round(qtd_total - quantidade_movida, 4)
```

---

## 11. Formatação numérica

O projeto usa **f-strings com specs de formatação** (`:.2f`, `:.0f`, `:<12`) para exibir números de forma legível.

```python
# main.py, linha 195
interface.linha(f"Alimento salvo:  {kg:.2f} kg")       # 2 casas decimais
interface.linha(f"CO2 evitado:     {co2:.2f} kg")
interface.linha(f"Água economizada:{agua:.0f} L")       # sem casas decimais
interface.linha(f"Dinheiro salvo:  R$ {reais:.2f}")
interface.linha(f"Aproveitamento:  {taxa*100:.0f}%")    # fração -> porcentagem
```

**Alinhamento de texto em coluna fixa** (não é número, mas é o mesmo mecanismo de formatação, `:<N`):

```python
# main.py, linha 89
texto = (f"{item['nome']:<12} {item['quantidade']}{item['unidade']:<6}"
         f" {item['local']:<10} vence {item['data_validade']} ({marca})")
```

**Gráfico de barras em texto**, repetindo caractere `N` vezes conforme um número:

```python
# impacto.py, linha 106
def grafico_barras(contagem):
    itens = sorted(contagem.items(), key=lambda par: par[1], reverse=True)
    linhas = []
    for categoria, qtd in itens:
        barra = "#" * qtd                      # repetição de string por número
        linhas.append(f"{categoria:<14} {barra} {qtd}")
    return linhas
```

---

## 12. Funções embutidas (built-ins)

Lista de built-ins do Python usados no projeto, com onde aparecem:

| Built-in | Onde é usada | Para quê |
|---|---|---|
| `len()` | `main.py:150` `maximo=len(ordenado) - 1` | tamanho de lista |
| `sorted()` | `inventario.py:84`, `impacto.py:115` | ordenar com `key=` |
| `sum()` | `impacto.py:95-96` | somar valores/condicionais |
| `enumerate()` | `main.py:129`, `main.py:144` | índice + valor no `for` |
| `round()` | `inventario.py:132` | arredondar float |
| `int()` / `float()` / `str()` | `interface.py` (vários) | conversão de tipos |
| `open()` | `persistencia.py:36`, `:51`, `:84` | abrir arquivos |
| `abs()` | `main.py:103` | valor absoluto (`dias vencidos`) |
| `print()` | em quase todo arquivo | saída no console |
| `input()` (via `_ler_linha`) | `interface.py` | entrada do usuário |
| `isinstance`/`type` (implícito via `try/except ValueError`) | `interface.py` | validação de tipo |

Exemplo combinando vários (`len`, `sorted` indireto via `listar_ordenado`, `enumerate`):

```python
# main.py, linha 144
for i, item in enumerate(ordenado):
    interface.linha(f"[{i}] {item['nome']} - {item['quantidade']}"
                    f"{item['unidade']} - vence {item['data_validade']}")
interface.borda()

indice = interface.ler_inteiro("Número do item: ", minimo=0,
                               maximo=len(ordenado) - 1)
```

---

## Como estudar isso na prática

1. Clone o repositório e rode `main.py` — ele é um app de terminal, então você pode interagir e ver o efeito de cada função.
2. O próprio repositório já tem `geladeira_zero/ROTEIRO_DE_ESTUDOS.md`, um roteiro de estudos bem completo escrito pelos autores — vale muito a pena ler junto com este guia.
3. Há também `test_basico.py`, com dezenas de testes unitários (usando `assert`) que mostram, na prática, o **comportamento esperado** de cada função — ótimo para ver "input -> output" de forma isolada.
4. Tente reescrever cada função aqui **sem olhar o original**, comparando depois.

```bash
git clone https://github.com/PedroVargas1204/geladeira_inteligente.git
cd geladeira_inteligente/geladeira_zero
python main.py
```
