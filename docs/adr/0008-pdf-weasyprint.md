# ADR 0008 — PDF generati dal server con WeasyPrint da template HTML

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

La scheda si scarica in PDF A4 identico da qualsiasi dispositivo (US-30 CA3), con tabelle, caselle per annotare carichi e salti pagina controllati (una pagina per giorno).

## Decisione

- Il backend genera il PDF con **WeasyPrint** a partire da un template **Jinja2** (HTML) e da un foglio di stile CSS per la stampa (`@page`, interruzioni di pagina, intestazioni ripetute).
- Font incorporati nell'immagine Docker, così il risultato non dipende dal sistema.
- Endpoint dedicato che restituisce il file con un nome comprensibile (es. `ppl-6-giorni-2026-10-27.pdf`).

## Alternative considerate

- **Stampa dal browser con CSS di stampa:** nessuna dipendenza lato server, ma risultato diverso tra browser e telefoni.
- **Chromium headless (Playwright) lato server:** fedeltà ottima, ma aggiunge alcune centinaia di MB all'immagine.
- **ReportLab:** controllo totale, ma il layout si scrive in codice, lento da modificare.

## Conseguenze

- Il layout del PDF si modifica con HTML e CSS, rapido da iterare.
- L'immagine Docker include le librerie di sistema di WeasyPrint (Pango); da verificare in M0.
- WeasyPrint non esegue JavaScript: il template deve ricevere dati già calcolati, coerente con ADR 0007.
