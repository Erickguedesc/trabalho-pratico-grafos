

### 1. `ESPECIFICACAO.md`

*Este arquivo contém as regras, requisitos obrigatórios e diretrizes dadas pelo professor Leonardo para o trabalho prático de 2026/1.*

```markdown
# Trabalho Prático: Teoria de Grafos e Computabilidade
**Curso de Engenharia de Software - PUC Minas (2026/1)** **Professor:** Leonardo V. Cardoso  

---

## 🎯 Objetivo Geral
Desenvolver uma ferramenta computacional que processe dados estruturados como grafos, aplicando conceitos da teoria dos grafos e boas práticas de engenharia de software. O projeto envolve o estudo de um repositório real de algum projeto de código aberto e a análise das interações dos colaboradores.

---

## 📋 Regras de Entrega e Formato
* **Grupo:** Até 4 alunos.
* **Linguagens permitidas:** Java ou Python.
* **Relatório:** Deve ser feito em LaTeX utilizando o template oficial da SBC (7 a 15 páginas).
* **Onde entregar:** No Canvas (prazo e data limite estipulados na tarefa).
* **Formato do arquivo:** Um arquivo `.zip` ou `.rar` contendo:
  * Código-fonte do trabalho.
  * Fonte do relatório (`.tex`).
  * PDF do relatório.
* **Atenção:** Cópias serão sumariamente zeradas. A falta de qualquer um dos itens do entregável resultará em nota zero.

---

## 🚀 Etapas do Trabalho

### Etapa 1: Modelagem e Planejamento da Solução
1. **Escolha do Repositório:** Escolha de um repositório público no GitHub com **mais de 5.000 estrelas** (comunidade ativa).
2. **Extração de Dados:** Foco nas interações entre usuários:
   * Comentários em issues e pull requests.
   * Fechamento de issues.
   * Abertura, revisão, aprovação e merge de pull requests.
3. **Modelagem do Grafo:** * Cada usuário = **Nó (Vértice)**.
   * Cada interação = **Aresta**.
   * O grafo deve ser **simples e direcionado** (relações bidirecionais usam arestas anti-paralelas).
4. **Estrutura dos Grafos:**
   * **Grafos Isolados:**
     * **Grafo 1:** Comentários em issues ou pull requests.
     * **Grafo 2:** Fechamento de issue por outro usuário.
     * **Grafo 3:** Revisões/aprovações/merges de pull requests.
   * **Grafo Integrado:** Combinação ponderada de todas as interações usando os seguintes pesos base:
     * Comentário em issue ou PR: **Peso 2**
     * Abertura de issue comentada por outro usuário: **Peso 3**
     * Revisão/aprovação de PR: **Peso 4**
     * Merge de PR: **Peso 5**

### Etapa 2: Desenvolvimento da Ferramenta
Implementação da estrutura de grafos do zero, algoritmos e interface mínima de uso.

#### Restrições Críticas
* 🚫 **Proibido** o uso de bibliotecas prontas de grafos (como NetworkX e similares).
* ⚙️ Grafos devem ser simples: **não permitir laços nem múltiplas arestas**.
* 🔄 O método `addEdge(u, v)` deve ser idempotente (não duplicar arestas).
* ⚠️ Deve-se lançar exceções para índices inválidos e operações inconsistentes.

#### Arquitetura de Classes Obrigatória
* `AbstractGraph` (Classe Abstrata): Define a API comum, atributos compartilhados (rótulos e pesos) e métodos auxiliares.
* `AdjacencyMatrixGraph` (Classe Concreta): Implementação utilizando matriz de adjacência. Construtor: `AdjacencyMatrixGraph(int numVertices)`.
* `AdjacencyListGraph` (Classe Concreta): Implementação utilizando lista de adjacência. Construtor: `AdjacencyListGraph(int numVertices)`.

#### API Obrigatória
```java
int getVertexCount();
int getEdgeCount();
boolean hasEdge(int u, int v);
void addEdge(int u, int v);
void removeEdge(int u, int v);
boolean isSucessor(int u, int v);
boolean isPredessor(int u, int v);
boolean isDivergent(int u1, int v1, int u2, int v2);
boolean isGridConvergent(int u1, int v1, int u2, int v2); // isConvergent
boolean isIncident(int u, int v, int x);
int getVertexInDegree(int u);
int getVertexOutDegree(int u);
void setVertexWeight(int v, double w);
double getVertexWeight(int v);
void setEdgeWeight(int u, int v, double w);
double getEdgeWeight(int u, int v);
boolean isConnected();
boolean isEmptyGraph();
boolean isCompleteGraph();
void exportToGEPHI(String path);

