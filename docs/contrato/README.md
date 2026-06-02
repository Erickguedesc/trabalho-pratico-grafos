# Contrato — diagramas PlantUML (compactos)

Diagramas **curtos**, `left to right direction`, pacotes por bloco do trabalho. Seguem notação UML de classes (PlantUML):

| Símbolo | Significado |
|---------|-------------|
| `+` / `#` / `-` | público / protegido / privado |
| `__` | separador atributos ↔ operações |
| `/nome` | atributo derivado (`@property`) |
| `{abstract}` | operação abstrata |
| `<\|--` | generalização (herança) |
| `*--` | composição (parte não vive sem o todo) |
| `o--` | agregação |
| `..>` | dependência (`«use»`, `«create»`, …) |
| `<<DTO>>`, `<<planned>>` | estereótipos |
| `artifact` | arquivo de persistência (`interacoes.json`) |

Classes com `<<planned>>` ainda não estão no código. Inspirado no formato de diagramas de outro grupo, **sem** repetir a arquitetura deles (ex.: não usamos NetworkX como TAD do grafo).

## Ficheiros

| Ficheiro | O quê |
|----------|--------|
| [diagrama-visao-geral.puml](diagrama-visao-geral.puml) | Fluxo entre minerador → JSON → construtor → grafos → métricas → demo. |
| [diagrama-contrato-interacoes.puml](diagrama-contrato-interacoes.puml) | DTO `Interaction` / linha de `interacoes.json`. |
| [diagrama-grafo.puml](diagrama-grafo.puml) | `AbstractGraph`, matriz e lista (API em camelCase; `ValueError`). |
| [diagrama-minerador.puml](diagrama-minerador.puml) | GitHub + cache JSON + cliente HTTP **externo**. |
| [diagrama-construtor-grafos.puml](diagrama-construtor-grafos.puml) | `UserMapper`, `GraphBuilder`, `GraphBundle`, ligação ao DTO. |
| [diagrama-analise.puml](diagrama-analise.puml) | `GraphAnalyzer` (planejado) lendo só `AbstractGraph`. |
| [diagrama-demo-aplicacao.puml](diagrama-demo-aplicacao.puml) | CLI / `main` que demonstra a API (e encosto opcional aos outros blocos). |

Não há pasta `include/` nem diagrama monolítico: cada `.puml` é **autónomo**.

## Exportar imagens

```bash
cd docs/contrato
plantuml -tsvg *.puml
```
