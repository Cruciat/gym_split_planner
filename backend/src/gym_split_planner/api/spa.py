"""Distribuzione del frontend compilato con ritorno a ``index.html`` (ADR 0009)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response

from gym_split_planner.api.errors import problem_response


def install_spa(app: FastAPI, static_dir: Path) -> None:
    """Serve i file del frontend per ogni percorso fuori da ``/api``.

    Un file esistente viene servito così com'è; qualunque altro percorso riceve
    ``index.html``, perché il routing è del client (Vue Router). I percorsi sotto
    ``/api`` che non corrispondono a nessun endpoint restano un 404 in Problem Details.
    """
    root = static_dir.resolve()
    index = root / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str) -> Response:
        if full_path == "api" or full_path.startswith("api/"):
            return problem_response(404, "not-found", "Risorsa non trovata")
        candidate = (root / full_path).resolve()
        if full_path and candidate.is_relative_to(root) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index, headers={"Cache-Control": "no-cache"})
