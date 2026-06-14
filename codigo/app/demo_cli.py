# =============================================================================
# demo_cli.py
# -----------------------------------------------------------------------------
# Responsabilidade:
#   Aplicação separada que importa e demonstra TODAS as operações da API de
#   grafos implementada na biblioteca. Obrigatório pelo enunciado do trabalho.
#
# Como rodar:
#   python demo_cli.py build          -> constrói os grafos a partir do JSON
#   python demo_cli.py metrics        -> exibe todas as métricas de análise
#   python demo_cli.py graph-smoke    -> testa todas as operações CRUD do grafo
#   python demo_cli.py export         -> exporta os grafos para Gephi (.gexf)
#   python demo_cli.py all            -> roda tudo acima em sequência
#
# Estrutura:
#   - Cada comando é uma função separada neste arquivo.
#   - A função main() decide qual comando executar com base no argumento de linha.
#   - Todos os resultados são impressos no terminal.
# =============================================================================

import sys
import os
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path para que os imports funcionem
# independente do diretório de onde o script é chamado.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Importa as implementações concretas de grafo.
from codigo.biblioteca.graph.adjacency_list import AdjacencyListGraph
from codigo.biblioteca.graph.adjacency_matrix import AdjacencyMatrixGraph

# Importa as peças do builder (mapeamento + construção + bundle).
from codigo.biblioteca.builder.user_mapper import UserMapper
from codigo.biblioteca.builder.graph_builder import GraphBuilder

# Importa o analisador de métricas.
from codigo.biblioteca.analysis.graph_analyzer import GraphAnalyzer


# Caminho padrão para o arquivo de interações gerado pelo minerador.
# Pode ser sobrescrito pela variável de ambiente INPUT_DIR.
DEFAULT_INPUT_DIR = PROJECT_ROOT / "dados"
INPUT_DIR = Path(os.getenv("INPUT_DIR", str(DEFAULT_INPUT_DIR)))
INTERACOES_FILE = INPUT_DIR / "interacoes.json"

# Pasta de saída dos arquivos exportados para o Gephi.
OUTPUT_GEPHI_DIR = PROJECT_ROOT / "dados" / "gephi"


# =============================================================================
# COMANDO 1: graph-smoke
# Demonstra todas as operações CRUD da API de grafos com dados sintéticos.
# =============================================================================

