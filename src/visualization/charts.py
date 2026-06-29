"""Generate static and interactive visualizations for the sustainability report."""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from loguru import logger

from src.utils.config import EXTERNAL_DIR, FIGURES_DIR


def plot_ranking_bar(insm: pd.DataFrame, top_n: int = 30, title: str = "Top municípios - INSM 2021") -> go.Figure:
    """Horizontal bar chart of top-N municipalities by INSM score."""
    df = insm.nlargest(top_n, "insm_score").sort_values("insm_score")
    df["label"] = df["municipio"] + " - " + df["uf_sigla"]

    fig = px.bar(
        df, x="insm_score", y="label", orientation="h",
        color="insm_score", color_continuous_scale="Greens",
        title=title,
        labels={"insm_score": "INSM (0-100)", "label": "Município"},
    )
    fig.update_layout(height=max(600, top_n * 22), showlegend=False)
    return fig


def plot_choropleth(insm: pd.DataFrame, shp_path: Path | None = None) -> go.Figure:
    """Choropleth map of Brazil colored by INSM score."""
    if shp_path is None:
        shp_path = EXTERNAL_DIR / "ibge" / "municipios_2022" / "BR_Municipios_2022.shp"

    if not shp_path.exists():
        logger.warning("Shapefile not found; skipping choropleth.")
        return go.Figure()

    gdf = gpd.read_file(shp_path)
    gdf["geocodigo"] = gdf["CD_MUN"].astype(str).str[:7]
    merged = gdf.merge(insm[["geocodigo", "insm_score", "municipio", "uf_sigla"]], on="geocodigo", how="left")
    merged = merged.to_crs(epsg=4326)

    geojson = merged.__geo_interface__

    fig = px.choropleth(
        merged,
        geojson=geojson,
        locations=merged.index,
        color="insm_score",
        color_continuous_scale="RdYlGn",
        range_color=(0, 100),
        hover_name="municipio",
        hover_data={"uf_sigla": True, "insm_score": ":.1f"},
        title="Ranking Nacional de Sustentabilidade Municipal (INSM 2021)",
        labels={"insm_score": "INSM"},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=700, margin={"r": 0, "t": 50, "l": 0, "b": 0})
    return fig


def plot_scatter_pib_insm(insm: pd.DataFrame, master: pd.DataFrame) -> go.Figure:
    """Scatter plot: PIB per capita vs INSM score colored by region."""
    df = master.merge(insm[["geocodigo", "insm_score"]], on="geocodigo", how="inner")
    df = df.dropna(subset=["pib_per_capita", "insm_score"])

    fig = px.scatter(
        df, x="pib_per_capita", y="insm_score",
        hover_name="municipio",
        hover_data={"uf_sigla": True},
        color="uf_sigla",
        size="populacao",
        size_max=25,
        opacity=0.6,
        title="Relação entre PIB per capita e Sustentabilidade",
        labels={"pib_per_capita": "PIB per capita (R$)", "insm_score": "INSM", "uf_sigla": "UF"},
        log_x=True,
        trendline="ols",
    )
    return fig


def plot_correlation_heatmap(master: pd.DataFrame) -> go.Figure:
    """Correlation heatmap of main indicators."""
    num_cols = master.select_dtypes(include=[np.number]).columns.tolist()
    excl = ["ano", "uf_id"]
    num_cols = [c for c in num_cols if c not in excl][:15]

    corr = master[num_cols].corr()
    fig = px.imshow(
        corr,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title="Matriz de Correlação dos Indicadores",
        aspect="auto",
        text_auto=".2f",
    )
    fig.update_layout(height=700)
    return fig


def plot_cluster_boxplot(clusters: pd.DataFrame, insm: pd.DataFrame) -> go.Figure:
    """Boxplot of INSM scores by cluster."""
    df = clusters.copy()
    if "insm_score" not in df.columns:
        df = df.merge(insm[["geocodigo", "insm_score"]], on="geocodigo", how="left")
    elif "insm_score_x" in df.columns:
        df = df.rename(columns={"insm_score_x": "insm_score"}).drop(columns=["insm_score_y"], errors="ignore")
    fig = px.box(
        df, x="cluster_label", y="insm_score",
        color="cluster_label",
        title="Distribuição do INSM por Cluster",
        labels={"insm_score": "INSM", "cluster_label": "Cluster"},
    )
    fig.update_xaxes(tickangle=20)
    return fig


def plot_feature_importance(fi: pd.DataFrame, title: str = "Feature Importance (LightGBM)") -> go.Figure:
    """Horizontal bar chart of feature importances."""
    df = fi.sort_values("importance", ascending=True)
    fig = px.bar(
        df, x="importance", y="feature", orientation="h",
        color="importance", color_continuous_scale="Blues",
        title=title,
    )
    return fig


def save_all_figures(insm: pd.DataFrame, master: pd.DataFrame, clusters: pd.DataFrame, fi: pd.DataFrame) -> None:
    """Generate and save all report figures."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    figs = {
        "ranking_top30": plot_ranking_bar(insm, top_n=30),
        "choropleth": plot_choropleth(insm),
        "scatter_pib_insm": plot_scatter_pib_insm(insm, master),
        "correlation_heatmap": plot_correlation_heatmap(master),
        "cluster_boxplot": plot_cluster_boxplot(clusters, insm),
        "feature_importance": plot_feature_importance(fi),
    }

    for name, fig in figs.items():
        html_path = FIGURES_DIR / f"{name}.html"
        fig.write_html(str(html_path))
        logger.success(f"Saved: {html_path}")

    logger.success(f"All figures saved to {FIGURES_DIR}")
