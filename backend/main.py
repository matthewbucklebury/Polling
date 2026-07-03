"""FastAPI app: JSON API + built React frontend, one process."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import api, report

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

app = FastAPI(title="UK Planning Applications Tracker", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.include_router(api.router)
app.include_router(report.router)

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        candidate = FRONTEND_DIST / path
        if path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/", include_in_schema=False)
    def missing_frontend():
        return JSONResponse({"error": "Frontend not built. Run `make build` (or `make run`, which builds it)."}, 503)
