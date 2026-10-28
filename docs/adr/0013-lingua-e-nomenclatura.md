# ADR 0013 — Italiano per interfaccia e documenti, inglese per il codice

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

L'utente usa l'italiano; la ricerca e i nomi degli esercizi sono in italiano. Il codice usa librerie e convenzioni in inglese, e lo schema dell'Excel mescolava nomi italiani.

## Decisione

- **Interfaccia, contenuti del catalogo, specifica e ADR:** italiano, con i termini tecnici inglesi d'uso comune lasciati in inglese (endpoint, seed, slot, CI).
- **Codice, nomi di tabelle e colonne, API, messaggi di commit:** inglese (`exercise`, `muscle`, `movement_family`, `plan`, `plan_slot`).
- La corrispondenza tra termini italiani e inglesi è nel glossario della specifica (sezione 4) ed è l'unico riferimento.
- I testi dell'interfaccia stanno in un unico file di traduzioni, anche se la lingua è una sola: evita testi sparsi nei componenti.

## Alternative considerate

- **Tutto in italiano, compreso il codice:** coerente con il dominio, ma stride con librerie, framework e strumenti, e rende il codice meno riutilizzabile.
- **Tutto in inglese, compresa l'interfaccia:** contrario alla preferenza dell'utente e ai contenuti della ricerca.

## Conseguenze

- Lo schema della banca dati cambia nomi rispetto all'Excel (`esercizi` → `exercise`); il seed fa la conversione.
- Il glossario va tenuto aggiornato quando si introduce un concetto nuovo.
