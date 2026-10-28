# ADR 0009 — Un solo container che serve API e frontend

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

L'app ha un backend FastAPI e un frontend compilato in file statici. Va distribuita sull'homelab con il minor numero di parti mobili possibile.

## Decisione

- Build multi-stadio: uno stadio Node 22 compila il frontend; lo stadio finale `python:3.12-slim` installa il backend e copia i file statici.
- FastAPI serve l'API sotto `/api` e i file statici del frontend per tutte le altre rotte, con ritorno a `index.html` per il routing lato client.
- All'avvio il container applica le migrazioni Alembic, poi avvia Uvicorn.
- Endpoint `/api/health` per i controlli di salute di Docker.
- Utente non root nel container; dati solo nel volume `/data`.

## Alternative considerate

- **Due container (Nginx per il frontend, backend separato):** separazione più netta, ma più configurazione senza benefici per un utente.
- **Frontend su un hosting statico esterno:** contrario all'idea di un servizio interno alla tailnet.

## Conseguenze

- Una sola immagine da versionare e distribuire.
- Frontend e backend si aggiornano sempre insieme, quindi non serve gestire versioni incompatibili tra i due.