def cmd_graph_smoke():
    """
    Demonstra todas as operações obrigatórias da API do grafo.

    Usa um grafo pequeno e sintético (4 vértices, dados fictícios) para que
    cada operação fique visível e verificável de forma direta.

    Operações demonstradas:
        addEdge, removeEdge, hasEdge,
        getVertexInDegree, getVertexOutDegree,
        isSucessor, isPredessor,
        isDivergent, isConvergent,
        isIncident, isConnected,
        isEmptyGraph, isCompleteGraph,
        setEdgeWeight, getEdgeWeight,
        setVertexWeight, getVertexWeight,
        setVertexLabel, getVertexLabel,
        exportToGEPHI
    """

    print("\n" + "=" * 60)
    print("DEMO: Operações da API do Grafo (dados sintéticos)")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # Cria dois grafos do mesmo tamanho — um de cada implementação.
    # Permite comparar os resultados e mostrar que ambos funcionam igual.
    # -------------------------------------------------------------------------
    print("\n[1] Criando grafos com 4 vértices...")
    g_matrix = AdjacencyMatrixGraph(4)  # implementação por matriz de adjacência
    g_list   = AdjacencyListGraph(4)    # implementação por lista de adjacência

    # -------------------------------------------------------------------------
    # Rótulos dos vértices — simula logins do GitHub.
    # -------------------------------------------------------------------------
    print("[2] Definindo rótulos dos vértices (logins simulados)...")
    for g in [g_matrix, g_list]:
        g.setVertexLabel(0, "alice")
        g.setVertexLabel(1, "bob")
        g.setVertexLabel(2, "carol")
        g.setVertexLabel(3, "dan")

    print(f"    Vértice 0 = '{g_list.getVertexLabel(0)}'")
    print(f"    Vértice 1 = '{g_list.getVertexLabel(1)}'")

    # -------------------------------------------------------------------------
    # Pesos dos vértices.
    # -------------------------------------------------------------------------
    print("[3] Definindo pesos dos vértices...")
    g_list.setVertexWeight(0, 10.5)
    print(f"    Peso do vértice 0: {g_list.getVertexWeight(0)}")

    # -------------------------------------------------------------------------
    # isEmptyGraph — deve ser True antes de adicionar arestas.
    # -------------------------------------------------------------------------
    print(f"\n[4] isEmptyGraph (antes de addEdge): {g_list.isEmptyGraph()}")

    # -------------------------------------------------------------------------
    # addEdge — adiciona arestas direcionadas.
    # -------------------------------------------------------------------------
    print("\n[5] Adicionando arestas...")
    for g in [g_matrix, g_list]:
        g.addEdge(0, 1)  # alice -> bob
        g.addEdge(0, 2)  # alice -> carol
        g.addEdge(2, 3)  # carol -> dan
        g.addEdge(3, 1)  # dan   -> bob

    print(f"    Arestas adicionadas: {g_list.getEdgeCount()}")

    # -------------------------------------------------------------------------
    # addEdge idempotente — chamar de novo não duplica.
    # -------------------------------------------------------------------------
    print("[6] addEdge idempotente (adicionando 0->1 de novo)...")
    g_list.addEdge(0, 1)
    print(f"    Contagem de arestas após re-adição: {g_list.getEdgeCount()} (deve ser 4)")

    # -------------------------------------------------------------------------
    # hasEdge — verifica existência de arestas.
    # -------------------------------------------------------------------------
    print("\n[7] hasEdge:")
    print(f"    0->1 (alice->bob):   {g_list.hasEdge(0, 1)}  (esperado: True)")
    print(f"    1->0 (bob->alice):   {g_list.hasEdge(1, 0)}  (esperado: False)")
    print(f"    2->3 (carol->dan):   {g_list.hasEdge(2, 3)}  (esperado: True)")

    # -------------------------------------------------------------------------
    # Pesos das arestas.
    # -------------------------------------------------------------------------
    print("\n[8] Pesos das arestas (setEdgeWeight / getEdgeWeight):")
    g_list.setEdgeWeight(0, 1, 4.0)  # alice->bob: revisão de PR (peso 4)
    g_list.setEdgeWeight(0, 2, 2.0)  # alice->carol: comentário (peso 2)
    print(f"    Peso aresta 0->1: {g_list.getEdgeWeight(0, 1)}")
    print(f"    Peso aresta 0->2: {g_list.getEdgeWeight(0, 2)}")

    # -------------------------------------------------------------------------
    # isSucessor / isPredessor.
    # -------------------------------------------------------------------------
    print("\n[9] isSucessor / isPredessor:")
    print(f"    bob é sucessor de alice (0->1)?    {g_list.isSucessor(0, 1)}")
    print(f"    alice é predecessor de bob (0->1)? {g_list.isPredessor(1, 0)}")

    # -------------------------------------------------------------------------
    # isDivergent / isConvergent.
    # -------------------------------------------------------------------------
    print("\n[10] isDivergent (mesma origem) / isConvergent (mesmo destino):")
    # 0->1 e 0->2 divergem do vértice 0.
    print(f"    0->1 e 0->2 são divergentes? {g_list.isDivergent(0, 1, 0, 2)}")
    # 0->1 e 3->1 convergem para o vértice 1.
    print(f"    0->1 e 3->1 são convergentes? {g_list.isConvergent(0, 1, 3, 1)}")

    # -------------------------------------------------------------------------
    # isIncident — verifica se vértice participa de uma aresta.
    # -------------------------------------------------------------------------
    print("\n[11] isIncident (vértice pertence a uma aresta?):")
    print(f"    0 é incidente em 0->1? {g_list.isIncident(0, 1, 0)}")  # é a origem
    print(f"    1 é incidente em 0->1? {g_list.isIncident(0, 1, 1)}")  # é o destino
    print(f"    2 é incidente em 0->1? {g_list.isIncident(0, 1, 2)}")  # não participa

    # -------------------------------------------------------------------------
    # Graus de entrada e saída.
    # -------------------------------------------------------------------------
    print("\n[12] Graus de entrada (in) e saída (out):")
    for v in range(4):
        label = g_list.getVertexLabel(v)
        in_d  = g_list.getVertexInDegree(v)
        out_d = g_list.getVertexOutDegree(v)
        print(f"    {label:<8}: in={in_d}, out={out_d}")

    # -------------------------------------------------------------------------
    # isConnected — BFS com conectividade fraca.
    # -------------------------------------------------------------------------
    print(f"\n[13] isConnected: {g_list.isConnected()}  (esperado: True)")

    # -------------------------------------------------------------------------
    # isCompleteGraph — todos conectados com todos?
    # -------------------------------------------------------------------------
    print(f"[14] isCompleteGraph: {g_list.isCompleteGraph()}  (esperado: False)")

    # -------------------------------------------------------------------------
    # removeEdge — remove uma aresta.
    # -------------------------------------------------------------------------
    print("\n[15] removeEdge(0, 2)...")
    g_list.removeEdge(0, 2)
    print(f"    hasEdge(0, 2) após remoção: {g_list.hasEdge(0, 2)}  (esperado: False)")
    print(f"    Total de arestas: {g_list.getEdgeCount()}  (esperado: 3)")

    # -------------------------------------------------------------------------
    # Self-loop — deve lançar ValueError.
    # -------------------------------------------------------------------------
    print("\n[16] Self-loop (deve lançar ValueError):")
    try:
        g_list.addEdge(1, 1)
        print("    ERRO: deveria ter lançado ValueError!")
    except ValueError as e:
        print(f"    ValueError capturado corretamente: {e}")

    # -------------------------------------------------------------------------
    # Índice inválido — deve lançar ValueError.
    # -------------------------------------------------------------------------
    print("\n[17] Índice inválido (deve lançar ValueError):")
    try:
        g_list.addEdge(0, 99)
        print("    ERRO: deveria ter lançado ValueError!")
    except ValueError as e:
        print(f"    ValueError capturado corretamente: {e}")

    # -------------------------------------------------------------------------
    # exportToGEPHI — gera arquivo .gexf para visualização no Gephi.
    # -------------------------------------------------------------------------
    print("\n[18] exportToGEPHI — gerando arquivo .gexf...")
    gexf_path = str(OUTPUT_GEPHI_DIR / "smoke_test.gexf")
    g_list.exportToGEPHI(gexf_path)
    print(f"    Arquivo gerado em: {gexf_path}")

    # Verifica que o arquivo foi criado e tem conteúdo.
    gexf_file = Path(gexf_path)
    if gexf_file.exists():
        print(f"    Tamanho do arquivo: {gexf_file.stat().st_size} bytes ✓")
    else:
        print("    AVISO: arquivo não foi criado!")

    print("\n✓ Demo graph-smoke concluída com sucesso!")


