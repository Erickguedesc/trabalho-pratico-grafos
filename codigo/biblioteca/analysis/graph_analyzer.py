# =============================================================================
# graph_analyzer.py
# -----------------------------------------------------------------------------
# Responsabilidade:
#   Calcular todas as métricas de redes complexas exigidas pela Etapa 3
#   do trabalho, usando apenas a API do grafo (sem NetworkX ou similares).
#
# Métricas implementadas:
#
#   CENTRALIDADE:
#     - Grau (degree centrality)
#     - Betweenness centrality (intermediação)
#     - Closeness centrality (proximidade)
#     - PageRank
#
#   ESTRUTURA:
#     - Densidade da rede
#     - Coeficiente de clustering (aglomeração)
#     - Assortatividade
#
#   COMUNIDADE:
#     - Detecção de comunidades por label propagation
#     - Bridging ties (pontes entre comunidades)
# =============================================================================

from collections import deque
from ..graph.abstract_graph import AbstractGraph


class GraphAnalyzer:
    """
    Calcula métricas de redes complexas sobre um grafo direcionado e ponderado.

    Todas as métricas são implementadas do zero, sem uso de bibliotecas externas
    como NetworkX, igraph ou similares — conforme exigido pelo enunciado.

    Uso:
        analyzer = GraphAnalyzer(bundle.integrated, bundle.mapper)
        print(analyzer.degree_centrality())
        print(analyzer.pagerank())
        print(analyzer.density())
    """

    def __init__(self, graph: AbstractGraph, mapper=None):
        """
        Cria um analisador para o grafo recebido.

        Recebe:
            graph  (AbstractGraph): grafo a ser analisado (qualquer implementação).
            mapper (UserMapper, opcional): para converter índice -> login nos resultados.
                   Se None, os resultados usam os índices numéricos como chave.
        """

        # Guarda o grafo que será analisado.
        self.graph = graph

        # Guarda o mapper para exibir logins em vez de números nos resultados.
        self.mapper = mapper

        # Atalho: quantidade de vértices (usado em muitos algoritmos).
        self.n = graph.getVertexCount()

    def _label(self, v: int) -> str:
        """
        Converte um índice de vértice em um rótulo legível.

        Se o mapper foi fornecido, retorna o login do GitHub.
        Caso contrário, retorna o índice como string.

        Recebe:
            v (int): índice do vértice.

        Retorna:
            str: login ou índice como texto.
        """

        if self.mapper is not None:
            try:
                return self.mapper.get_login(v)
            except KeyError:
                pass
        return str(v)

    # =========================================================================
    # MÉTRICAS DE CENTRALIDADE
    # =========================================================================

    def degree_centrality(self) -> dict[str, dict]:
        """
        Calcula a centralidade de grau de todos os vértices.

        O que é:
            Mede quantas conexões diretas cada vértice tem.
            No contexto do projeto, indica quais usuários participaram mais
            de revisões, discussões e colaborações.

        Fórmula (grau normalizado):
            in_degree_centrality(v)  = in_degree(v)  / (n - 1)
            out_degree_centrality(v) = out_degree(v) / (n - 1)

        A normalização divide pelo máximo teórico (n-1) para que o valor
        fique entre 0 e 1, independente do tamanho do grafo.

        Retorna:
            dict: {login: {"in": float, "out": float, "total": float}}
                  ordenado pelo grau total decrescente.
        """

        result = {}

        # Evita divisão por zero em grafos com 1 vértice.
        divisor = max(self.n - 1, 1)

        for v in range(self.n):
            in_deg  = self.graph.getVertexInDegree(v)
            out_deg = self.graph.getVertexOutDegree(v)

            result[self._label(v)] = {
                "in":    round(in_deg  / divisor, 4),
                "out":   round(out_deg / divisor, 4),
                "total": round((in_deg + out_deg) / (2 * divisor), 4),
            }

        # Retorna ordenado pelo grau total decrescente (mais central primeiro).
        return dict(sorted(result.items(), key=lambda x: x[1]["total"], reverse=True))

    # def betweenness_centrality(self) -> dict[str, float]:
    #     """
    #     Calcula a centralidade de intermediação (betweenness) de cada vértice.

    #     O que é:
    #         Mede quantas vezes cada vértice aparece nos caminhos mínimos
    #         entre todos os pares de vértices do grafo.
    #         Indica quem age como "ponte" entre grupos diferentes do projeto.

    #     Algoritmo:
    #         Brandes (2001) — O(V * E) com BFS, implementado do zero.
    #         Para cada vértice s:
    #           1. BFS para encontrar os caminhos mínimos a partir de s.
    #           2. Acumulação reversa das dependências.

    #     Normalização:
    #         O valor é dividido por (n-1)*(n-2) para grafos direcionados,
    #         normalizando entre 0 e 1.

    #     Retorna:
    #         dict: {login: float} ordenado pelo valor decrescente.
    #     """

    #     # Inicializa a pontuação de cada vértice com 0.
    #     betweenness = [0.0] * self.n

    #     for s in range(self.n):
    #         # ---- Inicialização para BFS a partir de s ----

    #         # Pilha de processamento (ordem de descoberta).
    #         stack = []

    #         # predecessores[w] = lista de vértices que antecederam w
    #         # nos caminhos mínimos a partir de s.
    #         predecessors = [[] for _ in range(self.n)]

    #         # sigma[t] = número de caminhos mínimos de s até t.
    #         sigma = [0] * self.n
    #         sigma[s] = 1

    #         # dist[t] = distância mínima de s até t (-1 = não visitado).
    #         dist = [-1] * self.n
    #         dist[s] = 0

    #         # Fila da BFS.
    #         queue = deque([s])

    #         # ---- BFS: encontra todos os caminhos mínimos a partir de s ----
    #         while queue:
    #             v = queue.popleft()
    #             stack.append(v)

    #             for w in range(self.n):
    #                 if not self.graph.hasEdge(v, w):
    #                     continue

    #                 # Se w ainda não foi visitado: define a distância.
    #                 if dist[w] == -1:
    #                     dist[w] = dist[v] + 1
    #                     queue.append(w)

    #                 # Se w está no nível seguinte de v: atualiza contagem de caminhos.
    #                 if dist[w] == dist[v] + 1:
    #                     sigma[w] += sigma[v]
    #                     predecessors[w].append(v)

    #         # ---- Acumulação reversa das dependências ----
    #         # delta[v] = fração de dependência de s sobre v.
    #         delta = [0.0] * self.n

    #         while stack:
    #             w = stack.pop()
    #             for v in predecessors[w]:
    #                 if sigma[w] > 0:
    #                     # Propaga a dependência de w para seu predecessor v.
    #                     delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])

    #             # O vértice s não conta para si mesmo.
    #             if w != s:
    #                 betweenness[w] += delta[w]

    #     # Normaliza para grafos direcionados: divide por (n-1)*(n-2).
    #     norm = max((self.n - 1) * (self.n - 2), 1)
    #     result = {
    #         self._label(v): round(betweenness[v] / norm, 6)
    #         for v in range(self.n)
    #     }

    #     return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))


    def betweenness_centrality(self) -> dict[str, float]:
        """
        Calcula a centralidade de intermediação (Betweenness Centrality)
        usando o algoritmo de Brandes para grafos direcionados.
        """

        betweenness = [0.0] * self.n

        for s in range(self.n):

            stack = []

            predecessors = [[] for _ in range(self.n)]

            sigma = [0] * self.n
            sigma[s] = 1

            dist = [-1] * self.n
            dist[s] = 0

            queue = deque([s])

            # --------------------------------------------------
            # BFS
            # --------------------------------------------------

            while queue:

                v = queue.popleft()
                stack.append(v)

                # CORREÇÃO:
                # percorre apenas vizinhos existentes
                for w in self.graph.adjacency_list[v].keys():

                    if dist[w] == -1:
                        dist[w] = dist[v] + 1
                        queue.append(w)

                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        predecessors[w].append(v)

            # --------------------------------------------------
            # Acumulação reversa
            # --------------------------------------------------

            delta = [0.0] * self.n

            while stack:

                w = stack.pop()

                for v in predecessors[w]:

                    if sigma[w] > 0:
                        delta[v] += (
                            sigma[v] / sigma[w]
                        ) * (1.0 + delta[w])

                if w != s:
                    betweenness[w] += delta[w]

        norm = max((self.n - 1) * (self.n - 2), 1)

        result = {
            self._label(v): round(betweenness[v] / norm, 6)
            for v in range(self.n)
        }

        return dict(
            sorted(
                result.items(),
                key=lambda x: x[1],
                reverse=True
            )
    )

    def closeness_centrality(self) -> dict[str, float]:
        """
        Calcula a centralidade de proximidade (closeness) de cada vértice.

        O que é:
            Identifica quem está mais "próximo" de todos os outros no grafo,
            ou seja, quem tem acesso mais rápido à informação.
            Um valor alto indica que o usuário consegue alcançar os demais
            com poucos passos.

        Fórmula:
            closeness(v) = (n_alcancaveis - 1)² / ((n - 1) * soma_distancias)

            Onde:
              - n_alcancaveis = quantos vértices v consegue alcançar via BFS.
              - soma_distancias = soma das distâncias até cada vértice alcançável.

            Esta fórmula (Wasserman & Faust) é adaptada para grafos desconexos
            e evita resultados enganosos quando um vértice não alcança todos os outros.

        Retorna:
            dict: {login: float} ordenado pelo valor decrescente.
        """

        result = {}

        for v in range(self.n):
            # BFS a partir de v para descobrir distâncias até todos os outros.
            dist = self._bfs_distances(v)

            # Considera apenas os vértices que v consegue alcançar (excluindo si mesmo).
            reachable_dists = [d for d in dist if d > 0]
            n_reached = len(reachable_dists)

            if n_reached == 0:
                # Vértice isolado: closeness é 0.
                result[self._label(v)] = 0.0
            else:
                # Fórmula normalizada de Wasserman & Faust.
                sum_d = sum(reachable_dists)
                closeness = (n_reached ** 2) / ((self.n - 1) * sum_d)
                result[self._label(v)] = round(closeness, 6)

        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def pagerank(self, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-6) -> dict[str, float]:
        """
        Calcula o PageRank de cada vértice.

        O que é:
            Mede a influência de um vértice, levando em conta não apenas
            quantas conexões ele tem, mas também a importância de quem
            está conectado a ele.
            É o algoritmo que o Google usava para ranquear páginas web.
            No projeto, indica quem são os colaboradores mais influentes.

        Algoritmo:
            Power iteration com fator de amortecimento (damping factor).
            O algoritmo itera até a soma das diferenças ser menor que `tol`
            ou até atingir `max_iter` iterações.

        Fórmula:
            PR(v) = (1 - d) / n  +  d * soma_u( PR(u) / out_degree(u) )

            Onde:
              - d = fator de amortecimento (padrão 0.85).
              - n = número de vértices.
              - soma_u = soma sobre todos os vértices u que apontam para v.

        Recebe:
            damping  (float): fator de amortecimento, entre 0 e 1 (padrão 0.85).
            max_iter (int):   número máximo de iterações (padrão 100).
            tol      (float): tolerância para convergência (padrão 1e-6).

        Retorna:
            dict: {login: float} com valores somando ~1.0, ordenado decrescente.
        """

        # Inicializa o PageRank de cada vértice com valor uniforme: 1/n.
        pr = [1.0 / self.n] * self.n

        # Calcula o grau de saída de cada vértice (usado como divisor).
        out_degrees = [self.graph.getVertexOutDegree(v) for v in range(self.n)]

        # Iteração do algoritmo.
        for _ in range(max_iter):
            new_pr = [0.0] * self.n

            for v in range(self.n):
                # Acumula contribuições de todos os vértices que apontam para v.
                for u in range(self.n):
                    if self.graph.hasEdge(u, v) and out_degrees[u] > 0:
                        new_pr[v] += pr[u] / out_degrees[u]

                # Aplica o fator de amortecimento e a componente de teleporte.
                new_pr[v] = (1 - damping) / self.n + damping * new_pr[v]

            # Verifica convergência: se a soma das diferenças for menor que tol, para.
            diff = sum(abs(new_pr[v] - pr[v]) for v in range(self.n))
            pr = new_pr

            if diff < tol:
                break

        # Normaliza os valores para que somem exatamente 1.
        total = sum(pr)
        if total > 0:
            pr = [p / total for p in pr]

        result = {
            self._label(v): round(pr[v], 6)
            for v in range(self.n)
        }

        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    # =========================================================================
    # MÉTRICAS DE ESTRUTURA
    # =========================================================================

    def density(self) -> float:
        """
        Calcula a densidade da rede.

        O que é:
            Proporção entre o número de arestas existentes e o número máximo
            possível de arestas. Indica o quão colaborativa é a rede como um todo.

        Fórmula:
            density = edges / (n * (n - 1))

        Valor entre 0 e 1:
            - 0: grafo sem nenhuma aresta.
            - 1: grafo completo (todo mundo conectado com todo mundo).
            - Grafos de colaboração reais tipicamente têm densidade < 0.1.

        Retorna:
            float: valor entre 0 e 1.
        """

        max_edges = self.n * (self.n - 1)

        if max_edges == 0:
            return 0.0

        return round(self.graph.getEdgeCount() / max_edges, 6)

    def clustering_coefficient(self) -> dict[str, float]:
        """
        Calcula o coeficiente de clustering (aglomeração) de cada vértice.

        O que é:
            Mede a tendência dos vizinhos de um vértice de também serem
            conectados entre si — formando "triângulos" ou "clusters".
            Um valor alto indica que os colaboradores do usuário também
            colaboram entre si (grupos coesos).

        Fórmula (versão não-direcionada simplificada):
            cc(v) = triangulos(v) / (grau(v) * (grau(v) - 1))

            Onde grau(v) é o grau total (entrada + saída sem duplicatas),
            e triangulos é o número de pares de vizinhos que se conectam entre si.

        Retorna:
            dict: {login: float} com o coeficiente de cada vértice, ordenado decrescente.
        """

        result = {}

        for v in range(self.n):
            # Coleta todos os vizinhos de v (entrada + saída, sem duplicatas).
            neighbors = set()
            for u in range(self.n):
                if u == v:
                    continue
                if self.graph.hasEdge(v, u) or self.graph.hasEdge(u, v):
                    neighbors.add(u)

            degree = len(neighbors)

            # Vértices com grau 0 ou 1 não podem formar triângulos.
            if degree < 2:
                result[self._label(v)] = 0.0
                continue

            # Conta quantos pares de vizinhos estão conectados entre si.
            triangles = 0
            neighbor_list = list(neighbors)
            for i in range(len(neighbor_list)):
                for j in range(i + 1, len(neighbor_list)):
                    a = neighbor_list[i]
                    b = neighbor_list[j]
                    # Conta conexão em qualquer direção.
                    if self.graph.hasEdge(a, b) or self.graph.hasEdge(b, a):
                        triangles += 1

            # Número máximo de pares de vizinhos.
            max_triangles = degree * (degree - 1) / 2
            result[self._label(v)] = round(triangles / max_triangles, 4)

        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def assortativity(self) -> float:
        """
        Calcula a assortatividade da rede por grau.

        O que é:
            Mede se vértices com muitas conexões tendem a se conectar entre si
            (rede assortativa) ou se preferem vértices com poucas conexões
            (rede disassortativa).

        Interpretação:
            > 0: assortativa — hubs se conectam com outros hubs.
            < 0: disassortativa — hubs conectam com nós periféricos.
            = 0: sem preferência.

        Algoritmo:
            Correlação de Pearson entre o grau de saída da origem e o grau de
            entrada do destino para cada aresta.

        Retorna:
            float: entre -1 e 1.
        """

        # Coleta pares de grau (out_degree(u), in_degree(v)) para cada aresta u->v.
        pairs = []
        for u in range(self.n):
            for v in range(self.n):
                if self.graph.hasEdge(u, v):
                    pairs.append((
                        self.graph.getVertexOutDegree(u),
                        self.graph.getVertexInDegree(v),
                    ))

        if len(pairs) < 2:
            return 0.0

        # Calcula a correlação de Pearson entre os dois conjuntos de graus.
        x_vals = [p[0] for p in pairs]
        y_vals = [p[1] for p in pairs]

        n = len(pairs)
        mean_x = sum(x_vals) / n
        mean_y = sum(y_vals) / n

        numerator   = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
        denom_x     = sum((x - mean_x) ** 2 for x in x_vals) ** 0.5
        denom_y     = sum((y - mean_y) ** 2 for y in y_vals) ** 0.5
        denominator = denom_x * denom_y

        if denominator == 0:
            return 0.0

        return round(numerator / denominator, 4)

    # =========================================================================
    # MÉTRICAS DE COMUNIDADE
    # =========================================================================

    def detect_communities(self, max_iter: int = 50) -> dict[str, int]:
        """
        Detecta comunidades usando o algoritmo Label Propagation.

        O que é:
            Identifica grupos de usuários que trabalham mais frequentemente juntos
            — como equipes informais dentro do projeto.

        Algoritmo (Label Propagation):
            1. Atribui uma comunidade diferente a cada vértice (rótulo = índice).
            2. Itera: cada vértice adota a comunidade mais frequente entre seus vizinhos.
            3. Para quando nenhuma mudança ocorre ou atinge max_iter iterações.

        Por que Label Propagation?
            É simples, eficiente (O(E)) e funciona sem definir o número de comunidades
            previamente — adequado para implementar do zero.

        Recebe:
            max_iter (int): limite de iterações para garantir que o algoritmo termina.

        Retorna:
            dict: {login: comunidade_id} onde comunidade_id é um inteiro.
        """

        # Inicialização: cada vértice começa com sua própria comunidade.
        community = list(range(self.n))

        for _ in range(max_iter):
            changed = False

            # Percorre os vértices em ordem aleatória implícita (lista direta).
            for v in range(self.n):
                # Coleta os rótulos de todos os vizinhos (entrada e saída).
                neighbor_labels = []
                for u in range(self.n):
                    if u == v:
                        continue
                    if self.graph.hasEdge(v, u) or self.graph.hasEdge(u, v):
                        neighbor_labels.append(community[u])

                if not neighbor_labels:
                    continue  # Vértice isolado: mantém sua comunidade.

                # Encontra o rótulo mais frequente entre os vizinhos.
                label_counts: dict[int, int] = {}
                for lbl in neighbor_labels:
                    label_counts[lbl] = label_counts.get(lbl, 0) + 1

                best_label = max(label_counts, key=label_counts.get)

                if best_label != community[v]:
                    community[v] = best_label
                    changed = True

            # Se nenhum vértice mudou de comunidade, o algoritmo convergiu.
            if not changed:
                break

        # Renumera as comunidades de 0 até K-1 para facilitar leitura.
        unique_labels = sorted(set(community))
        remap = {old: new for new, old in enumerate(unique_labels)}
        community = [remap[c] for c in community]

        return {self._label(v): community[v] for v in range(self.n)}

    def bridging_ties(self, communities: dict[str, int]) -> dict[str, int]:
        """
        Identifica os bridging ties — usuários que conectam comunidades diferentes.

        O que é:
            Analisa quem atua como elo entre grupos que, de outra forma,
            seriam isolados. São os usuários mais estratégicos para a
            difusão de informação no projeto.

        Definição usada:
            Um usuário é considerado bridging tie se ele tem vizinhos em
            pelo menos 2 comunidades diferentes.
            O score é o número de comunidades distintas com as quais
            ele se conecta.

        Recebe:
            communities (dict): resultado de detect_communities().

        Retorna:
            dict: {login: numero_de_comunidades_distintas}
                  apenas usuários que conectam 2+ comunidades, ordenado decrescente.
        """

        result = {}

        for v in range(self.n):
            label_v = self._label(v)
            own_community = communities.get(label_v, -1)

            # Coleta as comunidades distintas dos vizinhos.
            neighbor_communities = set()
            for u in range(self.n):
                if u == v:
                    continue
                if self.graph.hasEdge(v, u) or self.graph.hasEdge(u, v):
                    label_u = self._label(u)
                    neighbor_communities.add(communities.get(label_u, -1))

            # Conta comunidades distintas (incluindo a própria, se houver vizinhos externos).
            all_communities = neighbor_communities | {own_community}

            if len(all_communities) >= 2:
                result[label_v] = len(all_communities)

        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    # =========================================================================
    # MÉTODO AUXILIAR INTERNO
    # =========================================================================

    from collections import deque

    def _bfs_distances(self, source: int) -> list[int]:
        """
        Executa BFS a partir de um vértice e retorna a lista de distâncias.

        Retorna:
            list[int]: distâncias até cada vértice.
                    -1 significa não alcançável.
        """

        dist = [-1] * self.n
        dist[source] = 0

        queue = deque([source])

        while queue:
            v = queue.popleft()

            # Percorre SOMENTE os vizinhos existentes
            for w in self.graph.adjacency_list[v].keys():

                if dist[w] == -1:
                    dist[w] = dist[v] + 1
                    queue.append(w)

        return dist

    def full_report(self) -> str:
        """
        Gera um relatório textual com todas as métricas calculadas.

        Útil para a demo CLI e para incluir no relatório LaTeX.
        Exibe apenas os top-10 em cada métrica de ranking.

        Retorna:
            str: texto formatado com todas as métricas.
        """

        lines = []
        SEP = "=" * 55

        lines.append(SEP)
        lines.append("RELATÓRIO DE ANÁLISE DO GRAFO")
        lines.append(f"  Vértices: {self.n} | Arestas: {self.graph.getEdgeCount()}")
        lines.append(SEP)

        # --- Densidade ---
        lines.append(f"\n{'DENSIDADE':}")
        lines.append(f"  {self.density():.6f}  (0 = sem arestas, 1 = grafo completo)")

        # --- Assortatividade ---
        lines.append(f"\n{'ASSORTATIVIDADE':}")
        assort = self.assortativity()
        interp = "assortativa (hubs se conectam)" if assort > 0 else "disassortativa (hubs conectam periféricos)"
        lines.append(f"  {assort:.4f}  → {interp}")

        # --- Centralidade de Grau (top 10) ---
        lines.append(f"\n{'DEGREE CENTRALITY — TOP 10':}")
        lines.append(f"  {'Usuário':<25} {'In':>8} {'Out':>8} {'Total':>8}")
        lines.append(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*8}")
        for user, vals in list(self.degree_centrality().items())[:10]:
            lines.append(f"  {user:<25} {vals['in']:>8.4f} {vals['out']:>8.4f} {vals['total']:>8.4f}")

        # --- Betweenness (top 10) ---
        lines.append(f"\n{'BETWEENNESS CENTRALITY — TOP 10':}")
        for user, val in list(self.betweenness_centrality().items())[:10]:
            lines.append(f"  {user:<25} {val:.6f}")

        # --- Closeness (top 10) ---
        lines.append(f"\n{'CLOSENESS CENTRALITY — TOP 10':}")
        for user, val in list(self.closeness_centrality().items())[:10]:
            lines.append(f"  {user:<25} {val:.6f}")

        # --- PageRank (top 10) ---
        lines.append(f"\n{'PAGERANK — TOP 10':}")
        for user, val in list(self.pagerank().items())[:10]:
            lines.append(f"  {user:<25} {val:.6f}")

        # --- Clustering (top 10) ---
        lines.append(f"\n{'CLUSTERING COEFFICIENT — TOP 10':}")
        for user, val in list(self.clustering_coefficient().items())[:10]:
            lines.append(f"  {user:<25} {val:.4f}")

        # --- Comunidades ---
        lines.append(f"\n{'COMUNIDADES (Label Propagation)':}")
        communities = self.detect_communities()
        num_communities = len(set(communities.values()))
        lines.append(f"  {num_communities} comunidades detectadas.")

        # Agrupa por comunidade para exibir.
        from collections import defaultdict
        groups: dict[int, list[str]] = defaultdict(list)
        for user, comm_id in communities.items():
            groups[comm_id].append(user)

        for comm_id, members in sorted(groups.items()):
            preview = ", ".join(members[:5])
            suffix = f"... (+{len(members)-5})" if len(members) > 5 else ""
            lines.append(f"  Comunidade {comm_id}: {preview}{suffix}")

        # --- Bridging Ties ---
        lines.append(f"\n{'BRIDGING TIES':}")
        bridges = self.bridging_ties(communities)
        if bridges:
            for user, score in list(bridges.items())[:10]:
                lines.append(f"  {user:<25} conecta {score} comunidades")
        else:
            lines.append("  Nenhum bridging tie encontrado.")

        lines.append(f"\n{SEP}")
        return "\n".join(lines)