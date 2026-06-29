"""INEP data downloaders: IDEB and Censo Escolar."""
from pathlib import Path

import pandas as pd
from loguru import logger

from src.utils.config import RAW_DIR
from src.utils.geocodes import normalize_geocodigo
from src.utils.http import download_file

IDEB_URLS = {
    2021: "https://download.inep.gov.br/educacao_basica/portal_ideb/planilhas_para_download/2021/divulgacao_anos_iniciais_municipios_2021.xlsx",
    2019: "https://download.inep.gov.br/educacao_basica/portal_ideb/planilhas_para_download/2019/divulgacao_anos_iniciais_municipios_2019.xlsx",
    2017: "https://download.inep.gov.br/educacao_basica/portal_ideb/planilhas_para_download/2017/divulgacao_anos_iniciais_municipios_2017.xlsx",
    2015: "https://download.inep.gov.br/educacao_basica/portal_ideb/planilhas_para_download/2015/divulgacao_anos_iniciais_municipios_2015.xlsx",
    2013: "https://download.inep.gov.br/educacao_basica/portal_ideb/planilhas_para_download/2013/divulgacao_anos_iniciais_municipios_2013.xlsx",
}


def download_ideb() -> Path:
    """Download IDEB scores by municipality."""
    out = RAW_DIR / "inep" / "ideb.parquet"
    if out.exists():
        return out

    out.parent.mkdir(parents=True, exist_ok=True)
    frames = []

    for year, url in IDEB_URLS.items():
        xlsx_path = RAW_DIR / "inep" / f"ideb_{year}.xlsx"
        try:
            download_file(url, xlsx_path, f"IDEB {year}")
            # IDEB files have header rows; data starts around row 10
            for skip in [9, 10, 8, 7]:
                try:
                    df = pd.read_excel(xlsx_path, skiprows=skip, dtype=str)
                    # Find column with municipality code
                    geo_col = None
                    for c in df.columns:
                        sample = df[c].dropna().head(20).tolist()
                        if any(str(v).isdigit() and len(str(v)) in [6, 7] for v in sample):
                            geo_col = c
                            break
                    if geo_col:
                        df = df.rename(columns={geo_col: "geocodigo"})
                        df["ano"] = year
                        frames.append(df)
                        logger.debug(f"IDEB {year}: {len(df)} rows (skip={skip})")
                        break
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"IDEB {year}: {e}")

    if not frames:
        stub = pd.DataFrame(columns=["geocodigo", "ano", "ideb"])
        stub.to_parquet(out, index=False)
        return out

    df = pd.concat(frames, ignore_index=True)
    if "geocodigo" in df.columns:
        df["geocodigo"] = df["geocodigo"].apply(
            lambda x: normalize_geocodigo(x) if pd.notna(x) and str(x).strip().isdigit() else None
        )
        df = df.dropna(subset=["geocodigo"])

    df.to_parquet(out, index=False)
    logger.success(f"IDEB saved: {len(df):,} rows")
    return out
