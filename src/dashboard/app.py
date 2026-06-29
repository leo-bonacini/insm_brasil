"""Streamlit Dashboard: Ranking Nacional de Sustentabilidade Municipal."""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ranking Sustentabilidade Municipal",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

PARQUET_DIR = Path(__file__).parent.parent.parent / "data" / "parquet"
EXTERNAL_DIR = Path(__file__).parent.parent.parent / "data" / "external"


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    insm = pd.read_parquet(PARQUET_DIR / "insm_ranking.parquet")
    master = pd.read_parquet(PARQUET_DIR / "master_indicators.parquet")
    clusters = pd.read_parquet(PARQUET_DIR / "clusters.parquet")
    fi = pd.read_parquet(PARQUET_DIR / "feature_importance.parquet") if (PARQUET_DIR / "feature_importance.parquet").exists() else pd.DataFrame()
    return insm, master, clusters, fi


@st.cache_data
def load_geodata():
    shp = EXTERNAL_DIR / "ibge" / "municipios_2022" / "BR_Municipios_2022.shp"
    if shp.exists():
        import geopandas as gpd
        gdf = gpd.read_file(shp).to_crs(epsg=4326)
        gdf["geocodigo"] = gdf["CD_MUN"].astype(str).str[:7]
        return gdf
    return None


insm, master, clusters, fi = load_data()

# Merge for display
display = insm.merge(clusters[["geocodigo", "cluster_label"]], on="geocodigo", how="left")
display = display.merge(master[["geocodigo", "pct_nativa", "pct_florestal", "pct_agro",
                                 "pib_per_capita", "variacao_nativa_pp"]], on="geocodigo", how="left")

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.title("🌿 Filtros")
st.sidebar.markdown("---")

ufs = sorted(display["uf_sigla"].dropna().unique())
sel_ufs = st.sidebar.multiselect("Estado (UF)", ufs, default=[])

clusters_avail = sorted(display["cluster_label"].dropna().unique())
sel_clusters = st.sidebar.multiselect("Cluster / Perfil", clusters_avail, default=[])

pop_min, pop_max = int(display["populacao"].min()), int(display["populacao"].max())
pop_range = st.sidebar.slider("Faixa de população", pop_min, pop_max, (pop_min, pop_max), step=1000)

pib_min, pib_max = float(display["pib_per_capita"].min()), float(display["pib_per_capita"].max())
pib_range = st.sidebar.slider("PIB per capita (R$)", pib_min, pib_max, (pib_min, pib_max))

top_n = st.sidebar.slider("Top N municípios no ranking", 10, 200, 50)

# Apply filters
mask = (
    display["populacao"].between(pop_range[0], pop_range[1]) &
    display["pib_per_capita"].between(pib_range[0], pib_range[1])
)
if sel_ufs:
    mask &= display["uf_sigla"].isin(sel_ufs)
if sel_clusters:
    mask &= display["cluster_label"].isin(sel_clusters)

filtered = display[mask].copy()

# ── Main layout ───────────────────────────────────────────────────────────────
st.title("🌿 Ranking Nacional de Sustentabilidade dos Municípios Brasileiros")
st.markdown("**Índice Nacional de Sustentabilidade Municipal (INSM)** · Dados: IBGE, MapBiomas, INPE · Ano base: 2021")
st.markdown("---")

# ── KPIs ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Municípios analisados", f"{len(filtered):,}")
c2.metric("INSM médio", f"{filtered['insm_score'].mean():.1f}")
c3.metric("INSM máximo", f"{filtered['insm_score'].max():.1f}")
c4.metric("Cobertura nativa média", f"{filtered['pct_nativa'].mean():.1f}%")
c5.metric("PIB per capita médio", f"R$ {filtered['pib_per_capita'].mean():,.0f}")

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🗺️ Mapa", "📊 Ranking", "🔍 Análise", "🏘️ Clusters", "📌 Perfil"])

# TAB 1: Map
with tab1:
    st.subheader("Mapa Coropleto: INSM por Município")
    gdf = load_geodata()
    if gdf is not None:
        merged_geo = gdf.merge(filtered[["geocodigo", "insm_score", "municipio", "uf_sigla"]], on="geocodigo", how="inner")
        if not merged_geo.empty:
            geojson = merged_geo.__geo_interface__
            fig_map = px.choropleth(
                merged_geo,
                geojson=geojson,
                locations=merged_geo.index,
                color="insm_score",
                color_continuous_scale="RdYlGn",
                range_color=(0, 100),
                hover_name="municipio",
                hover_data={"uf_sigla": True, "insm_score": ":.1f"},
                labels={"insm_score": "INSM"},
            )
            fig_map.update_geos(fitbounds="locations", visible=False)
            fig_map.update_layout(height=600, margin={"r": 0, "t": 10, "l": 0, "b": 0})
            st.plotly_chart(fig_map, width='stretch')
        else:
            st.info("Nenhum dado geográfico disponível com os filtros atuais.")
    else:
        st.warning("Shapefile não encontrado. Execute o pipeline de download primeiro.")

