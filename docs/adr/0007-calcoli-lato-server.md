# ADR 0007 — Volumi e punteggi calcolati solo dal backend

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

Il pannello volume deve aggiornarsi a ogni modifica (US-13 CA3) entro 300 ms (NF1), e il menu delle varianti deve mostrare l'effetto di ogni alternativa (US-14 CA1). Calcolare tutto nel browser darebbe risposte immediate, ma duplicherebbe in TypeScript la logica del modulo di dominio Python, con il rischio che le due versioni divergano.

## Decisione

- Il backend è l'unica fonte dei calcoli. Ogni modifica alla scheda è una richiesta all'API, che salva e restituisce la scheda aggiornata con i volumi ricalcolati e gli avvisi.
- Il menu delle varianti chiede al backend un'anteprima: per ogni candidato, la differenza di volume per muscolo rispetto alla scelta attuale.
- Il frontend applica la modifica in modo ottimistico solo per gli aspetti visivi (ordine, valori inseriti) e sostituisce i numeri con quelli restituiti dal server.

## Alternative considerate

- **Calcolo nel browser:** risposta immediata, ma doppia implementazione e doppi test.
- **Calcolo in WebAssembly dallo stesso codice Python (Pyodide):** elimina la duplicazione, ma aggiunge decine di MB e complessità di build.

## Conseguenze

- Una sola implementazione, testata una volta.
- L'app richiede la connessione al server per modificare le schede: accettabile, dato che si accede comunque tramite la tailnet.
- Con un carico di dati piccolo e la tailnet, il tempo di risposta atteso è ampiamente sotto i 300 ms; da verificare con un test in M4.
