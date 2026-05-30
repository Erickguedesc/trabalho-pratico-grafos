import pytest

from codigo.biblioteca.graph.adjacency_list import AdjacencyListGraph


def test_estado_inicial_do_grafo():
    graph = AdjacencyListGraph(4)

    assert graph.getVertexCount() == 4
    assert graph.getEdgeCount() == 0
    assert graph.isEmptyGraph() is True


def test_rotulos_e_pesos_dos_vertices():
    graph = AdjacencyListGraph(3)

    graph.setVertexLabel(0, "alice")
    graph.setVertexLabel(1, "bob")

    assert graph.getVertexLabel(0) == "alice"
    assert graph.getVertexLabel(1) == "bob"

    graph.setVertexWeight(0, 10.5)
    assert graph.getVertexWeight(0) == 10.5


def test_add_edge_remove_edge_e_has_edge():
    graph = AdjacencyListGraph(4)

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
    graph = AdjacencyListGraph(3)

    graph.addEdge(0, 1)
    graph.addEdge(0, 1)

    assert graph.hasEdge(0, 1) is True
    assert graph.getEdgeCount() == 1


def test_remove_edge_inexistente_nao_lanca_erro():
    graph = AdjacencyListGraph(3)

    graph.removeEdge(0, 1)

    assert graph.getEdgeCount() == 0


def test_pesos_das_arestas():
    graph = AdjacencyListGraph(3)

    graph.addEdge(0, 1)
    graph.setEdgeWeight(0, 1, 2.5)

    assert graph.getEdgeWeight(0, 1) == 2.5


def test_get_edge_weight_em_aresta_inexistente_lanca_erro():
    graph = AdjacencyListGraph(3)

    with pytest.raises(ValueError):
        graph.getEdgeWeight(0, 1)


def test_set_edge_weight_em_aresta_inexistente_lanca_erro():
    graph = AdjacencyListGraph(3)

    with pytest.raises(ValueError):
        graph.setEdgeWeight(0, 1, 4.0)


def test_graus_de_entrada_e_saida():
    graph = AdjacencyListGraph(3)

    graph.addEdge(0, 1)
    graph.addEdge(0, 2)
    graph.addEdge(2, 1)

    assert graph.getVertexOutDegree(0) == 2
    assert graph.getVertexInDegree(1) == 2
    assert graph.getVertexOutDegree(1) == 0


def test_metodos_sucessor_predessor_incidente_divergente_convergente():
    graph = AdjacencyListGraph(4)

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
    graph = AdjacencyListGraph(4)

    graph.addEdge(0, 1)
    graph.addEdge(0, 2)
    graph.addEdge(2, 3)

    assert graph.isConnected() is True


def test_is_complete_graph():
    graph = AdjacencyListGraph(3)

    graph.addEdge(0, 1)
    graph.addEdge(0, 2)
    graph.addEdge(1, 0)
    graph.addEdge(1, 2)
    graph.addEdge(2, 0)
    graph.addEdge(2, 1)

    assert graph.isCompleteGraph() is True
    assert graph.getEdgeCount() == 6


def test_self_loop_lanca_value_error():
    graph = AdjacencyListGraph(3)

    with pytest.raises(ValueError):
        graph.addEdge(1, 1)


def test_indice_invalido_lanca_value_error():
    graph = AdjacencyListGraph(3)

    with pytest.raises(ValueError):
        graph.addEdge(-1, 2)

    with pytest.raises(ValueError):
        graph.addEdge(0, 99)


def test_export_to_gephi_gera_arquivo(tmp_path):
    graph = AdjacencyListGraph(3)

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


def test_str_mostra_lista_de_adjacencia():
    graph = AdjacencyListGraph(3)
    graph.addEdge(0, 1)
    graph.addEdge(0, 2)
    graph.setEdgeWeight(0, 2, 3.5)

    representation = str(graph)

    assert "0: 1(w=1.0), 2(w=3.5)" in representation
    assert "1: []" in representation
    assert "2: []" in representation


def test_is_not_connected():
    graph = AdjacencyListGraph(4)
    graph.addEdge(0, 1)

    assert graph.isConnected() is False


def test_grafo_grande_imprime_lista_no_terminal():
    total_vertices = 100
    graph = AdjacencyListGraph(total_vertices)

    # Cria um grafo maior com várias conexões direcionadas sem self-loop.
    # Também define pesos variados para exercitar set/get de peso.
    for u in range(total_vertices):
        for step, weight in ((1, 2.0), (3, 4.0), (7, 5.0)):
            v = (u + step) % total_vertices
            graph.addEdge(u, v)
            graph.setEdgeWeight(u, v, weight)

    # Atualiza um peso para validar sobrescrita.
    graph.setEdgeWeight(0, 1, 3.0)

    # Exibe a lista de adjacência no terminal (use pytest -s para visualizar).
    print("\n=== GRAFO GRANDE (LISTA DE ADJACENCIA) ===")
    print(graph)

    assert graph.getVertexCount() == total_vertices
    assert graph.getEdgeCount() == total_vertices * 3
    assert graph.getVertexOutDegree(0) == 3
    assert graph.getVertexInDegree(0) == 3
    assert graph.getEdgeWeight(0, 1) == 3.0
    assert graph.getEdgeWeight(0, 3) == 4.0
    assert graph.getEdgeWeight(0, 7) == 5.0
    assert graph.hasEdge(0, 0) is False
