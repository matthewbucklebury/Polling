"""Shared pipeline plumbing: paths, config, cached downloads, loud failures."""
from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
REFERENCE_DIR = DATA_DIR / "reference"
DB_PATH = DATA_DIR / "planning.sqlite"

log = logging.getLogger("pipeline")


class SourceError(Exception):
    """A pipeline stage failed. Message must name the file/sheet that broke."""


def load_yaml(name: str) -> dict:
    path = CONFIG_DIR / name
    if not path.exists():
        raise SourceError(f"Missing config file: {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def sources_config() -> dict:
    return load_yaml("sources.yml")


def settings() -> dict:
    return load_yaml("settings.yml")


def download(url: str, filename: str, *, offline: bool = False, retries: int = 3) -> Path:
    """Download `url` into data/raw/`filename`, reusing the cached copy if present.

    With offline=True the cache is required. Failures raise SourceError naming the file.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / filename
    if dest.exists() and dest.stat().st_size > 0:
        log.info("using cached %s (%.1f MB)", dest.name, dest.stat().st_size / 1e6)
        return dest
    if offline:
        raise SourceError(f"Offline mode and no cached copy of {filename} in {RAW_DIR}")

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            log.info("downloading %s (attempt %d)", filename, attempt)
            tmp = dest.with_suffix(dest.suffix + ".part")
            with httpx.stream("GET", url, follow_redirects=True, timeout=120) as resp:
                resp.raise_for_status()
                with open(tmp, "wb") as f:
                    for chunk in resp.iter_bytes():
                        f.write(chunk)
            shutil.move(tmp, dest)
            log.info("downloaded %s (%.1f MB)", dest.name, dest.stat().st_size / 1e6)
            return dest
        except Exception as e:  # noqa: BLE001 - report any failure per-source
            last_err = e
            if attempt < retries:
                time.sleep(2**attempt)
    raise SourceError(f"Failed to download {filename} from {url}: {last_err}")
