"""IBGE data downloaders: SIDRA API, shapefiles, PIB, population, PAM, PPM."""
import zipfile
from pathlib import Path

import pandas as pd
from loguru import logger

from src.utils.config import (
    EXTERNAL_DIR,
    IBGE_BIOMAS_ZIP,
    IBGE_MUNICIPIOS_ZIP,
    IBGE_SIDRA_BASE,
    IBGE_SIDRA_MUNICIPIOS,
    RAW_DIR,
)
from src.utils.http import download_file, get_json
from src.utils.geocodes import normalize_geocodigo


# ── SIDRA helper ──────────────────────────────────────────────────────────────

UF_CODES = [11,12,13,14,15,16,17,21,22,23,24,25,26,27,28,29,31,32,33,35,41,42,43,50,51,52,53]


def _sidra_query_all_municipalities(
    table: int,
    variable: str,
    periodo: str,
) -> pd.DataFrame:
    """Fetch SIDRA data for ALL municipalities by querying UF by UF.

    The SIDRA v3 API returns 500 for N6[all]; the workaround is N6[N3[uf_code]].
    """
    frames = []
    for uf in UF_CODES:
        localidade = f"N6[N3[{uf}]]"
        url = (
            f"{IBGE_SIDRA_BASE}/{table}/periodos/{periodo}"
            f"/variaveis/{variable}"
            f"?localidades={localidade}"
            f"&formato=json&view=flat"
        )
        try:
            raw = get_json(url)
            if raw and len(raw) > 1:
                frames.append(pd.DataFrame(raw[1:]))
        except Exception as e:
            logger.debug(f"SIDRA {table} UF {uf} {periodo}: {e}")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ── PIB Municipal ─────────────────────────────────────────────────────────────

