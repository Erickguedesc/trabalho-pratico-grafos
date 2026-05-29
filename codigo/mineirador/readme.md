# Minerador — Coleta de Interações do GitHub

> Módulo responsável por coletar interações entre usuários de um repositório GitHub e gerar o arquivo `interacoes.json` usado pelo restante do projeto.

---

## Sumário

- [O que o minerador faz](#o-que-o-minerador-faz)
- [Estrutura de arquivos](#estrutura-de-arquivos)
- [Arquitetura interna](#arquitetura-interna)
- [Fluxo de execução](#fluxo-de-execução)
- [Tipos de interação coletados](#tipos-de-interação-coletados)
- [Configuração](#configuração)
- [Como rodar](#como-rodar)
- [Cache em disco](#cache-em-disco)
- [Contrato de saída](#contrato-de-saída)

---

## O que o minerador faz

O minerador acessa a API REST do GitHub e coleta todas as interações entre usuários de um repositório (issues, pull requests, comentários, revisões e merges). Cada interação representa uma relação entre dois usuários — quem realizou a ação (`source_user`) e quem a recebeu (`target_user`) — e é salva em um arquivo JSON que alimenta a construção dos grafos.

---

## Estrutura de arquivos

```
mineirador/
├── config.py          # Lê as configurações do arquivo .env
├── json_cache.py      # Cache em disco para evitar repetir chamadas à API
├── github_client.py   # Cliente HTTP com paginação e controle de rate-limit
├── miner.py           # Orquestrador principal — coordena tudo e gera o JSON
├── requirements.txt   # Dependências do módulo
└── __init__.py        # Exporta as classes públicas do módulo
```

---

## Arquitetura interna

O módulo é organizado em camadas, onde cada camada tem uma responsabilidade única:

```
GitHubMinerador  (miner.py)
      │  orquestra a coleta e transforma os dados
      ↓
GitHubClient  (github_client.py)
      │  faz as requisições HTTP à API do GitHub
      ↓
CacheJson  (json_cache.py)
      │  lê e grava respostas em disco para evitar requisições repetidas
      ↓
MinerConfig  (config.py)
      │  fornece as configurações lidas do .env para todas as camadas
```

### `config.py` — MinerConfig

Dataclass que centraliza todas as configurações do minerador. As variáveis são lidas das variáveis de ambiente (definidas no `.env`) no momento em que a classe é instanciada.

Após criar os campos, o método `__post_init__` é chamado automaticamente e garante que as pastas de saída (`dados/` e `dados/cache/`) existam em disco.

As propriedades `repo_full_name`, `output_file` e `has_token` são acessadas como atributos normais mas calculam seu valor dinamicamente.

### `json_cache.py` — CacheJson

Persiste respostas da API em arquivos `.json` dentro da pasta `cache/`. Antes de fazer qualquer requisição, o `GitHubClient` verifica se já existe uma resposta salva para aquela chave — se sim, lê direto do disco sem consumir a cota da API.

| Método | O que faz |
|---|---|
| `get(key)` | Lê e retorna o objeto em cache, ou `None` se não existir |
| `set(key, data)` | Grava o objeto em disco |
| `has(key)` | Verifica se a chave existe sem ler o conteúdo |
| `invalidate(key)` | Remove uma entrada específica do cache |
| `clear()` | Apaga todo o cache |

O método interno `_path(key)` converte a chave em um nome de arquivo válido, trocando `/` e espaços por `_`.

### `github_client.py` — GitHubClient

Abstrai todas as chamadas à API REST do GitHub. Recebe `MinerConfig` e `CacheJson` no construtor.

**Métodos públicos** — cada um corresponde a um endpoint da API:

| Método | Endpoint chamado |
|---|---|
| `get_all_issues()` | `GET /repos/{owner}/{repo}/issues?state=all` |
| `get_issue_comments(n)` | `GET /repos/{owner}/{repo}/issues/{n}/comments` |
| `get_all_pulls()` | `GET /repos/{owner}/{repo}/pulls?state=all` |
| `get_pull_comments(n)` | `GET /repos/{owner}/{repo}/pulls/{n}/comments` |
| `get_pull_reviews(n)` | `GET /repos/{owner}/{repo}/pulls/{n}/reviews` |
| `get_issue_events(n)` | `GET /repos/{owner}/{repo}/issues/{n}/events` |

Todos os métodos públicos delegam para `_get_paged`, que verifica o cache antes de bater na API e percorre todas as páginas automaticamente usando o cabeçalho `Link: rel="next"` da resposta.

Em caso de erro 403 ou 429 (rate-limit da API), `_fetch_page` aguarda o tempo indicado no cabeçalho `Retry-After` e tenta novamente.

### `miner.py` — GitHubMinerador e Interaction

**`Interaction`** é um dataclass que representa uma única interação entre dois usuários, com os campos definidos pelo contrato do projeto. O método `to_dict()` o serializa para gravação em JSON.

**`GitHubMinerador`** é o orquestrador principal. Instancia `CacheJson` e `GitHubClient` a partir da configuração recebida.

- `run()` — ponto de entrada: chama os dois métodos de mineração, filtra auto-interações (`source == target`) e interações sem usuário, e grava o arquivo final.
- `_mine_issue_interactions()` — itera sobre todas as issues (excluindo PRs, que a API devolve junto), e para cada uma coleta comentários (peso 2) e, se fechada, o primeiro evento de fechamento por outro usuário (peso 3).
- `_mine_pr_interactions()` — itera sobre todos os PRs e coleta: abertura do PR (peso 3), comentários inline (peso 2), revisões do tipo `APPROVED`, `CHANGES_REQUESTED` ou `COMMENTED` (peso 4), e merges quando `merged_at` está preenchido (peso 5).
- `_save()` — grava o arquivo em formato **JSON Lines**: uma interação por linha.
- `_login()` — utilitário que extrai o campo `login` de um objeto usuário da API, retornando `""` quando o usuário não existe (conta deletada, bot, etc.).

---

## Fluxo de execução

```
main()
  ├── carrega variáveis do .env
  ├── cria MinerConfig
  ├── cria GitHubMinerador
  │     ├── cria CacheJson  →  aponta para dados/cache/
  │     └── cria GitHubClient  →  recebe config + cache
  └── chama miner.run()
        ├── _mine_issue_interactions()
        │     ├── get_all_issues()  →  _get_paged()  →  cache ou HTTP
        │     ├── get_issue_comments(n)  →  para cada issue
        │     └── get_issue_events(n)   →  para issues fechadas
        ├── _mine_pr_interactions()
        │     ├── get_all_pulls()
        │     ├── get_pull_comments(n)  →  para cada PR
        │     └── get_pull_reviews(n)   →  para cada PR
        ├── filtra auto-interações e entradas sem usuário
        └── _save()  →  grava dados/interacoes.json
```

---

## Tipos de interação coletados

| Tipo | Descrição | Peso |
|---|---|:---:|
| `issue_comment` | Usuário comenta em uma issue de outro | 2 |
| `pr_comment` | Usuário faz comentário inline em um PR de outro | 2 |
| `issue_close` | Usuário fecha a issue de outro | 3 |
| `pr_open` | Usuário abre um pull request direcionado a outro colaborador | 3 |
| `pr_review` | Usuário revisa, aprova ou pede mudanças em um PR | 4 |
| `pr_merge` | Usuário realiza o merge do PR de outro | 5 |

---

## Configuração

Crie um arquivo `.env` na raiz do projeto com as variáveis abaixo (use `.env.example` como base):

```env
# Obrigatório — dono e nome do repositório a ser minerado
OWNER=starship
REPO=starship

# Recomendado — token de acesso pessoal do GitHub
# Sem token: 60 req/h   |   Com token: 5.000 req/h
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxx

# Opcional — pasta onde os dados serão gravados (padrão: dados)
OUTPUT_DIR=dados
```

---

## Como rodar

**Instale as dependências:**

```bash
pip install -r mineirador/requirements.txt
```

**Execute o minerador:**

```bash
python -m mineirador
```

Ou via Docker (a imagem do minerador é independente do restante do projeto):

```bash
docker compose up minerador
```

Ao final da execução, o arquivo `dados/interacoes.json` estará disponível para o módulo `biblioteca`.

---

## Cache em disco

Para evitar esgotar a cota da API do GitHub em execuções repetidas, todas as respostas são salvas em `dados/cache/`. Na segunda execução, o minerador lê direto do disco sem fazer nenhuma requisição.

Para forçar uma nova coleta completa, apague a pasta de cache:

```bash
rm -rf dados/cache/
```

---

## Contrato de saída

O arquivo `dados/interacoes.json` segue o formato **JSON Lines** (uma interação por linha):

```json
{"source_user": "alice", "target_user": "bob", "type": "pr_review", "weight": 4, "repo": "owner/repo", "created_at": "2024-03-15T10:22:00Z"}
{"source_user": "carol", "target_user": "alice", "type": "issue_comment", "weight": 2, "repo": "owner/repo", "created_at": "2024-03-14T08:11:00Z"}
{"source_user": "bob", "target_user": "carol", "type": "pr_open", "weight": 3, "repo": "owner/repo", "created_at": "2024-03-13T14:05:00Z"}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `source_user` | `string` | Login do usuário que realizou a ação |
| `target_user` | `string` | Login do usuário que recebeu a ação |
| `type` | `string` | Tipo da interação (ver tabela acima) |
| `weight` | `int` | Peso da aresta no grafo |
| `repo` | `string` | Repositório no formato `owner/repo` |
| `created_at` | `string` | Data e hora da interação em ISO 8601 |