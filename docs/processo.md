# Processo di sviluppo

| Campo | Valore |
| --- | --- |
| Stato | Bozza |
| Data | 2026-10-27 |

## 1. Principi

1. **Prima si decide, poi si costruisce.** Nessuna tappa parte finché i documenti di cui ha bisogno (specifica, ADR, modello dati, algoritmo, contratto delle API) non sono approvati.
2. **Fette verticali.** Ogni tappa produce qualcosa di funzionante dal database all'interfaccia, o comunque verificabile da sola.
3. **Il dominio prima dell'interfaccia.** I calcoli si scrivono e si testano prima delle schermate che li mostrano.
4. **Deploy presto.** La prima tappa porta sull'homelab una pagina vuota, per eliminare subito i rischi di infrastruttura.
5. **Niente entra senza test e senza CI verde.**

## 2. Fasi del progetto

| Fase | Contenuto |
| --- | --- |
| 1 | Catalogo consultabile e modificabile, creazione e modifica delle schede da split predefiniti, varianti, lucchetto, pannello volume, PDF, esportazione e importazione |
| 2 | Ribilanciamento automatico, split personalizzati salvati come preset, guida integrata |
| 3 | Registrazione degli allenamenti, progressione, storico, timer, app installabile |
| 4 | Mesocicli e scarichi programmati |

## 3. Documenti prima della fase 1

| Ordine | Documento | Serve a partire con |
| --- | --- | --- |
| 1 | Specifica della fase 1 e ADR 0001-0014 | Tutto |
| 2 | Modello dati | M1 |
| 3 | Algoritmo | M2 |
| 4 | Dati iniziali (famiglie, split Push/Pull e Full body, test di riferimento) | M1, M2 |
| 5 | Contratto delle API | M3 |
| 6 | Wireframe | M3, M4 |

M0 può partire appena sono accettati gli ADR 0002, 0004, 0009-0012.

## 4. Tappe della fase 1

| Tappa | Contenuto | Risultato verificabile |
| --- | --- | --- |
| M0 Scheletro | Repository, strumenti di qualità, CI, immagine su GHCR, deploy sull'homelab con Tailscale, PDF di prova | L'indirizzo della tailnet mostra l'app dal telefono; l'endpoint di prova restituisce un PDF |
| M1 Dati | Modello, migrazioni, seed con le famiglie, test di validità e di riferimento | Il database riproduce i volumi dell'Excel |
| M2 Motore | Volume, punteggio, generazione, stima della durata nel modulo di dominio | Test di riferimento verdi; copertura ≥ 90% |
| M3 Catalogo | API e schermate di consultazione e modifica | US-01 → US-08 soddisfatte |
| M4 Editor | Procedura guidata, scheda vuota, giorni, varianti, lucchetto, serie, rigenerazione, salvataggio | US-10 → US-21 soddisfatte; primi test Playwright |
| M5 PDF | Template e download | US-30 soddisfatta |
| M6 Chiusura | Esportazione e importazione, rifiniture, rilascio | US-31, US-40, US-41; rilascio v1.0.0 |

## 5. Ciclo di lavoro

1. **Issue** su GitHub con descrizione, criteri di accettazione e riferimento alle storie utente, assegnata a una tappa.
2. **Branch** dedicato (`feat/…`, `fix/…`, `docs/…`).
3. **Sviluppo con test.** Per il dominio i test si scrivono prima del codice.
4. **Pull request** con descrizione di cosa cambia e come verificarlo; CI verde obbligatoria.
5. **Revisione** del proprietario del progetto.
6. **Merge** con squash.
7. **Rilascio** a fine tappa: tag, immagine su GHCR, aggiornamento della versione nel monorepo dell'homelab.

## 6. Definizione di fatto

Vedi ADR 0012. In breve: criteri di accettazione verificati, test verdi, documentazione aggiornata, migrazione se serve, distribuito sull'homelab a fine tappa.

## 7. Strategia di test

| Livello | Cosa copre | Quando |
| --- | --- | --- |
| Unità (dominio) | Volume, punteggio, generazione, durata, validazioni | Sempre; soglia 90% |
| Riferimento | I volumi dei preset coincidono con quelli dell'Excel | Da M1 |
| Validità dei dati | Ogni esercizio ha una famiglia e un muscolo P; nessun riferimento rotto; ogni slot ha candidati | Da M1 |
| Integrazione API | Endpoint su database temporaneo | Da M3 |
| End-to-end | Crea scheda → cambia variante → scarica PDF | Da M4 |

## 8. Ruoli

- **Claude:** bozze di documenti e codice, test, pull request.
- **Proprietario del progetto:** revisione e approvazione di documenti e pull request, decisioni sulle domande aperte.
