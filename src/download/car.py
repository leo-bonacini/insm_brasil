"""CAR (Cadastro Ambiental Rural) downloader."""
from pathlib import Path

import pandas as pd
import requests
from loguru import logger

from src.utils.config import HTTP_TIMEOUT, RAW_DIR
from src.utils.geocodes import normalize_geocodigo

CAR_API_BASE = "https://www.car.gov.br/api/v2"


def download_car_stats() -> Path:
    """Download CAR statistics aggregated by municipality."""
    out = RAW_DIR / "car" / "car_municipio.parquet"
    if out.exists():
        return out

    out.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Fetching CAR statistics from SICAR API...")
    frames = []

    # SICAR public API - national totals by municipality
    try:
        # Try the statistics endpoint
        api_url = "https://www.car.gov.br/api/v2/municipio/imoveis"
        resp = requests.get(api_url, timeout=HTTP_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                df = pd.DataFrame(data)
                frames.append(df)
    except Exception as e:
        logger.warning(f"CAR API: {e}")

    # Fallback: public statistics endpoint
    if not frames:
        try:
            stats_url = "https://www.car.gov.br/publico/imoveis/consolidado"
            resp = requests.get(stats_url, timeout=HTTP_TIMEOUT)
            if resp.status_code == 200 and "json" in resp.headers.get("content-type", ""):
                data = resp.json()
                if data:
                    df = pd.DataFrame(data if isinstance(data, list) else [data])
                    frames.append(df)
        except Exception as e:
            logger.debug(f"CAR stats fallback: {e}")

    if not frames:
        logger.warning("CAR data unavailable - generating stub.")
        stub = pd.DataFrame(columns=["geocodigo", "imoveis_cadastrados", "area_cadastrada_ha",
                                     "reserva_legal_ha", "app_ha", "vegetacao_nativa_ha"])
        stub.to_parquet(out, index=False)
        return out

    df = pd.concat(frames, ignore_index=True)
    rename = {
        "geocodigoMunicipio": "geocodigo",
        "codIbge": "geocodigo",
        "municipioId": "geocodigo",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "geocodigo" in df.columns:
        df["geocodigo"] = df["geocodigo"].apply(normalize_geocodigo)

    df.to_parquet(out, index=False)
    logger.success(f"CAR saved: {len(df):,} rows")
    return out
