# Changelog

Tutte le modifiche rilevanti, per versione. Formato basato su [Keep a Changelog](https://keepachangelog.com/it-IT/1.1.0/); versioni secondo [SemVer](https://semver.org/lang/it/).

## [Non rilasciato]

## [0.3.0] - 2026-10-28

Tappa M2: il motore. Nessuna funzione nuova nell'interfaccia; i calcoli serviranno a catalogo e schede (M3, M4).

### Aggiunto

- Motore: volume settimanale frazionario, valori effettivi con le personalizzazioni, volume per seduta e tetto.
- Motore: punteggio dei candidati con etichette e preferenze, generazione e rigenerazione delle schede; test di riferimento sui volumi dei 6 split.
- Motore: anteprima delle varianti (anche per la seconda seduta), stima della durata delle sedute, analisi della scheda con gli avvisi.

## [0.2.0] - 2026-10-28

Tappa M1: i dati. Nessuna funzione nuova nell'interfaccia; il database contiene il catalogo e gli split.

### Aggiunto

- Modello dati della fase 1 (catalogo, etichette, split, schede, impostazioni) con migrazione e vincoli nel database.
- Backup giornaliero automatico del database in `/data/backups`, conservati gli ultimi 14.
- Dati iniziali caricati al primo avvio: 81 esercizi, 40 famiglie, 33 muscoli, 3 etichette, 6 split, stretching, mini-allenamento, impostazioni.

## [0.1.0] - 2026-10-28

Prima versione: scheletro del progetto (tappa M0). Nessuna funzione per l'utente oltre alla pagina di stato e al PDF di prova.

### Aggiunto

- Documentazione di progettazione della fase 1: specifica, ADR 0001-0016, modello dati, algoritmo, dati iniziali, contratto delle API, wireframe.
- Struttura del progetto: backend FastAPI a strati, frontend Vue 3, controlli di qualità e integrazione continua.
- `GET /api/health` con stato del database.
- Errori dell'API in formato Problem Details.
- Immagine Docker unica (API e frontend) e workflow di rilascio su GHCR.
- `GET /api/pdf/test`: PDF di prova generato con WeasyPrint, temporaneo fino a M5.

[Non rilasciato]: https://github.com/Cruciat/gym_split_planner/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/Cruciat/gym_split_planner/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Cruciat/gym_split_planner/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Cruciat/gym_split_planner/releases/tag/v0.1.0
