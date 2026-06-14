# =============================================================================
# graph_builder.py
# -----------------------------------------------------------------------------
# Responsabilidade:
#   Ler o arquivo interacoes.json gerado pelo minerador e construir os 4 grafos
#   do trabalho, usando a API de grafos implementada na biblioteca.
#
# Fluxo interno:
#   1. Lê todas as linhas do interacoes.json (formato JSON Lines).
#   2. Passa 1: coleta todos os logins únicos e constrói o UserMapper.
#   3. Cria os 4 grafos vazios com o tamanho certo (num_users vértices).
#   4. Define os rótulos dos vértices como os logins dos usuários.
#   5. Passa 2: percorre as interações novamente e adiciona as arestas.
#   6. Agrupa tudo num GraphBundle e retorna.
#
# Detalhes dos pesos (conforme o enunciado):
#   issue_comment -> peso 2   (comentário em issue)
#   pr_comment    -> peso 2   (comentário em PR)
#   issue_close   -> peso 3   (fechou issue de outro)
#   pr_open       -> peso 3   (abriu PR)
#   pr_review     -> peso 4   (revisou/aprovou PR)
#   pr_merge      -> peso 5   (fez merge do PR)
# =============================================================================

import json
from pathlib import Path

from ..graph.adjacency_list import AdjacencyListGraph
from .user_mapper import UserMapper
from .graph_bundle import GraphBundle


# Tabela de pesos: tipo de interação -> peso no grafo.
# Qualquer tipo não listado aqui será ignorado silenciosamente.
INTERACTION_WEIGHTS: dict[str, float] = {
    "issue_comment": 2.0,
    "pr_comment":    2.0,
    "issue_close":   3.0,
    "pr_open":       3.0,
    "pr_review":     4.0,
    "pr_merge":      5.0,
}

# Quais tipos de interação pertencem a cada grafo separado.
# G1 = comentários, G2 = fechamentos, G3 = tudo relacionado a PR.
GRAPH_TYPES = {
    "G1_comments":    {"issue_comment", "pr_comment"},
    "G2_issue_close": {"issue_close"},
    "G3_pr_events":   {"pr_open", "pr_review", "pr_merge"},
}


