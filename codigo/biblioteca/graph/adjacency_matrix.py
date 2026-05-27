from .abstract_graph import AbstractGraph


class AdjacencyMatrixGraph(AbstractGraph):
    """
    Implementação concreta de grafo usando matriz de adjacência.

    Esta classe herda de AbstractGraph (class mãe) e implementa os métodos abstratos
    que dependem diretamente da estrutura interna do grafo.

    Estruturas usadas:
    - adjacency_matrix[u][v]: indica se existe aresta u -> v.
    - edge_weights[u][v]: armazena o peso da aresta u -> v.

    O grafo é:
    - direcionado;
    - simples;
    - sem self-loop;
    - sem múltiplas arestas entre os mesmos vértices.
    """

    def __init__(self, num_vertices: int):
        """
        Construtor do grafo por matriz de adjacência.

        Recebe:
            num_vertices (int): quantidade de vértices do grafo.

        Cria:
            - matriz booleana de adjacência;
            - matriz de pesos das arestas.

        Observação:
            Os atributos comuns, como quantidade de vértices, quantidade
            de arestas, pesos dos vértices e rótulos, são inicializados
            pela classe mãe AbstractGraph.
        """

        super().__init__(num_vertices)

        # Matriz que indica existência de arestas.
        # adjacency_matrix[u][v] == True significa que existe aresta u -> v.
        self.adjacency_matrix = [
            [False for _ in range(num_vertices)]
            for _ in range(num_vertices)
        ]

        # Matriz que guarda os pesos das arestas.
        # O peso só deve ser considerado válido quando a aresta existe.
        self.edge_weights = [
            [0.0 for _ in range(num_vertices)]
            for _ in range(num_vertices)
        ]

    def hasEdge(self, u: int, v: int) -> bool:
        """
        Verifica se existe uma aresta direcionada u -> v.

        Recebe:
            u (int): vértice de origem.
            v (int): vértice de destino.

        Retorna:
            bool: True se existe aresta u -> v, False caso contrário.

        Lança:
            ValueError: se algum índice de vértice for inválido.
        """

        self._validate_vertices(u, v)
        return self.adjacency_matrix[u][v]

    def addEdge(self, u: int, v: int):
        """
        Adiciona uma aresta direcionada u -> v.

        Recebe:
            u (int): vértice de origem.
            v (int): vértice de destino.

        Regras:
            - Não permite índices inválidos.
            - Não permite self-loop.
            - Não duplica aresta já existente.
            - Só aumenta edge_count quando a aresta é nova.

        Observação:
            Como addEdge não recebe peso no enunciado, a aresta criada
            recebe peso padrão 1.0. O peso pode ser alterado depois com
            setEdgeWeight(u, v, w).
        """

        self._validate_vertices(u, v)
        self._validate_no_self_loop(u, v)

        # addEdge deve ser idempotente:
        # se a aresta já existe, não faz nada.
        if self.adjacency_matrix[u][v]:
            return

        self.adjacency_matrix[u][v] = True
        self.edge_weights[u][v] = 1.0
        self.edge_count += 1

    def removeEdge(self, u: int, v: int):
        """
        Remove a aresta direcionada u -> v, caso ela exista.

        Recebe:
            u (int): vértice de origem.
            v (int): vértice de destino.

        Regras:
            - Valida os índices.
            - Se a aresta existir, remove e diminui edge_count.
            - Se a aresta não existir, não lança erro e não faz nada.
        """

        self._validate_vertices(u, v)

        if not self.adjacency_matrix[u][v]:
            return

        self.adjacency_matrix[u][v] = False
        self.edge_weights[u][v] = 0.0
        self.edge_count -= 1

    def setEdgeWeight(self, u: int, v: int, w: float):
        """
        Define o peso de uma aresta existente.

        Recebe:
            u (int): vértice de origem.
            v (int): vértice de destino.
            w (float): peso que será atribuído à aresta.

        Lança:
            ValueError: se os índices forem inválidos ou se a aresta não existir.
        """

        self._validate_vertices(u, v)

        if not self.adjacency_matrix[u][v]:
            raise ValueError(f"Aresta inexistente: {u} -> {v}")

        self.edge_weights[u][v] = w

    def getEdgeWeight(self, u: int, v: int) -> float:
        """
        Retorna o peso de uma aresta existente.

        Recebe:
            u (int): vértice de origem.
            v (int): vértice de destino.

        Retorna:
            float: peso da aresta u -> v.

        Lança:
            ValueError: se os índices forem inválidos ou se a aresta não existir.
        """

        self._validate_vertices(u, v)

        if not self.adjacency_matrix[u][v]:
            raise ValueError(f"Aresta inexistente: {u} -> {v}")

        return self.edge_weights[u][v]

    def getVertexInDegree(self, u: int) -> int:
        """
        Calcula o grau de entrada do vértice u.

        O grau de entrada representa quantas arestas chegam em u.

        Recebe:
            u (int): vértice analisado.

        Retorna:
            int: quantidade de arestas que chegam no vértice u.

        Exemplo:
            Se existem as arestas 1 -> 0 e 2 -> 0,
            então getVertexInDegree(0) retorna 2.
        """

        self._validate_vertex(u)

        in_degree = 0

        # Para grau de entrada, percorremos a coluna u da matriz.
        for origin in range(self.num_vertices):
            if self.adjacency_matrix[origin][u]:
                in_degree += 1

        return in_degree

    def getVertexOutDegree(self, u: int) -> int:
        """
        Calcula o grau de saída do vértice u.

        O grau de saída representa quantas arestas saem de u.

        Recebe:
            u (int): vértice analisado.

        Retorna:
            int: quantidade de arestas que saem do vértice u.

        Exemplo:
            Se existem as arestas 0 -> 1 e 0 -> 2,
            então getVertexOutDegree(0) retorna 2.
        """

        self._validate_vertex(u)

        out_degree = 0

        # Para grau de saída, percorremos a linha u da matriz.
        for destination in range(self.num_vertices):
            if self.adjacency_matrix[u][destination]:
                out_degree += 1

        return out_degree