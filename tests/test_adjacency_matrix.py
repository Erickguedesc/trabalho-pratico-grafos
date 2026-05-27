import pytest

from codigo.biblioteca.graph.adjacency_matrix import AdjacencyMatrixGraph


def test_estado_inicial_do_grafo():
    """
    Testa se o grafo por matriz inicia corretamente.

    Verifica:
    - quantidade de vértices;
    - quantidade inicial de arestas;
    - se o grafo começa vazio.
    """

    graph = AdjacencyMatrixGraph(4)

    assert graph.getVertexCount() == 4
    assert graph.getEdgeCount() == 0
    assert graph.isEmptyGraph() is True


def test_rotulos_e_pesos_dos_vertices():
    """
    Testa métodos herdados da AbstractGraph para rótulos e pesos dos vértices.

    Esses dados ficam na classe mãe porque são comuns para matriz e lista.
    """

    graph = AdjacencyMatrixGraph(3)

    graph.setVertexLabel(0, "alice")
    graph.setVertexLabel(1, "bob")

    assert graph.getVertexLabel(0) == "alice"
    assert graph.getVertexLabel(1) == "bob"

    graph.setVertexWeight(0, 10.5)

    assert graph.getVertexWeight(0) == 10.5


def test_add_edge_remove_edge_e_has_edge():
    """
    Testa as operações principais da matriz:
    - addEdge;
    - hasEdge;
    - removeEdge;
    - getEdgeCount.
    """

    graph = AdjacencyMatrixGraph(4)

    graph.addEdge(0, 1)
    graph.addEdge(0, 2)

    assert graph.hasEdge(0, 1) is True
    assert graph.hasEdge(0, 2) is True
    assert graph.hasEdge(1, 0) is False
    assert graph.getEdgeCount() == 2

    graph.removeEdge(0, 1)

    assert graph.hasEdge(0, 1) is False
    assert graph.getEdgeCount() == 1


def test_add_edge_idempotente_nao_duplica_aresta():
    """
    Testa a regra obrigatória do trabalho:
    addEdge deve ser idempotente.

    Ou seja:
    chamar addEdge(0, 1) duas vezes não pode criar duas arestas.
    """

    graph = AdjacencyMatrixGraph(3)

    graph.addEdge(0, 1)
    graph.addEdge(0, 1)

    assert graph.hasEdge(0, 1) is True
    assert graph.getEdgeCount() == 1


def test_remove_edge_inexistente_nao_lanca_erro():
    """
    Testa a regra combinada pela dupla:
    remover uma aresta inexistente não lança erro.

    A operação apenas não faz nada.
    """

    graph = AdjacencyMatrixGraph(3)

    graph.removeEdge(0, 1)

    assert graph.getEdgeCount() == 0


def test_pesos_das_arestas():
    """
    Testa definição e consulta de pesos das arestas na matriz.

    O peso da aresta fica na estrutura concreta:
    edge_weights[u][v]
    """

    graph = AdjacencyMatrixGraph(3)

    graph.addEdge(0, 1)
    graph.setEdgeWeight(0, 1, 2.5)

    assert graph.getEdgeWeight(0, 1) == 2.5


def test_get_edge_weight_em_aresta_inexistente_lanca_erro():
    """
    Testa se getEdgeWeight lança ValueError ao consultar uma aresta inexistente.
    """

    graph = AdjacencyMatrixGraph(3)

    with pytest.raises(ValueError):
        graph.getEdgeWeight(0, 1)


def test_set_edge_weight_em_aresta_inexistente_lanca_erro():
    """
    Testa se setEdgeWeight lança ValueError ao tentar alterar peso
    de uma aresta que não existe.
    """

    graph = AdjacencyMatrixGraph(3)

    with pytest.raises(ValueError):
        graph.setEdgeWeight(0, 1, 4.0)