def download_pib_municipal(years: list[int] | None = None) -> Path:
    """Download PIB Municipal from SIDRA table 5938."""
    if years is None:
        years = list(range(2010, 2022))

    out = RAW_DIR / "ibge" / "pib_municipal.parquet"
    if out.exists():
        logger.info("PIB Municipal already downloaded.")
        return out

    logger.info(f"Downloading PIB Municipal (table 5938) for {years[0]}-{years[-1]}...")

    # Variable 37 = PIB a preços correntes (mil reais)
    frames = []
    for y in years:
        df_y = _sidra_query_all_municipalities(table=5938, variable="37", periodo=str(y))
        if not df_y.empty:
            frames.append(df_y)
            logger.info(f"PIB {y}: {len(df_y)} municipalities")
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    if df.empty:
        logger.error("Could not download PIB data from SIDRA.")
        return out

    # Rename standard SIDRA columns
    col_map = {
        "Município (Código)": "geocodigo",
        "Município": "municipio",
        "Ano": "ano",
        "Valor": "valor",
        "Variável": "variavel",
        "Variável (Código)": "variavel_codigo",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    if "geocodigo" in df.columns:
        df["geocodigo"] = df["geocodigo"].apply(normalize_geocodigo)
    if "valor" in df.columns:
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    logger.success(f"PIB Municipal saved: {out} ({len(df):,} rows)")
    return out


# ── População ─────────────────────────────────────────────────────────────────

def download_populacao(years: list[int] | None = None) -> Path:
    """Download estimated population from SIDRA table 6579."""
    if years is None:
        years = list(range(2010, 2024))

    out = RAW_DIR / "ibge" / "populacao.parquet"
    if out.exists():
        logger.info("Population data already downloaded.")
        return out

    logger.info("Downloading population estimates from SIDRA...")
    frames = []
    for y in years:
        df_y = _sidra_query_all_municipalities(table=6579, variable="9324", periodo=str(y))
        if not df_y.empty:
            frames.append(df_y)
            logger.info(f"Population {y}: {len(df_y)} rows")

    if not frames:
        logger.warning("Using fallback population table 202 (Censo)...")
        for y in [2010, 2022]:
            df_y = _sidra_query_all_municipalities(table=202, variable="93", periodo=str(y))
            if not df_y.empty:
                frames.append(df_y)

    if not frames:
        logger.error("Could not download population data.")
        return out

    df = pd.concat(frames, ignore_index=True)
    col_map = {
        "Município (Código)": "geocodigo",
        "Município": "municipio",
        "Ano": "ano",
        "Valor": "populacao",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    if "geocodigo" in df.columns:
        df["geocodigo"] = df["geocodigo"].apply(normalize_geocodigo)
    if "populacao" in df.columns:
        df["populacao"] = pd.to_numeric(df["populacao"], errors="coerce")

    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    logger.success(f"Population saved: {out} ({len(df):,} rows)")
    return out


# ── Área Territorial ──────────────────────────────────────────────────────────

def download_area_territorial() -> Path:
    """Download municipal area from IBGE SIDRA (table 9601) and localidades API."""
    out = RAW_DIR / "ibge" / "area_territorial.parquet"
    if out.exists():
        return out

    out.parent.mkdir(parents=True, exist_ok=True)

    # Try SIDRA table 9601 (area - Censo 2022)
    logger.info("Downloading area territorial from SIDRA table 9601...")
    df = _sidra_query_all_municipalities(table=9601, variable="606", periodo="2022")

    if df.empty:
        # Fallback: IBGE geoftp XLS (try different years)
        for year in [2023, 2022, 2021, 2020]:
            xlsx_url = (
                f"https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/"
                f"areas_territoriais/{year}/AR_BR_RG_UF_RGINT_RGIME_MES_MIC_MUN_{year}.xlsx"
            )
            xlsx_path = RAW_DIR / "ibge" / f"area_territorial_{year}.xlsx"
            try:
                download_file(xlsx_url, xlsx_path, f"Área territorial {year}")
                xl = pd.ExcelFile(xlsx_path)
                sheet = next((s for s in xl.sheet_names if "MUN" in s.upper()), xl.sheet_names[-1])
                df = pd.read_excel(xlsx_path, sheet_name=sheet)
                if len(df) > 100:
                    break
            except Exception as e:
                logger.debug(f"Area {year}: {e}")

    if df.empty:
        # Last resort: compute from shapefile after download
        logger.warning("Area territorial not available from direct download. Will compute from shapefile.")
        stub = pd.DataFrame(columns=["geocodigo", "municipio", "area_km2"])
        stub.to_parquet(out, index=False)
        return out

    # Normalize from SIDRA format
    rename = {
        "D1C": "geocodigo",
        "D1N": "municipio",
        "V": "area_km2",
        "CD_MUN": "geocodigo",
        "NM_MUN": "municipio",
        "AR_MUN_2022": "area_km2",
        "AR_MUN_2023": "area_km2",
        "AR_MUN_2021": "area_km2",
        "AR_MUN_2020": "area_km2",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "geocodigo" in df.columns:
        df["geocodigo"] = df["geocodigo"].astype(str).apply(normalize_geocodigo)
    if "area_km2" in df.columns:
        df["area_km2"] = pd.to_numeric(df["area_km2"], errors="coerce")

    cols = [c for c in ["geocodigo", "municipio", "area_km2"] if c in df.columns]
    df[cols].to_parquet(out, index=False)
    logger.success(f"Area territorial saved: {len(df):,} municipalities")
    return out


# ── Shapefile Municipal ───────────────────────────────────────────────────────

def download_shapefile_municipios() -> Path:
    """Download and extract IBGE 2022 municipal shapefile."""
    shp_dir = EXTERNAL_DIR / "ibge" / "municipios_2022"
    shp_file = shp_dir / "BR_Municipios_2022.shp"
    if shp_file.exists():
        return shp_file

    zip_path = EXTERNAL_DIR / "ibge" / "BR_Municipios_2022.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    download_file(IBGE_MUNICIPIOS_ZIP, zip_path, "Shapefile municípios")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(shp_dir)
    logger.success(f"Shapefile extracted to: {shp_dir}")
    return shp_file


# ── Shapefile Biomas ─────────────────────────────────────────────────────────

def download_shapefile_biomas() -> Path:
    """Download and extract IBGE biomes shapefile."""
    biomas_dir = EXTERNAL_DIR / "ibge" / "biomas"
    shp_candidates = list(biomas_dir.glob("*.shp"))
    if shp_candidates:
        return shp_candidates[0]

    zip_path = EXTERNAL_DIR / "ibge" / "Biomas_250mil.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    download_file(IBGE_BIOMAS_ZIP, zip_path, "Shapefile biomas")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(biomas_dir)
    shp_candidates = list(biomas_dir.glob("*.shp"))
    return shp_candidates[0] if shp_candidates else biomas_dir


# ── Produção Agrícola Municipal ────────────────────────────────────────────────

def download_pam(years: list[int] | None = None) -> Path:
    """Download Produção Agrícola Municipal (PAM) from SIDRA table 5457."""
    if years is None:
        years = list(range(2012, 2022))

    out = RAW_DIR / "ibge" / "pam.parquet"
    if out.exists():
        return out

    logger.info("Downloading PAM from SIDRA table 5457...")
    frames = []
    for y in years:
        df_y = _sidra_query_all_municipalities(table=5457, variable="214|215|216", periodo=str(y))
        if not df_y.empty:
            df_y["_year"] = y
            frames.append(df_y)
            logger.info(f"PAM {y}: {len(df_y)} rows")

    if not frames:
        logger.warning("PAM data unavailable.")
        return out

    df = pd.concat(frames, ignore_index=True)
    col_map = {
        "Município (Código)": "geocodigo",
        "Ano": "ano",
        "Valor": "valor",
        "Variável": "variavel",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    if "geocodigo" in df.columns:
        df["geocodigo"] = df["geocodigo"].apply(normalize_geocodigo)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    logger.success(f"PAM saved: {len(df):,} rows")
    return out


# ── Produção Pecuária Municipal ───────────────────────────────────────────────

def download_ppm(years: list[int] | None = None) -> Path:
    """Download Produção Pecuária Municipal (PPM) from SIDRA table 3939."""
    if years is None:
        years = list(range(2012, 2022))

    out = RAW_DIR / "ibge" / "ppm.parquet"
    if out.exists():
        return out

    logger.info("Downloading PPM from SIDRA table 3939...")
    frames = []
    for y in years:
        df_y = _sidra_query_all_municipalities(table=3939, variable="105", periodo=str(y))
        if not df_y.empty:
            df_y["_year"] = y
            frames.append(df_y)
            logger.info(f"PPM {y}: {len(df_y)} rows")

    if not frames:
        return out

    df = pd.concat(frames, ignore_index=True)
    col_map = {"Município (Código)": "geocodigo", "Ano": "ano", "Valor": "rebanho_total"}
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    if "geocodigo" in df.columns:
        df["geocodigo"] = df["geocodigo"].apply(normalize_geocodigo)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    logger.success(f"PPM saved: {len(df):,} rows")
    return out
