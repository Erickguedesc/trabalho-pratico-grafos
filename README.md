# Trabalho Prático — Teoria de Grafos e Computabilidade
**PUC Minas · Engenharia de Software · 2026/1**  
Prof. Leonardo V. Cardoso

> Ferramenta computacional para análise de redes de colaboração em repositórios GitHub, modelada com grafos dirigidos e ponderados.

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
- [Neo4j — Banco de Dados de Grafos](#neo4j--banco-de-dados-de-grafos)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Contrato JSON](#contrato-json)
- [Membros do Grupo](#membros-do-grupo)

---

## Visão Geral

O projeto minera interações de usuários em um repositório público do GitHub (com mais de 5.000 estrelas), constrói grafos dirigidos representando essas interações e aplica métricas de redes complexas para analisar a colaboração entre os contribuidores.

**Repositório analisado:** `<owner>/<repo>` _https://github.com/starship/starship_ 57.7k de estrelas.

**Tipos de interação modeladas:**

| Tipo | Peso | Grafo |
|------|------|-------|
| Comentário em issue ou PR | 2 | G1 |
| Fechamento de issue por outro usuário | 3 | G2 |
| Revisão / aprovação / merge de PR | 4 e 5 | G3 |
| Todas as interações combinadas | ponderado | G4 (integrado) |

---

## Arquitetura do Projeto

O sistema é dividido em três blocos independentes que se comunicam via **contrato JSON**:

```
GitHub API
    │
    ▼
┌─────────────┐        ┌──────────────┐
│  minerador  │──JSON──▶  biblioteca  │
│  (coleta)   │  /dados │  (grafos +  │
└─────────────┘        │   análise)  │
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐        ┌──────────┐
                        │     app      │────────▶│  Neo4j   │
                        │  (demo/CLI)  │         │  :7687   │
                        └──────────────┘        └──────────┘
```

- **`minerador`** → bate na API do GitHub, abstrai as interações e grava o JSON em `/dados/`
- **`biblioteca`** → implementa `AbstractGraph`, `AdjacencyMatrixGraph`, `AdjacencyListGraph`, `GraphBuilder` e `GraphMetrics`
- **`app`** → consome a biblioteca e demonstra todas as operações da API (exigência do enunciado)
- **`Neo4j`** → banco de dados nativo de grafos; persiste os nós e arestas para consultas analíticas pesadas

---

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/) **ou** Python 3.11+
- Token de acesso pessoal do GitHub (aumenta o rate limit de 60 para 5.000 req/hora)
  - Gere em: **GitHub → Settings → Developer settings → Personal access tokens**
  - Permissões necessárias: `public_repo` (somente leitura)
- Neo4j 5.x (incluído automaticamente via Docker Compose)
  - Se rodar localmente: [baixe o Neo4j Desktop](https://neo4j.com/download/) ou instale via `brew install neo4j`

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
OWNER=nome-do-dono
REPO=nome-do-repositorio
OUTPUT_DIR=/dados
INPUT_DIR=/dados

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=senha123
```

> ⚠️ O arquivo `.env` está no `.gitignore`. **Nunca commite seu token.**

---

## Como Rodar

### Ordem obrigatória de execução

```
1. Neo4j (banco)  →  2. Minerador  →  3. Build dos grafos  →  4. App (demo)
```

O Neo4j deve estar de pé antes da aplicação, e o minerador deve rodar antes do build dos grafos.

---

### 1. Mineração dos Dados

O minerador coleta as interações do GitHub e salva em `dados/interacoes.json`.

**Com Docker:**
```bash
docker compose --profile mine up minerador
```

**Localmente:**
```bash
cd codigo/minerador
pip install -r ../../requirements.txt
python miner.py
```

✅ Ao final, o arquivo `dados/interacoes.json` deve existir.  
⏱ Dependendo do repositório, pode levar alguns minutos. O cache evita re-coletas.

---

### 2. Processamento e Análise

Com o JSON gerado, o `GraphBuilder` constrói os quatro grafos e o `GraphMetrics` calcula as métricas.

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
python demo_cli.py graph-smoke   # testa operações CRUD do grafo
python demo_cli.py build         # constrói G1, G2, G3 e G4
python demo_cli.py metrics       # exibe todas as métricas
python demo_cli.py mine          # (opcional) aciona o minerador direto
```

---

## Rodando com Docker

### Subir tudo de uma vez

```bash
# Passo 1 — sobe o Neo4j (fica de pé em background)
docker compose up -d neo4j

# Aguarde ~15 segundos para o Neo4j inicializar, então:

# Passo 2 — minerar (roda e termina automaticamente)
docker compose --profile mine up --build minerador

# Passo 3 — sobe a aplicação
docker compose --profile run up --build app
```

### Verificar se o Neo4j está saudável

Acesse o painel web do Neo4j em: **http://localhost:7474**  
Login padrão: `neo4j` / `senha123` (conforme seu `.env`)

### Parar e limpar containers

```bash
docker compose down
```

### Parar e apagar os dados do Neo4j também

```bash
docker compose down -v   # remove os volumes — use com cuidado!
```

### Recriar sem usar cache do Docker

```bash
docker compose --profile run up --build --force-recreate app
```

> **Dica:** o volume `./dados` persiste os JSONs fora dos containers. O volume `neo4j_data` persiste o banco. Ambos sobrevivem a `docker compose down`.

---

## Rodando Localmente (sem Docker)

```bash
# 1. Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Suba o Neo4j localmente (via Neo4j Desktop ou Docker isolado)
docker run -d \
  --name neo4j-local \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/senha123 \
  neo4j:5

# 4. Rode o minerador
python -m codigo.minerador.miner

# 5. Rode a demo
python -m codigo.app.demo_cli build
python -m codigo.app.demo_cli metrics
```

---

## Neo4j — Banco de Dados de Grafos

O Neo4j é usado para **persistir os grafos construídos** e executar consultas analíticas pesadas de forma eficiente, sem precisar reprocessar o JSON toda vez.

### Como o projeto usa o Neo4j

Após o `GraphBuilder` construir os quatro grafos em memória, o `Neo4j Service` os escreve no banco usando a linguagem **Cypher**:

```cypher
-- Exemplo: criando nó e aresta
CREATE (alice:User {login: "alice"})
CREATE (bob:User {login: "bob"})
CREATE (alice)-[:INTERAGIU {type: "pr_review", weight: 4}]->(bob)

-- Exemplo: consultando colaboradores mais influentes
MATCH (u:User)-[r:INTERAGIU]->(v:User)
RETURN u.login, count(r) AS total_interacoes
ORDER BY total_interacoes DESC
LIMIT 10
```

### Acessar o painel web

Com o container rodando, acesse: **http://localhost:7474**

| Campo | Valor |
|-------|-------|
| Bolt URL | `bolt://localhost:7687` |
| Usuário | `neo4j` |
| Senha | `senha123` _(conforme `.env`)_ |

### Módulos relacionados no projeto

| Arquivo | Função |
|---------|--------|
| `utils/neo4j_connector.py` | Gerencia a conexão com o banco |
| `services/neo4j_service.py` | Escreve e lê grafos no Neo4j |
| `services/shared_queries.py` | Queries Cypher reutilizáveis |

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
├── dados/                        # JSONs gerados pelo minerador (volume Docker)
│   └── .gitkeep
│
├── docs/
│   └── diagramas/                # arquivos .puml do contrato
│
└── codigo/
    │
    ├── minerador/                # container isolado — coleta de dados
    │   ├── Dockerfile
    │   ├── __init__.py
    │   ├── config.py             # MinerConfig (owner, repo, token, cache_dir)
    │   ├── github_client.py      # GitHubClient — HTTP + paginação
    │   ├── json_cache.py         # CacheJson — leitura e gravação em disco
    │   └── miner.py              # GitHubMinerador — orquestrador principal
    │
    ├── biblioteca/               # núcleo do trabalho — sem Dockerfile próprio
    │   ├── __init__.py
    │   │
    │   ├── graph/                # TAD do grafo (exigência do enunciado)
    │   │   ├── __init__.py
    │   │   ├── abstract_graph.py       # AbstractGraph — API completa
    │   │   ├── adjacency_matrix.py     # AdjacencyMatrixGraph
    │   │   ├── adjacency_list.py       # AdjacencyListGraph
    │   │   └── errors.py              # GrafoError, VerticeInvalidoError
    │   │
    │   ├── builder/              # JSON → grafos
    │   │   ├── __init__.py
    │   │   ├── user_mapper.py         # UserMapper — login ↔ id inteiro
    │   │   ├── graph_builder.py       # GraphBuilder — monta G1/G2/G3/G4
    │   │   └── graph_bundle.py        # GraphBundle — agrupa os quatro grafos
    │   │
    │   └── analysis/             # métricas (sem NetworkX/igraph)
    │       ├── __init__.py
    │       └── graph_metrics.py       # GraphMetrics — centralidade, densidade, etc.
    │
    ├── app/                      # container da interface / demo CLI
    │   ├── Dockerfile
    │   ├── __init__.py
    │   ├── demo_cli.py           # DemoCLI — demonstra toda a API do grafo
    │   └── pages/                # telas Streamlit (se aplicável)
    │
    ├── services/                 # camada de serviço — orquestra biblioteca + Neo4j
    │   ├── __init__.py
    │   ├── neo4j_service.py      # escreve/lê grafos no Neo4j via Cypher
    │   ├── graph_service.py      # fachada geral de operações de grafo
    │   └── shared_queries.py     # queries Cypher reutilizáveis
    │
    ├── utils/                    # utilitários sem regra de negócio
    │   ├── __init__.py
    │   ├── neo4j_connector.py    # gerencia conexão bolt://neo4j:7687
    │   └── github_parser.py      # parsing auxiliar de respostas da API
    │
    └── export/                   # exportação para ferramentas externas
        └── gephi_exporter.py     # exportToGEPHI — formatos aceitos pelo GEPHI
```

---

## Contrato JSON

O minerador grava e o construtor lê linhas no seguinte formato:

```json
{
  "source_user": "alice",
  "target_user": "bob",
  "type": "pr_review",
  "weight": 4,
  "repo": "owner/repo",
  "created_at": "2024-01-10T14:32:00Z"
}
```

**Tipos possíveis e seus pesos:**

| `type` | Descrição | Peso |
|--------|-----------|------|
| `issue_comment` | Comentário em issue | 2 |
| `pr_comment` | Comentário em pull request | 2 |
| `issue_close` | Fechamento de issue por outro usuário | 3 |
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