def test_graus_de_entrada_e_saida():
    """
    Testa os graus de entrada e saída na matriz.

    Grafo usado:
    0 -> 1
    0 -> 2
    2 -> 1

    Saídas:
    - grau de saída de 0 = 2
    - grau de entrada de 1 = 2
    """

    graph = AdjacencyMatrixGraph(3)

    graph.addEdge(0, 1)
    graph.addEdge(0, 2)
    graph.addEdge(2, 1)

    assert graph.getVertexOutDegree(0) == 2
    assert graph.getVertexInDegree(1) == 2
    assert graph.getVertexOutDegree(1) == 0


def test_metodos_sucessor_predessor_incidente_divergente_convergente():
    """
    Testa métodos comuns herdados da AbstractGraph.

    Esses métodos usam hasEdge, que é implementado na matriz.
    """

    graph = AdjacencyMatrixGraph(4)

    graph.addEdge(0, 1)
    graph.addEdge(0, 2)
    graph.addEdge(3, 2)

    assert graph.isSucessor(0, 1) is True
    assert graph.isPredessor(1, 0) is True

    assert graph.isDivergent(0, 1, 0, 2) is True
    assert graph.isConvergent(0, 2, 3, 2) is True

    assert graph.isIncident(0, 1, 0) is True
    assert graph.isIncident(0, 1, 1) is True
    assert graph.isIncident(0, 1, 2) is False


def test_is_connected_com_conectividade_fraca():
    """
    Testa o método isConnected usando conectividade fraca.

    Mesmo o grafo sendo direcionado, a verificação de conectividade
    ignora temporariamente a direção das arestas.

    Grafo:
    0 -> 1
    0 -> 2
    2 -> 3

    Ignorando a direção, todos os vértices pertencem ao mesmo componente.
    """

    graph = AdjacencyMatrixGraph(4)

    graph.addEdge(0, 1)
    graph.addEdge(0, 2)
    graph.addEdge(2, 3)

    assert graph.isConnected() is True


def test_is_complete_graph():
    """
    Testa se o grafo completo é identificado corretamente.

    Em grafo direcionado simples com 3 vértices,
    o número máximo de arestas é:

    n * (n - 1) = 3 * 2 = 6
    """

    graph = AdjacencyMatrixGraph(3)

    graph.addEdge(0, 1)
    graph.addEdge(0, 2)
    graph.addEdge(1, 0)
    graph.addEdge(1, 2)
    graph.addEdge(2, 0)
    graph.addEdge(2, 1)

    assert graph.isCompleteGraph() is True
    assert graph.getEdgeCount() == 6


def test_self_loop_lanca_value_error():
    """
    Testa a regra de grafo simples:
    não pode existir aresta do tipo u -> u.
    """

    graph = AdjacencyMatrixGraph(3)

    with pytest.raises(ValueError):
        graph.addEdge(1, 1)


def test_indice_invalido_lanca_value_error():
    """
    Testa se índices inválidos lançam ValueError.
    """

    graph = AdjacencyMatrixGraph(3)

    with pytest.raises(ValueError):
        graph.addEdge(-1, 2)

    with pytest.raises(ValueError):
        graph.addEdge(0, 99)


def test_export_to_gephi_gera_arquivo(tmp_path):
    """
    Testa se exportToGEPHI gera um arquivo GEXF.

    O tmp_path é uma pasta temporária criada pelo pytest.
    Assim, o teste não suja o projeto com arquivos de teste.
    """

    graph = AdjacencyMatrixGraph(3)

    graph.setVertexLabel(0, "alice")
    graph.setVertexLabel(1, "bob")
    graph.setVertexLabel(2, "carol")

    graph.addEdge(0, 1)
    graph.setEdgeWeight(0, 1, 2.0)

    output_file = tmp_path / "grafo_teste.gexf"

    graph.exportToGEPHI(str(output_file))

    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")

    assert "<gexf" in content
    assert 'label="alice"' in content
    assert 'label="bob"' in content
    assert 'source="0"' in content
    assert 'target="1"' in content
    assert 'weight="2.0"' in content

def test_is_not_connected():
    """
    Testa se isConnected retorna False quando o grafo não é conexo.

    Grafo:
    0 -> 1
    Vértices 2 e 3 estão isolados.
    """

    graph = AdjacencyMatrixGraph(4)
    graph.addEdge(0, 1)

    assert graph.isConnected() is False