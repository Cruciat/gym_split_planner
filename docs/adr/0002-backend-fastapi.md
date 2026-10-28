# ADR 0002 — Backend in Python con FastAPI, SQLAlchemy 2 e Alembic

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

Il backend deve esporre un'API per catalogo e schede, eseguire i calcoli di volume e generazione (e in fase 2 il ribilanciamento), produrre PDF e gestire le migrazioni dello schema (NF7). Lo sviluppatore conosce già Python, FastAPI e SQLAlchemy dal tirocinio.

## Decisione

- **Python 3.12**, gestione delle dipendenze con **uv** (`pyproject.toml` e lockfile).
- **FastAPI** per l'API HTTP; validazione e serializzazione con **Pydantic v2**.
- **SQLAlchemy 2.x** in stile tipizzato (`Mapped[...]`), accesso sincrono.
- **Alembic** per le migrazioni; ogni modifica allo schema ha la sua migrazione, applicata all'avvio del container.
- Server **Uvicorn**.

L'accesso al database è sincrono: con un solo utente e SQLite l'asincrono non porta vantaggi e complica test e transazioni.

## Alternative considerate

- **Django e Django REST Framework:** completo e con admin incluso, ma più pesante e meno adatto a separare un dominio puro (ADR 0005); stack non già noto.
- **Node.js (NestJS o Express) con TypeScript:** un solo linguaggio con il frontend, ma i calcoli e la futura ottimizzazione sono più naturali in Python, e lo stack sarebbe nuovo.
- **SQLAlchemy asincrono:** nessun beneficio misurabile con un utente; più attrito con SQLite e nei test.

## Conseguenze

- Documentazione OpenAPI generata automaticamente, utile per verificare il contratto delle API.
- Lo stesso linguaggio per API, dominio, seed e generazione del PDF.
- Due linguaggi nel repository (Python e TypeScript), accettato.
