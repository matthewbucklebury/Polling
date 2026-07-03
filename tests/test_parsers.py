"""Parser unit tests over small fixture files checked into the repo.

PS1/PS2 fixtures are literal excerpts of the real MHCLG open-data CSVs
(title/footnote rows included); the ODS/xlsx fixtures reproduce the real
layout quirks: cover sheets, headers rows down the sheet, note-suffixed year
headers, '[x]' markers, grouping rows without codes.
"""
from pathlib import Path

import pytest

from pipeline.sources import authority_meta, housing_delivery, mhclg_applications, pins_appeals
from pipeline.common import SourceError

FIX = Path(__file__).parent / "fixtures"


class TestPS1:
    def test_parses_long_facts(self):
        df = mhclg_applications.parse_ps1(FIX / "ps1_sample.csv")
        assert set(df.columns) == {"LPACD", "LPANM", "Region", "quarter", "dev_type", "metric", "value"}
        assert set(df["metric"]) == {"received", "decided_all_types", "withdrawn"}
        assert (df["dev_type"] == "all").all()
        adur = df[(df.LPACD == "E07000223") & (df.metric == "received")]
        assert len(adur) > 5
        assert (adur["value"] > 0).all()

    def test_quarter_format(self):
        df = mhclg_applications.parse_ps1(FIX / "ps1_sample.csv")
        assert df["quarter"].str.match(r"^\d{4}Q[1-4]$").all()


class TestPS2:
    def test_parses_expected_metrics(self):
        df = mhclg_applications.parse_ps2(FIX / "ps2_sample.csv")
        metrics = set(df["metric"])
        assert {"decisions", "granted", "refused", "decisions_expa", "intime_expa",
                "decisions_pa", "intime_pa", "band1"} <= metrics
        assert {"all", "major", "minor", "other", "major_res", "minor_res", "householder"} <= set(df["dev_type"])

    def test_granted_le_decisions(self):
        df = mhclg_applications.parse_ps2(FIX / "ps2_sample.csv")
        wide = df.pivot_table(index=["LPACD", "quarter", "dev_type"], columns="metric", values="value")
        both = wide.dropna(subset=["granted", "decisions"])
        assert (both["granted"] <= both["decisions"]).all()

    def test_missing_columns_fail_loudly(self, tmp_path):
        bad = tmp_path / "bad.csv"
        bad.write_text("Region,LPANM,LPACD,Quarter,Nonsense\nSouth East,Adur,E07000223,2024 Q1,1\n")
        with pytest.raises(SourceError, match="columns missing"):
            mhclg_applications.parse_ps2(bad)


class TestPINS:
    def test_counts_only_decided_planning_type_appeals(self):
        df = pins_appeals.parse_casework(FIX / "pins_casework_sample.xlsx", "Data Set")
        # 8 fixture cases: 1 enforcement notice excluded -> 7 kept
        assert len(df) == 7
        assert set(df["outcome"]) == {"allowed", "dismissed", "split"}
        # 'Allowed with Conditions' counts as allowed
        assert (df["outcome"] == "allowed").sum() == 2
        # lowercase 'refused' and 'Refusal - Reserved Matters' count as refusal appeals;
        # the 'Failure' (non-determination) appeal does not
        assert df["is_refusal"].sum() == 6
        assert df["is_major_res"].sum() == 3

    def test_aggregate_shapes(self):
        df = pins_appeals.parse_casework(FIX / "pins_casework_sample.xlsx", "Data Set")
        facts = pins_appeals.aggregate(df)
        adur_q2 = facts[(facts.code == "E07000223") & (facts.quarter == "2023Q2")]
        decided = adur_q2[(adur_q2.metric == "appeals_decided") & (adur_q2.dev_type == "all")]["value"]
        assert decided.item() == 2  # one allowed + one dismissed in 2023Q2

    def test_wrong_sheet_fails_loudly(self):
        with pytest.raises(SourceError):
            pins_appeals.parse_casework(FIX / "pins_casework_sample.xlsx", "No Such Sheet")


class TestLT122:
    def test_parses_lpa_rows_only(self):
        df = housing_delivery.parse_lt122(FIX / "lt122_sample.ods", min_records=5, min_years=2)
        codes = set(df["code"])
        assert "E06000022" in codes and "E07000223" in codes
        assert "ENG" in codes                      # England mapped to pseudo-code
        assert "E12000001" not in codes            # regions excluded (would double count)
        bath = df[(df.code == "E06000022") & (df.year == 2002)]
        assert bath["value"].item() == 270

    def test_note_suffixed_years_and_x_markers(self):
        df = housing_delivery.parse_lt122(FIX / "lt122_sample.ods", min_records=5, min_years=2)
        assert 2005 in set(df["year"])             # '2004-05 [note 1]' parsed
        adur = df[(df.code == "E07000223")]
        assert 2005 not in set(adur["year"])       # '[x]' -> skipped, not zero


class TestHDT:
    def test_measure_scaled_to_percent(self):
        df = housing_delivery.parse_hdt(FIX / "hdt_sample.ods", min_records=5)
        adur = df[(df.code == "E07000223") & (df.metric == "hdt_measure")]
        assert adur["value"].item() == pytest.approx(81.0)
        req = df[(df.code == "E07000223") & (df.metric == "hdt_required")]
        assert req["value"].item() == pytest.approx(492.97)

    def test_year_from_title(self):
        df = housing_delivery.parse_hdt(FIX / "hdt_sample.ods", min_records=5)
        assert set(df["year"]) == {2023}


class TestBoundaries:
    def test_parse_features(self):
        rows = authority_meta.parse_boundaries(FIX / "boundaries_sample.geojson", min_features=1)
        assert len(rows) == 6
        code, name, ruc, feature = rows[0]
        assert code.startswith("E") and "Urban" in ruc
        import json
        f = json.loads(feature)
        assert f["properties"]["code"] == code and f["geometry"]["type"] == "Polygon"

    def test_too_few_features_fails_loudly(self):
        with pytest.raises(SourceError, match="features"):
            authority_meta.parse_boundaries(FIX / "boundaries_sample.geojson", min_features=250)
