"""MapBiomas Collection 9 statistics downloader."""
from pathlib import Path

import pandas as pd
from loguru import logger

from src.utils.config import (
    MAPBIOMAS_AGRO_CODES,
    MAPBIOMAS_FOREST_CODES,
    MAPBIOMAS_NATIVE_VEGETATION_CODES,
    MAPBIOMAS_STATS_URL,
    MAPBIOMAS_URBAN_CODES,
    RAW_DIR,
)
from src.utils.geocodes import normalize_geocodigo
from src.utils.http import download_file


def download_mapbiomas_stats() -> Path:
    """Download MapBiomas Collection 9 land use statistics by municipality."""
    out = RAW_DIR / "mapbiomas" / "mapbiomas_col9_municipio.parquet"
    if out.exists():
        return out

    out.parent.mkdir(parents=True, exist_ok=True)
    xlsx_path = RAW_DIR / "mapbiomas" / "mapbiomas_col9_municipio.xlsx"
    download_file(MAPBIOMAS_STATS_URL, xlsx_path, "MapBiomas Col.9 stats")

    logger.info("Parsing MapBiomas XLSX (sheet COVERAGE_9)...")
    try:
        df = pd.read_excel(xlsx_path, sheet_name="COVERAGE_9")
    except Exception as e:
        logger.error(f"Failed to read MapBiomas XLSX COVERAGE_9: {e}")
        # Save raw for inspection
        try:
            xl = pd.ExcelFile(xlsx_path)
            df = pd.read_excel(xlsx_path, sheet_name=xl.sheet_names[1])
            df.to_parquet(out.with_suffix(".raw.parquet"), index=False)
        except Exception:
            pass
        stub = pd.DataFrame(columns=["geocodigo", "ano", "classe_codigo", "area_ha"])
        stub.to_parquet(out, index=False)
        return out

    logger.info(f"MapBiomas raw: {len(df):,} rows, {len(df.columns)} cols")

    # Expected columns: geocode, class, 1985..2023
    df = df.rename(columns={"geocode": "geocodigo", "class": "classe_codigo"})
    df["geocodigo"] = df["geocodigo"].apply(normalize_geocodigo)

    # Keep only municipality-level rows (geocodigo = 7 digits representing a municipality)
    # The file may include state/country aggregates with different geocode lengths
    df = df[df["geocodigo"].str.len() == 7].copy()

    # Year columns: 1985-2023 (numeric column names)
    year_cols = [c for c in df.columns if isinstance(c, int) and 1985 <= c <= 2024]
    if not year_cols:
        # Sometimes they come as strings
        year_cols = [c for c in df.columns if str(c).isdigit() and 1985 <= int(c) <= 2024]

    id_cols = ["geocodigo", "classe_codigo"]
    # Also keep state and municipality name for reference
    for extra in ["state", "municipality", "country"]:
        if extra in df.columns:
            id_cols.append(extra)

    df_long = df[id_cols + year_cols].melt(id_vars=id_cols, var_name="ano", value_name="area_ha")
    df_long["ano"] = pd.to_numeric(df_long["ano"], errors="coerce").astype("Int64")
    df_long["area_ha"] = pd.to_numeric(df_long["area_ha"], errors="coerce")
    df_long["classe_codigo"] = pd.to_numeric(df_long["classe_codigo"], errors="coerce").astype("Int64")

    # Drop rows with no area data
    df_long = df_long.dropna(subset=["area_ha"])
    df_long = df_long[df_long["area_ha"] > 0]

    df_long.to_parquet(out, index=False)
    logger.success(f"MapBiomas saved: {len(df_long):,} rows covering {df_long['geocodigo'].nunique()} municipalities")
    return out


def compute_mapbiomas_features(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate MapBiomas data into key coverage features per municipality per year."""
    if df.empty or "classe_codigo" not in df.columns:
        return df

    df = df.copy()
    df["classe_codigo"] = pd.to_numeric(df["classe_codigo"], errors="coerce")
    df["area_ha"] = pd.to_numeric(df["area_ha"], errors="coerce").fillna(0)

    # Flag class groups
    df["is_native"] = df["classe_codigo"].isin(MAPBIOMAS_NATIVE_VEGETATION_CODES)
    df["is_forest"] = df["classe_codigo"].isin(MAPBIOMAS_FOREST_CODES)
    df["is_agro"] = df["classe_codigo"].isin(MAPBIOMAS_AGRO_CODES)
    df["is_urban"] = df["classe_codigo"].isin(MAPBIOMAS_URBAN_CODES)

    agg = (
        df.groupby(["geocodigo", "ano"])
        .agg(
            area_total_ha=("area_ha", "sum"),
            area_nativa_ha=("area_ha", lambda x: x[df.loc[x.index, "is_native"]].sum()),
            area_florestal_ha=("area_ha", lambda x: x[df.loc[x.index, "is_forest"]].sum()),
            area_agro_ha=("area_ha", lambda x: x[df.loc[x.index, "is_agro"]].sum()),
            area_urbana_ha=("area_ha", lambda x: x[df.loc[x.index, "is_urban"]].sum()),
        )
        .reset_index()
    )

    agg["pct_nativa"] = agg["area_nativa_ha"] / agg["area_total_ha"].replace(0, float("nan")) * 100
    agg["pct_florestal"] = agg["area_florestal_ha"] / agg["area_total_ha"].replace(0, float("nan")) * 100
    agg["pct_agro"] = agg["area_agro_ha"] / agg["area_total_ha"].replace(0, float("nan")) * 100
    agg["pct_urbana"] = agg["area_urbana_ha"] / agg["area_total_ha"].replace(0, float("nan")) * 100

    return agg
