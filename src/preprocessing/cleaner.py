"""Clean and standardize raw SIDRA/API data into normalized DataFrames."""
import pandas as pd
from loguru import logger

from src.utils.geocodes import normalize_geocodigo


def clean_sidra(df: pd.DataFrame, value_col: str, name_col: str | None = None) -> pd.DataFrame:
    """Normalize a raw SIDRA flat-view DataFrame.

    SIDRA returns columns like D1C (municipality code), D1N (name), D2C/D2N (year),
    V (value). Maps them to geocodigo, municipio, ano, <value_col>.
    """
    if df.empty:
        return df

    rename = {
        "D1C": "geocodigo",
        "D1N": "municipio",
        "D2C": "ano",
        "V": value_col,
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    if "geocodigo" not in df.columns:
        logger.warning("geocodigo column missing after rename.")
        return pd.DataFrame()

    df["geocodigo"] = df["geocodigo"].astype(str).apply(normalize_geocodigo)
    df["ano"] = pd.to_numeric(df.get("ano", pd.Series()), errors="coerce").astype("Int64")
    df[value_col] = pd.to_numeric(df[value_col].replace("..", None), errors="coerce")

    keep = ["geocodigo", "ano", value_col]
    if "municipio" in df.columns:
        keep.insert(1, "municipio")

    return df[keep].dropna(subset=["geocodigo", "ano"]).copy()


def clean_pib(df: pd.DataFrame) -> pd.DataFrame:
    """Clean PIB Municipal: return geocodigo, municipio, ano, pib_mil_reais."""
    return clean_sidra(df, value_col="pib_mil_reais")


def clean_populacao(df: pd.DataFrame) -> pd.DataFrame:
    """Clean population: return geocodigo, municipio, ano, populacao."""
    return clean_sidra(df, value_col="populacao")


def clean_pam(df: pd.DataFrame) -> pd.DataFrame:
    """Clean PAM: pivot variables 214/215/216 into wide format per municipality/year."""
    if df.empty:
        return df

    rename = {
        "D1C": "geocodigo",
        "D1N": "municipio",
        "D2C": "ano",
        "D3C": "variavel_codigo",
        "D3N": "variavel_nome",
        "V": "valor",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    df["geocodigo"] = df["geocodigo"].astype(str).apply(normalize_geocodigo)
    df["ano"] = pd.to_numeric(df.get("ano"), errors="coerce").astype("Int64")
    df["valor"] = pd.to_numeric(df["valor"].replace("..", None), errors="coerce")
    df["variavel_codigo"] = pd.to_numeric(df.get("variavel_codigo"), errors="coerce").astype("Int64")

    var_names = {214: "producao_ton", 215: "valor_producao_mil", 216: "area_plantada_ha"}
    df["variavel_nome_clean"] = df["variavel_codigo"].map(var_names)
    df = df.dropna(subset=["variavel_nome_clean", "valor"])

    wide = df.pivot_table(
        index=["geocodigo", "ano"],
        columns="variavel_nome_clean",
        values="valor",
        aggfunc="sum",
    ).reset_index()
    wide.columns.name = None
    return wide


def clean_ppm(df: pd.DataFrame) -> pd.DataFrame:
    """Clean PPM: return geocodigo, ano, rebanho_total."""
    return clean_sidra(df, value_col="rebanho_total")


def clean_area(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize area territorial."""
    df = df.copy()
    if "geocodigo" not in df.columns:
        return df
    df["geocodigo"] = df["geocodigo"].astype(str).apply(normalize_geocodigo)
    df["area_km2"] = pd.to_numeric(df["area_km2"], errors="coerce")
    return df[["geocodigo", "municipio", "uf_sigla", "area_km2"]].dropna(subset=["geocodigo"])
