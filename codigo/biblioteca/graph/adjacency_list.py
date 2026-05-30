from .abstract_graph import AbstractGraph


class AdjacencyListGraph(AbstractGraph):
    """
    Implementação concreta de grafo usando lista de adjacência.

    O grafo é:
    - direcionado;
    - simples;
    - sem self-loop;
    - sem arestas duplicadas.
    """

    def __init__(self, num_vertices: int):
        super().__init__(num_vertices)

        # Cada elemento da lista é um dicionário que mapeia o vértice destino
        # para o peso da aresta u -> v.
        self.adjacency_list = [dict() for _ in range(num_vertices)]

    def hasEdge(self, u: int, v: int) -> bool:
        self._validate_vertices(u, v)
        return v in self.adjacency_list[u]

    def addEdge(self, u: int, v: int):
        self._validate_vertices(u, v)
        self._validate_no_self_loop(u, v)

        if v in self.adjacency_list[u]:
            return

        self.adjacency_list[u][v] = 1.0
        self.edge_count += 1

    def removeEdge(self, u: int, v: int):
        self._validate_vertices(u, v)

        if v not in self.adjacency_list[u]:
            return

        del self.adjacency_list[u][v]
        self.edge_count -= 1

    def setEdgeWeight(self, u: int, v: int, w: float):
        self._validate_vertices(u, v)

        if v not in self.adjacency_list[u]:
            raise ValueError(f"Aresta inexistente: {u} -> {v}")

        self.adjacency_list[u][v] = w

    def getEdgeWeight(self, u: int, v: int) -> float:
        self._validate_vertices(u, v)

        if v not in self.adjacency_list[u]:
            raise ValueError(f"Aresta inexistente: {u} -> {v}")

        return self.adjacency_list[u][v]

    def getVertexInDegree(self, u: int) -> int:
        self._validate_vertex(u)

        in_degree = 0
        for origin in range(self.num_vertices):
            if u in self.adjacency_list[origin]:
                in_degree += 1

        return in_degree

    def getVertexOutDegree(self, u: int) -> int:
        self._validate_vertex(u)
        return len(self.adjacency_list[u])

    def __str__(self) -> str:
        lines = ["Adjacency List:"]

        for u, neighbors in enumerate(self.adjacency_list):
            if neighbors:
                entries = [f"{v}(w={w})" for v, w in neighbors.items()]
                lines.append(f"{u}: " + ", ".join(entries))
            else:
                lines.append(f"{u}: []")

        return "\n".join(lines)
