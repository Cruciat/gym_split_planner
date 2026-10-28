"""PDF della scheda (US-30; API, § 6.10; wireframe, § 6)."""

import io
import re
import time
from datetime import date
from typing import Any

from fastapi.testclient import TestClient
from pypdf import PdfReader


def _create(api: TestClient, split: str | None, name: str = "PPL 6 giorni — autunno") -> Any:
    splits = {s["code"]: s["id"] for s in api.get("/api/splits").json()}
    response = api.post(
        "/api/plans", json={"split_id": splits[split] if split else None, "name": name}
    )
    assert response.status_code == 201
    return response.json()


def _pdf(api: TestClient, plan_id: int, **params: Any) -> tuple[Any, list[str]]:
    response = api.get(f"/api/plans/{plan_id}/pdf", params=params)
    assert response.status_code == 200, response.text
    pages = [page.extract_text() for page in PdfReader(io.BytesIO(response.content)).pages]
    return response, pages


def test_download_as_attachment(api: TestClient) -> None:
    plan = _create(api, "ppl-6")

    response, pages = _pdf(api, plan["id"])

    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        f'attachment; filename="ppl-6-giorni-autunno-{date.today().isoformat()}.pdf"'
    )
    assert response.content.startswith(b"%PDF-")
    # Una pagina per giorno e il riepilogo (CA1).
    assert len(pages) == 4


def test_day_page(api: TestClient) -> None:
    plan = _create(api, "ppl-6")

    _, pages = _pdf(api, plan["id"])
    push = pages[0]

    assert "PPL 6 giorni — autunno" in push
    assert "Push/Pull/Legs, 6 giorni" in push
    assert "PUSH" in push
    assert "2 volte a settimana" in push
    assert "Riscaldamento:" in push
    assert re.search(r"Chest press inclinata\s+3 × 6-12\s+0-2\*\s+2′30″", push)
    assert "S4" in push
    assert "S5" not in push
    # Note delle etichette come richiami sotto la tabella (CA1).
    assert "1 Collo: accorgimento: Se le spalle non salgono" in push
    assert "* Ultima serie a cedimento." in push
    # Facoltativi marcati (CA2) e stretching del giorno.
    assert re.search(r"Shoulder press a macchina.*\s+facoltativo", push)
    assert "Stretching:" in push
    assert "30 s × 3" in push


def test_second_session_variant(api: TestClient) -> None:
    plan = _create(api, "ppl-6")
    slot = plan["days"][0]["slots"][0]
    exercises = {e["code"]: e["id"] for e in api.get("/api/catalog").json()["exercises"]}
    api.patch(
        f"/api/plans/{plan['id']}/slots/{slot['id']}",
        json={"second_exercise_id": exercises["incline-bench-press"]},
        headers={"If-Match": f'"{plan["revision"]}"'},
    )

    _, pages = _pdf(api, plan["id"])

    # Il giorno resta su una pagina, con la variante sotto l'esercizio (CA2).
    assert len(pages) == 4
    assert "2ª seduta: Panca inclinata a 30°" in pages[0]
    assert re.search(r"~\d+ / ~\d+ min", pages[0])


def test_summary_page(api: TestClient) -> None:
    plan = _create(api, "ppl-6")

    _, pages = _pdf(api, plan["id"])
    summary = pages[-1]

    assert "VOLUME SETTIMANALE" in summary
    assert re.search(r"Tricipite, capo lungo\s+8\s+10\u201318\s+sotto", summary)
    assert re.search(r"Quadricipiti \(vasti\)\s+12\s+6\u201310\s+sopra", summary)
    assert "LEGENDA" in summary
    assert "Collo: attenzione" in summary
    assert "MINI-ALLENAMENTO QUOTIDIANO" in summary
    assert "Flessione cranio-cervicale da sdraiati (chin tuck)" in summary


def test_weeks(api: TestClient) -> None:
    plan = _create(api, "ppl-3")

    _, pages = _pdf(api, plan["id"], weeks=8)
    too_many = api.get(f"/api/plans/{plan['id']}/pdf", params={"weeks": 9})
    none = api.get(f"/api/plans/{plan['id']}/pdf", params={"weeks": 0})

    assert "S8" in pages[0]
    assert too_many.json()["code"] == "validation-error"
    assert none.status_code == 422


def test_empty_plan_and_missing_plan(api: TestClient) -> None:
    plan = _create(api, None, name="Vuota")

    response, pages = _pdf(api, plan["id"])

    assert response.headers["content-disposition"].startswith('attachment; filename="vuota-')
    assert len(pages) == 1
    assert "VOLUME SETTIMANALE" in pages[0]
    assert api.get("/api/plans/999/pdf").json()["code"] == "not-found"


def test_generation_time(api: TestClient) -> None:
    """Obiettivo sotto 1 s; la soglia larga evita falsi allarmi su macchine lente o cariche."""
    plan = _create(api, "ppl-6")
    api.get(f"/api/plans/{plan['id']}/pdf")

    start = time.perf_counter()
    api.get(f"/api/plans/{plan['id']}/pdf")

    assert time.perf_counter() - start < 3
