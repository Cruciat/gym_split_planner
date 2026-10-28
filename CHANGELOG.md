# Changelog

Tutte le modifiche rilevanti, per versione. Formato basato su [Keep a Changelog](https://keepachangelog.com/it-IT/1.1.0/); versioni secondo [SemVer](https://semver.org/lang/it/).

## [Non rilasciato]

### Aggiunto

- Documentazione di progettazione della fase 1: specifica, ADR 0001-0015, modello dati, algoritmo, dati iniziali, contratto delle API, wireframe.
- Struttura del progetto: backend FastAPI a strati, frontend Vue 3, controlli di qualità e integrazione continua.
- `GET /api/health` con stato del database.
- Errori dell'API in formato Problem Details.
- Immagine Docker unica (API e frontend) e workflow di rilascio su GHCR.
- `GET /api/pdf/test`: PDF di prova generato con WeasyPrint, temporaneo fino a M5.
