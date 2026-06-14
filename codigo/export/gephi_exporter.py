from pathlib import Path
from lxml import etree


class GephiExporter:
    """
    Exporta um grafo para formato GEXF.
    Compatível com Gephi.
    """

    @staticmethod
    def export(graph, mapper, output_file: str):

        gexf = etree.Element(
            "gexf",
            version="1.2"
        )

        graph_xml = etree.SubElement(
            gexf,
            "graph",
            defaultedgetype="directed"
        )

        nodes_xml = etree.SubElement(graph_xml, "nodes")
        edges_xml = etree.SubElement(graph_xml, "edges")

        # ----------------------------
        # Nós
        # ----------------------------

        for v in range(graph.getVertexCount()):

            etree.SubElement(
                nodes_xml,
                "node",
                id=str(v),
                label=mapper.get_login(v)
            )

        # ----------------------------
        # Arestas
        # ----------------------------

        edge_id = 0

        for u in range(graph.getVertexCount()):

            for v in graph.getNeighbors(u):

                etree.SubElement(
                    edges_xml,
                    "edge",
                    id=str(edge_id),
                    source=str(u),
                    target=str(v),
                    weight=str(graph.getEdgeWeight(u, v))
                )

                edge_id += 1

        tree = etree.ElementTree(gexf)

        Path(output_file).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        tree.write(
            output_file,
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8"
        )

        return output_file