# Trabalho Prático — Teoria de Grafos e Computabilidade
**PUC Minas · Engenharia de Software · 2026/1**  
Prof. Leonardo V. Cardoso

> Ferramenta computacional para análise de redes de colaboração em repositórios GitHub, modelada com grafos dirigidos e ponderados.

---

<div align="center">

### 🎬 Demonstração da Aplicação

[![Assista no YouTube](https://img.shields.io/badge/▶%20Assistir%20no%20YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/6AQ8Z6wUyU0)

[![Thumbnail do vídeo](https://img.youtube.com/vi/6AQ8Z6wUyU0/maxresdefault.jpg)](https://youtu.be/6AQ8Z6wUyU0)

> Clique na imagem acima para assistir à demonstração completa da ferramenta.

</div>

---

## Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura do Projeto](#arquitetura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Como Rodar](#como-rodar)
  - [1. Mineração dos Dados](#1-mineração-dos-dados)
  - [2. Processamento e Análise](#2-processamento-e-análise)
  - [3. Aplicação / Interface](#3-aplicação--interface)
- [Rodando com Docker](#rodando-com-docker)
- [Rodando Localmente (sem Docker)](#rodando-localmente-sem-docker)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Contrato JSON](#contrato-json)
- [Membros do Grupo](#membros-do-grupo)

---

## Visão Geral

O projeto minera interações de usuários em um repositório público do GitHub (com mais de 5.000 estrelas), constrói grafos dirigidos representando essas interações e aplica métricas de redes complexas para analisar a colaboração entre os contribuidores.

**Repositório analisado:** `starship/starship` — https://github.com/starship/starship · 57.7k estrelas.

**Tipos de interação modeladas:**

| Tipo | Peso | Grafo |
|------|------|-------|
| Comentário em issue ou PR | 2 | G1 |
| Fechamento de issue por outro usuário | 3 | G2 |
| Revisão / aprovação / merge de PR | 4 e 5 | G3 |
| Todas as interações combinadas | ponderado | G4 (integrado) |

---

## Arquitetura do Projeto

O sistema é dividido em três blocos independentes que se comunicam via **arquivo JSON**:

```
GitHub API
    │
    ▼
┌─────────────┐        ┌──────────────────────────────┐
│  minerador  │──JSON──▶  biblioteca                  │
│  (coleta)   │  /dados │  GraphBuilder + GraphAnalyzer│
└─────────────┘        └──────────────┬───────────────┘
                                       │
                               ┌───────▼────────┐
                               │   app / demo   │
                               │  CLI + Streamlit│
                               └────────────────┘
```

- **`minerador`** → bate na API do GitHub, abstrai as interações e grava o JSON em `dados/`
- **`biblioteca`** → implementa `AbstractGraph`, `AdjacencyMatrixGraph` e `AdjacencyListGraph`; o `GraphBuilder` lê o JSON e constrói os grafos em memória; o `GraphAnalyzer` calcula as métricas
- **`app`** → consome a biblioteca e demonstra todas as operações da API via CLI e interface Streamlit

### Fluxo de dados

```
GitHub → Minerador → interacoes.json → UserMapper → GraphBuilder → API de Grafos → App/Demo
```

1. **Minerador** coleta os dados do GitHub e grava `dados/interacoes.json` (uma linha por interação)
2. **UserMapper** converte logins em índices inteiros de vértices (`alice → 0`, `bob → 1`)
3. **GraphBuilder** lê o JSON, usa o UserMapper e chama a API de grafos para construir G1, G2, G3 e G4
4. **API de Grafos** (`AbstractGraph`, `AdjacencyMatrixGraph`, `AdjacencyListGraph`) armazena e manipula os grafos em memória
5. **App/Demo** consome a API e demonstra todas as operações disponíveis

---

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/) **ou** Python 3.11+
- Token de acesso pessoal do GitHub (aumenta o rate limit de 60 para 5.000 req/hora)
  - Gere em: **GitHub → Settings → Developer settings → Personal access tokens**
  - Permissões necessárias: `public_repo` (somente leitura)

---

## Configuração do Ambiente

**1. Clone o repositório:**
```bash
git clone <url-do-repositorio>
cd trabalho-pratico-grafos
```

**2. Crie o arquivo `.env` na raiz do projeto:**
```bash
cp .env.example .env
```

**3. Preencha o `.env` com suas credenciais:**
```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxx
# GITHUB_TOKENS=ghp_a,ghp_b   # opcional: vários tokens (rotação automática)
OWNER=starship
REPO=starship
OUTPUT_DIR=dados
INPUT_DIR=dados
```

> ⚠️ O arquivo `.env` está no `.gitignore`. **Nunca commite seu token.**

---

## Como Rodar

### Ordem de execução

```
1. Minerador  →  2. Build dos grafos  →  3. App (demo)
```

O minerador deve rodar antes do build dos grafos, pois o `interacoes.json` precisa existir.

---

### 1. Mineração dos Dados

O minerador coleta as interações do GitHub e salva em `dados/interacoes.json`.

**Com Docker:**
```bash
docker compose --profile mine up minerador
```

**Localmente:**
```bash
cd codigo/mineirador
pip install -r ../../requirements.txt
python miner.py
```

✅ Ao final, o arquivo `dados/interacoes.json` deve existir.  
⏱ Dependendo do repositório, pode levar alguns minutos. O cache em `dados/cache/` evita re-coletas — se já rodou antes, as respostas da API são lidas do disco.

---

### 2. Processamento e Análise

Com o JSON gerado, o `GraphBuilder` constrói os quatro grafos em memória e o `GraphAnalyzer` calcula as métricas.

**Com Docker:**
```bash
docker compose --profile run up app
```

**Localmente:**
```bash
cd codigo/app
python demo_cli.py build       # constrói os grafos a partir do JSON
python demo_cli.py metrics     # calcula e exibe as métricas
```

---

### 3. Aplicação / Interface

A demo CLI expõe **todas as operações públicas** da API de grafos, conforme exigido pelo enunciado.

```bash
python demo_cli.py graph-smoke   # testa operações CRUD do grafo com dados sintéticos
python demo_cli.py build         # constrói G1, G2, G3 e G4 a partir do JSON
python demo_cli.py metrics       # exibe todas as métricas de rede
python demo_cli.py export        # exporta os 4 grafos para dados/gephi/ (.gexf)
python demo_cli.py all           # executa todos os comandos acima em sequência
```

A interface web (Streamlit) pode ser iniciada com:

```bash
streamlit run codigo/app/pages/app.py
```

---

## Rodando com Docker

### Subir tudo de uma vez

```bash
# Passo 1 — minerar (roda e termina automaticamente)
docker compose --profile mine up --build minerador

# Passo 2 — sobe a aplicação
docker compose --profile run up --build app
```

### Parar e limpar containers

```bash
docker compose down
```

### Recriar sem usar cache do Docker

```bash
docker compose --profile run up --build --force-recreate app
```

> **Dica:** o volume `./dados` persiste os JSONs e o cache fora dos containers. Ele sobrevive a `docker compose down` — se quiser forçar uma nova coleta do GitHub, apague a pasta `dados/cache/` antes de rodar o minerador.

---

## Rodando Localmente (sem Docker)

```bash
# 1. Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode o minerador
python -m codigo.mineirador.miner

# 4. Rode a demo CLI
python -m codigo.app.demo_cli build
python -m codigo.app.demo_cli metrics

# 5. (Opcional) Suba a interface web
streamlit run codigo/app/pages/app.py
```

---

## Estrutura de Pastas

```
trabalho-pratico-grafos/
│
├── docker-compose.yml            # orquestração dos containers
├── .env                          # variáveis de ambiente (não commitar)
├── .env.example                  # modelo do .env
├── .gitignore
├── requirements.txt
├── README.md
│
├── dados/                        # gerado em tempo de execução
│   ├── interacoes.json           # saída do minerador (JSON Lines)
│   ├── cache/                    # cache das respostas da API do GitHub
│   └── gephi/                    # grafos exportados (.gexf)
│
└── codigo/
    │
    ├── mineirador/               # coleta de dados
    │   ├── Dockerfile
    │   ├── config.py             # MinerConfig (tokens, cache, rate-limit)
    │   ├── github_client.py      # GitHubClient — requisições + paginação
    │   ├── json_cache.py         # CacheJson — leitura e gravação em disco
    │   └── miner.py              # GitHubMinerador + dataclass Interaction
    │
    ├── biblioteca/               # núcleo do trabalho
    │   │
    │   ├── graph/                # TAD do grafo (exigência do enunciado)
    │   │   ├── abstract_graph.py       # AbstractGraph — API completa
    │   │   ├── adjacency_matrix.py     # AdjacencyMatrixGraph
    │   │   ├── adjacency_list.py       # AdjacencyListGraph
    │   │   └── erros.py               # exceções customizadas
    │   │
    │   ├── builder/              # JSON → grafos em memória
    │   │   ├── user_mapper.py         # UserMapper — login ↔ índice inteiro
    │   │   ├── graph_builder.py       # GraphBuilder — monta G1/G2/G3/G4
    │   │   └── graph_bundle.py        # GraphBundle — agrupa os quatro grafos
    │   │
    │   └── analysis/             # métricas (sem NetworkX/igraph)
    │       └── graph_analyzer.py      # GraphAnalyzer — centralidade, densidade, etc.
    │
    ├── app/                      # interface
    │   ├── Dockerfile
    │   ├── demo_cli.py           # CLI — demonstra toda a API do grafo
    │   └── pages/
    │       └── app.py            # interface web Streamlit
    │
    └── export/
        └── gephi_exporter.py     # exporta grafos para .gexf (Gephi)
```

---

## Contrato JSON

O minerador grava e o construtor lê linhas no seguinte formato (JSON Lines — uma linha por interação):

```json
{
  "source_user": "alice",
  "target_user": "bob",
  "type": "pr_review",
  "weight": 4,
  "repo": "starship/starship",
  "created_at": "2024-01-10T14:32:00Z"
}
```

**Tipos possíveis e seus pesos:**

| `type` | Descrição | Peso |
|--------|-----------|------|
| `issue_comment` | Comentário em issue | 2 |
| `pr_comment` | Comentário em pull request | 2 |
| `issue_close` | Fechamento de issue por outro usuário | 3 |
| `pr_open` | Abertura de PR (autor → merger/assignee) | 3 |
| `pr_review` | Revisão ou aprovação de PR | 4 |
| `pr_merge` | Merge de pull request | 5 |

---

## Membros do Grupo

| Nome | Responsabilidade |
|------|-----------------|
| _(preencher)_ | _(preencher)_ |
| _(preencher)_ | _(preencher)_ |
| _(preencher)_ | _(preencher)_ |
| _(preencher)_ | _(preencher)_ |
