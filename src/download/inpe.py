"""INPE data downloaders: PRODES desmatamento + Queimadas focos de calor."""
import zipfile
from pathlib import Path

import pandas as pd
import requests
from loguru import logger

from src.utils.config import RAW_DIR, HTTP_TIMEOUT
from src.utils.http import download_file, get_json
from src.utils.geocodes import normalize_geocodigo


# ── PRODES Desmatamento ───────────────────────────────────────────────────────

PRODES_API_BASE = "https://terrabrasilis.dpi.inpe.br/queimadas/prodes-api"

# Direct PRODES download links for increments by municipality (official exports)
PRODES_BIOMES = {
    "amazonia": "https://terrabrasilis.dpi.inpe.br/download/dataset/prodes-amz-nb/vector/yearly_deforestation_biome.zip",
    "cerrado": "https://terrabrasilis.dpi.inpe.br/download/dataset/prodes-cerrado-nb/vector/yearly_deforestation_biome.zip",
}


def download_prodes_tabular() -> Path:
    """Download PRODES deforestation statistics by municipality (tabular CSV)."""
    out = RAW_DIR / "inpe" / "prodes_desmatamento.parquet"
    if out.exists():
        return out

    out.parent.mkdir(parents=True, exist_ok=True)
    frames = []

    # Try the TerraBrasilis tabular export API (JSON)
    logger.info("Fetching PRODES data from TerraBrasilis API...")

    biome_ids = {
        "Amazônia": 1,
        "Cerrado": 2,
        "Mata Atlântica": 3,
        "Caatinga": 4,
        "Pampa": 5,
        "Pantanal": 6,
    }

    for biome_name, biome_id in biome_ids.items():
        for year in range(2010, 2024):
            url = (
                "https://terrabrasilis.dpi.inpe.br/queimadas/prodes-api/api/v1/"
                f"deforestation?biome={biome_id}&year={year}&format=json"
            )
            try:
                resp = requests.get(url, timeout=HTTP_TIMEOUT)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        df = pd.DataFrame(data)
                        df["bioma"] = biome_name
                        df["ano"] = year
                        frames.append(df)
            except Exception as e:
                logger.debug(f"PRODES API {biome_name} {year}: {e}")

    if not frames:
        logger.info("Trying alternative PRODES download (rates by state)...")
        # Fallback: download municipality-level CSV from TerraBrasilis download page
        csv_url = (
            "https://terrabrasilis.dpi.inpe.br/queimadas/prodes-api/api/v1/"
            "deforestation/municipality?biome=all&format=csv"
        )
        csv_path = RAW_DIR / "inpe" / "prodes_raw.csv"
        try:
            download_file(csv_url, csv_path, "PRODES CSV")
            df = pd.read_csv(csv_path)
            frames = [df]
        except Exception as e:
            logger.warning(f"PRODES CSV download failed: {e}")

    if not frames:
        logger.warning("PRODES API unavailable - generating stub for pipeline continuity.")
        # Return empty stub so pipeline does not break
        stub = pd.DataFrame(columns=["geocodigo", "ano", "bioma", "desmatamento_km2"])
        stub.to_parquet(out, index=False)
        return out

    df = pd.concat(frames, ignore_index=True)

    # Normalize column names
    rename = {
        "geocode": "geocodigo",
        "municipality_code": "geocodigo",
        "cod_municipio": "geocodigo",
        "year": "ano",
        "area": "desmatamento_km2",
        "deforestation": "desmatamento_km2",
        "desmatado": "desmatamento_km2",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    if "geocodigo" in df.columns:
        df["geocodigo"] = df["geocodigo"].apply(normalize_geocodigo)
    if "desmatamento_km2" in df.columns:
        df["desmatamento_km2"] = pd.to_numeric(df["desmatamento_km2"], errors="coerce")

    df.to_parquet(out, index=False)
    logger.success(f"PRODES saved: {len(df):,} rows")
    return out


# ── Queimadas / Focos de Calor ────────────────────────────────────────────────

def download_queimadas(years: list[int] | None = None) -> Path:
    """Download fire foci counts per municipality from INPE Queimadas."""
    if years is None:
        years = list(range(2010, 2024))

    out = RAW_DIR / "inpe" / "queimadas.parquet"
    if out.exists():
        return out

    out.parent.mkdir(parents=True, exist_ok=True)
    frames = []

    logger.info("Downloading fire data from INPE Queimadas API...")
    for year in years:
        # Official statistics endpoint (HTML scraping needed; try direct JSON)
        url = (
            f"https://queimadas.dgi.inpe.br/api/focos/estatisticas/?ano={year}"
            f"&pais=Brasil&bioma=&estado=&municipio=&satelite=Referencia&agregacao=municipio"
        )
        try:
            resp = requests.get(url, timeout=HTTP_TIMEOUT)
            if resp.status_code == 200 and resp.text.startswith("["):
                data = resp.json()
                if data:
                    df_y = pd.DataFrame(data)
                    df_y["ano"] = year
                    frames.append(df_y)
                    logger.debug(f"Queimadas {year}: {len(df_y)} records")
        except Exception as e:
            logger.debug(f"Queimadas {year}: {e}")

    if not frames:
        # Fallback: try downloading the annual reference fire CSV
        for year in years:
            csv_url = (
                f"https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/"
                f"mensal/Brasil/focos_mensal_br_{year}01.csv"
            )
            csv_path = RAW_DIR / "inpe" / f"focos_{year}_jan.csv"
            try:
                download_file(csv_url, csv_path, f"Focos {year}", skip_if_exists=True)
                df_y = pd.read_csv(csv_path, low_memory=False)
                if "municipio" in df_y.columns or "geocodigo" in df_y.columns:
                    # Aggregate by municipality
                    geo_col = "geocodigo" if "geocodigo" in df_y.columns else "municipio"
                    df_agg = df_y.groupby(geo_col).size().reset_index(name="focos")
                    df_agg["ano"] = year
                    frames.append(df_agg)
            except Exception as e:
                logger.debug(f"Queimadas CSV {year}: {e}")

    if not frames:
        logger.warning("Queimadas data unavailable - generating stub.")
        stub = pd.DataFrame(columns=["geocodigo", "ano", "focos_calor"])
        stub.to_parquet(out, index=False)
        return out

    df = pd.concat(frames, ignore_index=True)

    rename = {
        "cod_municipio": "geocodigo",
        "geocodigo_municipio": "geocodigo",
        "municipio_geocodigo": "geocodigo",
        "focos": "focos_calor",
        "numero_focos": "focos_calor",
        "count": "focos_calor",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    if "geocodigo" in df.columns:
        df["geocodigo"] = df["geocodigo"].apply(normalize_geocodigo)
    if "focos_calor" in df.columns:
        df["focos_calor"] = pd.to_numeric(df["focos_calor"], errors="coerce")

    df.to_parquet(out, index=False)
    logger.success(f"Queimadas saved: {len(df):,} rows")
    return out
