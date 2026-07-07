"""API smoke tests against the real built database.

These run only when data/planning.sqlite exists (i.e. after `make pipeline`);
they are the fastest way for a session to prove the backend still serves every
page's data after a change. `make test` runs them automatically.
"""
import pytest

from pipeline.common import DB_PATH

pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(), reason="no built database — run `make pipeline` first"
)


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from backend.main import app
    return TestClient(app)


def test_meta(client):
    j = client.get("/api/meta").json()
    assert len(j["quarters"]) > 50
    assert j["latest_quarter"] >= "2025Q1"
    assert "friction_score" in j["metrics"]
    assert isinstance(j["sample_sources"], list)


def test_authorities_list(client):
    j = client.get("/api/authorities").json()
    assert len(j["authorities"]) > 250
    names = {a["name"] for a in j["authorities"]}
    assert "Cumberland" in names  # 2023 reorganisation successor present and active


def test_authority_profile(client):
    j = client.get("/api/authorities/E07000223").json()  # Adur
    assert j["authority"]["name"] == "Adur"
    assert j["series"]["authority"]["approval_rate_all"], "profile series empty"
    assert j["series"]["england"]["approval_rate_all"], "England comparison series empty"
    assert len(j["summary"]) > 30


def test_unknown_authority_404(client):
    assert client.get("/api/authorities/NOPE").status_code == 404


def test_map_values(client):
    meta = client.get("/api/meta").json()
    q = meta["latest_quarter"]
    j = client.get(f"/api/map?metric=approval_rate_all&quarter={q}").json()
    assert len(j["values"]) > 250


def test_league_threshold_excludes(client):
    meta = client.get("/api/meta").json()
    q = meta["latest_quarter"]
    j = client.get(f"/api/league?metric=approval_rate_major_res&quarter={q}").json()
    assert j["entries"], "league empty"
    assert j["excluded_below_threshold"] > 0, "min-volume threshold not applied"
    ranks = [e["rank"] for e in j["entries"]]
    assert ranks == sorted(ranks)


def test_compare(client):
    j = client.get("/api/compare?codes=E07000223,E06000063&metric=approval_rate_all").json()
    assert set(j["names"].values()) >= {"Adur", "Cumberland", "England"}


def test_national(client):
    j = client.get("/api/national").json()
    assert j["series_4q"]["eot_share_all"], "EOT national series missing"


def test_geojson(client):
    j = client.get("/api/geojson").json()
    assert len(j["features"]) >= 290


def test_report_html(client):
    r = client.get("/api/authorities/E07000223/report")
    assert r.status_code == 200
    assert "planning performance report" in r.text
    assert "<svg" in r.text  # charts rendered inline
