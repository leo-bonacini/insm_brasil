"""Central configuration and path management."""
from pathlib import Path
import os

# Project root: the insm_brasil directory
ROOT = Path(__file__).parent.parent.parent.resolve()

# Data directories
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"
PARQUET_DIR = DATA_DIR / "parquet"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

# DuckDB
DUCKDB_PATH = DATA_DIR / "sustainability.duckdb"

# Reproducibility
RANDOM_SEED = 42
REFERENCE_YEAR = 2021  # Latest year with complete multi-source data

# IBGE API
IBGE_SIDRA_BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"
# Use N6[all] (bracket notation) for municipality queries - N6/all returns 500
IBGE_SIDRA_MUNICIPIOS = "N6[all]"
IBGE_LOCALIDADES_BASE = "https://servicodados.ibge.gov.br/api/v1/localidades"

# TerraBrasilis (INPE)
TERRABRASILIS_BASE = "https://terrabrasilis.dpi.inpe.br"

# Queimadas INPE
QUEIMADAS_BASE = "https://queimadas.dgi.inpe.br"

# SICONFI (Tesouro Nacional)
SICONFI_BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"

# MapBiomas Col 9 statistics
MAPBIOMAS_STATS_URL = (
    "https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/"
    "collection_9/downloads/mapbiomas_brasil_col9_state_municipality.xlsx"
)
MAPBIOMAS_DEFOR_URL = (
    "https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/"
    "collection_9/downloads/mapbiomas_brasil_col9_deforestation_and_secondary_vegetation_state_municipality.xlsx"
)

# IBGE shapefiles
IBGE_MUNICIPIOS_ZIP = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_municipais/municipio_2022/Brasil/BR/BR_Municipios_2022.zip"
)
IBGE_BIOMAS_ZIP = (
    "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/"
    "biomas/vetores/Biomas_250mil.zip"
)

# HTTP settings
HTTP_TIMEOUT = 120
HTTP_RETRIES = 3
HTTP_CHUNK_SIZE = 1024 * 1024  # 1 MB

# MapBiomas class codes (Collection 9)
MAPBIOMAS_CLASSES = {
    1: "Floresta",
    3: "Formação Florestal",
    4: "Formação Savânica",
    5: "Mangue",
    6: "Floresta Alagável",
    9: "Silvicultura",
    10: "Formação Natural Não Florestal",
    11: "Campo Alagado e Área Pantanosa",
    12: "Formação Campestre",
    13: "Outra Formação não Florestal",
    14: "Agropecuária",
    15: "Pastagem",
    18: "Agricultura",
    19: "Lavoura Temporária",
    20: "Cana",
    21: "Mosaico de Usos",
    22: "Área não Vegetada",
    23: "Praia, Duna e Areal",
    24: "Área Urbanizada",
    25: "Outra Área não Vegetada",
    26: "Corpo D'água",
    27: "Não Observado",
    29: "Afloramento Rochoso",
    30: "Mineração",
    31: "Aquicultura",
    32: "Apicum",
    33: "Rio, Lago e Oceano",
    35: "Palma",
    36: "Lavoura Perene",
    39: "Soja",
    40: "Arroz",
    41: "Outras Lavouras Temporárias",
    46: "Café",
    47: "Citrus",
    48: "Outras Lavouras Perenes",
    49: "Restinga Arbórea",
    50: "Restinga Herbácea",
}

MAPBIOMAS_NATIVE_VEGETATION_CODES = [1, 3, 4, 5, 6, 10, 11, 12, 13, 29, 32, 49, 50]
MAPBIOMAS_FOREST_CODES = [1, 3, 4, 5, 6]
MAPBIOMAS_AGRO_CODES = [14, 15, 18, 19, 20, 35, 36, 39, 40, 41, 46, 47, 48]
MAPBIOMAS_URBAN_CODES = [24]
MAPBIOMAS_MINING_CODES = [30]


def ensure_dirs() -> None:
    """Create all required directories."""
    for d in [RAW_DIR, PROCESSED_DIR, EXTERNAL_DIR, PARQUET_DIR, FIGURES_DIR, TABLES_DIR]:
        d.mkdir(parents=True, exist_ok=True)
