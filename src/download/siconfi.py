"""Tesouro Nacional SICONFI / FINBRA downloader."""
from pathlib import Path

import pandas as pd
import requests
from loguru import logger

from src.utils.config import RAW_DIR, SICONFI_BASE, HTTP_TIMEOUT
from src.utils.geocodes import normalize_geocodigo


def download_finbra(years: list[int] | None = None) -> Path:
    """Download municipal finances (FINBRA) from SICONFI DataLake API."""
    if years is None:
        years = list(range(2015, 2023))

    out = RAW_DIR / "siconfi" / "finbra.parquet"
    if out.exists():
        return out

    out.parent.mkdir(parents=True, exist_ok=True)
    frames = []

    logger.info("Downloading FINBRA data from SICONFI API...")
    for year in years:
        # RREO (Relatório Resumido de Execução Orçamentária) - Demonstrativo da Receita
        url = (
            f"{SICONFI_BASE}/rreo"
            f"?an_exercicio={year}"
            f"&in_periodicidade=A"
            f"&co_tipo_demonstrativo=RREO"
            f"&no_municipio="
            f"&co_poder=E"  # Poder Executivo
        )
        try:
            resp = requests.get(url, timeout=HTTP_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", data) if isinstance(data, dict) else data
                if items:
                    df_y = pd.DataFrame(items)
                    df_y["ano"] = year
                    frames.append(df_y)
                    logger.debug(f"FINBRA {year}: {len(df_y)} records")
        except Exception as e:
            logger.warning(f"FINBRA {year}: {e}")

    if not frames:
        # Fallback: try DCA (Demonstrativo das Contas Anuais)
        for year in years:
            url = (
                f"{SICONFI_BASE}/dca"
                f"?an_exercicio={year}"
                f"&no_municipio="
                f"&co_tipo_demonstrativo=ANEXO I-LRF"
            )
            try:
                resp = requests.get(url, timeout=HTTP_TIMEOUT)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", data) if isinstance(data, dict) else data
                    if items:
                        df_y = pd.DataFrame(items)
                        df_y["ano"] = year
                        frames.append(df_y)
            except Exception as e:
                logger.debug(f"DCA {year}: {e}")

    if not frames:
        logger.warning("SICONFI unavailable - generating stub.")
        stub = pd.DataFrame(columns=["geocodigo", "ano", "receita_total", "gasto_ambiental"])
        stub.to_parquet(out, index=False)
        return out

    df = pd.concat(frames, ignore_index=True)

    rename = {
        "co_municipio_ibge": "geocodigo",
        "id_ente": "geocodigo",
        "co_ibge": "geocodigo",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    if "geocodigo" in df.columns:
        df["geocodigo"] = df["geocodigo"].apply(
            lambda x: normalize_geocodigo(x) if pd.notna(x) and str(x).strip() else x
        )

    df.to_parquet(out, index=False)
    logger.success(f"FINBRA saved: {len(df):,} rows")
    return out


def download_gastos_ambientais(years: list[int] | None = None) -> Path:
    """Download environmental spending (função 18 - Gestão Ambiental) from SICONFI."""
    if years is None:
        years = list(range(2015, 2023))

    out = RAW_DIR / "siconfi" / "gastos_ambientais.parquet"
    if out.exists():
        return out

    out.parent.mkdir(parents=True, exist_ok=True)
    frames = []

    logger.info("Downloading environmental spending (função 18) from SICONFI...")
    for year in years:
        url = (
            f"{SICONFI_BASE}/rreo"
            f"?an_exercicio={year}"
            f"&in_periodicidade=A"
            f"&co_tipo_demonstrativo=RREO"
            f"&co_funcao=18"
        )
        try:
            resp = requests.get(url, timeout=HTTP_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", data) if isinstance(data, dict) else data
                if items:
                    df_y = pd.DataFrame(items)
                    df_y["ano"] = year
                    frames.append(df_y)
        except Exception as e:
            logger.debug(f"Gastos ambientais {year}: {e}")

    if not frames:
        stub = pd.DataFrame(columns=["geocodigo", "ano", "gasto_ambiental_reais"])
        stub.to_parquet(out, index=False)
        return out

    df = pd.concat(frames, ignore_index=True)
    rename = {"co_municipio_ibge": "geocodigo", "id_ente": "geocodigo"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "geocodigo" in df.columns:
        df["geocodigo"] = df["geocodigo"].apply(
            lambda x: normalize_geocodigo(x) if pd.notna(x) else x
        )

    df.to_parquet(out, index=False)
    logger.success(f"Gastos ambientais saved: {len(df):,} rows")
    return out
