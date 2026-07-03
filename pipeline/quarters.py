"""Quarter string helpers. Canonical form 'YYYYQn' (calendar quarter), lexically sortable."""
from __future__ import annotations

import re

_QUARTER_RE = re.compile(r"^\s*(\d{4})\s*Q?\s*([1-4])\s*$")


def parse_quarter(text: str) -> str:
    """'1996 Q2' / '2024Q3' / '2024 q1' -> '1996Q2'. Raises ValueError otherwise."""
    m = _QUARTER_RE.match(str(text))
    if not m:
        raise ValueError(f"Unrecognised quarter: {text!r}")
    return f"{m.group(1)}Q{m.group(2)}"


def quarter_of_date(year: int, month: int) -> str:
    return f"{year}Q{(month - 1) // 3 + 1}"


def quarter_seq(q: str) -> int:
    """Monotonic integer for arithmetic: 2024Q3 -> 2024*4+2."""
    return int(q[:4]) * 4 + int(q[5]) - 1


def seq_quarter(seq: int) -> str:
    return f"{seq // 4}Q{seq % 4 + 1}"


def shift(q: str, n: int) -> str:
    return seq_quarter(quarter_seq(q) + n)