# TAB 2: Ranking
with tab2:
    st.subheader(f"Top {top_n} Municípios mais Sustentáveis")
    top_df = filtered.nlargest(top_n, "insm_score").reset_index(drop=True)
    top_df.index += 1

    # Bar chart
    fig_bar = px.bar(
        top_df.sort_values("insm_score").tail(30),
        x="insm_score", y="municipio", orientation="h",
        color="insm_score", color_continuous_scale="Greens",
        hover_data={"uf_sigla": True, "pct_nativa": ":.1f"},
        labels={"insm_score": "INSM", "municipio": "Município"},
    )
    fig_bar.update_layout(height=600)
    st.plotly_chart(fig_bar, width='stretch')

    # Table
    show_cols = ["insm_ranking", "municipio", "uf_sigla", "insm_score", "pct_nativa",
                 "pct_florestal", "pib_per_capita", "cluster_label"]
    show_cols = [c for c in show_cols if c in top_df.columns]
    st.dataframe(
        top_df[show_cols].rename(columns={
            "insm_ranking": "Ranking",
            "municipio": "Município",
            "uf_sigla": "UF",
            "insm_score": "INSM",
            "pct_nativa": "% Nativa",
            "pct_florestal": "% Florestal",
            "pib_per_capita": "PIB per capita",
            "cluster_label": "Cluster",
        }),
        width='stretch',
    )

    # Export
    csv = top_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar CSV", csv, "ranking_insm.csv", "text/csv")

# TAB 3: Analysis
with tab3:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("PIB per capita vs INSM")
        fig_scatter = px.scatter(
            filtered.dropna(subset=["pib_per_capita", "insm_score"]),
            x="pib_per_capita", y="insm_score",
            hover_name="municipio",
            color="uf_sigla", size="populacao", size_max=20,
            opacity=0.6, log_x=True,
            labels={"pib_per_capita": "PIB per capita (R$)", "insm_score": "INSM", "uf_sigla": "UF"},
        )
        st.plotly_chart(fig_scatter, width='stretch')

    with col_r:
        st.subheader("Variação de Vegetação Nativa (2015-2021)")
        fig_change = px.histogram(
            filtered.dropna(subset=["variacao_nativa_pp"]),
            x="variacao_nativa_pp", nbins=50,
            color_discrete_sequence=["#2ecc71"],
            labels={"variacao_nativa_pp": "Variação (pontos percentuais)"},
        )
        fig_change.add_vline(x=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig_change, width='stretch')

    if not fi.empty:
        st.subheader("Importância das Variáveis (LightGBM)")
        fig_fi = px.bar(
            fi.sort_values("importance", ascending=True),
            x="importance", y="feature", orientation="h",
            color="importance", color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_fi, width='stretch')

# TAB 4: Clusters
with tab4:
    st.subheader("Perfis de Sustentabilidade (K-Means Clustering)")
    cl_data = filtered.copy()
    if "cluster_label" in cl_data.columns:
        fig_box = px.box(
            cl_data.dropna(subset=["cluster_label"]),
            x="cluster_label", y="insm_score",
            color="cluster_label",
            labels={"insm_score": "INSM", "cluster_label": "Perfil"},
        )
        fig_box.update_xaxes(tickangle=15)
        st.plotly_chart(fig_box, width='stretch')

        # Cluster summary table
        summary = (
            cl_data.groupby("cluster_label")
            .agg(
                municípios=("geocodigo", "count"),
                insm_médio=("insm_score", "mean"),
                pct_nativa_média=("pct_nativa", "mean"),
                pib_pc_médio=("pib_per_capita", "mean"),
            )
            .round(2)
        )
        st.dataframe(summary, width='stretch')
    else:
        st.info("Clustering não disponível.")

# TAB 5: Municipality Profile
with tab5:
    st.subheader("Perfil Detalhado por Município")
    sorted_muns = filtered.sort_values("insm_score", ascending=False)["municipio"].tolist()
    sel_mun = st.selectbox("Selecione um município", sorted_muns)

    if sel_mun:
        mun_data = filtered[filtered["municipio"] == sel_mun].iloc[0]
        master_data = master[master["municipio"] == sel_mun]

        col1, col2, col3 = st.columns(3)
        col1.metric("INSM Score", f"{mun_data.get('insm_score', 'N/A'):.1f}")
        col2.metric("Ranking Nacional", f"#{int(mun_data.get('insm_ranking', 0)):,}")
        col3.metric("UF", mun_data.get("uf_sigla", ""))

        col4, col5, col6 = st.columns(3)
        col4.metric("Cobertura Nativa", f"{mun_data.get('pct_nativa', 0):.1f}%")
        col5.metric("Cobertura Florestal", f"{mun_data.get('pct_florestal', 0):.1f}%")
        col6.metric("Área Agropecuária", f"{mun_data.get('pct_agro', 0):.1f}%")

        col7, col8, col9 = st.columns(3)
        col7.metric("PIB per capita", f"R$ {mun_data.get('pib_per_capita', 0):,.0f}")
        col8.metric("População", f"{mun_data.get('populacao', 0):,.0f} hab")
        col9.metric("Área", f"{mun_data.get('area_km2', 0):,.1f} km²")

        st.markdown(f"**Cluster:** {mun_data.get('cluster_label', 'N/A')}")
        st.markdown(f"**Variação vegetação nativa (2015-2021):** {mun_data.get('variacao_nativa_pp', 0):+.2f} p.p.")

        # Radar chart of normalized indicators
        norm_cols = [c for c in display.columns if c.startswith("norm_")]
        if norm_cols and sel_mun in insm["municipio"].values:
            insm_row = insm[insm["municipio"] == sel_mun].iloc[0]
            values = [insm_row.get(c, 0) for c in norm_cols]
            labels = [c.replace("norm_", "") for c in norm_cols]
            fig_radar = go.Figure(go.Scatterpolar(
                r=values + [values[0]],
                theta=labels + [labels[0]],
                fill="toself",
                name=sel_mun,
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(range=[0, 100])),
                title=f"Perfil de Indicadores: {sel_mun}",
            )
            st.plotly_chart(fig_radar, width='stretch')

# Footer
st.markdown("---")
st.markdown(
    "**Fontes:** IBGE (PIB, População, PAM, PPM) · MapBiomas Coleção 9 (uso do solo 1985-2023) · "
    "Metodologia: PCA + Entropy Weight Method para pesos, LightGBM para modelagem preditiva."
)
