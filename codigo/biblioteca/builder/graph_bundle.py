# =============================================================================
# graph_bundle.py
# -----------------------------------------------------------------------------
# Responsabilidade:
#   Agrupar os 4 grafos do trabalho em um único objeto para facilitar o uso.
#
# Por que 4 grafos?
#   O enunciado exige que as interações sejam separadas por tipo, e que exista
#   também um grafo integrado que combina tudo com pesos ponderados.
#
#   G1 — Grafo de comentários (issue_comment + pr_comment, peso 2)
#   G2 — Grafo de fechamentos de issue (issue_close, peso 3)
#   G3 — Grafo de eventos de PR (pr_open peso 3, pr_review peso 4, pr_merge peso 5)
#   G4 — Grafo integrado (soma ponderada de todas as interações)
# =============================================================================

from ..graph.abstract_graph import AbstractGraph


class GraphBundle:
    """
    Contêiner que agrupa os 4 grafos construídos pelo GraphBuilder.

    Atributos públicos:
        comments     (AbstractGraph): G1 — comentários em issues e PRs.
        issue_closes (AbstractGraph): G2 — fechamentos de issues.
        pr_events    (AbstractGraph): G3 — eventos de pull requests.
        integrated   (AbstractGraph): G4 — grafo integrado com todos os pesos.
        mapper       (UserMapper):    mapeamento login <-> índice.

    Uso típico:
        bundle = GraphBuilder.build_from_file("dados/interacoes.json")
        g4 = bundle.integrated
        print(g4.getEdgeCount())
    """

    def __init__(self, comments, issue_closes, pr_events, integrated, mapper):
        """
        Cria um GraphBundle com os 4 grafos e o mapper.

        Recebe:
            comments     (AbstractGraph): G1 — comentários.
            issue_closes (AbstractGraph): G2 — fechamentos de issues.
            pr_events    (AbstractGraph): G3 — pull requests.
            integrated   (AbstractGraph): G4 — grafo consolidado com pesos somados.
            mapper       (UserMapper):    tabela de conversão login <-> índice.
        """

        # G1: apenas comentários em issues e PRs (peso 2 cada).
        self.comments: AbstractGraph = comments

        # G2: apenas fechamentos de issues por outro usuário (peso 3 cada).
        self.issue_closes: AbstractGraph = issue_closes

        # G3: apenas eventos de pull request —
        #     abertura (peso 3), revisão/aprovação (peso 4), merge (peso 5).
        self.pr_events: AbstractGraph = pr_events

        # G4: grafo integrado — todos os tipos de interação juntos.
        #     O peso de cada aresta é a soma acumulada de todas as interações
        #     entre os dois usuários, considerando os pesos de cada tipo.
        self.integrated: AbstractGraph = integrated

        # Guarda o mapper para que qualquer código que receba o bundle
        # consiga converter índice -> login para exibir resultados legíveis.
        self.mapper = mapper

    def summary(self) -> str:
        """
        Retorna um resumo textual dos 4 grafos do bundle.

        Útil para verificar rapidamente os dados após a construção,
        ou para exibir na demo CLI da entrevista.

        Retorna:
            str: texto com vértices e arestas de cada grafo.
        """

        n = self.mapper.num_users()

        lines = [
            "=" * 50,
            f"GraphBundle — {n} usuários únicos",
            "=" * 50,
            f"G1 comentários  : {self.comments.getVertexCount()} vértices, "
            f"{self.comments.getEdgeCount()} arestas",

            f"G2 fechamentos  : {self.issue_closes.getVertexCount()} vértices, "
            f"{self.issue_closes.getEdgeCount()} arestas",

            f"G3 pull requests: {self.pr_events.getVertexCount()} vértices, "
            f"{self.pr_events.getEdgeCount()} arestas",

            f"G4 integrado    : {self.integrated.getVertexCount()} vértices, "
            f"{self.integrated.getEdgeCount()} arestas",
            "=" * 50,
        ]

        return "\n".join(lines)

    def __repr__(self) -> str:
        """Representação curta do bundle para debug."""
        return (
            f"GraphBundle("
            f"n={self.mapper.num_users()}, "
            f"G1={self.comments.getEdgeCount()} arestas, "
            f"G2={self.issue_closes.getEdgeCount()} arestas, "
            f"G3={self.pr_events.getEdgeCount()} arestas, "
            f"G4={self.integrated.getEdgeCount()} arestas)"
        )