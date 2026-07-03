"""Core derivation logic: quarters, reorganisation mapping, ratio/rolling maths,
and the friction composite — against a small in-memory database."""
import sqlite3

import pytest

from pipeline import metrics
from pipeline.authority_lookup import canonical, clean_name
from pipeline.db import SCHEMA
from pipeline.quarters import parse_quarter, quarter_seq, shift


class TestQuarters:
    def test_parse_variants(self):
        assert parse_quarter("1996 Q2") == "1996Q2"
        assert parse_quarter("2024Q3") == "2024Q3"
        with pytest.raises(ValueError):
            parse_quarter("Q3 2024")

    def test_shift(self):
        assert shift("2024Q4", 1) == "2025Q1"
        assert shift("2024Q1", -1) == "2023Q4"
        assert quarter_seq("2024Q2") - quarter_seq("2023Q2") == 4


class TestAuthorityLookup:
    def test_gss_code_mapping(self):
        assert canonical("E07000026", "Allerdale")[0] == "E06000063"  # -> Cumberland

    def test_chain_resolution(self):
        # Taunton Deane -> Somerset West and Taunton (2019) -> Somerset (2023)
        assert canonical("E07000190", "Taunton Deane")[0] == "E06000066"

    def test_legacy_code_falls_back_to_name(self):
        assert canonical("Q2908", "Alnwick")[0] == "E06000057"  # -> Northumberland

    def test_active_authority_unchanged(self):
        assert canonical("E07000223", "Adur") == ("E07000223", "Adur")

    def test_clean_name(self):
        assert clean_name("Allerdale Borough Council") == "allerdale"
        assert clean_name("City of Westminster Council") == "westminster"
        assert clean_name("Somerset West & Taunton") == "somerset west and taunton"


def _mini_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.row_factory = sqlite3.Row
    conn.execute("INSERT INTO authorities (code,name,region,authority_type,active) VALUES "
                 "('E07000901','Testborough','Testland','district',1)")
    conn.execute("INSERT INTO authorities (code,name,region,authority_type,active) VALUES "
                 "('E07000902','Otherton','Testland','district',1)")
    # predecessor mapped into Testborough
    conn.execute("INSERT INTO authorities (code,name,active,successor_code) VALUES "
                 "('E07000900','Oldshire',0,'E07000901')")
    facts = []
    for i, q in enumerate(["2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1"]):
        # Testborough: 80 decisions/quarter, 60 granted; half of the granted in Q1 come
        # from the predecessor to prove predecessor aggregation.
        code = "E07000900" if q == "2023Q1" else "E07000901"
        facts += [
            (code, q, "all", "decisions", 80), (code, q, "all", "granted", 60), (code, q, "all", "refused", 20),
            (code, q, "all", "decisions_expa", 50), (code, q, "all", "intime_expa", 40),
            (code, q, "all", "decisions_pa", 30), (code, q, "all", "intime_pa", 30),
            ("E07000902", q, "all", "decisions", 40), ("E07000902", q, "all", "granted", 10),
            ("E07000902", q, "all", "refused", 30),
            ("E07000902", q, "all", "decisions_expa", 40), ("E07000902", q, "all", "intime_expa", 10),
            ("E07000902", q, "all", "decisions_pa", 0), ("E07000902", q, "all", "intime_pa", 0),
        ]
    conn.executemany(
        "INSERT INTO facts (authority_code, quarter, dev_type, metric, value, source) VALUES (?,?,?,?,?,'test')",
        facts)
    conn.commit()
    return conn


class TestDerivation:
    def test_ratios_rolling_and_predecessor_aggregation(self):
        conn = _mini_db()
        n = metrics.derive_all(conn)
        assert n > 0

        def val(code, metric, window, quarter):
            r = conn.execute("SELECT value FROM metrics WHERE authority_code=? AND metric=? AND window=? AND quarter=?",
                             (code, metric, window, quarter)).fetchone()
            return r["value"] if r else None

        # quarterly approval rate
        assert val("E07000901", "approval_rate_all", "Q", "2023Q2") == pytest.approx(75.0)
        # predecessor quarter counted into successor's rolling year
        assert val("E07000901", "decisions_all", "4Q", "2023Q4") == pytest.approx(320)
        # 4Q ratio is sum/sum, not mean of ratios
        assert val("E07000901", "approval_rate_all", "4Q", "2023Q4") == pytest.approx(75.0)
        # headline in-time counts agreed extensions as in time; statutory basis does not
        assert val("E07000901", "pct_intime_headline_all", "Q", "2023Q2") == pytest.approx(87.5)
        assert val("E07000901", "pct_intime_statutory_all", "Q", "2023Q2") == pytest.approx(80.0)
        assert val("E07000901", "eot_share_all", "Q", "2023Q2") == pytest.approx(37.5)
        # England aggregate = both authorities
        assert val("ENG", "decisions_all", "Q", "2023Q2") == pytest.approx(120)

    def test_no_facts_is_graceful(self):
        conn = sqlite3.connect(":memory:")
        conn.executescript(SCHEMA)
        conn.row_factory = sqlite3.Row
        assert metrics.derive_all(conn) == 0
