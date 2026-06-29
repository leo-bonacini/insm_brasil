"""ETL pipeline: clean raw data, compute features, build DuckDB data warehouse."""
import sys
from pathlib import Path

import duckdb
import pandas as pd
from loguru import logger

from src.utils.config import DUCKDB_PATH, PARQUET_DIR, RAW_DIR, ensure_dirs
from src.preprocessing.cleaner import clean_pib, clean_populacao, clean_pam, clean_ppm, clean_area
from src.feature_engineering.indicators import compute_base_indicators, compute_temporal_change


def load_raw() -> dict[str, pd.DataFrame]:
    """Load all available raw parquet files."""
    sources = {
        "pib": RAW_DIR / "ibge" / "pib_municipal.parquet",
        "pop": RAW_DIR / "ibge" / "populacao.parquet",
        "area": RAW_DIR / "ibge" / "area_territorial.parquet",
        "pam": RAW_DIR / "ibge" / "pam.parquet",
        "ppm": RAW_DIR / "ibge" / "ppm.parquet",
        "mapbiomas": RAW_DIR / "mapbiomas" / "mapbiomas_col9_municipio.parquet",
        "prodes": RAW_DIR / "inpe" / "prodes_desmatamento.parquet",
        "queimadas": RAW_DIR / "inpe" / "queimadas.parquet",
        "finbra": RAW_DIR / "siconfi" / "finbra.parquet",
        "ideb": RAW_DIR / "inep" / "ideb.parquet",
        "car": RAW_DIR / "car" / "car_municipio.parquet",
    }
    dfs = {}
    for name, path in sources.items():
        if path.exists():
            df = pd.read_parquet(path)
            dfs[name] = df
            rows = len(df)
            status = "REAL" if rows > 100 else "STUB"
            logger.info(f"[{status}] {name}: {rows:,} rows")
        else:
            logger.warning(f"Missing: {path}")
            dfs[name] = pd.DataFrame()
    return dfs


def clean_all(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Apply cleaning/normalization to all raw DataFrames."""
    return {
        "pib":       clean_pib(raw["pib"]),
        "pop":       clean_populacao(raw["pop"]),
        "area":      clean_area(raw["area"]),
        "pam":       clean_pam(raw["pam"]),
        "ppm":       clean_ppm(raw["ppm"]),
        "mapbiomas": raw["mapbiomas"],
        "prodes":    raw["prodes"],
        "queimadas": raw["queimadas"],
        "finbra":    raw["finbra"],
        "ideb":      raw["ideb"],
        "car":       raw["car"],
    }


def build_fact_tables(clean: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Build star-schema fact and dimension tables."""
    fact_tables = {}

    # dim_city: one row per municipality
    fact_tables["dim_city"] = clean["area"].copy()

    # fact_economy: pib + population + agro + livestock per municipality/year
    economy = clean["pib"].merge(clean["pop"], on=["geocodigo", "ano"], how="outer", suffixes=("", "_pop"))
    # Remove duplicate municipio columns
    if "municipio_pop" in economy.columns:
        economy = economy.drop(columns=["municipio_pop"])
    if not clean["pam"].empty and "geocodigo" in clean["pam"].columns:
        economy = economy.merge(clean["pam"], on=["geocodigo", "ano"], how="left")
    if not clean["ppm"].empty:
        economy = economy.merge(clean["ppm"], on=["geocodigo", "ano"], how="left")
    fact_tables["fact_economy"] = economy

    # fact_environment: MapBiomas coverage + PRODES + Queimadas
    mapbiomas = clean["mapbiomas"]
    if not mapbiomas.empty and "classe_codigo" in mapbiomas.columns:
        from src.feature_engineering.indicators import _aggregate_mapbiomas
        # Build per-year environmental facts
        year_frames = []
        for year in sorted(mapbiomas["ano"].dropna().unique()):
            mb_y = mapbiomas[mapbiomas["ano"] == year]
            if len(mb_y) < 100:
                continue
            agg = _aggregate_mapbiomas(mb_y).reset_index()
            agg["ano"] = int(year)
            year_frames.append(agg)
        if year_frames:
            fact_tables["fact_environment"] = pd.concat(year_frames, ignore_index=True)
        else:
            fact_tables["fact_environment"] = pd.DataFrame()
    else:
        fact_tables["fact_environment"] = pd.DataFrame()

    # fact_education: IDEB
    fact_tables["fact_education"] = clean["ideb"].copy()

    return fact_tables


def build_master_table(clean: dict[str, pd.DataFrame], ref_year: int = 2021) -> pd.DataFrame:
    """Build the master analytical table with all indicators for index construction."""
    logger.info(f"Building master table for ref_year={ref_year}...")
    df = compute_base_indicators(
        pib=clean["pib"],
        pop=clean["pop"],
        area=clean["area"],
        pam=clean["pam"],
        ppm=clean["ppm"],
        mapbiomas=clean["mapbiomas"],
        ref_year=ref_year,
    )

    # Add temporal change in vegetation
    if not clean["mapbiomas"].empty:
        change = compute_temporal_change(clean["mapbiomas"], year_start=2015, year_end=ref_year)
        if not change.empty and "geocodigo" in change.columns:
            df = df.merge(change, on="geocodigo", how="left")

    return df


def save_to_parquet(fact_tables: dict[str, pd.DataFrame], master: pd.DataFrame) -> None:
    """Save all fact tables and master table as Parquet."""
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in fact_tables.items():
        if not df.empty:
            out = PARQUET_DIR / f"{name}.parquet"
            df.to_parquet(out, index=False)
            logger.success(f"Saved {name}: {len(df):,} rows → {out}")

    master_path = PARQUET_DIR / "master_indicators.parquet"
    master.to_parquet(master_path, index=False)
    logger.success(f"Saved master_indicators: {len(master):,} rows → {master_path}")


def save_to_duckdb(fact_tables: dict[str, pd.DataFrame], master: pd.DataFrame) -> None:
    """Register all tables in DuckDB for analytical queries."""
    con = duckdb.connect(str(DUCKDB_PATH))
    for name, df in fact_tables.items():
        if not df.empty:
            con.register(name, df)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM {name}")
            logger.success(f"DuckDB: {name} ({len(df):,} rows)")

    con.register("master_indicators", master)
    con.execute("CREATE OR REPLACE TABLE master_indicators AS SELECT * FROM master_indicators")
    logger.success(f"DuckDB: master_indicators ({len(master):,} rows)")
    con.close()


def run_transform() -> pd.DataFrame:
    """Full ETL: load → clean → features → save."""
    ensure_dirs()
    raw = load_raw()
    clean = clean_all(raw)
    fact_tables = build_fact_tables(clean)
    master = build_master_table(clean)
    save_to_parquet(fact_tables, master)
    save_to_duckdb(fact_tables, master)
    return master


if __name__ == "__main__":
    master = run_transform()
    logger.info(f"\nMaster table shape: {master.shape}")
    logger.info(f"Columns: {master.columns.tolist()}")
    logger.info(f"\nSample:\n{master.head(3).to_string()}")
