# UK Planning Applications Tracker
# One-time:  make setup
# Launch:    make run          (builds the frontend if needed, serves on http://127.0.0.1:8000)
# Data:      make pipeline     (rerun quarterly after updating config/sources.yml)
# Tests:     make test

PY := .venv/bin/python
UVICORN := .venv/bin/uvicorn

.PHONY: setup pipeline pipeline-offline run build test clean-db

setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip setuptools wheel
	.venv/bin/pip install -r requirements.txt
	cd frontend && npm install

pipeline:
	$(PY) -m pipeline.cli run

pipeline-offline:
	$(PY) -m pipeline.cli run --offline

frontend/dist/index.html: $(wildcard frontend/src/* frontend/src/**/* frontend/index.html)
	cd frontend && npm run build

build: frontend/dist/index.html

run: build
	@test -f data/planning.sqlite || (echo "No database yet — running the pipeline first (a few minutes)…" && $(PY) -m pipeline.cli run)
	$(UVICORN) backend.main:app --host 127.0.0.1 --port 8000

test:
	$(PY) -m pytest tests/ -q

clean-db:
	$(PY) -m pipeline.cli reset
