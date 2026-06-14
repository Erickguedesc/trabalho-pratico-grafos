import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Garante imports do projeto
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from codigo.biblioteca.builder.graph_builder import GraphBuilder
from codigo.biblioteca.analysis.graph_analyzer import GraphAnalyzer
from codigo.export.gephi_exporter import GephiExporter

# =============================================================================
# Configuração da página
# =============================================================================

st.set_page_config(
    page_title="Análise de Grafos GitHub",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# CSS customizado
# =============================================================================

st.markdown("""
<style>
    /* ── Paleta Starship ───────────────────────────────────────────────────────
       Fundo: preto espacial #080c14
       Primária: amarelo-ouro do foguete #f5c518
       Secundária: laranja de propulsão #f97316
       Accent frio: branco estrelado #e2e8f0
       Muted: cinza cosmos #475569
    ─────────────────────────────────────────────────────────────────────────── */

    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
        background-color: #080c14;
    }

    /* ── Header ── */
    .main-header {
        background: linear-gradient(135deg, #080c14 0%, #121f0f 50%, #1a1200 100%);
        padding: 2rem 2.5rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        border: 1px solid #f5c51833;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: "🚀";
        position: absolute;
        right: 2rem;
        top: 50%;
        transform: translateY(-50%) rotate(-45deg);
        font-size: 5rem;
        opacity: 0.07;
        pointer-events: none;
    }
    .main-header .eyebrow {
        font-size: 0.72rem;
        font-weight: 700;
        color: #f5c518;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        margin-bottom: 0.4rem;
    }
    .main-header h1 {
        color: #f0f9ff;
        font-size: 1.9rem;
        font-weight: 800;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.5px;
    }
    .main-header h1 span { color: #f5c518; }
    .main-header p {
        color: #64748b;
        margin: 0;
        font-size: 0.88rem;
    }
    .main-header .repo-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: #f5c51814;
        border: 1px solid #f5c51833;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #f5c518;
        padding: 0.25rem 0.8rem;
        margin-top: 0.8rem;
    }

    /* ── Cards de estatísticas ── */
    .stat-card {
        background: #0d1117;
        border: 1px solid #1e293b;
        border-top: 2px solid #f5c51844;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        text-align: center;
    }
    .stat-card .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f5c518;
        line-height: 1;
        margin-bottom: 0.3rem;
    }
    .stat-card .label {
        font-size: 0.75rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* ── Aviso "construa primeiro" ── */
    .build-cta {
        background: linear-gradient(90deg, #1a1200, #12100000);
        border: 1px solid #f5c51833;
        border-left: 3px solid #f5c518;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.4rem;
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 1rem;
    }
    .build-cta .icon { font-size: 1.4rem; }
    .build-cta .text { font-size: 0.88rem; color: #94a3b8; line-height: 1.4; }
    .build-cta .text b { color: #f5c518; }

    /* ── Explainer cards ── */
    .metric-explainer {
        background: #0d1117;
        border: 1px solid #1e293b;
        border-left: 3px solid #f5c518;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }
    .metric-explainer .title {
        font-size: 0.78rem;
        font-weight: 700;
        color: #f5c518;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.35rem;
    }
    .metric-explainer .text {
        font-size: 0.87rem;
        color: #94a3b8;
        line-height: 1.55;
        margin: 0;
    }

    /* ── Insight box ── */
    .insight-box {
        background: #0a0f00;
        border: 1px solid #f5c51822;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-top: 0.5rem;
    }
    .insight-box .insight-title {
        font-size: 0.73rem;
        font-weight: 700;
        color: #f5c518;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.4rem;
    }
    .insight-box p {
        font-size: 0.86rem;
        color: #cbd5e1;
        margin: 0;
        line-height: 1.5;
    }

    /* ── Badges ── */
    .status-ok {
        display: inline-block;
        background: #052e16;
        color: #4ade80;
        border: 1px solid #166534;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.7rem;
    }
    .status-err {
        display: inline-block;
        background: #2d0a0a;
        color: #f87171;
        border: 1px solid #7f1d1d;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.7rem;
    }

    /* ── Tabela de ranking ── */
    .rank-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.87rem;
    }
    .rank-table th {
        background: #12180a;
        color: #64748b;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        padding: 0.55rem 0.8rem;
        text-align: left;
        border-bottom: 1px solid #f5c51822;
    }
    .rank-table td {
        padding: 0.5rem 0.8rem;
        border-bottom: 1px solid #1a1f0e;
        color: #e2e8f0;
    }
    .rank-table tr:hover td { background: #12180a; }
    .rank-table .pos { color: #334155; font-size: 0.78rem; width: 2rem; }
    .rank-table .user { font-weight: 500; }
    .rank-table .val {
        color: #f5c518;
        font-weight: 600;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 0.82rem;
    }
    .rank-table .bar-cell { width: 120px; }
    .bar-bg {
        background: #1e293b;
        border-radius: 999px;
        height: 6px;
        width: 100%;
    }
    .bar-fill {
        background: linear-gradient(90deg, #f5c518, #f97316);
        border-radius: 999px;
        height: 6px;
    }

    /* ── Community pills ── */
    .comm-pill {
        display: inline-block;
        background: #12180a;
        color: #94a3b8;
        border-radius: 6px;
        font-size: 0.78rem;
        padding: 0.15rem 0.5rem;
        margin: 0.15rem 0.2rem;
        border: 1px solid #1e293b;
    }
    .comm-header {
        font-size: 0.8rem;
        font-weight: 700;
        color: #f5c518;
        margin-bottom: 0.3rem;
    }
    .comm-block {
        background: #0d1117;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.5rem;
    }

    /* ── Abas ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #0d1117;
        border-radius: 10px;
        padding: 4px;
        border: 1px solid #1e293b;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 7px;
        color: #475569;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.45rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        background: #1a1200 !important;
        color: #f5c518 !important;
        border: 1px solid #f5c51833 !important;
    }

    /* ── Streamlit overrides ── */
    .block-container { padding-top: 1.5rem; max-width: 1200px; }
    div[data-testid="stExpander"] {
        border: 1px solid #1e293b;
        border-radius: 8px;
        background: #0d1117;
    }
    .stButton > button {
        background: #1a1200;
        color: #f5c518;
        border: 1px solid #f5c51855;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.88rem;
        padding: 0.5rem 1.5rem;
    }
    .stButton > button:hover {
        background: #f5c518;
        color: #080c14;
        border-color: #f5c518;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Header
# =============================================================================

st.markdown("""
<div class="main-header">
    <div class="eyebrow">🛸 Repositório analisado</div>
    <h1>Starship <span>·</span> Análise de Colaboração</h1>
    <p>Teoria de Grafos e Computabilidade · PUC Minas 2026/1 · Visualização dos grafos de interação entre colaboradores</p>
    <div class="repo-badge">⭐ starship-rs / starship · Terminal prompt cross-shell</div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# Setup de arquivo e construção
# =============================================================================

dados_dir = Path(os.getenv("INPUT_DIR", "dados"))
arquivo = dados_dir / "interacoes.json"

col_src, col_btn = st.columns([3, 1])

with col_src:
    if arquivo.exists():
        st.markdown(f'<span class="status-ok">✓ {arquivo}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="status-err">✗ Arquivo não encontrado: {arquivo}</span>', unsafe_allow_html=True)
        st.stop()

with col_btn:
    build_btn = st.button("🚀 Construir Grafos", use_container_width=True)

# Aviso de passo a passo — some depois que os grafos são construídos
if "bundle" not in st.session_state:
    st.markdown("""
    <div class="build-cta">
        <div class="icon">👆</div>
        <div class="text">
            <b>Comece aqui:</b> clique em <b>🚀 Construir Grafos</b> no canto superior direito
            para carregar os dados minerados e liberar todas as abas de análise.
        </div>
    </div>
    """, unsafe_allow_html=True)

if build_btn:
    with st.spinner("Construindo grafos..."):
        bundle = GraphBuilder.build_from_file(str(arquivo))
        st.session_state["bundle"] = bundle
        st.session_state["analyzer"] = None
    st.success("Grafos construídos com sucesso!")

# Stats rápidos no topo
if "bundle" in st.session_state:
    bundle = st.session_state["bundle"]
    g = bundle.integrated

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (bundle.mapper.num_users(), "Usuários únicos"),
        (g.getEdgeCount(), "Interações (G4)"),
        (bundle.comments.getEdgeCount(), "Comentários (G1)"),
        (bundle.issue_closes.getEdgeCount(), "Fechamentos (G2)"),
        (bundle.pr_events.getEdgeCount(), "Pull Requests (G3)"),
    ]
    for col, (val, lbl) in zip([c1, c2, c3, c4, c5], cards):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div class="value">{val:,}</div>
                <div class="label">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # =========================================================================
    # ABAS PRINCIPAIS
    # =========================================================================

    aba_estrutura, aba_centralidade, aba_estrutura_rede, aba_comunidades, aba_export = st.tabs([
        "🗂️ Estrutura do Grafo",
        "📡 Centralidade",
        "🔗 Estrutura da Rede",
        "🏘️ Comunidades",
        "📤 Exportar",
    ])

    # =========================================================================
    # ABA 1 — ESTRUTURA DO GRAFO
    # =========================================================================

    with aba_estrutura:
        st.markdown("### Representações do Grafo Integrado (G4)")
        st.markdown("""
        <div class="metric-explainer">
            <div class="title">O que é o Grafo Integrado?</div>
            <p class="text">
                O G4 combina todos os tipos de interação em um único grafo ponderado.
                Cada aresta tem um peso que reflete a intensidade da colaboração:
                comentários valem 2, abertura de issue comentada vale 3,
                revisão de PR vale 4 e merge vale 5.
                Quanto maior o peso acumulado entre dois usuários, mais forte é o laço de colaboração entre eles.
            </p>
        </div>
        """, unsafe_allow_html=True)

        top_vertices = sorted(
            range(g.getVertexCount()),
            key=lambda v: g.getVertexOutDegree(v),
            reverse=True
        )[:10]

        sub1, sub2 = st.tabs(["Lista de Adjacência", "Matriz de Adjacência"])

        with sub1:
            st.caption("Top 10 usuários por grau de saída — expanda para ver as conexões de cada um.")
            for v in top_vertices:
                origem = bundle.mapper.get_login(v)
                vizinhos = [bundle.mapper.get_login(u)
                            for u in range(g.getVertexCount()) if g.hasEdge(v, u)]
                with st.expander(f"👤 {origem}  —  {len(vizinhos)} conexões  |  out-degree: {g.getVertexOutDegree(v)}  |  in-degree: {g.getVertexInDegree(v)}"):
                    if vizinhos:
                        st.markdown(" → ".join(f"`{x}`" for x in vizinhos[:20]))
                        if len(vizinhos) > 20:
                            st.caption(f"Mostrando 20 de {len(vizinhos)} conexões.")
                    else:
                        st.write("Sem conexões.")

        with sub2:
            st.caption("Célula = 1 indica aresta direcionada da linha para a coluna.")
            usuarios = [bundle.mapper.get_login(v) for v in top_vertices]
            matriz = [[1 if g.hasEdge(o, d) else 0 for d in top_vertices] for o in top_vertices]
            df = pd.DataFrame(matriz, index=usuarios, columns=usuarios)
            st.dataframe(df, use_container_width=True)

    # =========================================================================
    # ABA 2 — CENTRALIDADE
    # =========================================================================

    with aba_centralidade:
        st.markdown("### Métricas de Centralidade")
        st.caption("Clique em **Executar análise** para calcular. Pode levar alguns segundos para grafos grandes.")

        if st.button("▶ Executar análise de centralidade"):
            with st.spinner("Calculando métricas..."):
                analyzer = GraphAnalyzer(bundle.integrated, mapper=bundle.mapper)
                st.session_state["analyzer"] = analyzer
                st.session_state["degree"]      = analyzer.degree_centrality()
                st.session_state["between"]     = analyzer.betweenness_centrality()
                st.session_state["closeness"]   = analyzer.closeness_centrality()
                st.session_state["pagerank"]    = analyzer.pagerank()

        if "degree" in st.session_state:

            def render_ranking(data: dict, value_key=None, top=10, fmt=".4f"):
                """Renderiza tabela de ranking com barra visual e coluna %."""
                items = list(data.items())[:top]
                if not items:
                    return
                if value_key:
                    values = [v[value_key] for _, v in items]
                else:
                    values = [v for _, v in items]
                max_val = max(values) if values else 1
                total   = sum(values) if sum(values) > 0 else 1

                rows = ""
                for i, (user, val) in enumerate(items):
                    v     = val[value_key] if value_key else val
                    bar   = int((v / max_val) * 100) if max_val > 0 else 0
                    share = (v / total) * 100
                    rows += f"""
                    <tr>
                        <td class="pos">#{i+1}</td>
                        <td class="user">{user}</td>
                        <td class="val">{v:{fmt}} <span style="color:#64748b;font-size:0.75rem">· {share:.1f}%</span></td>
                        <td class="bar-cell">
                            <div class="bar-bg"><div class="bar-fill" style="width:{bar}%"></div></div>
                        </td>
                    </tr>"""
                st.markdown(f"""
                <table class="rank-table">
                    <thead><tr>
                        <th></th><th>Usuário</th><th>Valor · % do top10</th><th>Escala</th>
                    </tr></thead>
                    <tbody>{rows}</tbody>
                </table>""", unsafe_allow_html=True)

            # -- Degree Centrality --
            st.markdown("---")
            st.markdown("#### Centralidade de Grau")
            st.markdown("""
            <div class="metric-explainer">
                <div class="title">O que mede</div>
                <p class="text">
                    Quantas conexões diretas cada usuário tem, normalizado pelo total possível.
                    <b style="color:#e2e8f0">In</b> = quantas pessoas interagiram <em>com</em> ele.
                    <b style="color:#e2e8f0">Out</b> = com quantas pessoas ele interagiu ativamente.
                    Indica quem participa mais de revisões, discussões e colaborações.
                </p>
            </div>
            """, unsafe_allow_html=True)

            deg = st.session_state["degree"]
            c_in, c_out, c_tot = st.columns(3)
            with c_in:
                st.caption("🔽 Top 10 — In-degree")
                render_ranking(
                    dict(sorted(deg.items(), key=lambda x: x[1]["in"], reverse=True)[:10]),
                    value_key="in"
                )
            with c_out:
                st.caption("🔼 Top 10 — Out-degree")
                render_ranking(
                    dict(sorted(deg.items(), key=lambda x: x[1]["out"], reverse=True)[:10]),
                    value_key="out"
                )
            with c_tot:
                st.caption("⚖️ Top 10 — Total")
                render_ranking(deg, value_key="total")

            # -- Betweenness --
            st.markdown("---")
            st.markdown("#### Centralidade de Intermediação (Betweenness)")
            st.markdown("""
            <div class="metric-explainer">
                <div class="title">O que mede</div>
                <p class="text">
                    Com que frequência um usuário aparece nos caminhos mínimos entre todos os pares de colaboradores.
                    Quem tem betweenness alto age como <b style="color:#e2e8f0">"ponte"</b> entre grupos diferentes do projeto.
                    Se essas pessoas pararem de contribuir, partes da rede ficam desconectadas entre si.
                </p>
            </div>
            """, unsafe_allow_html=True)
            render_ranking(st.session_state["between"], fmt=".6f")

            # -- Closeness --
            st.markdown("---")
            st.markdown("#### Centralidade de Proximidade (Closeness)")
            st.markdown("""
            <div class="metric-explainer">
                <div class="title">O que mede</div>
                <p class="text">
                    Quem consegue alcançar todos os outros usuários com <b style="color:#e2e8f0">menos passos</b> no grafo.
                    Um closeness alto significa que a informação chega mais rápido para esse usuário —
                    ele está no "centro geográfico" da rede.
                    Valores baixos no geral são esperados em redes esparsas como esta.
                </p>
            </div>
            """, unsafe_allow_html=True)
            render_ranking(st.session_state["closeness"], fmt=".6f")

            # -- PageRank --
            st.markdown("---")
            st.markdown("#### PageRank")
            st.markdown("""
            <div class="metric-explainer">
                <div class="title">O que mede</div>
                <p class="text">
                    A <b style="color:#e2e8f0">influência qualitativa</b> de cada usuário — não só quantas conexões tem,
                    mas a importância de quem está conectado a ele.
                    Uma interação de um usuário influente vale mais do que dez de usuários periféricos.
                    É o algoritmo que o Google usava para ranquear páginas web.
                </p>
            </div>
            """, unsafe_allow_html=True)
            render_ranking(st.session_state["pagerank"], fmt=".6f")

            st.markdown("""
            <div class="insight-box" style="margin-top:1rem">
                <div class="insight-title">💡 Como ler esses resultados juntos</div>
                <p>
                    Um usuário pode liderar no <b>out-degree</b> (muito ativo) sem liderar no <b>PageRank</b> (suas interações são com usuários periféricos).
                    O contrário também acontece: quem lidera o PageRank recebe atenção de colaboradores já influentes.
                    O <b>betweenness</b> revela os pontos de fragilidade da rede — quem sai pode fragmentar a comunicação entre grupos.
                </p>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # ABA 3 — ESTRUTURA DA REDE
    # =========================================================================

    with aba_estrutura_rede:
        st.markdown("### Estrutura e Coesão da Rede")

        if st.button("▶ Executar análise de estrutura"):
            with st.spinner("Calculando..."):
                analyzer = GraphAnalyzer(bundle.integrated, mapper=bundle.mapper)
                st.session_state["analyzer"] = analyzer
                st.session_state["density"]      = analyzer.density()
                st.session_state["assortativity"]= analyzer.assortativity()
                st.session_state["clustering"]   = analyzer.clustering_coefficient()

        if "density" in st.session_state:
            d = st.session_state["density"]
            a = st.session_state["assortativity"]

            # Densidade
            st.markdown("---")
            st.markdown("#### Densidade da Rede")
            st.markdown("""
            <div class="metric-explainer">
                <div class="title">O que mede</div>
                <p class="text">
                    Proporção entre arestas existentes e o máximo possível.
                    Valor 0 = sem nenhuma conexão. Valor 1 = todos conectados com todos.
                    Redes de colaboração reais tipicamente ficam abaixo de <b style="color:#e2e8f0">0.01</b>
                    — a maioria das pessoas interage com pouquíssimas outras.
                </p>
            </div>
            """, unsafe_allow_html=True)

            col_d1, col_d2 = st.columns([1, 3])
            with col_d1:
                st.markdown(f"""
                <div class="stat-card" style="margin-top:0.5rem">
                    <div class="value">{d:.6f}</div>
                    <div class="label">Densidade</div>
                </div>""", unsafe_allow_html=True)
            with col_d2:
                pct = min(d * 100, 100)
                interp = "Muito esparsa" if d < 0.01 else ("Moderada" if d < 0.1 else "Densa")
                st.markdown(f"""
                <div class="insight-box" style="margin-top:0.5rem; height:90px; display:flex; flex-direction:column; justify-content:center;">
                    <div class="insight-title">Interpretação</div>
                    <p>{interp} — apenas <b>{pct:.4f}%</b> de todas as conexões possíveis existem.
                    Com {g.getVertexCount():,} usuários, o máximo teórico seria {g.getVertexCount() * (g.getVertexCount()-1):,} arestas.
                    Existem {g.getEdgeCount():,}.</p>
                </div>""", unsafe_allow_html=True)

            # Assortatividade
            st.markdown("---")
            st.markdown("#### Assortatividade")
            st.markdown("""
            <div class="metric-explainer">
                <div class="title">O que mede</div>
                <p class="text">
                    Se usuários com muitas conexões tendem a se conectar entre si (<b style="color:#4ade80">assortativa &gt; 0</b>)
                    ou se os hubs preferem interagir com usuários periféricos (<b style="color:#f87171">disassortativa &lt; 0</b>).
                    Calculada como correlação de Pearson entre grau de saída da origem e grau de entrada do destino.
                </p>
            </div>
            """, unsafe_allow_html=True)

            col_a1, col_a2 = st.columns([1, 3])
            assort_color = "#4ade80" if a > 0 else "#f87171"
            assort_label = "Assortativa" if a > 0 else "Disassortativa"
            assort_desc = (
                "Os hubs se conectam principalmente com outros hubs — rede centralizada."
                if a > 0 else
                "Os hubs (maintainers) conectam com colaboradores periféricos — padrão típico de open source."
            )
            with col_a1:
                st.markdown(f"""
                <div class="stat-card" style="margin-top:0.5rem">
                    <div class="value" style="color:{assort_color}">{a:.4f}</div>
                    <div class="label">{assort_label}</div>
                </div>""", unsafe_allow_html=True)
            with col_a2:
                st.markdown(f"""
                <div class="insight-box" style="margin-top:0.5rem; height:90px; display:flex; flex-direction:column; justify-content:center;">
                    <div class="insight-title">Interpretação</div>
                    <p>{assort_desc}</p>
                </div>""", unsafe_allow_html=True)

            # Clustering
            st.markdown("---")
            st.markdown("#### Coeficiente de Clustering (Aglomeração)")
            st.markdown("""
            <div class="metric-explainer">
                <div class="title">O que mede</div>
                <p class="text">
                    A tendência dos vizinhos de um usuário de também se conectarem entre si — formando "triângulos".
                    Valor 1.0 = todos os vizinhos desse usuário se conhecem.
                    Valores altos em nós periféricos (poucos vizinhos) são esperados em redes esparsas.
                    O interessante é observar usuários com grau alto <em>e</em> clustering alto — grupos coesos de verdade.
                </p>
            </div>
            """, unsafe_allow_html=True)

            clust = st.session_state["clustering"]

            def render_ranking_simple(data, top=10, fmt=".4f"):
                items   = list(data.items())[:top]
                values  = [v for _, v in items]
                max_val = max(values) if values else 1
                total   = sum(values) if sum(values) > 0 else 1
                rows = ""
                for i, (user, val) in enumerate(items):
                    bar   = int((val / max_val) * 100) if max_val > 0 else 0
                    share = (val / total) * 100
                    rows += f"""
                    <tr>
                        <td class="pos">#{i+1}</td>
                        <td class="user">{user}</td>
                        <td class="val">{val:{fmt}} <span style="color:#64748b;font-size:0.75rem">· {share:.1f}%</span></td>
                        <td class="bar-cell">
                            <div class="bar-bg"><div class="bar-fill" style="width:{bar}%"></div></div>
                        </td>
                    </tr>"""
                st.markdown(f"""
                <table class="rank-table">
                    <thead><tr><th></th><th>Usuário</th><th>Coef. · % do top10</th><th>Escala</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>""", unsafe_allow_html=True)

            render_ranking_simple(clust)

    # =========================================================================
    # ABA 4 — COMUNIDADES
    # =========================================================================

    with aba_comunidades:
        st.markdown("### Detecção de Comunidades")
        st.markdown("""
        <div class="metric-explainer">
            <div class="title">Como funciona</div>
            <p class="text">
                O algoritmo <b style="color:#e2e8f0">Label Propagation</b> atribui uma comunidade a cada usuário e itera:
                cada um adota a comunidade mais frequente entre seus vizinhos, até estabilizar.
                Identifica grupos que colaboram mais frequentemente entre si — como times informais dentro do projeto.
                Os <b style="color:#e2e8f0">Bridging Ties</b> são os usuários que conectam comunidades diferentes,
                atuando como elos estratégicos de comunicação entre grupos.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("▶ Detectar comunidades e bridging ties"):
            with st.spinner("Executando Label Propagation..."):
                analyzer = GraphAnalyzer(bundle.integrated, mapper=bundle.mapper)
                st.session_state["analyzer"]    = analyzer
                st.session_state["communities"] = analyzer.detect_communities()
                st.session_state["bridges"]     = analyzer.bridging_ties(st.session_state["communities"])

        if "communities" in st.session_state:
            communities = st.session_state["communities"]
            bridges     = st.session_state["bridges"]

            from collections import defaultdict
            groups: dict[int, list[str]] = defaultdict(list)
            for user, comm_id in communities.items():
                groups[comm_id].append(user)

            num_comms = len(groups)
            big = sum(1 for m in groups.values() if len(m) >= 10)
            small = num_comms - big

            col_c1, col_c2, col_c3 = st.columns(3)
            for col, (val, lbl) in zip([col_c1, col_c2, col_c3], [
                (num_comms, "Comunidades"),
                (big, "Grupos grandes (≥10)"),
                (len(bridges), "Bridging ties"),
            ]):
                with col:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="value">{val}</div>
                        <div class="label">{lbl}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            col_left, col_right = st.columns([3, 2])

            with col_left:
                st.markdown("##### Comunidades detectadas")
                sorted_groups = sorted(groups.items(), key=lambda x: -len(x[1]))
                for comm_id, members in sorted_groups[:30]:
                    preview = members[:8]
                    extra = len(members) - 8
                    pills = "".join(f'<span class="comm-pill">{m}</span>' for m in preview)
                    suffix = f'<span class="comm-pill" style="color:#475569">+{extra} mais</span>' if extra > 0 else ""
                    st.markdown(f"""
                    <div class="comm-block">
                        <div class="comm-header">Comunidade {comm_id} · {len(members)} membros</div>
                        {pills}{suffix}
                    </div>""", unsafe_allow_html=True)
                if len(groups) > 30:
                    st.caption(f"Mostrando 30 de {len(groups)} comunidades.")

            with col_right:
                st.markdown("##### Bridging Ties")
                st.markdown("""
                <div class="insight-box" style="margin-bottom:0.8rem">
                    <div class="insight-title">O que são</div>
                    <p>Usuários que têm vizinhos em 2 ou mais comunidades distintas.
                    São os elos mais estratégicos — se saírem, grupos inteiros ficam isolados.</p>
                </div>
                """, unsafe_allow_html=True)

                if bridges:
                    rows = ""
                    items = list(bridges.items())[:15]
                    max_v = max(v for _, v in items)
                    total_v = sum(v for _, v in items) or 1
                    for i, (user, score) in enumerate(items):
                        bar   = int((score / max_v) * 100)
                        share = (score / total_v) * 100
                        rows += f"""
                        <tr>
                            <td class="pos">#{i+1}</td>
                            <td class="user">{user}</td>
                            <td class="val">{score} <span style="color:#64748b;font-size:0.75rem">· {share:.1f}%</span></td>
                            <td class="bar-cell">
                                <div class="bar-bg"><div class="bar-fill" style="width:{bar}%"></div></div>
                            </td>
                        </tr>"""
                    st.markdown(f"""
                    <table class="rank-table">
                        <thead><tr><th></th><th>Usuário</th><th>Comunidades · % do total</th><th></th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>""", unsafe_allow_html=True)
                else:
                    st.info("Nenhum bridging tie encontrado.")

    # =========================================================================
    # ABA 5 — EXPORTAR
    # =========================================================================

    with aba_export:
        st.markdown("### Exportar para Gephi")
        st.markdown("""
        <div class="metric-explainer">
            <div class="title">Formato GEXF</div>
            <p class="text">
                Os 4 grafos são exportados no formato <b style="color:#e2e8f0">.gexf</b> (Graph Exchange XML Format),
                aceito diretamente pelo Gephi para visualização interativa.
                Cada arquivo contém os nós com rótulos (logins) e as arestas com pesos.
                Os arquivos são salvos em <code style="color:#38bdf8">dados/gephi/</code>.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        | Arquivo | Conteúdo |
        |---------|----------|
        | `g1_comentarios.gexf` | Comentários em issues e PRs (peso 2) |
        | `g2_fechamentos.gexf` | Fechamento de issue por outro usuário (peso 3) |
        | `g3_pull_requests.gexf` | Revisões, aprovações e merges de PR (peso 4–5) |
        | `g4_integrado.gexf` | Grafo combinado com todos os pesos |
        """)

        if st.button("📤 Exportar os 4 grafos"):
            bundle = st.session_state["bundle"]
            try:
                export_dir = dados_dir / "gephi"
                export_dir.mkdir(parents=True, exist_ok=True)

                exports = [
                    ("g1_comentarios.gexf", bundle.comments),
                    ("g2_fechamentos.gexf", bundle.issue_closes),
                    ("g3_pull_requests.gexf", bundle.pr_events),
                    ("g4_integrado.gexf", bundle.integrated),
                ]

                progress = st.progress(0)
                for i, (nome, grafo) in enumerate(exports):
                    GephiExporter.export(grafo, bundle.mapper, str(export_dir / nome))
                    progress.progress((i + 1) / len(exports))

                st.success(f"✓ 4 arquivos exportados para `{export_dir}/`")

                for nome, _ in exports:
                    st.markdown(f"- `{export_dir / nome}`")

            except Exception as e:
                st.error(f"Erro na exportação: {e}")