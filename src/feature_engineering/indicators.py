"""Compute derived sustainability indicators from cleaned data."""
import numpy as np
import pandas as pd
from loguru import logger

from src.utils.config import MAPBIOMAS_NATIVE_VEGETATION_CODES, MAPBIOMAS_FOREST_CODES, MAPBIOMAS_AGRO_CODES, MAPBIOMAS_URBAN_CODES


def compute_base_indicators(
    pib: pd.DataFrame,
    pop: pd.DataFrame,
    area: pd.DataFrame,
    pam: pd.DataFrame,
    ppm: pd.DataFrame,
    mapbiomas: pd.DataFrame,
    ref_year: int = 2021,
) -> pd.DataFrame:
    """Build the base feature table for a given reference year.

    Returns a DataFrame indexed by geocodigo with all computable indicators.
    """
    logger.info(f"Computing base indicators for year {ref_year}...")

    # ── 1. Filter reference year ─────────────────────────────────────────────
    pib_y = pib[pib["ano"] == ref_year][["geocodigo", "pib_mil_reais"]].drop_duplicates("geocodigo")
    pop_y = pop[pop["ano"] == ref_year][["geocodigo", "municipio", "populacao"]].drop_duplicates("geocodigo")
    pam_y = pam[pam["ano"] == ref_year].drop_duplicates("geocodigo") if not pam.empty else pd.DataFrame()
    ppm_y = ppm[ppm["ano"] == ref_year][["geocodigo", "rebanho_total"]].drop_duplicates("geocodigo") if not ppm.empty else pd.DataFrame()

    # ── 2. MapBiomas: aggregate by municipality (use closest year available) ─
    mb_year = ref_year
    if not mapbiomas.empty and "ano" in mapbiomas.columns:
        avail_years = mapbiomas["ano"].dropna().unique().tolist()
        if ref_year not in avail_years:
            mb_year = max([y for y in avail_years if y <= ref_year], default=avail_years[-1])
        mb_y = mapbiomas[mapbiomas["ano"] == mb_year].copy()
    else:
        mb_y = mapbiomas.copy()

    mb_agg = _aggregate_mapbiomas(mb_y) if not mb_y.empty else pd.DataFrame()

    # ── 3. Join all datasets ─────────────────────────────────────────────────
    df = area.set_index("geocodigo")
    # Drop duplicate columns before joining
    pop_join = pop_y.drop(columns=[c for c in pop_y.columns if c in area.columns and c != "geocodigo"]).set_index("geocodigo")
    df = df.join(pop_join, how="left")
    df = df.join(pib_y.set_index("geocodigo"), how="left")

    if not pam_y.empty:
        df = df.join(pam_y.set_index("geocodigo"), how="left")
    if not ppm_y.empty:
        df = df.join(ppm_y.set_index("geocodigo"), how="left")
    if not mb_agg.empty:
        df = df.join(mb_agg, how="left")

    df = df.reset_index().rename(columns={"index": "geocodigo"})

    # ── 4. Derived indicators ────────────────────────────────────────────────
    df = _compute_derived(df)

    logger.success(f"Base indicators computed: {len(df):,} municipalities, {len(df.columns)} features")
    return df


