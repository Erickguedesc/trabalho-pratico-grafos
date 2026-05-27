from abc import ABC, abstractmethod
from collections import deque
from html import escape
from pathlib import Path


class AbstractGraph(ABC):
    """
    Classe abstrata (classe mãe) que define a API comum para os grafos do projeto.

    Esta classe funciona como a classe mãe das duas implementações concretas:
    - AdjacencyMatrixGraph: implementação usando matriz de adjacência;
    - AdjacencyListGraph: implementação usando lista de adjacência.

    Responsabilidades desta classe:
    - Guardar atributos comuns a qualquer grafo;
    - Definir os métodos obrigatórios da API;
    - Implementar métodos que são iguais para matriz e lista;
    - Declarar como abstratos os métodos que dependem da estrutura interna.
    """

    def __init__(self, num_vertices: int):
        """
        Construtor da classe abstrata.

        Recebe:
            num_vertices (int): quantidade de vértices do grafo.

        Cria:
            - num_vertices: total de vértices;
            - edge_count: contador de arestas;
            - vertex_weights: lista de pesos dos vértices;
            - vertex_labels: lista de rótulos dos vértices.

        Observação:
            Os vértices são representados por índices inteiros:
            0 até num_vertices - 1.
        """

        if num_vertices <= 0:
            raise ValueError("O número de vértices deve ser positivo.")

        self.num_vertices = num_vertices
        self.edge_count = 0

        # Peso de cada vértice. Por padrão, todos começam com peso 0.0.
        self.vertex_weights = [0.0] * num_vertices

        # Rótulo de cada vértice. Por padrão, usa o próprio índice como texto.
        # Depois, o GraphBuilder poderá trocar isso pelo login do GitHub.
        self.vertex_labels = [str(i) for i in range(num_vertices)]

    def _validate_vertex(self, v: int):
        """
        Valida se um índice de vértice existe no grafo.

        Recebe:
            v (int): índice do vértice.

        Lança:
            ValueError: se o índice for negativo ou maior/igual ao número de vértices.
        """

        if v < 0 or v >= self.num_vertices:
            raise ValueError(f"Índice de vértice inválido: {v}")

    def _validate_vertices(self, u: int, v: int):
        """
        Valida dois vértices ao mesmo tempo.

        Recebe:
            u (int): vértice de origem.
            v (int): vértice de destino.

        Uso:
            Deve ser chamado antes de operações com arestas, como addEdge,
            removeEdge, hasEdge, setEdgeWeight e getEdgeWeight.
        """

        self._validate_vertex(u)
        self._validate_vertex(v)

    def _validate_no_self_loop(self, u: int, v: int):
        """
        Verifica se a aresta não é um self-loop.

        Recebe:
            u (int): vértice de origem.
            v (int): vértice de destino.

        Lança:
            ValueError: se u e v forem iguais.

        Regra do trabalho:
            O grafo deve ser simples, portanto não pode existir aresta do tipo u -> u.
        """

        if u == v:
            raise ValueError("Self-loop não é permitido em grafo simples.")

    def getVertexCount(self) -> int:
        """
        Retorna a quantidade de vértices do grafo.

        Retorna:
            int: número total de vértices.
        """

        return self.num_vertices

    def getEdgeCount(self) -> int:
        """
        Retorna a quantidade de arestas do grafo.

        Retorna:
            int: número total de arestas existentes.
        """

        return self.edge_count

    def setVertexWeight(self, v: int, w: float):
        """
        Define o peso de um vértice.

        Recebe:
            v (int): índice do vértice.
            w (float): peso que será atribuído ao vértice.

        Uso:
            Pode ser usado futuramente para representar alguma importância,
            métrica ou valor associado ao usuário/vértice.
        """

        self._validate_vertex(v)
        self.vertex_weights[v] = w

    def getVertexWeight(self, v: int) -> float:
        """
        Retorna o peso de um vértice.

        Recebe:
            v (int): índice do vértice.

        Retorna:
            float: peso armazenado para o vértice.
        """

        self._validate_vertex(v)
        return self.vertex_weights[v]

    def setVertexLabel(self, v: int, label: str):
        """
        Define o rótulo de um vértice.

        Recebe:
            v (int): índice do vértice.
            label (str): texto associado ao vértice.

        Uso:
            No projeto, o rótulo normalmente será o login do usuário no GitHub.
            Exemplo: vértice 0 -> "alice".
        """

        self._validate_vertex(v)
        self.vertex_labels[v] = label

    def getVertexLabel(self, v: int) -> str:
        """
        Retorna o rótulo de um vértice.

        Recebe:
            v (int): índice do vértice.

        Retorna:
            str: rótulo associado ao vértice.
        """

        self._validate_vertex(v)
        return self.vertex_labels[v]

    def isEmptyGraph(self) -> bool:
        """
        Verifica se o grafo está vazio em relação às arestas.

        Retorna:
            bool: True se o grafo não possui nenhuma aresta.
        """

        return self.edge_count == 0

    def isCompleteGraph(self) -> bool:
        """
        Verifica se o grafo é completo.

        Como o grafo é direcionado e simples, o número máximo de arestas é:
            n * (n - 1)

        Isso porque:
            - não são permitidos self-loops;
            - para cada par de vértices diferentes, pode existir uma aresta em cada direção.

        Retorna:
            bool: True se o grafo possui todas as arestas possíveis.
        """

        max_edges = self.num_vertices * (self.num_vertices - 1)
        return self.edge_count == max_edges

    def isSucessor(self, u: int, v: int) -> bool:
        """
        Verifica se v é sucessor de u.

        Recebe:
            u (int): vértice de origem.
            v (int): vértice de destino.

        Retorna:
            bool: True se existe aresta u -> v.

        Observação:
            O nome foi mantido como está no enunciado do trabalho.
        """

        self._validate_vertices(u, v)
        return self.hasEdge(u, v)

    def isPredessor(self, u: int, v: int) -> bool:
        """
        Verifica se v é predecessor de u.

        Recebe:
            u (int): vértice analisado.
            v (int): possível predecessor.

        Retorna:
            bool: True se existe aresta v -> u.

        Observação:
            O nome foi mantido como está no enunciado do trabalho.
        """

        self._validate_vertices(u, v)
        return self.hasEdge(v, u)

    def isDivergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        """
        Verifica se duas arestas são divergentes.

        Duas arestas são divergentes quando:
            - as duas existem;
            - possuem o mesmo vértice de origem.

        Recebe:
            u1, v1: primeira aresta u1 -> v1.
            u2, v2: segunda aresta u2 -> v2.

        Retorna:
            bool: True se as duas arestas existem e partem do mesmo vértice.

        Exemplo:
            0 -> 1
            0 -> 2
            São divergentes, pois ambas saem do vértice 0.
        """

        self._validate_vertices(u1, v1)
        self._validate_vertices(u2, v2)

        return u1 == u2 and self.hasEdge(u1, v1) and self.hasEdge(u2, v2)

    def isConvergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        """
        Verifica se duas arestas são convergentes.

        Duas arestas são convergentes quando:
            - as duas existem;
            - possuem o mesmo vértice de destino.

        Recebe:
            u1, v1: primeira aresta u1 -> v1.
            u2, v2: segunda aresta u2 -> v2.

        Retorna:
            bool: True se as duas arestas existem e chegam ao mesmo vértice.

        Exemplo:
            1 -> 0
            2 -> 0
            São convergentes, pois ambas chegam ao vértice 0.
        """

        self._validate_vertices(u1, v1)
        self._validate_vertices(u2, v2)

        return v1 == v2 and self.hasEdge(u1, v1) and self.hasEdge(u2, v2)

    def isIncident(self, u: int, v: int, x: int) -> bool:
        """
        Verifica se um vértice é incidente a uma aresta.

        Recebe:
            u (int): origem da aresta.
            v (int): destino da aresta.
            x (int): vértice que será verificado.

        Retorna:
            bool: True se a aresta u -> v existe e x participa dela.

        Um vértice é incidente a uma aresta se ele é origem ou destino dela.
        """

        self._validate_vertices(u, v)
        self._validate_vertex(x)

        return self.hasEdge(u, v) and (x == u or x == v)

    def isConnected(self) -> bool:
        """
        Verifica se o grafo é conexo usando conectividade fraca.

        Como o grafo do trabalho é direcionado, a conectividade será avaliada
        ignorando temporariamente a direção das arestas.

        Isso significa que, durante a busca, uma ligação u -> v também permite
        considerar v conectado a u apenas para efeito de conectividade.

        Retorna:
            bool: True se todos os vértices pertencem ao mesmo componente conectado.

        Estratégia:
            - Usa BFS a partir do vértice 0;
            - Considera conexão entre dois vértices se existir u -> v ou v -> u;
            - Ao final, verifica se todos os vértices foram visitados.
        """

        visited = set()
        queue = deque([0])
        visited.add(0)

        while queue:
            current = queue.popleft()

            for neighbor in range(self.num_vertices):
                if neighbor == current:
                    continue

                # Conectividade fraca:
                # considera que existe ligação se houver aresta em qualquer direção.
                has_connection = (
                    self.hasEdge(current, neighbor)
                    or self.hasEdge(neighbor, current)
                )

                if has_connection and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == self.num_vertices

    def exportToGEPHI(self, path: str):
        """
        Exporta o grafo para um arquivo GEXF, formato aceito pelo Gephi.

        Recebe:
            path (str): caminho onde o arquivo será salvo.

        O arquivo exportado contém:
            - nós;
            - rótulos dos nós;
            - pesos dos vértices;
            - arestas direcionadas;
            - pesos das arestas.

        Observação:
            Este método é genérico porque usa os métodos da própria API:
            - getVertexLabel;
            - getVertexWeight;
            - hasEdge;
            - getEdgeWeight.

            Assim, funciona tanto para matriz quanto para lista.
        """

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">',
            '  <graph mode="static" defaultedgetype="directed">',
            '    <nodes>'
        ]

        # Criação dos nós do grafo.
        for v in range(self.num_vertices):
            label = escape(str(self.getVertexLabel(v)))
            weight = self.getVertexWeight(v)

            lines.append(f'      <node id="{v}" label="{label}">')
            lines.append('        <attvalues>')
            lines.append(f'          <attvalue for="vertex_weight" value="{weight}" />')
            lines.append('        </attvalues>')
            lines.append('      </node>')

        lines.append('    </nodes>')
        lines.append('    <edges>')

        # Criação das arestas direcionadas.
        edge_id = 0

        for u in range(self.num_vertices):
            for v in range(self.num_vertices):
                if u != v and self.hasEdge(u, v):
                    weight = self.getEdgeWeight(u, v)

                    lines.append(
                        f'      <edge id="{edge_id}" '
                        f'source="{u}" target="{v}" weight="{weight}" />'
                    )

                    edge_id += 1

        lines.append('    </edges>')
        lines.append('  </graph>')
        lines.append('</gexf>')

        output_path.write_text("\n".join(lines), encoding="utf-8")

    @abstractmethod
    def hasEdge(self, u: int, v: int) -> bool:
        """
        Verifica se existe uma aresta direcionada u -> v.

        Deve ser implementado nas subclasses:
            - Na matriz: verifica adjacency_matrix[u][v];
            - Na lista: verifica se v está em adjacency_list[u].
        """
        pass

    @abstractmethod
    def addEdge(self, u: int, v: int):
        """
        Adiciona uma aresta direcionada u -> v.

        Deve:
            - validar os índices;
            - impedir self-loop;
            - não duplicar aresta;
            - atualizar edge_count apenas se a aresta for nova.
        """
        pass

    @abstractmethod
    def removeEdge(self, u: int, v: int):
        """
        Remove a aresta direcionada u -> v, se ela existir.

        Deve:
            - validar os índices;
            - diminuir edge_count apenas se a aresta existia;
            - não lançar erro se a aresta não existir.
        """
        pass

    @abstractmethod
    def setEdgeWeight(self, u: int, v: int, w: float):
        """
        Define o peso de uma aresta existente.

        Recebe:
            u (int): origem da aresta.
            v (int): destino da aresta.
            w (float): peso da aresta.

        Deve lançar ValueError se a aresta não existir.
        """
        pass

    @abstractmethod
    def getEdgeWeight(self, u: int, v: int) -> float:
        """
        Retorna o peso de uma aresta existente.

        Recebe:
            u (int): origem da aresta.
            v (int): destino da aresta.

        Retorna:
            float: peso da aresta.

        Deve lançar ValueError se a aresta não existir.
        """
        pass

    @abstractmethod
    def getVertexInDegree(self, u: int) -> int:
        """
        Retorna o grau de entrada do vértice u.

        O grau de entrada representa quantas arestas chegam em u.

        Deve ser implementado em cada subclasse para aproveitar melhor
        a estrutura interna usada: matriz ou lista.
        """
        pass

    @abstractmethod
    def getVertexOutDegree(self, u: int) -> int:
        """
        Retorna o grau de saída do vértice u.

        O grau de saída representa quantas arestas saem de u.

        Deve ser implementado em cada subclasse para aproveitar melhor
        a estrutura interna usada: matriz ou lista.
        """
        pass