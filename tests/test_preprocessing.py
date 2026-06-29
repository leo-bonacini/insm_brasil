"""Tests for preprocessing and cleaning functions."""
import pandas as pd
import pytest

from src.preprocessing.cleaner import clean_area, clean_pib, clean_populacao
from src.utils.geocodes import normalize_geocodigo

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def raw_pib_sidra():
    """Simulate raw SIDRA FLAT response for PIB."""
    return pd.DataFrame([
        {"D1C": "1100015", "D1N": "Alta Floresta D'Oeste - RO", "D2C": "2021", "D2N": "2021",
         "D3C": "37", "D3N": "PIB a preços correntes", "V": "498980", "NC": "6", "NN": "Município", "MC": "40", "MN": "Mil Reais"},
        {"D1C": "3550308", "D1N": "São Paulo - SP", "D2C": "2021", "D2N": "2021",
         "D3C": "37", "D3N": "PIB a preços correntes", "V": "850000000", "NC": "6", "NN": "Município", "MC": "40", "MN": "Mil Reais"},
        {"D1C": "5300108", "D1N": "Brasília - DF", "D2C": "2021", "D2N": "2021",
         "D3C": "37", "D3N": "PIB a preços correntes", "V": "..", "NC": "6", "NN": "Município", "MC": "40", "MN": "Mil Reais"},
    ])


@pytest.fixture
def raw_pop_sidra():
    return pd.DataFrame([
        {"D1C": "1100015", "D1N": "Alta Floresta D'Oeste", "D2C": "2021", "D2N": "2021",
         "D3C": "9324", "V": "23167", "NC": "6", "NN": "Município", "MC": "45", "MN": "Pessoas"},
        {"D1C": "3550308", "D1N": "São Paulo", "D2C": "2021", "D2N": "2021",
         "D3C": "9324", "V": "12400000", "NC": "6", "NN": "Município", "MC": "45", "MN": "Pessoas"},
    ])


@pytest.fixture
def raw_area():
    return pd.DataFrame([
        {"geocodigo": "1100015", "municipio": "Alta Floresta D'Oeste", "uf_sigla": "RO", "area_km2": 7067.127},
        {"geocodigo": "3550308", "municipio": "São Paulo", "uf_sigla": "SP", "area_km2": 1521.11},
        {"geocodigo": "5300108", "municipio": "Brasília", "uf_sigla": "DF", "area_km2": 5760.78},
    ])


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_clean_pib_basic(raw_pib_sidra):
    df = clean_pib(raw_pib_sidra)
    assert "geocodigo" in df.columns
    assert "pib_mil_reais" in df.columns
    assert "ano" in df.columns
    assert len(df) == 3  # NaN rows are kept (not dropped by default); ".." becomes NaN


def test_clean_pib_geocodigo_7digits(raw_pib_sidra):
    df = clean_pib(raw_pib_sidra)
    assert all(df["geocodigo"].str.len() == 7)


def test_clean_pib_numeric_values(raw_pib_sidra):
    df = clean_pib(raw_pib_sidra)
    assert df["pib_mil_reais"].dtype in [float, "float64"]
    assert df[df["geocodigo"] == "1100015"]["pib_mil_reais"].iloc[0] == 498980.0


def test_clean_populacao(raw_pop_sidra):
    df = clean_populacao(raw_pop_sidra)
    assert "populacao" in df.columns
    assert len(df) == 2
    assert df[df["geocodigo"] == "3550308"]["populacao"].iloc[0] == 12400000.0


def test_clean_area(raw_area):
    df = clean_area(raw_area)
    assert "geocodigo" in df.columns
    assert "area_km2" in df.columns
    assert len(df) == 3
    assert df["area_km2"].notna().all()


def test_clean_pib_empty():
    df = clean_pib(pd.DataFrame())
    assert df.empty


def test_normalize_geocodigo_7digits():
    assert normalize_geocodigo("1100015") == "1100015"
    assert normalize_geocodigo(1100015) == "1100015"
    assert normalize_geocodigo("11000150") == "1100015"  # truncate to 7


def test_normalize_geocodigo_float():
    assert normalize_geocodigo(3550308.0) == "3550308"


# ── Integration: full cleaning pipeline ──────────────────────────────────────

def test_clean_pipeline_integration(raw_pib_sidra, raw_pop_sidra, raw_area):
    pib = clean_pib(raw_pib_sidra)
    pop = clean_populacao(raw_pop_sidra)
    area = clean_area(raw_area)

    merged = area.set_index("geocodigo")
    pop_join = pop.drop(columns=[c for c in pop.columns if c in area.columns and c != "geocodigo"]).set_index("geocodigo")
    merged = merged.join(pop_join, how="left")
    pib_join = pib.drop(columns=[c for c in pib.columns if c in merged.columns and c != "geocodigo"]).set_index("geocodigo")
    merged = merged.join(pib_join, how="left")
    merged = merged.reset_index()

    assert len(merged) == 3
    assert "area_km2" in merged.columns
    assert "populacao" in merged.columns
    assert "pib_mil_reais" in merged.columns