# =============================================================================
# COMANDO 2: build
# Constrói os 4 grafos reais a partir do arquivo interacoes.json.
# =============================================================================

def cmd_build() -> object:
    """
    Lê o interacoes.json e constrói os 4 grafos do trabalho.

    Retorna:
        GraphBundle: objeto com os 4 grafos e o mapper, ou None se falhar.
    """

    print("\n" + "=" * 60)
    print("DEMO: Construção dos Grafos a partir do JSON")
    print("=" * 60)
    print(f"\nArquivo de entrada: {INTERACOES_FILE}")

    if not INTERACOES_FILE.exists():
        print(f"\n[ERRO] Arquivo não encontrado: {INTERACOES_FILE}")
        print("Execute o minerador primeiro:")
        print("  python -m codigo.mineirador.miner")
        return None

    # Chama o GraphBuilder para ler o JSON e construir os grafos.
    bundle = GraphBuilder.build_from_file(str(INTERACOES_FILE))

    # Exibe o resumo dos grafos construídos.
    print()
    print(bundle.summary())

    # Exibe os 5 usuários com maior grau no grafo integrado.
    print("\nTop 5 usuários por grau de saída no grafo integrado (G4):")
    g4 = bundle.integrated
    degrees = [
        (bundle.mapper.get_login(v), g4.getVertexOutDegree(v))
        for v in range(g4.getVertexCount())
    ]
    degrees.sort(key=lambda x: x[1], reverse=True)
    for login, deg in degrees[:5]:
        print(f"  {login:<30} out-degree={deg}")

    print("\n✓ Grafos construídos com sucesso!")
    return bundle


