# Changelog

Tutte le modifiche rilevanti, per versione. Formato basato su [Keep a Changelog](https://keepachangelog.com/it-IT/1.1.0/); versioni secondo [SemVer](https://semver.org/lang/it/).

## [Non rilasciato]

### Aggiunto

- Varianti di un esercizio toccandone il nome: candidati con attrezzo, simboli, punteggio e cambi di volume in verde se avvicinano alla fascia e in arancione se allontanano; «Perché?» con le voci del punteggio; esclusi in fondo, scelti solo dopo conferma.
- Variante della seconda seduta: «Nessuna variante», gli esercizi della famiglia, poi le altre famiglie con la ricerca per nome.
- Rigenerazione dall'editor: differenze con le preferenze attuali, tutte spuntate, applicazione solo di quelle scelte; gli esercizi bloccati restano e sono contati.
- Primi test end-to-end con Playwright sull'app compilata, su desktop e telefono (`make e2e`), anche nella CI.
- Editor della scheda: giorni in schede, esercizi con famiglia, simboli delle etichette, variante della seconda seduta e nota; serie e ripetizioni modificabili nella riga, lucchetto, facoltativo, settimane alterne; aggiunta (famiglia, poi esercizio), cambio di famiglia ed eliminazione degli esercizi.
- Giorni: aggiunta, nome e volte a settimana (con conferma se si perdono varianti della seconda seduta), spostamento, eliminazione con conferma.
- Riordino di giorni ed esercizi trascinandoli; sul telefono, e per la tastiera, con la modalità "Riordina" e le frecce.
- Pannello del volume con fasce, stato a parole e con icona, filtro (prioritari, con obiettivo, tutti) e muscoli personalizzati segnati; avvisi che portano al muscolo, al giorno o all'esercizio. Sul telefono una barra con il riassunto apre il pannello a tutto schermo.
- Salvataggio automatico in coda, una modifica alla volta: indicatore di stato, "Riprova" senza rete, ricarica con avviso se la scheda è cambiata su un altro dispositivo.
- Elenco delle schede con split, giorni, data di modifica e scheda attiva; rinomina, duplica, rendi attiva ed elimina con conferma. L'app si apre sulla scheda attiva, o sull'elenco se non ce n'è.
- Creazione guidata in tre passi: split predefinito o scheda vuota, preferenze (già pronte), nome; poi si apre la scheda.
- Preferenze della scheda: ordine degli attrezzi, durata massima, personalizzazioni di muscoli ed etichette con il valore del catalogo e il ripristino. Si salvano da sole; gli errori compaiono accanto ai campi.
- API delle schede (tappa M4, ancora senza interfaccia): split predefiniti, creazione da uno split con generazione automatica o vuota, scheda completa con volumi, sedute e avvisi, elenco, rinomina, duplicazione, eliminazione, scheda attiva.
- Controllo delle revisioni tra dispositivi: `ETag` e `If-Match` sulle schede, con `412` se la scheda è cambiata nel frattempo.
- Gli avvisi di slot vuoto dicono quali etichette escludono gli esercizi della famiglia.
- API per modificare una scheda: preferenze e personalizzazioni con i valori del catalogo e quelli effettivi; giorni (aggiunta, modifica, eliminazione, ordine); slot (aggiunta con il miglior candidato, cambio di esercizio o di famiglia, variante della seconda seduta, serie, ripetizioni, facoltativo, settimane alterne, lucchetto, nota, eliminazione, ordine); candidati di uno slot con punteggio ed effetto sul volume.
- API della rigenerazione: anteprima delle differenze con le preferenze correnti (slot bloccati esclusi e contati) e applicazione di tutte o di una parte, senza toccare serie e ripetizioni.
- API delle impostazioni globali: lettura, sostituzione validata e valori iniziali; le analisi delle schede si aggiornano subito.

### Modificato

- Caricamento del catalogo per i calcoli più leggero: una modifica di una scheda risponde in circa 30 ms.

## [0.4.0] - 2026-10-28

Tappa M3: il catalogo. La banca dati degli esercizi si consulta e si modifica dall'app, dal computer e dal telefono (US-01 → US-08).

### Aggiunto

- Navigazione tra Schede, Catalogo e Impostazioni: in alto su computer, in basso su telefono. Schede e Impostazioni sono ancora segnaposto.
- Elenco degli esercizi con filtri combinabili (gruppo, muscolo come P o anche S, famiglia, attrezzo, etichetta con o senza, confidenza, ricerca per nome) che restano nell'URL; su telefono, elenco a schede e filtri in un pannello dal basso.
- Dettaglio dell'esercizio con muscoli P e S, etichette e note, famiglie, varianti cliccabili e fonti.
- Creazione e modifica degli esercizi: griglia dei muscoli a tre stati, etichette con nota, fonti (anche nuove), errori accanto ai campi, conferma prima di uscire senza salvare.
- Disattivazione, riattivazione ed eliminazione degli esercizi; un esercizio usato in una scheda si può solo disattivare.
- Famiglie, etichette e muscoli modificabili in linea, ciascuno nella sua scheda del catalogo; eliminazioni con conferma che riporta gli utilizzi.
- Selezione multipla nell'elenco degli esercizi per assegnare o togliere un'etichetta a più esercizi insieme.
- API del catalogo: `GET /api/catalog` (con `ETag`), esercizi, fonti, famiglie, muscoli ed etichette in lettura e scrittura, con gli utilizzi prima di eliminare. Gli errori `rule-violation` elencano tutte le regole violate con il loro campo; `invalid-band` protegge le fasce personalizzate delle schede.

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

[Non rilasciato]: https://github.com/Cruciat/gym_split_planner/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/Cruciat/gym_split_planner/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Cruciat/gym_split_planner/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Cruciat/gym_split_planner/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Cruciat/gym_split_planner/releases/tag/v0.1.0