```

> *Obs: Uma aplicação separada deve consumir a API para demonstrar todas as operações.*

### Etapa 3: Análise do Repositório Baseada em Dados

Análise usando algoritmos aprendidos e métricas de redes complexas:

* **Centralidade:** Grau (degree), Intermediação (betweenness), Proximidade (closeness) e PageRank/Eigenvector.
* **Estrutura e Coesão:** Densidade da rede, Coeficiente de aglomeração (clustering coefficient) e Assortatividade.
* **Comunidade:** Detecção de comunidades (ex: modularidade/Girvan-Newman) e Bridging ties.

---

## 📈 Critérios de Avaliação Técnica

* Corretude da API implementada.
* Utilização correta de herança e abstração orientada a objetos.
* Clareza, legibilidade do código e histórico de commits individuais no Git.
* Cobertura de testes unitários para garantir a mineração e funcionamento da API.

```

---

### 2. `GUIA_ORGANIZACAO.md`
*Este arquivo serve como um guia didático e estratégico para o time organizar o desenvolvimento ao longo das semanas, entender o fluxo de dados e evitar gargalos.*

```markdown
# Guia de Orientação e Organização do Projeto

Este guia divide o projeto em **4 blocos funcionais** e sugere uma estratégia de desenvolvimento distribuída em **4 semanas (Sprints)** para evitar que as duplas fiquem travadas.

---

## 🧱 Os 4 Blocos do Projeto

| Bloco | Nome | Responsabilidade | O que NÃO deve fazer |
| :--- | :--- | :--- | :--- |
| **Bloco 1** | Estrutura do Grafo | Implementar a estrutura do zero (Matriz, Lista, API, Pesos, Exceções). | Não deve saber que os dados vieram do GitHub. |
| **Bloco 2** | Minerador GitHub | Consultar a API do GitHub/Web scraping e salvar os dados brutos filtrados em JSON local. | Não deve saber como o grafo funciona internamente. |
| **Bloco 3** | Construtor de Grafos | Ler os JSONs locais, mapear strings de usuários para IDs inteiros (`UserMapper`) e montar os 4 grafos. | Não deve calcular métricas nem chamar o GitHub. |
| **Bloco 4** | Análise e Exportação | Pegar os grafos prontos, rodar as métricas complexas, gerar os rankings e exportar para o Gephi. | Não deve minerar dados do GitHub. |

---

## 🔄 Fluxo de Dados Completo


```

[GitHub API / Scraping]
│
▼ (Executado antes)
[Bloco 2: Minerador] ──► Salva em arquivos .json locais (Cache)
│
▼ (Na Apresentação / Execução)
[Bloco 3: Construtor] ──► Mapeia Usuários para Inteiros
│
▼
[Bloco 1: Estruturas de Grafo (Matriz/Lista)]
│
▼
[Bloco 4: Módulo de Análise] ──► Cálculos de Métricas & Gephi (.gexf)

