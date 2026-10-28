# ADR 0005 — Logica di dominio in un modulo puro, separato da API e database

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

Il valore dell'app sta nei calcoli: volume frazionario, punteggio dei candidati, generazione della scheda, stima della durata, e in fase 2 il ribilanciamento. Questi calcoli devono essere corretti (test di riferimento, US-12 CA4), deterministici e coperti da test al 90% (NF6). Mescolati con endpoint e query diventano difficili da testare e da far evolvere.

## Decisione

Il backend è diviso in tre strati, con dipendenze in una sola direzione (`api` → `services` → `domain`, e `services` → `db`):

| Strato | Contenuto | Può importare |
| --- | --- | --- |
| `domain` | Strutture dati immutabili (dataclass) e funzioni pure: calcolo dei volumi, punteggio, generazione, stima della durata, validazioni di dominio | Solo la libreria standard |
| `db` | Modelli SQLAlchemy, sessione, repository che convertono righe del database in oggetti di dominio e viceversa | `domain` |
| `services` | Casi d'uso: carica dal database, chiama il dominio, salva | `domain`, `db` |
| `api` | Router FastAPI, schemi Pydantic, gestione errori HTTP | `services` |

Una regola di lint (import-linter) impedisce a `domain` di importare FastAPI, SQLAlchemy o Pydantic.

## Alternative considerate

- **Logica dentro gli endpoint o nei modelli SQLAlchemy:** più rapido all'inizio, ma i test richiedono database e HTTP, e il ribilanciamento della fase 2 dovrebbe districarsi da questo codice.
- **Architettura esagonale completa con porte e adattatori formali:** eccessiva per un progetto di queste dimensioni.

## Conseguenze

- Il dominio si testa con oggetti in memoria, in millisecondi.
- Il ribilanciamento della fase 2 è un'aggiunta al modulo `domain`, senza toccare API e database.
- Costo: conversione esplicita tra modelli del database e oggetti di dominio nei repository.