class GraphBuilder:
    """
    Constrói os 4 grafos do trabalho a partir do arquivo interacoes.json.

    O builder usa AdjacencyListGraph para todos os grafos porque os grafos de
    colaboração são tipicamente esparsos — a maioria dos pares de usuários
    não interagiu diretamente — e a lista de adjacência é mais eficiente
    em memória para grafos esparsos.

    Uso:
        bundle = GraphBuilder.build_from_file("dados/interacoes.json")
        print(bundle.summary())
    """

    @staticmethod
    def build_from_file(path: str) -> GraphBundle:
        """
        Ponto de entrada principal: lê o JSON e constrói os 4 grafos.

        Recebe:
            path (str): caminho para o arquivo interacoes.json.

        Retorna:
            GraphBundle: objeto com os 4 grafos prontos e o mapper.

        Lança:
            FileNotFoundError: se o arquivo não existir.
            ValueError: se o arquivo estiver completamente vazio.
        """

        input_path = Path(path)

        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        # Lê todas as linhas do arquivo de uma vez.
        # O formato é JSON Lines: cada linha é um JSON separado.
        raw_lines = input_path.read_text(encoding="utf-8").strip().splitlines()

        if not raw_lines:
            raise ValueError(f"Arquivo está vazio: {path}")

        print(f"[GraphBuilder] Lendo {len(raw_lines)} interações de '{path}'...")

        # Passa 1: coleta todos os logins únicos e monta o UserMapper.
        # Isso é necessário para saber o tamanho dos grafos antes de criá-los.
        mapper, interactions = GraphBuilder._first_pass(raw_lines)

        print(f"[GraphBuilder] {mapper.num_users()} usuários únicos encontrados.")

        # Cria os 4 grafos vazios com o tamanho correto.
        n = mapper.num_users()
        g1 = AdjacencyListGraph(n)  # G1: comentários
        g2 = AdjacencyListGraph(n)  # G2: fechamentos de issues
        g3 = AdjacencyListGraph(n)  # G3: pull requests
        g4 = AdjacencyListGraph(n)  # G4: integrado (todos os tipos juntos)

        # Define os rótulos dos vértices como os logins dos usuários.
        # Assim, ao exportar para Gephi, os nós aparecem com o nome real.
        for idx, login in enumerate(mapper.all_logins()):
            g1.setVertexLabel(idx, login)
            g2.setVertexLabel(idx, login)
            g3.setVertexLabel(idx, login)
            g4.setVertexLabel(idx, login)

        # Passa 2: adiciona as arestas em cada grafo com os pesos corretos.
        GraphBuilder._second_pass(interactions, mapper, g1, g2, g3, g4)

        print(f"[GraphBuilder] Grafos construídos.")

        # Agrupa os 4 grafos num bundle e retorna.
        return GraphBundle(
            comments=g1,
            issue_closes=g2,
            pr_events=g3,
            integrated=g4,
            mapper=mapper,
        )

    @staticmethod
    def _first_pass(raw_lines: list[str]) -> tuple["UserMapper", list[dict]]:
        """
        Primeira passagem sobre as linhas do arquivo.

        Objetivos:
          1. Parsear cada linha de JSON em um dicionário Python.
          2. Registrar todos os logins únicos (source_user e target_user) no mapper.
          3. Filtrar linhas inválidas (JSON quebrado, campos faltando, auto-interação).

        Recebe:
            raw_lines (list[str]): linhas brutas do arquivo JSON Lines.

        Retorna:
            tuple: (UserMapper preenchido, lista de dicts válidos das interações)
        """

        mapper = UserMapper()
        valid_interactions = []

        for i, line in enumerate(raw_lines):
            line = line.strip()

            # Pula linhas vazias.
            if not line:
                continue

            # Tenta parsear a linha como JSON.
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"[GraphBuilder] Aviso: linha {i+1} não é JSON válido, ignorada.")
                continue

            # Extrai os campos obrigatórios.
            source = data.get("source_user", "").strip()
            target = data.get("target_user", "").strip()
            itype  = data.get("type", "").strip()

            # Ignora interações com usuário vazio (conta deletada, bot, etc.).
            if not source or not target:
                continue

            # Ignora auto-interações (mesmo usuário nos dois lados).
            # O enunciado exige grafo simples sem self-loop.
            if source == target:
                continue

            # Ignora tipos de interação desconhecidos (não estão na tabela de pesos).
            if itype not in INTERACTION_WEIGHTS:
                continue

            # Registra os dois usuários no mapper.
            # Se já foram registrados, apenas retorna o índice existente.
            mapper.add_login(source)
            mapper.add_login(target)

            valid_interactions.append(data)

        return mapper, valid_interactions

    @staticmethod
    def _second_pass(
        interactions: list[dict],
        mapper: "UserMapper",
        g1: AdjacencyListGraph,
        g2: AdjacencyListGraph,
        g3: AdjacencyListGraph,
        g4: AdjacencyListGraph,
    ):
        """
        Segunda passagem: adiciona as arestas nos grafos com os pesos corretos.

        Para cada interação válida:
          1. Converte os logins em índices via mapper.
          2. Identifica em qual grafo separado a interação pertence.
          3. Adiciona a aresta no grafo separado e acumula o peso.
          4. Adiciona a aresta no grafo integrado (G4) e acumula o peso lá também.

        Acumulação de peso:
          Se dois usuários já interagiram antes, o peso da aresta é somado.
          Exemplo: alice -> bob com issue_comment (peso 2) + pr_review (peso 4)
          resulta em aresta alice -> bob com peso 6 no grafo integrado.

        Recebe:
            interactions (list[dict]): interações já validadas pela primeira passagem.
            mapper (UserMapper): tabela login -> índice.
            g1, g2, g3, g4 (AdjacencyListGraph): grafos onde as arestas serão adicionadas.
        """

        for data in interactions:
            source = data["source_user"]
            target = data["target_user"]
            itype  = data["type"]

            # Converte logins em índices inteiros.
            u = mapper.get_id(source)
            v = mapper.get_id(target)

            # Obtém o peso desta interação.
            weight = INTERACTION_WEIGHTS[itype]

            # Identifica em qual grafo separado esta interação pertence.
            if itype in GRAPH_TYPES["G1_comments"]:
                GraphBuilder._add_or_accumulate(g1, u, v, weight)

            elif itype in GRAPH_TYPES["G2_issue_close"]:
                GraphBuilder._add_or_accumulate(g2, u, v, weight)

            elif itype in GRAPH_TYPES["G3_pr_events"]:
                GraphBuilder._add_or_accumulate(g3, u, v, weight)

            # G4 recebe TODOS os tipos, independente do grafo separado.
            GraphBuilder._add_or_accumulate(g4, u, v, weight)

    @staticmethod
    def _add_or_accumulate(graph: AdjacencyListGraph, u: int, v: int, weight: float):
        """
        Adiciona uma aresta ou acumula o peso se ela já existir.

        Comportamento:
          - Se a aresta u -> v ainda não existe: cria e define o peso.
          - Se a aresta u -> v já existe: soma o novo peso ao peso atual.

        Esse comportamento implementa a "combinação ponderada de todas as interações"
        exigida pelo enunciado para o grafo integrado (G4), e também para os
        grafos separados quando dois usuários interagem várias vezes do mesmo tipo.

        Recebe:
            graph  (AdjacencyListGraph): grafo onde a aresta será adicionada.
            u      (int): índice do vértice de origem.
            v      (int): índice do vértice de destino.
            weight (float): peso a ser adicionado ou acumulado.
        """

        if graph.hasEdge(u, v):
            # Aresta já existe: acumula o peso (soma ao peso atual).
            current_weight = graph.getEdgeWeight(u, v)
            graph.setEdgeWeight(u, v, current_weight + weight)
        else:
            # Aresta nova: cria e define o peso inicial.
            graph.addEdge(u, v)
            graph.setEdgeWeight(u, v, weight)