# =============================================================================
# COMANDO 3: metrics
# Calcula e exibe todas as métricas da Etapa 3 sobre o grafo integrado.
# =============================================================================

def cmd_metrics():
    """
    Constrói os grafos e calcula todas as métricas de análise.

    Usa o grafo integrado (G4) como base para todas as métricas,
    pois ele contém a rede completa de colaboração.
    """

    print("\n" + "=" * 60)
    print("DEMO: Análise de Métricas (Etapa 3)")
    print("=" * 60)

    # Primeiro constrói os grafos.
    bundle = cmd_build()
    if bundle is None:
        return

    # Cria o analisador sobre o grafo integrado.
    print("\nAnalisando grafo integrado (G4)...")
    analyzer = GraphAnalyzer(bundle.integrated, mapper=bundle.mapper)

    # Exibe o relatório completo.
    print(analyzer.full_report())

    print("\n✓ Análise concluída!")


# =============================================================================
# COMANDO 4: export
# Exporta todos os 4 grafos para arquivos .gexf para visualização no Gephi.
# =============================================================================

def cmd_export():
    """
    Constrói os grafos e exporta cada um para um arquivo .gexf.

    Os arquivos são salvos na pasta dados/gephi/ e podem ser abertos
    diretamente no software Gephi para visualização da rede.
    """

    print("\n" + "=" * 60)
    print("DEMO: Exportação para Gephi (.gexf)")
    print("=" * 60)

    # Primeiro constrói os grafos.
    bundle = cmd_build()
    if bundle is None:
        return

    # Cria a pasta de saída se não existir.
    OUTPUT_GEPHI_DIR.mkdir(parents=True, exist_ok=True)

    # Exporta cada grafo para um arquivo separado.
    grafos = [
        (bundle.comments,     "g1_comentarios.gexf"),
        (bundle.issue_closes, "g2_fechamentos.gexf"),
        (bundle.pr_events,    "g3_pull_requests.gexf"),
        (bundle.integrated,   "g4_integrado.gexf"),
    ]

    for grafo, filename in grafos:
        path = str(OUTPUT_GEPHI_DIR / filename)
        grafo.exportToGEPHI(path)
        size = Path(path).stat().st_size
        print(f"  ✓ {filename:<30} ({size:,} bytes)")

    print(f"\nArquivos salvos em: {OUTPUT_GEPHI_DIR}")
    print("\n✓ Exportação concluída!")


# =============================================================================
# PONTO DE ENTRADA PRINCIPAL
# =============================================================================

def main():
    """
    Ponto de entrada do script. Lê o argumento de linha de comando e
    decide qual comando executar.

    Uso:
        python demo_cli.py <comando>

    Comandos:
        graph-smoke  — testa toda a API do grafo com dados sintéticos
        build        — constrói os 4 grafos a partir do JSON real
        metrics      — exibe todas as métricas de análise (Etapa 3)
        export       — exporta os grafos para .gexf (Gephi)
        all          — executa tudo em sequência
    """

    # Obtém o comando do argumento de linha (padrão: "all").
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    # Mapa de comandos disponíveis.
    commands = {
        "graph-smoke": cmd_graph_smoke,
        "build":       cmd_build,
        "metrics":     cmd_metrics,
        "export":      cmd_export,
        "all": lambda: (
            cmd_graph_smoke(),
            cmd_build(),
            cmd_metrics(),
            cmd_export(),
        ),
    }

    if command not in commands:
        print(f"Comando desconhecido: '{command}'")
        print(f"Comandos disponíveis: {', '.join(commands.keys())}")
        sys.exit(1)

    # Executa o comando escolhido.
    commands[command]()


if __name__ == "__main__":
    main()