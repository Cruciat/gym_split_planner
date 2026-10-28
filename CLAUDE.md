# Gym Split Planner — istruzioni per chi lavora sul codice

Servizio web personale per consultare una banca dati di esercizi e creare schede di allenamento. Un solo utente, raggiungibile solo dalla tailnet.

## Prima di scrivere codice

- La documentazione in `docs/` è la fonte delle decisioni: specifica (`docs/spec/fase-1.md`), ADR (`docs/adr/`), modello dati, algoritmo, dati iniziali, contratto delle API, wireframe (`docs/design/`).
- Se una modifica contraddice un documento, prima si aggiorna il documento (o si scrive un ADR nuovo), poi il codice, nella stessa pull request.
- Ogni lavoro parte da una issue con criteri di accettazione, assegnata a una milestone (tappa M0-M6, `docs/processo.md`).

## Struttura

| Cartella | Contenuto |
| --- | --- |
| `backend/` | Python 3.12, uv, FastAPI, SQLAlchemy 2, Alembic, SQLite. Pacchetto `gym_split_planner` in `src/` |
| `frontend/` | Vue 3, TypeScript stretto, Vite, Pinia, Vue Router, Naive UI, icone Lucide |
| `docs/` | Documentazione di progetto, in italiano |
| `openapi.json` | Schema dell'API generato dal backend; da qui i tipi del frontend |

Strati del backend (ADR 0005), verificati da import-linter:

- `domain`: dataclass immutabili e funzioni pure, **solo libreria standard**. Qui stanno volumi, punteggio, generazione, durata.
- `db`: modelli SQLAlchemy, motore, migrazioni; può importare `domain`.
- `services`: casi d'uso; può importare `db` e `domain`.
- `api`: router, schemi Pydantic, errori; può importare **solo** `services`.
- `app.py` è l'unico punto che collega tutto (composizione); `config.py` legge le variabili `GSP_*`.

## Comandi

```bash
make setup          # dipendenze e hook di pre-commit
make dev-backend    # API su :8000
make dev-frontend   # frontend su :5173 con /api inoltrato
make check          # tutti i controlli della CI
make api-types      # dopo ogni modifica al contratto delle API
```

## Convenzioni (ADR 0012, 0013)

- **Lingua:** codice, nomi di tabelle, campi JSON ed endpoint in inglese; interfaccia, messaggi d'errore per l'utente, documentazione, docstring e commenti in italiano.
- **Commit e titoli delle PR:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `build:`, `test:`, `refactor:`). Merge solo con squash.
- **Branch:** `tipo/<numero-issue>-descrizione`, es. `feat/12-volume-frazionario`.
- **Errori dell'API:** sempre Problem Details con `code` stabile (`api/errors.py`, contratto § 3).
- **Test:** il dominio si scrive con i test prima del codice; copertura del dominio ≥ 90%. I test di riferimento (volumi dell'Excel) non si cambiano senza motivarlo nella PR.
- **Migrazioni:** ogni modifica allo schema ha la sua migrazione Alembic (`uv run alembic revision --autogenerate -m "…"` in `backend/`), con `render_as_batch` per SQLite.
- **Dipendenze:** solo licenze permissive (MIT, ISC, BSD, Apache). Per questo niente PrimeVue (ADR 0015). Controlla la licenza prima di aggiungere un pacchetto.
- **Tipi del client:** `frontend/src/api/schema.d.ts` è generato, non si modifica a mano.
