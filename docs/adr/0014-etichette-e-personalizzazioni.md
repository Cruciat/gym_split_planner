# ADR 0014 — Etichette sugli esercizi e personalizzazioni per scheda

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-28 |

## Contesto

La prima bozza del modello dati aveva un campo fisso `neck` (ok, attenzione, evitare) con una nota, e una politica fissa nel punteggio. Due limiti:

1. **Rigidità.** Ogni altro vincolo personale (attrezzi assenti nella propria palestra, un fastidio nuovo a spalla o gomito, esercizi preferiti) richiederebbe nuove colonne, nuove regole nel punteggio e nuove migrazioni.
2. **Visibilità.** Un esercizio "Attenzione" scelto nella scheda deve essere riconoscibile a colpo d'occhio, con il suo accorgimento, anche nel PDF.

Inoltre la prima bozza permetteva di cambiare per scheda solo la priorità dei muscoli, non le fasce obiettivo, e la politica sul collo era un caso speciale nelle preferenze.

## Decisione

### Etichette

1. Si introduce l'**etichetta** (`tag`): un'entità del catalogo con nome, simbolo, colore, effetto sul punteggio e intensità.
   - Effetti: `none` (solo segnalazione), `bonus`, `penalty`, `exclude`.
   - Intensità: punti aggiunti o tolti al punteggio, per `bonus` e `penalty`.
   - Se `show_badge` è attivo, il simbolo compare accanto all'esercizio in catalogo, scheda e PDF.
2. Un esercizio può avere più etichette. Ogni assegnazione (`exercise_tag`) ha una **nota** propria, per esempio l'accorgimento per il collo specifico di quell'esercizio.
3. I campi `neck` e `neck_note` dell'esercizio vengono eliminati. I giudizi della ricerca diventano due etichette iniziali:
   - "Collo: attenzione", penalità di **3 punti**, simbolo di avviso;
   - "Collo: evitare", esclusione, simbolo di divieto.
   Gli esercizi con collo OK non hanno etichette sul collo, tranne quelli "OK a una condizione": per loro c'è una terza etichetta, "Collo: accorgimento", senza effetto sul punteggio, che porta la condizione come nota (dettagli nel documento sui dati iniziali).
4. Nel punteggio la voce "collo" viene sostituita dalla somma degli effetti delle etichette (dettagli nel documento sull'algoritmo).
5. Le esclusioni valgono solo per le operazioni automatiche (generazione, rigenerazione); l'utente può sempre scegliere a mano un esercizio escluso.

### Personalizzazioni per scheda

6. Il catalogo definisce i valori predefiniti: priorità e fasce dei muscoli, effetto e intensità delle etichette.
7. Una scheda salva solo le **personalizzazioni**, cioè le differenze rispetto al catalogo. Il valore effettivo è la personalizzazione se esiste, altrimenti il valore del catalogo.
8. Modificare il catalogo cambia quindi tutte le schede, tranne i valori che una scheda ha personalizzato.
9. Ogni valore personalizzato si può ripristinare al valore del catalogo, e l'interfaccia lo segnala come personalizzato.

## Alternative considerate

- **Campo fisso per il collo, più un simbolo:** risolve la visibilità ma non la rigidità; ogni nuovo vincolo richiede una migrazione.
- **Più campi fissi (collo, spalla, gomito, disponibilità):** cresce senza limite e ogni campo ha regole proprie nel punteggio.
- **Copia dei valori del catalogo nella scheda alla creazione:** schede del tutto stabili, ma una modifica globale (per esempio alzare le fasce dei prioritari) va ripetuta a mano su ogni scheda.

## Conseguenze

- Nuovi vincoli personali si aggiungono dall'interfaccia, senza codice né migrazioni. Esempi previsti: "Non c'è nella mia palestra" (esclusione), "Preferito" (bonus).
- Una sola regola per tutte le personalizzazioni: la scheda eredita dal catalogo, tranne ciò che personalizzi.
- Il punteggio resta confrontabile tra versioni: le etichette sul collo riproducono il comportamento della prima bozza, con una penalità più forte (3 punti invece di 2,4).
- Costo: due tabelle in più e una regola di risoluzione dei valori effettivi, da coprire con test.
- Supera la parte del modello dati e dell'algoritmo che prevedevano `neck`, `neck_note` e `neck_caution_policy`.
