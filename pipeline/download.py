"""Main download orchestrator: runs all source downloaders in sequence."""
import sys
from pathlib import Path

from loguru import logger
from src.utils.config import ensure_dirs
from src.download.ibge import (
    download_pib_municipal,
    download_populacao,
    download_area_territorial,
    download_shapefile_municipios,
    download_shapefile_biomas,
    download_pam,
    download_ppm,
)
from src.download.inpe import download_prodes_tabular, download_queimadas
from src.download.mapbiomas import download_mapbiomas_stats
from src.download.siconfi import download_finbra, download_gastos_ambientais
from src.download.inep import download_ideb
from src.download.car import download_car_stats


def run_all(years: list[int] | None = None) -> dict:
    """Run all downloaders and return paths to raw files."""
    ensure_dirs()
    results = {}

    steps = [
        ("ibge_pib",           lambda: download_pib_municipal(years)),
        ("ibge_populacao",     lambda: download_populacao(years)),
        ("ibge_area",          download_area_territorial),
        ("ibge_shapefile",     download_shapefile_municipios),
        ("ibge_biomas",        download_shapefile_biomas),
        ("ibge_pam",           lambda: download_pam(years)),
        ("ibge_ppm",           lambda: download_ppm(years)),
        ("inpe_prodes",        download_prodes_tabular),
        ("inpe_queimadas",     lambda: download_queimadas(years)),
        ("mapbiomas",          download_mapbiomas_stats),
        ("siconfi_finbra",     lambda: download_finbra(years)),
        ("siconfi_ambiental",  lambda: download_gastos_ambientais(years)),
        ("inep_ideb",          download_ideb),
        ("car",                download_car_stats),
    ]

    for name, fn in steps:
        logger.info(f"[{name}] Starting...")
        try:
            path = fn()
            results[name] = str(path)
            logger.success(f"[{name}] Done: {path}")
        except Exception as e:
            logger.error(f"[{name}] FAILED: {e}")
            results[name] = None

    return results


if __name__ == "__main__":
    results = run_all()
    ok = sum(1 for v in results.values() if v is not None)
    total = len(results)
    logger.info(f"\nDownload complete: {ok}/{total} sources succeeded")
    if ok < total:
        failed = [k for k, v in results.items() if v is None]
        logger.warning(f"Failed sources: {failed}")
