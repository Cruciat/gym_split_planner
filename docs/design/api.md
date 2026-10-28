# Contratto delle API — Fase 1

| Campo | Valore |
| --- | --- |
| Stato | Bozza v0.1, in revisione |
| Data | 2026-10-28 |
| Riferimenti | Specifica fase 1 v0.2; modello dati v0.2; algoritmo v0.2; ADR 0002, 0007, 0011, 0013, 0014 |

Questo documento fissa forma e comportamento delle API: risorse, endpoint, formati, errori, concorrenza. Non elenca ogni campo di ogni schema: la fonte di verità dei campi è lo schema OpenAPI generato da FastAPI, che deve rispettare le regole e le forme descritte qui. Le forme principali sono comunque mostrate con esempi (§ 7, § 8).

## 1. Principi

1. **Un solo client, scritto insieme al server.** Il frontend Vue è l'unico consumatore. Le API servono a lui, non a terzi: niente versioni nell'URL (`/api`, non `/api/v1`), perché client e server si rilasciano sempre insieme nella stessa immagine (ADR 0009).
2. **Il server calcola, il client mostra** (ADR 0007). Volumi, stati delle fasce, punteggi, durate, avvisi e anteprime arrivano già calcolati. Il client non ricalcola nulla; può solo filtrare e ordinare dati già ricevuti.
3. **Ogni modifica a una scheda restituisce la scheda intera, con l'analisi aggiornata.** Una scheda ha al più qualche decina di slot: rimandarla tutta costa pochi kilobyte e qualche millisecondo, e il client sostituisce il suo stato senza logica di aggiornamento parziale. È anche ciò che rende verificabile NF1 (pannello aggiornato entro 300 ms).
4. **Catalogo caricato in blocco.** Il catalogo è piccolo (decine di muscoli e famiglie, meno di 500 esercizi anche in futuro): un endpoint lo restituisce tutto e i filtri di US-01 si applicano nel client, istantanei. Niente paginazione in fase 1.
5. **Forme prevedibili.** Stesse convenzioni per tutte le risorse (§ 2), stessi errori (§ 3), stessa concorrenza (§ 4).

## 2. Convenzioni

| Aspetto | Regola |
| --- | --- |
| Prefisso | `/api`. Tutto il resto dell'URL è servito dal frontend (ADR 0009) |
| Formato | JSON UTF-8. Eccezioni: PDF (§ 6.10), esportazione e importazione (§ 6.11) |
| Nomi dei campi | `snake_case`, in inglese (ADR 0013) |
| Identificatori | `id` intero negli URL e nei riferimenti tra risorse. I `code` sono attributi: compaiono nelle risposte, nel JSON delle preferenze (chiavi delle personalizzazioni) e nell'esportazione |
| `code` | Generato dal nome alla creazione (minuscole, trattini) se non fornito; **immutabile** dopo la creazione, per non rompere seed, esportazioni e personalizzazioni |
| Valori enumerati | Gli stessi del database (`priority`, `standard`, `none`; `compound`, `isolation`…) |
| Numeri | Volumi e punti come numeri decimali; nessun arrotondamento lato server oltre a quello dei calcoli (multipli di 0,5 per i volumi) |
| Date | ISO 8601 in UTC, es. `2026-10-28T09:15:00Z` |
| Metodi | `GET` lettura; `POST` creazione e azioni; `PATCH` modifica parziale; `PUT` sostituzione intera o ordinamento; `DELETE` eliminazione |
| Codici di successo | `200` con corpo; `201` creazione, con intestazione `Location`; `204` eliminazione senza corpo |
| Documentazione | Schema in `/api/openapi.json`, interfaccia di prova in `/api/docs`. Restano attivi: l'app è raggiungibile solo dalla tailnet (ADR 0011) |

## 3. Errori

Tutti gli errori usano il formato *Problem Details* (RFC 9457), con `Content-Type: application/problem+json`:

```json
{
  "type": "about:blank",
  "title": "Revisione non aggiornata",
  "status": 412,
  "code": "revision-mismatch",
  "detail": "La scheda è stata modificata da un altro dispositivo.",
  "current_revision": 18
}
```

`title` e `detail` sono in italiano e si possono mostrare all'utente così come sono. `code` è stabile e serve al client per decidere cosa fare. Campi aggiuntivi dipendono dal `code`.

