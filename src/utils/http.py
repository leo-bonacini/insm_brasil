"""HTTP utilities with retry, progress bar and checksum."""
import hashlib
import time
from pathlib import Path

import requests
import urllib3
from loguru import logger
from tqdm import tqdm

from src.utils.config import HTTP_CHUNK_SIZE, HTTP_RETRIES, HTTP_TIMEOUT

# Suppress SSL warnings for gov.br sites with legacy certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Domains that require SSL verification disabled (gov.br legacy certs)
NO_VERIFY_DOMAINS = {"download.inep.gov.br", "www.car.gov.br", "siconfi.tesouro.gov.br"}


def _needs_no_verify(url: str) -> bool:
    from urllib.parse import urlparse
    return urlparse(url).hostname in NO_VERIFY_DOMAINS


def download_file(url: str, dest: Path, desc: str = "", skip_if_exists: bool = True) -> Path:
    """Download a file with retry logic and progress bar."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if skip_if_exists and dest.exists() and dest.stat().st_size > 0:
        logger.info(f"Already exists, skipping: {dest.name}")
        return dest

    verify = not _needs_no_verify(url)
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            logger.info(f"Downloading ({attempt}/{HTTP_RETRIES}): {url}")
            with requests.get(url, stream=True, timeout=HTTP_TIMEOUT, verify=verify) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                with open(dest, "wb") as f, tqdm(
                    total=total, unit="B", unit_scale=True, desc=desc or dest.name, leave=False
                ) as bar:
                    for chunk in resp.iter_content(chunk_size=HTTP_CHUNK_SIZE):
                        f.write(chunk)
                        bar.update(len(chunk))
            logger.success(f"Downloaded: {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
            return dest
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt < HTTP_RETRIES:
                time.sleep(2 ** attempt)
            else:
                raise
    return dest


def get_json(url: str, params: dict | None = None) -> dict | list:
    """GET request returning parsed JSON with retry."""
    verify = not _needs_no_verify(url)
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=HTTP_TIMEOUT, verify=verify)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"JSON request attempt {attempt} failed: {e} | {url}")
            if attempt < HTTP_RETRIES:
                time.sleep(2 ** attempt)
            else:
                raise
    return {}


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
