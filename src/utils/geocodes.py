"""IBGE geocode utilities."""
from functools import lru_cache

import pandas as pd
import requests
from loguru import logger

from src.utils.config import IBGE_LOCALIDADES_BASE


@lru_cache(maxsize=1)
def load_municipios() -> pd.DataFrame:
    """Load all Brazilian municipalities from IBGE API."""
    url = f"{IBGE_LOCALIDADES_BASE}/municipios"
    logger.info("Loading municipality list from IBGE API...")
    data = requests.get(url, timeout=30).json()
    df = pd.json_normalize(data)
    df = df.rename(columns={
        "id": "geocodigo",
        "nome": "municipio",
        "microrregiao.mesorregiao.UF.id": "uf_id",
        "microrregiao.mesorregiao.UF.sigla": "uf_sigla",
        "microrregiao.mesorregiao.UF.nome": "uf_nome",
        "regiao-imediata.regiao-intermediaria.macrorregiao.id": "regiao_id",
        "regiao-imediata.regiao-intermediaria.macrorregiao.sigla": "regiao_sigla",
        "regiao-imediata.regiao-intermediaria.macrorregiao.nome": "regiao_nome",
    })
    df["geocodigo"] = df["geocodigo"].astype(str).str[:7]
    logger.success(f"Loaded {len(df)} municipalities")
    return df[["geocodigo", "municipio", "uf_id", "uf_sigla", "uf_nome", "regiao_sigla", "regiao_nome"]].copy()


def normalize_geocodigo(code) -> str:
    """Normalize any municipality code to 7-digit string."""
    s = str(int(float(str(code))))
    return s[:7] if len(s) >= 7 else s.zfill(7)


def get_uf_codes() -> list[int]:
    """Return all UF IBGE codes."""
    url = f"{IBGE_LOCALIDADES_BASE}/estados"
    data = requests.get(url, timeout=30).json()
    return [uf["id"] for uf in data]