| Stato | `code` | Quando | Campi aggiuntivi |
| --- | --- | --- | --- |
| 404 | `not-found` | Risorsa inesistente, anche se l'`id` esiste ma appartiene a un'altra scheda | |
| 409 | `in-use` | Eliminazione rifiutata perché la risorsa è usata (modello dati, § 6) | `usage` (§ 6.3) |
| 409 | `not-empty` | Importazione su istanza non vuota (US-31 CA3) | |
| 409 | `invalid-band` | Una modifica al catalogo renderebbe invalida la fascia effettiva di un muscolo in qualche scheda | `plans`: elenco di `id` e nomi |
| 412 | `revision-mismatch` | `If-Match` diverso dalla revisione attuale della scheda (§ 4) | `current_revision` |
| 422 | `validation-error` | Corpo o parametri non validi | `errors`: elenco di `{loc, msg, type}` come in Pydantic |
| 422 | `rule-violation` | Dati ben formati che violano una regola del dominio (es. esercizio di un'altra famiglia nello slot, variante della seconda seduta in un giorno fatto una volta sola) | `rule`: nome della prima regola violata; `violations`: tutte le regole violate, ciascuna `{rule, field, message}` (§ 3.1) |
| 428 | `revision-required` | Modifica a una scheda senza `If-Match` | |
| 500 | `internal-error` | Errore imprevisto; il dettaglio va nei log, non nella risposta | |

Il gestore degli errori di validazione di FastAPI viene sostituito, così anche i 422 automatici hanno questa forma.

### 3.1 Regole violate

Un `rule-violation` elenca **tutte** le regole violate dalla richiesta, così la form le mostra in una volta. `field` è il nome del campo del corpo a cui la regola si riferisce (`null` se riguarda l'insieme); `message` è in italiano e si mostra accanto al campo. `detail` riunisce i messaggi.

```json
{
  "type": "about:blank",
  "title": "Dati non accettati",
  "status": 422,
  "code": "rule-violation",
  "detail": "Serve almeno un muscolo P. Esiste già un esercizio chiamato «Dip».",
  "rule": "primary-muscle-required",
  "violations": [
    {"rule": "primary-muscle-required", "field": "muscles", "message": "Serve almeno un muscolo P."},
    {"rule": "name-taken", "field": "name", "message": "Esiste già un esercizio chiamato «Dip»."}
  ]
}
```

Regole del catalogo:

| `rule` | Quando |
| --- | --- |
| `primary-muscle-required` | Esercizio senza muscoli con livello P |
| `secondary-family-distinct` | Famiglia secondaria uguale alla principale |
| `name-taken` | Nome già usato da un altro esercizio (senza distinguere maiuscole) |
| `invalid-code`, `code-taken` | `code` fornito alla creazione malformato o già usato |
| `unknown-reference` | Famiglia, attrezzo, muscolo, etichetta o fonte inesistente |
| `duplicate-muscle`, `duplicate-tag` | Lo stesso muscolo o la stessa etichetta due volte nello stesso esercizio |
| `band-required` | Muscolo con un obiettivo (prioritario o non prioritario) senza minimo o massimo della fascia |
| `band-order`, `band-negative` | Fascia con minimo non inferiore al massimo, o minimo negativo |
| `points-required` | Etichetta con effetto bonus o penalità e punti non positivi |

## 4. Concorrenza

Il servizio ha un solo utente, ma più dispositivi: puoi avere la scheda aperta sul computer e sul telefono. Con il salvataggio automatico (US-19 CA3), una modifica fatta da un dispositivo con dati vecchi potrebbe annullarne una fatta dall'altro senza che te ne accorga. Per evitarlo, le schede usano il **controllo ottimistico con revisione**:

1. Ogni scheda ha una `revision` (modello dati, `plan.revision`) che cresce di 1 a ogni modifica della scheda, dei suoi giorni, dei suoi slot o delle sue preferenze.
2. Ogni risposta che contiene una scheda ha l'intestazione `ETag: "<revision>"` e il campo `revision` nel corpo.
3. Ogni richiesta che modifica una scheda deve avere `If-Match: "<revision>"`. Senza: `428 revision-required`. Con un valore vecchio: `412 revision-mismatch`, e niente viene modificato.
4. Alla risposta `412`, il client ricarica la scheda, mostra un avviso ("modificata da un altro dispositivo, ricaricata") e lascia ripetere l'ultima azione.

`If-Match` accetta la revisione tra virgolette (`"17"`, come l'`ETag`), con il prefisso `W/` o senza virgolette (`17`). Un valore che non è un numero vale come revisione sbagliata: `412` con `current_revision`.

Nel client le modifiche alla stessa scheda vanno in una **coda**: una alla volta, ognuna con la revisione restituita dalla precedente. Così modifiche rapide dallo stesso dispositivo non si scontrano tra loro.

Il catalogo non usa revisioni: le modifiche al catalogo sono rare e fatte da form esplicite, e l'ultima scrittura vince. È un compromesso dichiarato; se diventasse un problema, lo stesso meccanismo si estende agli esercizi.

## 5. Risorse e relazioni

```
/api
├── health, settings
├── catalog                      (lettura in blocco)
├── muscles/{id}
├── families/{id}
├── exercises/{id}
├── tags/{id}                    (+ assign, unassign)
├── sources/{id}
├── splits                       (solo lettura)
├── plans/{id}
│   ├── settings, preferences
│   ├── days/{day_id}
│   │   └── slots                (creazione, ordinamento)
│   ├── slots/{slot_id}          (+ candidates)
│   ├── regenerate               (+ preview)
│   └── pdf
├── export
└── import
```

Gli slot si modificano con un URL corto (`/plans/{id}/slots/{slot_id}`), senza il giorno: l'`id` dello slot è già univoco e il client non deve ricordare in che giorno sta. Il server verifica comunque che lo slot appartenga alla scheda dell'URL.

## 6. Endpoint

### 6.1 Sistema

| Metodo e percorso | Descrizione | Storie |
| --- | --- | --- |
| `GET /api/health` | `{"status": "ok", "version": "1.2.0", "database": "ok"}`. Usato dal controllo di salute del container | US-41 |
| `GET /api/settings` | Impostazioni globali (`app_setting`): pesi dei livelli, tetto per seduta, pesi del punteggio, parametri della durata, testo del riscaldamento, RIR | US-20 |
| `PUT /api/settings` | Sostituisce le impostazioni, con validazione (pesi ≥ 0, tetto > 0…). Effetto immediato sulle analisi; la generazione già fatta non cambia finché non si rigenera | US-20 |

### 6.2 Catalogo in lettura

`GET /api/catalog` restituisce tutto il catalogo in una risposta:

| Campo | Contenuto |
| --- | --- |
| `muscle_groups` | Gruppi in ordine |
| `muscles` | Muscoli con gruppo, priorità e fascia del catalogo |
| `equipment` | Attrezzi in ordine |
| `families` | Famiglie con gruppo e descrizione |
| `tags` | Etichette con simbolo, colore, effetto, punti |
| `exercises` | Riepiloghi degli esercizi: `id`, `code`, `name`, famiglie, `family_rank`, attrezzo, `kind`, allungamento, confidenza, `is_active`, mappa muscolare (`[{muscle_id, level}]`), etichette (`[{tag_id, note}]`) |
| `sources` | Fonti |
| `stretches`, `daily_routine` | Stretching e mini-allenamento |

I riepiloghi contengono già la mappa muscolare e le etichette: bastano per tutti i filtri di US-01 CA2 e per la lista. Le note lunghe e le fonti per esercizio stanno nel dettaglio.

| Metodo e percorso | Descrizione | Storie |
| --- | --- | --- |
| `GET /api/catalog` | Tutto il catalogo, come sopra. Intestazione `ETag` calcolata sul contenuto: il client può usare `If-None-Match` e ricevere `304` se nulla è cambiato | US-01 |
| `GET /api/exercises/{id}` | Dettaglio: tutti i campi, note, fonti, etichette con note, famiglie, **varianti** (gli altri esercizi attivi delle sue famiglie, ordinati per `family_rank`) | US-02 |

### 6.3 Catalogo in scrittura

| Metodo e percorso | Descrizione | Storie |
| --- | --- | --- |
| `POST /api/exercises` | Crea un esercizio. Corpo come il dettaglio, senza `id`: campi, mappa muscolare, etichette con note, `source_ids`. Almeno un muscolo P (`rule-violation` altrimenti) | US-04 |
| `PUT /api/exercises/{id}` | Sostituisce l'esercizio (la form invia sempre tutto). `is_active` si cambia qui | US-03, US-05 |
| `DELETE /api/exercises/{id}` | Elimina un esercizio mai usato; se usato in una scheda, `409 in-use` (va disattivato) | US-05 |
| `PATCH /api/muscles/{id}` | Modifica nome, nome breve, priorità, fascia, note. Se la nuova fascia renderebbe invalida una scheda: `409 invalid-band` | US-07 |
| `POST /api/families` | Crea una famiglia (nome, gruppo, descrizione) | US-06 |
| `PATCH /api/families/{id}` | Modifica nome, descrizione, gruppo, ordine | US-06 |
| `DELETE /api/families/{id}` | Elimina; `409 in-use` se ha esercizi principali o slot | US-06 |
| `POST /api/tags` | Crea un'etichetta | US-08 |
| `PATCH /api/tags/{id}` | Modifica nome, simbolo, colore, effetto, punti, visibilità, descrizione, ordine | US-08 |
| `DELETE /api/tags/{id}` | Elimina con assegnazioni e personalizzazioni (il client chiede conferma dopo aver letto `usage`) | US-08 |
| `POST /api/tags/{id}/assign` | `{"exercise_ids": [..], "note": "…"}`: assegna a più esercizi; la nota vale per tutti, ed è facoltativa. Se un esercizio l'ha già, la nota viene aggiornata solo se fornita | US-08 CA2 |
| `POST /api/tags/{id}/unassign` | `{"exercise_ids": [..]}`: toglie l'etichetta | US-08 CA2 |
| `POST /api/sources`, `PATCH /api/sources/{id}`, `DELETE /api/sources/{id}` | Gestione delle fonti, per la form dell'esercizio | US-03 |

Gruppi muscolari, muscoli e attrezzi non si creano né si eliminano dall'interfaccia in fase 1: arrivano dal seed o dall'importazione.

Note sui corpi:

- Nei campi di testo facoltativi una stringa vuota o di soli spazi vale `null`; gli spazi ai bordi si tolgono sempre.
- `POST /api/exercises` accetta un `code` facoltativo; senza, il server lo genera dal nome e, se è già usato, aggiunge `-2`, `-3`… `PUT` non lo accetta: il `code` non cambia.
- Le fonti nuove continuano la numerazione dell'Excel (`src-49`, `src-50`…). `url`, se presente, deve iniziare con `http://` o `https://`, perché l'interfaccia lo apre come link.
- Nei `PATCH` un campo omesso resta com'è; `null` svuota solo i campi facoltativi (note, descrizioni), mentre per quelli obbligatori è un `validation-error`.
- Famiglie ed etichette nuove ricevono il `code` dal nome come gli esercizi, e vanno in fondo all'ordine (`sort_order`).
- `PATCH /api/muscles/{id}` con `priority: "none"` svuota la fascia, anche se il corpo contiene minimo e massimo.
- `symbol` di un'etichetta è uno dei nomi dell'insieme chiuso del wireframe (§ 4.4): `warning`, `ban`, `info`, `star`, `heart`, `zap`, `flag`, `eye-off`.
- `assign` e `unassign` rispondono con gli utilizzi aggiornati dell'etichetta, nella stessa forma di `GET /api/tags/{id}/usage`. Un esercizio inesistente nell'elenco è un `rule-violation` (`unknown-reference`) e non cambia nulla.
- Eliminare un'etichetta personalizzata da una scheda modifica le preferenze di quella scheda: la sua `revision` cresce di 1 (§ 4).

**Utilizzi.** Prima di un'eliminazione il client chiede cosa verrebbe toccato, per scrivere la conferma con i numeri giusti:

| Metodo e percorso | Risposta |
| --- | --- |
| `GET /api/exercises/{id}/usage` | `{"plans": [{"id", "name", "slots"}]}` |
| `GET /api/families/{id}/usage` | `{"exercises": n, "secondary_exercises": n, "split_slots": n, "plans": [...]}` |
| `GET /api/tags/{id}/usage` | `{"exercises": n, "plans_with_overrides": [{"id", "name"}]}` |

La stessa struttura è il campo `usage` dell'errore `409 in-use`.

### 6.4 Split predefiniti

| Metodo e percorso | Descrizione | Storie |
| --- | --- | --- |
| `GET /api/splits` | Preset con descrizione, giorni (nome, volte a settimana) e slot (famiglia, serie, ripetizioni, facoltativo, peso, nota). Serve alla procedura guidata | US-10 CA1 |

### 6.5 Schede

| Metodo e percorso | Descrizione | Storie |
| --- | --- | --- |
| `GET /api/plans` | Elenco dalla modificata più di recente: `id`, `name`, `split_name`, `days_per_week`, `is_active`, `updated_at` | US-19 CA1 |
| `POST /api/plans` | `{"split_id": 3 \| null, "name": "…"?, "preferences": {…}?}`. Con `split_id`: copia lo split e genera (US-12). Con `null`: scheda vuota. Senza nome: "<nome dello split> — gg/mm/aaaa" o "Scheda vuota — gg/mm/aaaa". Le preferenze si normalizzano e validano come in § 6.6 e guidano già la generazione. Uno `split_id` inesistente è un `rule-violation` (`unknown-reference`). `201` con la scheda completa | US-10, US-11, US-12 |
| `GET /api/plans/{id}` | Scheda completa con analisi (§ 7) | US-13 |
| `PATCH /api/plans/{id}` | Rinomina. Richiede `If-Match` | US-19 CA2 |
| `DELETE /api/plans/{id}` | Elimina con giorni e slot. Non richiede `If-Match`: l'eliminazione è comunque confermata nell'interfaccia | US-19 CA2 |
| `POST /api/plans/{id}/duplicate` | Copia completa con nome "… (copia)", non attiva. `201` | US-19 CA2 |
| `POST /api/plans/{id}/activate` | La rende l'unica scheda attiva. Non conta come modifica della scheda: non richiede `If-Match` e non cambia la revisione | US-19 CA2 |

### 6.6 Preferenze e personalizzazioni

| Metodo e percorso | Descrizione | Storie |
| --- | --- | --- |
| `GET /api/plans/{id}/settings` | Vista per la schermata delle preferenze: ordine degli attrezzi, durata massima e, per ogni muscolo e ogni etichetta, i tre livelli `catalog`, `override`, `effective` (§ 8.1) | US-11 |
| `PUT /api/plans/{id}/preferences` | Sostituisce il JSON delle preferenze (modello dati, § 4.7). Il server normalizza: toglie le personalizzazioni uguali al catalogo e le chiavi inesistenti, poi valida sui valori effettivi. Restituisce la scheda completa. Richiede `If-Match` | US-11 |

Il ripristino di un valore ("torna al catalogo") non ha un endpoint proprio: il client invia le preferenze senza quella voce. Una regola sola, meno superficie.

Cambiare le preferenze **non** rigenera la scheda: aggiorna solo l'analisi (volumi e stati delle fasce con i nuovi valori effettivi). Per applicare le nuove preferenze agli esercizi si usa la rigenerazione (§ 6.9), che mostra prima le differenze.

### 6.7 Giorni

Tutte richiedono `If-Match` e restituiscono la scheda completa.

| Metodo e percorso | Descrizione | Storie |
| --- | --- | --- |
| `POST /api/plans/{id}/days` | `{"name": "Push", "times_per_week": 2, "position": 3?}`. Senza posizione va in fondo | US-21 CA1 |
| `PATCH /api/plans/{id}/days/{day_id}` | Nome e volte a settimana. Se le volte scendono a 1, le varianti della seconda seduta del giorno vengono rimosse nella stessa operazione; il client le ha già mostrate nella conferma, perché le conosce dalla scheda | US-21 CA2, CA3 |
| `DELETE /api/plans/{id}/days/{day_id}` | Elimina il giorno con i suoi slot | US-21 CA4 |
| `PUT /api/plans/{id}/days/order` | `{"day_ids": [..]}`: tutti gli `id` dei giorni della scheda nel nuovo ordine, né uno di più né uno di meno | US-21 CA2 |

### 6.8 Slot

Tutte richiedono `If-Match` e restituiscono la scheda completa.

| Metodo e percorso | Descrizione | Storie |
| --- | --- | --- |
| `POST /api/plans/{id}/days/{day_id}/slots` | `{"family_id": 4, "exercise_id": 12?, "sets": 3?, "rep_min": 8?, "rep_max": 12?, "position": 2?}`. Senza esercizio il server assegna il miglior candidato; senza serie e ripetizioni usa i default del tipo di esercizio (multiarticolare 3 × 6-12, isolamento 3 × 10-15) | US-16 CA3 |
| `PATCH /api/plans/{id}/slots/{slot_id}` | Modifica parziale: `exercise_id`, `second_exercise_id` (anche `null`), `family_id`, `sets`, `rep_min`, `rep_max`, `is_optional`, `weekly_weight`, `locked`, `note`. Regole sotto | US-14, US-15, US-16, US-17 |
| `DELETE /api/plans/{id}/slots/{slot_id}` | Toglie lo slot | US-16 CA3 |
| `PUT /api/plans/{id}/days/{day_id}/slots/order` | `{"slot_ids": [..]}`, come per i giorni | US-16 CA2 |
| `GET /api/plans/{id}/slots/{slot_id}/candidates` | Candidati con punteggio e anteprima del volume. Parametro `session=1` (esercizio principale, default) o `session=2` (variante della seconda seduta). Non modifica nulla | US-14, US-17 |

Regole del `PATCH` sullo slot:

- `exercise_id` deve avere la famiglia dello slot come principale o secondaria (`rule-violation` altrimenti). Un esercizio escluso da un'etichetta è accettato: l'esclusione vale solo per le scelte automatiche (algoritmo, § 3.1).
- `family_id` diverso dall'attuale cambia famiglia (US-16 CA5): se nello stesso corpo non c'è un `exercise_id`, il server assegna il miglior candidato della nuova famiglia.
- `second_exercise_id` è ammesso solo se il giorno si ripete almeno 2 volte, e deve essere diverso dall'esercizio principale. Può essere di qualunque famiglia.
- Lo slot bloccato si può comunque modificare a mano: il lucchetto protegge solo dalla rigenerazione (US-15 CA2).
- I campi si applicano tutti o nessuno, in una transazione.

Risposta di `candidates` (estratto):

```json
{
  "slot_id": 57,
  "session": 1,
  "current_exercise_id": 29,
  "candidates": [
    {
      "exercise_id": 31,
      "name": "Kickback ai cavi",
      "family_match": "primary",
      "score": 4.933,
      "score_breakdown": {"confidence": 0.9, "equipment": 2.667, "stretch": 0.2, "family": 1.0, "rank": 0.167, "tags": 0.0},
      "badges": [],
      "excluded_by": [],
      "volume_delta": [{"muscle_id": 7, "code": "triceps-long", "delta": 2.0}]
    }
  ]
}
```

- Ordine: candidati non esclusi per punteggio (algoritmo, § 3.3), poi gli esclusi, ciascuno con `excluded_by` (codici delle etichette). Con `session=2`, prima la famiglia dello slot, poi le altre (`family_match: "other"`).
- `volume_delta` contiene solo i muscoli che cambiano (algoritmo, § 5).
- `score_breakdown` serve a spiegare la scelta nell'interfaccia ("perché questo?"): la somma delle voci è `score`.

### 6.9 Rigenerazione

| Metodo e percorso | Descrizione | Storie |
| --- | --- | --- |
| `POST /api/plans/{id}/regenerate/preview` | Calcola le differenze tra la scheda e una nuova generazione con le preferenze correnti, senza modificare nulla. Per ogni slot che cambierebbe: `slot_id`, giorno, esercizio attuale e proposto, effetto sul volume. Non richiede `If-Match`, ma restituisce la `revision` su cui è calcolata | US-18 CA2 |
| `POST /api/plans/{id}/regenerate` | `{"slot_ids": [..]}`: applica le differenze degli slot scelti (tutti o una parte). Richiede `If-Match` con la revisione dell'anteprima: se nel frattempo la scheda è cambiata, `412` e si ricalcola l'anteprima | US-18 |

È un `POST` anche l'anteprima perché è un calcolo, non la lettura di una risorsa, e in futuro potrà ricevere opzioni nel corpo (per esempio il ribilanciamento della fase 2).

### 6.10 PDF

| Metodo e percorso | Descrizione | Storie |
| --- | --- | --- |
| `GET /api/plans/{id}/pdf` | `application/pdf` con `Content-Disposition: attachment; filename="<nome-della-scheda>-<data>.pdf"` (nome ridotto a minuscole e trattini, es. `ppl-6-giorni-2026-10-28.pdf`, come in ADR 0008). Parametro facoltativo `weeks` (1-8, default 4): quante colonne per carichi e ripetizioni | US-30 |

Il PDF si genera a ogni richiesta, senza cache: costa qualche centinaio di millisecondi ed è sempre allineato alla scheda.

Fino a M5 esiste anche `GET /api/pdf/test`, un PDF di prova che verifica WeasyPrint nell'immagine (issue #4). Viene rimosso quando arriva il PDF della scheda.

### 6.11 Esportazione e importazione

| Metodo e percorso | Descrizione | Storie |
| --- | --- | --- |
| `GET /api/export` | File JSON scaricabile, `schede-export-<data>.json`, con catalogo, schede e impostazioni. Tutti i riferimenti per `code` (per le schede, per posizione), nessun `id` | US-31 CA1 |
| `POST /api/import` | `multipart/form-data` con il file. Su istanza vuota (nessun esercizio e nessuna scheda): importa tutto in una transazione e restituisce i conteggi. Altrimenti `409 not-empty` | US-31 CA2, CA3 |

Forma del file:

```json
{
  "format": "gym-split-planner-export",
  "format_version": 1,
  "exported_at": "2026-10-28T09:15:00Z",
  "app_version": "1.0.0",
  "settings": {},
  "catalog": {"muscle_groups": [], "muscles": [], "equipment": [], "families": [], "tags": [], "sources": [], "exercises": [], "stretches": [], "daily_routine": [], "splits": []},
  "plans": []
}
```

`format_version` cresce quando la forma cambia; l'importazione converte le versioni precedenti, come le preferenze (modello dati, § 4.7). Il test di andata e ritorno (US-31 CA2) esporta, importa in un database vuoto, riesporta e confronta i due file escluso `exported_at`.

"Istanza vuota" non conta il seed: per importare su un'installazione nuova si avvia il container con la variabile `GSP_SKIP_SEED=1`. Così il seed non si mescola mai con i dati importati.

## 7. La scheda completa

Forma restituita da `GET /api/plans/{id}` e da tutte le modifiche. Estratto con un giorno e uno slot (l'estensione ai cavi scelta a mano al posto di quella alla macchina, quindi con il simbolo del collo):

```json
{
  "id": 4,
  "name": "PPL 6 giorni — 28/10/2026",
  "revision": 17,
  "is_active": true,
  "split": {"id": 2, "code": "ppl-6", "name": "Push/Pull/Legs, 6 giorni"},
  "created_at": "2026-10-28T09:15:00Z",
  "updated_at": "2026-10-28T09:40:12Z",
  "preferences": {"version": 2, "equipment_order": ["machine", "cable", "free-weight", "bodyweight"], "max_session_minutes": 75, "overrides": {"muscles": {}, "tags": {}}},
  "days": [
    {
      "id": 11,
      "name": "Push",
      "position": 1,
      "times_per_week": 2,
      "stretches": [{"id": 1, "code": "pec-doorway", "name": "Stretch del petto allo stipite…", "dose": "30 s, ripetuto fino a circa 60 s"}],
      "slots": [
        {
          "id": 56,
          "position": 5,
          "family": {"id": 11, "code": "triceps-overhead", "name": "Estensione sopra la testa"},
          "exercise": {
            "id": 24, "code": "cable-overhead-extension", "name": "Estensione sopra la testa ai cavi (barra o corda)",
            "equipment": "cable", "kind": "isolation", "is_active": true,
            "badges": [{"tag_id": 2, "code": "neck-caution", "name": "Collo: attenzione", "symbol": "warning", "color": "warning", "note": null}]
          },
          "second_exercise": null,
          "sets": 3, "rep_min": 10, "rep_max": 15,
          "is_optional": false, "weekly_weight": 1.0, "locked": false, "note": null,
          "rest_seconds": 90,
          "rir": "0-2",
          "last_set_to_failure": true
        }
      ]
    }
  ],
  "analysis": {
    "volumes": [
      {
        "muscle_id": 7, "code": "triceps-long", "name": "Tricipite, capo lungo", "group_code": "triceps",
        "volume": 8.0, "priority": "priority", "weekly_min": 10, "weekly_max": 18,
        "status": "below", "overridden": false
      }
    ],
    "sessions": [
      {"day_id": 11, "session": 1, "minutes": 60.5, "max_muscle_volume": {"muscle_id": 8, "volume": 8.0}},
      {"day_id": 11, "session": 2, "minutes": 60.5, "max_muscle_volume": {"muscle_id": 8, "volume": 8.0}}
    ],
    "warnings": [
      {"code": "volume-below", "muscle_id": 7, "volume": 8.0, "weekly_min": 10, "weekly_max": 18}
    ]
  }
}
```

Note sui campi:

- `badges` contiene solo le etichette con `show_badge` attivo, in `sort_order`. Le etichette senza simbolo visibile hanno ancora effetto sul punteggio ma non compaiono qui.
- `rest_seconds`, `rir` e `last_set_to_failure` sono **derivati** (tipo di esercizio, attrezzo, impostazioni `duration_params` ed `effort`): servono a schermata e PDF, non si salvano.
- `analysis.volumes` ha una riga per ogni muscolo, anche quelli a volume zero, con priorità e fascia **effettive**; `overridden` dice se la scheda li personalizza.
- `analysis.sessions` ha una riga per ogni seduta concreta (algoritmo, § 2.3): due per i giorni con almeno una variante della seconda seduta, una altrimenti.
- `analysis.warnings` usa i codici dell'algoritmo, § 8. È anche ciò che alimenta gli avvisi in pagina. Ogni avviso ha gli stessi campi, valorizzati secondo il codice: `day_id`, `session`, `slot_id` e `position` (slot vuoto), `family_id`, `muscle_id`, `volume`, `weekly_min` e `weekly_max` (fascia effettiva), `minutes`, `excluded_by` (per `empty-slot`: codici delle etichette che escludono i candidati della famiglia; vuoto se la famiglia non ha esercizi attivi).
- `analysis.volumes` riporta anche `short_name`, per tabelle strette e telefono.
- In `preferences.overrides` i campi non personalizzati valgono `null`: seguono il catalogo.

## 8. Altre forme

### 8.1 Vista delle personalizzazioni

`GET /api/plans/{id}/settings`, estratto:

```json
{
  "equipment_order": ["machine", "cable", "free-weight", "bodyweight"],
  "max_session_minutes": 75,
  "muscles": [
    {
      "muscle_id": 21, "code": "quads", "name": "Quadricipiti (vasti)",
      "catalog":   {"priority": "standard", "weekly_min": 6, "weekly_max": 10},
      "override":  {"weekly_max": 8},
      "effective": {"priority": "standard", "weekly_min": 6, "weekly_max": 8}
    }
  ],
  "tags": [
    {
      "tag_id": 2, "code": "neck-caution", "name": "Collo: attenzione",
      "catalog":   {"effect": "penalty", "points": 3},
      "override":  {},
      "effective": {"effect": "penalty", "points": 3}
    }
  ]
}
```

Con i tre livelli il client mostra il valore effettivo, segnala ciò che è personalizzato e sa a cosa tornerebbe il ripristino, senza ricalcolare nulla.

### 8.2 Differenze della rigenerazione

```json
{
  "revision": 17,
  "changes": [
    {
      "slot_id": 61, "day_id": 12, "day_name": "Pull", "position": 2,
      "current": {"exercise_id": 39, "name": "Pulley basso, presa larga"},
      "proposed": {"exercise_id": 38, "name": "Rematore con appoggio al petto"},
      "volume_delta": [{"muscle_id": 10, "code": "lats", "delta": 3.0}]
    }
  ]
}
```

## 9. Implementazione e verifica

- **Strati** (ADR 0005). I router FastAPI validano e traducono; i servizi aprono la transazione, controllano la revisione, chiamano il dominio, salvano, incrementano `revision` e costruiscono la risposta. Nessun calcolo nei router.
- **Un solo costruttore della scheda completa** (`build_plan_view`), usato da tutte le risposte che la restituiscono. Così la forma non può divergere tra endpoint.
- **Tipi del client generati.** `openapi-typescript` produce i tipi TypeScript dallo schema; il file generato è versionato e la CI lo rigenera e fallisce se cambia (ADR 0012). Ogni modifica al contratto è quindi visibile nella pull request.
- **Test di integrazione** (da M3) su un database temporaneo, uno o più per endpoint, più questi casi trasversali:

| ID | Caso | Atteso |
| --- | --- | --- |
| C1 | Modifica di uno slot senza `If-Match` | `428 revision-required`, nessuna modifica |
| C2 | Due modifiche con la stessa revisione | La prima `200` con `revision + 1`, la seconda `412` con `current_revision` |
| C3 | Ogni modifica della scheda | Risposta con la scheda completa, `ETag` uguale a `revision` |
| C4 | Slot di un'altra scheda nell'URL | `404 not-found` |
| C5 | Eliminazione di una famiglia usata | `409 in-use` con `usage` |
| C6 | Errore di validazione su un campo | `422 validation-error` in formato Problem Details |
| C7 | Esportazione, importazione su database vuoto, nuova esportazione | File identici escluso `exported_at` |
| C8 | Importazione su database con dati | `409 not-empty` |
| C9 | Volumi di `GET /api/plans/{id}` per ogni preset appena creato | Uguali ai valori di riferimento (dati iniziali, § 8.1) |
| C10 | Prestazioni: modifica di uno slot su una scheda `ppl-6` | Risposta sotto i 100 ms sul server (margine per NF1) |

## 10. Mappa delle storie utente

| Storia | Endpoint |
| --- | --- |
| US-01, US-02 | `GET /api/catalog`, `GET /api/exercises/{id}` |
| US-03, US-04, US-05 | `POST`, `PUT`, `DELETE /api/exercises…`, `/usage`, `/api/sources…` |
| US-06 | `/api/families…` |
| US-07 | `PATCH /api/muscles/{id}` |
| US-08 | `/api/tags…`, `assign`, `unassign` |
| US-10, US-12 | `GET /api/splits`, `POST /api/plans` |
| US-11 | `GET /api/plans/{id}/settings`, `PUT /api/plans/{id}/preferences` |
| US-13, US-20 | `analysis` nella scheda completa; `GET`/`PUT /api/settings` |
| US-14, US-17 | `GET …/slots/{slot_id}/candidates`, `PATCH …/slots/{slot_id}` |
| US-15, US-16 | `PATCH`, `POST`, `DELETE …/slots…`, `PUT …/slots/order` |
| US-18 | `POST …/regenerate/preview`, `POST …/regenerate` |
| US-19 | `GET`, `PATCH`, `DELETE /api/plans…`, `duplicate`, `activate` |
| US-21 | `…/days…` |
| US-30 | `GET /api/plans/{id}/pdf` |
| US-31 | `GET /api/export`, `POST /api/import` |
| US-40, US-41 | `GET /api/health` |

## 11. Decisioni prese in revisione

1. Default di serie e ripetizioni per uno slot aggiunto a mano senza indicarle (§ 6.8): 3 × 6-12 per i multiarticolari, 3 × 10-15 per l'isolamento. L'interfaccia li mostra già compilati e modificabili.
