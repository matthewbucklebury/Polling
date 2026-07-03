"""Local government reorganisation mapping.

Maps predecessor authorities to their successors (2009 unitarisations through the
2023 Cumbria/North Yorkshire/Somerset changes) so time series stay continuous.
GSS-coded predecessors match on code; pre-2009 rows carry legacy non-GSS codes
(e.g. 'Q2908') and match on cleaned name instead.
"""
from __future__ import annotations

import csv
import re
from functools import lru_cache

from .common import REFERENCE_DIR, SourceError

_SUFFIXES = re.compile(
    r"\s+(district council|borough council|city council|county council|council|"
    r"london borough|royal borough of|city of)\b",
    re.I,
)


def clean_name(name: str) -> str:
    """Normalise an authority name for matching across sources."""
    n = str(name).strip()
    n = re.sub(r"\s*\(.*?\)\s*", " ", n)  # drop parentheticals
    n = _SUFFIXES.sub("", " " + n).strip()
    n = re.sub(r"^(london borough of|royal borough of|city of)\s+", "", n, flags=re.I)
    n = n.replace("&", "and")
    n = re.sub(r"[.,'’]", "", n)
    n = re.sub(r"\s+", " ", n)
    return n.lower().strip(" -")


@lru_cache(maxsize=1)
def _load_changes() -> tuple[dict[str, tuple[str, str]], dict[str, tuple[str, str]]]:
    path = REFERENCE_DIR / "authority_changes.csv"
    if not path.exists():
        raise SourceError(f"Missing reference file {path}")
    by_code: dict[str, tuple[str, str]] = {}
    by_name: dict[str, tuple[str, str]] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            target = (row["new_code"], row["new_name"])
            if row["old_code"]:
                by_code[row["old_code"]] = target
            if row["old_name"]:
                by_name[clean_name(row["old_name"])] = target
    return by_code, by_name


def canonical(code: str, name: str) -> tuple[str, str]:
    """Resolve (code, name) to the current successor authority, following chains
    (e.g. Taunton Deane -> Somerset West and Taunton -> Somerset)."""
    by_code, by_name = _load_changes()
    cur_code, cur_name = str(code).strip(), str(name).strip()
    for _ in range(5):  # chains are short; guard against lookup cycles
        hit = by_code.get(cur_code)
        if hit is None:
            # pre-2009 rows carry legacy non-GSS codes; sources also disagree on
            # predecessor codes, so fall back to matching on cleaned name
            hit = by_name.get(clean_name(cur_name))
        if hit is None or hit[0] == cur_code:
            break
        cur_code, cur_name = hit
    return cur_code, cur_name


def is_gss(code: str) -> bool:
    return bool(re.match(r"^[EWS]\d{8}$", str(code).strip()))