```

---

## 📅 Planejamento das Sprints (4 Semanas)

### 🗓️ Semana 1: Planejamento e Contratos
* **Foco:** Definição do escopo inicial e alinhamento do time.
* **Tarefas:**
  * Escolher o repositório público (> 5.000 estrelas).
  * Definir a linguagem (Java ou Python).
  * Inicializar o repositório no GitHub Classroom.
  * Criar o rascunho do Diagrama de Classes e as assinaturas da API.
  * Criar um **JSON fictício** contendo interações simuladas para que o desenvolvimento do grafo não dependa do minerador estar pronto.
  * Iniciar o documento LaTeX no Overleaf.

### 🗓️ Semana 2: API de Grafos + Minerador Básico
* **Dupla A (Grafo):** Implementar `AbstractGraph`, estruturas base de `AdjacencyMatrixGraph` e `AdjacencyListGraph` com métodos fundamentais (`addEdge`, `removeEdge`, `hasEdge`). Criar testes unitários básicos.
* **Dupla B (Minerador):** Desenvolver o script de coleta inicial (coleta de autores, comentários de issues e salvamento do JSON com sistema de cache local).

> 🔑 **Frase-chave da Semana 2:** A Dupla A entrega o **contrato (interface)** da API. A Dupla B usa o JSON fictício da semana 1 para estruturar seus dados sem ficar esperando o código final da Dupla A.

### 🗓️ Semana 3: Integração e Análise
* **Dupla A:** Finalizar todos os métodos avançados de topologia da API, implementar o `UserMapper` (conversor de login para ID) e codificar o construtor que lê o JSON real e gera os 3 grafos isolados + o grafo integrado ponderado.
* **Dupla B:** Finalizar o minerador (incluindo PRs, revisões e merges), estruturar o cálculo das métricas de centralidade e densidade.
* **Todo o Grupo:** Implementar o método `exportToGEPHI`, gerar os arquivos `.gexf` e testar a abertura e visualização das redes no Gephi.

### 🗓️ Semana 4: Lapidação e Entregáveis
* **Foco:** Testes, documentação e ensaio. *Proibido inventar novas features aqui!*
* **Tarefas:**
  * Garantir cobertura de testes robusta (próxima ou superior a 90%).
  * Limpar o código (remover duplicações e *code smells*).
  * Escrever o relatório em LaTeX (entre 7 e 15 páginas).
  * Gravar o vídeo demonstrativo da ferramenta (5 a 10 minutos).
  * Preparar os slides e ensaiar a apresentação presencial (10 a 15 minutos).
  * Gerar o arquivo ZIP e fazer o upload no Canvas.

---

## ❓ Perguntas Prováveis na Arguição do Professor
Preparem-se para responder conceitualmente mostrando o código:
1. *Como o método `addEdge(u, v)` garante a idempotência e impede laços?*
2. *Qual a diferença de complexidade de tempo e espaço entre a sua implementação de matriz e a de lista?*
3. *Por que os dados coletados do GitHub foram salvos em JSON local em vez de processados em tempo real? (Resposta: Evitar limites de requisição da API do GitHub, lentidão e dependência de internet na apresentação).*
4. *O que significa, no contexto de colaboração de software, um nó possuir um alto grau de saída? E um alto PageRank?*

```

---

### 3. `RELATORIO_STREAMLIT.md`

*Este arquivo consolida o estudo de caso real realizado pelo grupo que analisou o repositório **Streamlit**, servindo como excelente base de conteúdo para o relatório oficial em LaTeX.*

