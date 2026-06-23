#  Geladeira Inteligente

Aplicação de linha de comando (com interface web opcional) para **gerenciar os alimentos da geladeira, despensa e freezer e reduzir o desperdício**. O programa sugere a validade de cada item, avisa o que está perto de vencer, sugere receitas com o que você tem e calcula o impacto ambiental e financeiro do que foi aproveitado.

##  Funcionalidades

- **Inventário inteligente** — cadastro de alimentos com cálculo automático da validade, baseado no local de armazenamento (geladeira, despensa ou freezer).
- **Alertas de vencimento** — destaca o que vence em até 3 dias (ou já venceu), ordenado por urgência.
- **Consumo parcial** — ao usar um item, é possível registrar só parte da quantidade; o resto continua no inventário.
- **Sugestão de receitas** — usa IA para criar uma receita priorizando o que está perto de vencer, respeitando restrições do usuário (vegetariano, vegano, alergias, tempo máximo). Funciona offline com um plano B (cache local ou receita genérica).
- **Impacto e economia** — calcula alimento salvo (kg), CO₂ evitado, água economizada, dinheiro poupado e taxa de aproveitamento, com gráfico por categoria.
- **Preferências do usuário** — perfil alimentar e restrições.
- **Exportação CSV** — exporta o histórico para análise externa.
- **Cancelamento por ESC** — em qualquer campo do programa de terminal, a tecla ESC aborta a operação e volta ao menu.

## 🚀 Como rodar

Requer **Python 3.12 ou superior**.

### Interface de terminal (principal)

```bash
python main.py
```

### Interface web (opcional, com Streamlit)

```bash
pip install streamlit
python -m streamlit run streamlit_app.py
```

O app abre no navegador (geralmente em `http://localhost:8501`) e compartilha os mesmos dados do terminal.

### Sugestão de receitas com IA (opcional)

A sugestão de receitas usa a API do GEMINI. Para ativá-la, defina a chave de API na variável de ambiente antes de rodar:

```bash
# Windows (PowerShell)
$env:IA_API_KEY="sua-chave-aqui"

# Linux / Mac
export IA_API_KEY="sua-chave-aqui"
```

Sem a chave (ou sem internet), o programa continua funcionando e usa o plano B automaticamente.

##  Testes

O projeto inclui testes automatizados das funções de cálculo:

```bash
# com pytest
pip install pytest
python -m pytest -v

# ou sem instalar nada
python test_basico.py
```

##  Arquitetura

O projeto é organizado em **camadas com baixo acoplamento**: a interface não conhece os detalhes da lógica, e a lógica não conhece os detalhes do armazenamento. Trocar a forma de salvar (de JSON para banco de dados, por exemplo) exigiria mudar apenas um arquivo.

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Ponto de entrada do terminal: menu, roteamento e salvamento. |
| `streamlit_app.py` | Interface web alternativa, reaproveitando a mesma lógica. |
| `interface.py` | Telas em modo texto e validação de toda entrada do usuário. |
| `inventario.py` | Regras de estoque: busca, validade, consumo/descarte. |
| `alertas.py` | Cálculo dos alertas de vencimento. |
| `ia.py` | Sugestão de receitas com IA e plano B (fallback). |
| `impacto.py` | Cálculo de economia, impacto ambiental e gráficos. |
| `persistencia.py` | Única camada que toca o disco: lê/grava JSON e exporta CSV. |
| `config.py` | Constantes e caminhos centralizados num único lugar. |
| `test_basico.py` | Testes automatizados das funções de cálculo. |

### Dados

Os dados ficam na pasta `data/`, em arquivos JSON:

- `base_alimentos.json` — catálogo de alimentos (validade por local, CO₂, água, preço, categoria).
- `inventario.json` — itens atualmente armazenados.
- `historico.json` — itens já consumidos ou descartados.
- `usuario.json` — preferências do usuário.
- `receitas_cache.json` — cache de receitas para uso offline.

##  Estrutura de pastas

```
geladeira_zero/
├── data/
│   ├── base_alimentos.json
│   ├── inventario.json
│   ├── historico.json
│   ├── usuario.json
│   └── receitas_cache.json
├── main.py
├── streamlit_app.py
├── interface.py
├── inventario.py
├── alertas.py
├── ia.py
├── impacto.py
├── persistencia.py
├── config.py
└── test_basico.py
```

##  Equipe

Projeto desenvolvido em grupo, com responsabilidades divididas por módulo:

- **Pessoa A** — `main.py`, `interface.py`
- **Pessoa B** — `inventario.py`, `alertas.py`
- **Pessoa C** — `ia.py`
- **Pessoa D** — `config.py`, `impacto.py`, `persistencia.py`