def _aggregate_mapbiomas(mb: pd.DataFrame) -> pd.DataFrame:
    """Aggregate MapBiomas by municipality: total area and per-class percentages."""
    mb = mb.copy()
    mb["classe_codigo"] = pd.to_numeric(mb["classe_codigo"], errors="coerce")
    mb["area_ha"] = pd.to_numeric(mb["area_ha"], errors="coerce").fillna(0)

    mb["is_native"] = mb["classe_codigo"].isin(MAPBIOMAS_NATIVE_VEGETATION_CODES)
    mb["is_forest"] = mb["classe_codigo"].isin(MAPBIOMAS_FOREST_CODES)
    mb["is_agro"] = mb["classe_codigo"].isin(MAPBIOMAS_AGRO_CODES)
    mb["is_urban"] = mb["classe_codigo"].isin(MAPBIOMAS_URBAN_CODES)

    agg = (
        mb.groupby("geocodigo")
        .apply(lambda g: pd.Series({
            "mb_total_ha": g["area_ha"].sum(),
            "mb_nativa_ha": g.loc[g["is_native"], "area_ha"].sum(),
            "mb_florestal_ha": g.loc[g["is_forest"], "area_ha"].sum(),
            "mb_agro_ha": g.loc[g["is_agro"], "area_ha"].sum(),
            "mb_urbana_ha": g.loc[g["is_urban"], "area_ha"].sum(),
        }))
        .reset_index()
        .set_index("geocodigo")
    )

    total = agg["mb_total_ha"].replace(0, np.nan)
    agg["pct_nativa"] = agg["mb_nativa_ha"] / total * 100
    agg["pct_florestal"] = agg["mb_florestal_ha"] / total * 100
    agg["pct_agro"] = agg["mb_agro_ha"] / total * 100
    agg["pct_urbana"] = agg["mb_urbana_ha"] / total * 100

    return agg


def _compute_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-capita and per-km² derived indicators."""
    df = df.copy()

    pop = df["populacao"].replace(0, np.nan)
    area = df["area_km2"].replace(0, np.nan)
    pib = df["pib_mil_reais"].replace(0, np.nan)

    # Economic
    df["pib_per_capita"] = pib * 1000 / pop          # R$ per capita
    df["pib_por_km2"] = pib * 1000 / area             # R$ per km²
    df["densidade_pop"] = pop / area                   # habitantes/km²

    # Agricultural
    if "area_plantada_ha" in df.columns:
        df["pct_agricola_area"] = df["area_plantada_ha"] / (area * 100) * 100  # area km² to ha
    if "rebanho_total" in df.columns:
        df["rebanho_por_km2"] = df["rebanho_total"] / area

    # Vegetation (from MapBiomas)
    if "pct_nativa" in df.columns:
        df["indice_conservacao"] = df["pct_nativa"]
    if "pct_florestal" in df.columns:
        df["indice_florestal"] = df["pct_florestal"]
    if "pct_agro" in df.columns and "pct_nativa" in df.columns:
        # Pressure index: more agriculture/less native = more pressure
        df["indice_pressao_ambiental"] = df["pct_agro"] / (df["pct_nativa"].replace(0, np.nan) + 1)

    return df


def compute_temporal_change(mapbiomas: pd.DataFrame, year_start: int = 2015, year_end: int = 2021) -> pd.DataFrame:
    """Compute change in native vegetation cover between two years."""
    if mapbiomas.empty or "ano" not in mapbiomas.columns:
        return pd.DataFrame()

    def get_native_pct(year: int) -> pd.Series:
        mb_y = mapbiomas[mapbiomas["ano"] == year].copy()
        if mb_y.empty:
            return pd.Series(dtype=float, name=f"pct_nativa_{year}")
        mb_y["is_native"] = mb_y["classe_codigo"].isin(MAPBIOMAS_NATIVE_VEGETATION_CODES)
        mb_y["area_ha"] = pd.to_numeric(mb_y["area_ha"], errors="coerce").fillna(0)
        agg = mb_y.groupby("geocodigo").apply(lambda g: pd.Series({
            "native_ha": g.loc[g["is_native"], "area_ha"].sum(),
            "total_ha": g["area_ha"].sum(),
        }))
        agg[f"pct_nativa_{year}"] = agg["native_ha"] / agg["total_ha"].replace(0, np.nan) * 100
        return agg[f"pct_nativa_{year}"]

    s_start = get_native_pct(year_start)
    s_end = get_native_pct(year_end)

    change = pd.DataFrame({
        f"pct_nativa_{year_start}": s_start,
        f"pct_nativa_{year_end}": s_end,
    })
    change["variacao_nativa_pp"] = change[f"pct_nativa_{year_end}"] - change[f"pct_nativa_{year_start}"]
    change["taxa_variacao_nativa_pct"] = (
        change["variacao_nativa_pp"] / change[f"pct_nativa_{year_start}"].replace(0, np.nan) * 100
    )
    return change.reset_index()