```markdown
# Estudo de Caso: Análise de Colaboração no Repositório Streamlit
**Repositório Analisado:** [streamlit/streamlit](https://github.com/streamlit/streamlit)

---

## 📊 Justificativa do Repositório
O Streamlit foi selecionado por cumprir com folga os critérios de amostragem do projeto:
* **Estrelas:** 41.2 mil (Exigência: > 5.000).
* **Volume de Dados:** Mais de 200 pull requests abertos e 7.000 fechados no momento da análise.
* **Comunidade:** Altamente ativa, garantindo um volume massivo de interações (issues, PRs, revisões) para gerar uma modelagem de rede complexa robusta.

---

## 🛠️ Detalhes da Implementação Realizada
* **Linguagem do Minerador:** Python.
* **Estratégia de Coleta:** Abordagem híbrida utilizando `BeautifulSoup` para raspagem web na listagem de Issues e a **API oficial do GitHub** para extração cirúrgica de Pull Requests e revisões.
* **Persistência de Suporte:** Utilização do banco de dados orientado a grafos `Neo4j` para armazenamento e estruturação intermediária das entidades coletadas antes da conversão para as estruturas em memória.

---

## 📐 Resultados dos Experimentos de Desempenho

O custo computacional de tempo para a alocação e inserção de arestas foi medido em ambiente controlado, comparando as duas estruturas implementadas em memória:

### Tempo de Construção do Grafo (em milissegundos)

| Vértices (Usuários) | Arestas (Interações) | Matriz de Adjacência | Lista de Adjacência |
| :--- | :--- | :--- | :--- |
| 100 | 1.179 | 2 ms | 2 ms |
| 500 | 2.060 | 49 ms | 40 ms |
| 1.000 | 2.783 | 185 ms | 170 ms |
| **4.061 (Grafo Real)**| **8.098** | **2.758 ms** | **2.562 ms** |

> 💡 **Conclusão Estrutural:** Conforme esperado teoricamente, a **Lista de Adjacência** demonstrou maior eficiência computacional em cenários de grande escala devido à sua complexidade $\mathcal{O}(V + E)$, mostrando-se ideal para redes colaborativas que são majoritariamente esparsas. A Matriz de Adjacência sofre com o crescimento quadrático $\mathcal{O}(V^2)$ de alocação de memória.

---

## 📈 Análise Topológica e Métricas da Rede

Ao rodar os algoritmos de análise sobre o **Grafo Integrado Ponderado** do Streamlit (compostos por 4.061 vértices e 8.098 arestas), os seguintes valores globais foram extraídos:

| Métrica Estrutural | Valor Obtido |
| :--- | :--- |
| **Densidade da Rede** | 0.00049 |
| **Coeficiente de Aglomeração Médio** | 0.2668 |
| **Assortatividade** | -0.2452 |

### Interpretação dos Resultados Globais
* **Densidade Baixa (0.00049):** Confirma que a rede é altamente esparsa. Em grandes ecossistemas open-source, a maioria dos usuários interage apenas em pontos específicos e isolados.
* **Aglomeração Elevada (0.2668):** Indica uma forte tendência de formação de *clusters* e pequenos subgrupos locais densamente conectados (ex: desenvolvedores focados em módulos ou features específicas).
* **Assortatividade Negativa (-0.2452):** Caracteriza uma **rede hierárquica disassortativa**. Nós com altíssimo grau (*hubs*) conectam-se massivamente com nós de baixo grau. Na prática, significa que os mantenedores principais interagem diretamente com contribuidores casuais/ocasionais que abrem issues ou enviam PRs simples.

---

## 👑 Centralidade e Distribuição de Influência

A análise ranqueou os usuários mais centrais a partir da consolidação do fluxo de interações.

### Top 5 Usuários Mais Influentes
1. `dependabot[bot]` (Ferramenta de automação de dependências)
2. `lukasmasuch` (Mantenedor Humano Principal)
3. `raethlein`
4. `willhuang1997`
5. `mayagbarnes`

---

## 👥 Estrutura de Comunidades (Girvan-Newman)
O algoritmo divisivo de Girvan-Newman foi aplicado limitando a análise exploratória aos primeiros desmembramentos devido à alta complexidade computacional:
* **Total de Comunidades Identificadas:** 259 comunidades.
* **Comunidade Gigante:** A maior comunidade detém **3.803 membros**.
* **Demais Comunidades:** Possuem apenas 1 membro cada.
* **Arestas de Ponte (Bridges):** Nenhuma encontrada de forma isolada.

> 🔍 **Análise:** O ecossistema possui um **núcleo denso, gigante e altamente coeso**. O fato de as outras 258 comunidades possuírem apenas um membro isolado evidencia uma vasta periferia de usuários casuais que realizam interações únicas com o núcleo mantenedor e não retornam.

---

## 🏁 Conclusões do Diagnóstico de Governança
A análise visual e métrica gerada pela ferramenta desconstrói o mito de que o projeto se comporta como uma "comunidade distribuída e descentralizada":
1. **Gargalo de Liderança (Gatekeeper):** O usuário `lukasmasuch` atua como o principal ponto de articulação do ecossistema. Ele possui uma métrica de grau **três vezes superior ao segundo colocado**.
2. **Ponto Único de Falha:** Embora essa centralização extrema garanta uma rigorosa consistência de código (centralizando revisões e merges), ela gera um gargalo operacional. Caso o mantenedor principal se ausente, o fluxo de evolução do repositório corre o risco de sofrer uma paralisia severa.
3. **Recomendação de Engenharia:** Recomenda-se à governança do Streamlit descentralizar as responsabilidades técnicas de revisão de código, distribuindo o poder de aprovação de PRs entre outros membros da comunidade para aumentar a resiliência do projeto.

```