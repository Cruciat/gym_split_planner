# Specifica funzionale — Fase 1

| Campo | Valore |
| --- | --- |
| Stato | Bozza v0.2, in revisione |
| Data | 2026-10-28 |
| Riferimenti | Documento di ricerca "Ricerca schede palestra"; `banca_dati_esercizi.xlsx`; ADR 0001-0014 |
| Modifiche v0.2 | Etichette al posto del campo "collo" (US-08, ADR 0014); priorità, fasce ed effetti delle etichette personalizzabili per scheda (US-11) |

## 1. Scopo

Un servizio web personale per **consultare e modificare la banca dati degli esercizi** nata dalla ricerca e per **creare schede di allenamento** a partire da uno split, scegliendo per ogni posto della scheda l'esercizio preferito, con il controllo continuo del volume settimanale per muscolo. La scheda si scarica in PDF.

La fase 1 deve sostituire completamente l'Excel attuale e renderlo più facile da consultare, estendere e modificare.

## 2. Obiettivi

| ID | Obiettivo | Come si verifica |
| --- | --- | --- |
| O1 | Il catalogo degli esercizi è consultabile e filtrabile dal browser, da qualsiasi dispositivo della tailnet | US-01, US-02 |
| O2 | Il catalogo è modificabile dall'app senza toccare file o codice | US-03 → US-08 |
| O3 | Si crea una scheda completa partendo da uno split predefinito, con una prima proposta automatica, oppure da zero | US-10 → US-12, US-21 |
| O4 | Ogni esercizio della scheda si può sostituire con una variante, vedendo prima l'effetto sul volume | US-14 |
| O5 | Il volume settimanale per muscolo è sempre visibile e confrontato con le fasce obiettivo | US-13, US-20 |
| O6 | La scheda si scarica in PDF stampabile | US-30 |
| O7 | I dati sono persistenti e si possono esportare e reimportare | US-31, US-41 |

## 3. Fuori dalla fase 1

Esclusi esplicitamente, per non allargare il progetto. Il modello dati li deve comunque rendere aggiungibili senza riscritture (vedi ADR 0006).

- Ribilanciamento automatico dei volumi (fase 2). In fase 1 il lucchetto esiste già e serve alla rigenerazione (US-18).
- Split personalizzati salvati come preset riutilizzabili (fase 2). In fase 1 uno split inventato si costruisce in una scheda (vuota o da preset, US-10 e US-21) e si riusa duplicando la scheda (US-19).
- Guida integrata con i testi della ricerca (fase 2). In fase 1 ogni esercizio mostra le sue fonti come link.
- Registrazione degli allenamenti, storico, progressione, timer (fase 3).
- App installabile (PWA) e funzionamento offline (fase 3).
- Login, più utenti, permessi (vedi ADR 0011).
- Mesocicli e scarichi programmati (fase 4).

## 4. Glossario

I termini italiani sono quelli dell'interfaccia; tra parentesi il nome usato nel codice (ADR 0013).

| Termine | Definizione |
| --- | --- |
| Gruppo muscolare (`muscle_group`) | Raggruppamento della ricerca: petto, spalle, tricipiti, schiena, bicipiti, avambracci, gambe, core |
| Muscolo (`muscle`) | Unità su cui si conta il volume: un muscolo o un fascio (es. petto alto). Ha una priorità e, se prioritario, una fascia obiettivo |
| Esercizio (`exercise`) | Voce del catalogo, con attrezzo, tipo (multiarticolare o isolamento), allungamento, confidenza delle fonti ed etichette |
| Etichetta (`tag`) | Segno attribuibile agli esercizi, con nome, simbolo ed effetto sul punteggio (nessuno, bonus, penalità, esclusione). Ogni assegnazione può avere una nota. Esempi: "Collo: attenzione", "Non c'è nella mia palestra", "Preferito" |
| Personalizzazione | Valore che una scheda imposta al posto di quello del catalogo: priorità o fascia di un muscolo, effetto o intensità di un'etichetta. Ciò che non è personalizzato segue il catalogo |
| Coinvolgimento (`exercise_muscle`) | Livello con cui un esercizio allena un muscolo: P = primario (1 serie), S = secondario (0,5 serie) |
| Famiglia di movimento (`movement_family`) | Insieme di esercizi intercambiabili ai fini della scheda (es. "spinta inclinata"). Ogni esercizio ha una famiglia principale ed eventualmente una secondaria |
| Split (`split_template`) | Modello settimanale: elenco di giorni con quante volte si ripetono a settimana |
| Giorno (`day_template`) | Giorno tipo di uno split (Push, Pull, Legs, Upper, Lower, Full body) |
| Slot (`slot_template`) | Posto in un giorno: chiede una famiglia di movimento, con serie e ripetizioni predefinite |
| Scheda (`plan`) | Istanza concreta creata da uno split, con esercizi scelti, serie e preferenze. Modificabile e salvabile |
| Variante | Altro esercizio della stessa famiglia, proposto al posto di quello scelto |
| Lucchetto (`locked`) | Esercizio bloccato: le operazioni automatiche non lo cambiano |
| Volume frazionario | Somma, per muscolo, di serie × valore del livello (1 o 0,5) × volte a settimana del giorno |
| Fascia obiettivo | Intervallo di volume settimanale desiderato per un muscolo (es. 10-18) |
| Punteggio | Valore numerico con cui il sistema ordina i candidati di uno slot, in base a preferenze e attributi dell'esercizio (definito nel documento sull'algoritmo) |
| Seconda seduta | Quando un giorno si ripete due volte a settimana, ogni esercizio può avere una variante per la seconda ripetizione, anche di un'altra famiglia |

## 5. Utente

Un solo utente, che accede da computer e telefono attraverso la tailnet. Nessuna distinzione di ruoli.

## 6. Storie utente e criteri di accettazione

Formato: ogni criterio (CA) deve essere verificabile da un test automatico o da una prova manuale descritta.

### 6.1 Catalogo

**US-01 — Consultare il catalogo.** Come utente voglio vedere tutti gli esercizi e filtrarli, per trovare rapidamente quello che mi serve.
- CA1: la lista mostra nome, gruppo, famiglia, attrezzo, simboli delle etichette, confidenza.
- CA2: filtri combinabili per gruppo, muscolo allenato (con livello minimo P o S), famiglia, attrezzo, etichetta (con o senza), confidenza; ricerca testuale sul nome.
- CA3: i filtri attivi restano nell'URL, così una ricerca si può salvare tra i preferiti del browser.
- CA4: gli esercizi disattivati non compaiono, salvo con il filtro "mostra disattivati".
- CA5: usabile su uno schermo largo 380 px.

**US-02 — Vedere il dettaglio di un esercizio.**
- CA1: mostra tutti gli attributi, la mappa dei muscoli con P e S, le etichette con le rispettive note (es. l'accorgimento per il collo), le famiglie, le varianti (gli altri esercizi delle sue famiglie) e le fonti come link.
- CA2: dalle varianti si passa al loro dettaglio con un clic.

**US-03 — Modificare un esercizio.**
- CA1: tutti i campi sono modificabili da un form, compresa la mappa muscolare tramite una griglia (clic su un muscolo: vuoto → S → P → vuoto) e le etichette con le loro note.
- CA2: un esercizio deve avere almeno un muscolo P e una famiglia principale; altrimenti il salvataggio è rifiutato con un messaggio chiaro.
- CA3: dopo il salvataggio, i volumi delle schede che usano quell'esercizio riflettono la modifica alla prossima apertura.

**US-04 — Creare un esercizio.** Stessi campi e regole di US-03.

**US-05 — Disattivare o eliminare un esercizio.**
- CA1: un esercizio usato in almeno una scheda si può solo disattivare: resta nelle schede esistenti, non viene più proposto.
- CA2: un esercizio mai usato si può eliminare, previa conferma.

**US-06 — Gestire le famiglie di movimento.**
- CA1: creare, rinominare, descrivere, eliminare una famiglia.
- CA2: una famiglia usata da uno slot o con esercizi assegnati non si può eliminare; il messaggio dice da cosa è usata.

**US-07 — Modificare i muscoli.**
- CA1: priorità (prioritario, non prioritario, nessun obiettivo) e fascia minima e massima modificabili.
- CA2: la fascia è obbligatoria per prioritari e non prioritari, assente per "nessun obiettivo"; minimo < massimo.
- CA3: i nuovi valori valgono subito per tutte le schede, tranne quelle che hanno personalizzato quel muscolo (US-11).

**US-08 — Gestire le etichette.**
- CA1: creare, modificare ed eliminare un'etichetta: nome, simbolo (da un insieme predefinito di icone), colore, effetto (nessuno, bonus, penalità, esclusione), intensità in punti per bonus e penalità, visibilità del simbolo, descrizione.
- CA2: assegnare e togliere un'etichetta a un esercizio, con una nota facoltativa per quell'assegnazione; anche dalla lista del catalogo, su più esercizi selezionati insieme.
- CA3: eliminando un'etichetta assegnata, l'app chiede conferma indicando a quanti esercizi è assegnata e quante schede la personalizzano; poi rimuove assegnazioni e personalizzazioni.
- CA4: il cambio di effetto o intensità vale subito per tutte le schede che non l'hanno personalizzato; la generazione già fatta non cambia finché non si rigenera (US-18).

### 6.2 Schede

**US-10 — Creare una scheda.**
- CA1: la procedura guidata propone i preset della sezione 7, con descrizione e giorni a settimana, più l'opzione "Scheda vuota".
- CA2: al termine esiste una scheda con un nome predefinito (es. "PPL 6 giorni — 27/10/2026" o "Scheda vuota — 27/10/2026"), modificabile.
- CA3: una scheda vuota non ha giorni; si costruisce con US-21 e US-16.

**US-11 — Impostare le preferenze.**
- CA1: preferenze disponibili: ordine di preferenza degli attrezzi (macchina, cavi, pesi liberi, corpo libero) e durata massima indicativa della seduta.
- CA2: personalizzazioni disponibili: priorità e fascia di ogni muscolo, effetto e intensità di ogni etichetta. Si parte dai valori del catalogo; ogni valore personalizzato è segnalato e si può ripristinare al valore del catalogo con un clic.
- CA3: un muscolo portato a "prioritario" o "non prioritario" deve avere una fascia valida (minimo < massimo), presa dal catalogo o personalizzata; altrimenti il salvataggio è rifiutato con un messaggio chiaro.
- CA4: preferenze e personalizzazioni sono salvate con la scheda e modificabili in seguito.

**US-12 — Generazione automatica.**
- CA1: ogni slot riceve il candidato con punteggio più alto tra gli esercizi attivi della sua famiglia non esclusi da un'etichetta.
- CA2: se uno slot non ha candidati validi, resta vuoto e viene segnalato, con il motivo (es. "tutti esclusi dall'etichetta 'Non c'è nella mia palestra'").
- CA3: a parità di dati e preferenze il risultato è identico (generazione deterministica).
- CA4: la generazione dei preset PPL 6 giorni e Upper/Lower 4 giorni con le preferenze predefinite produce i volumi dei test di riferimento (ricavati dall'Excel, tolleranza 0).

**US-13 — Vedere la scheda e il pannello volume.**
- CA1: la scheda mostra i giorni in schede (tab) o colonne, con esercizi in ordine, serie, ripetizioni, lucchetto, facoltativo.
- CA2: il pannello volume mostra, per ogni muscolo con fascia, il volume settimanale e la fascia, con stato: sotto (rosso), dentro (verde), sopra (arancione). I muscoli senza fascia sono mostrati in una sezione richiudibile.
- CA3: il pannello si aggiorna dopo ogni modifica alla scheda senza ricaricare la pagina.
- CA4: accanto a ogni esercizio compaiono i simboli delle sue etichette visibili; toccando o passando sopra un simbolo si leggono il nome dell'etichetta e la nota dell'assegnazione.

**US-14 — Scegliere una variante.**
- CA1: su ogni esercizio un menu elenca le varianti ordinate per punteggio, con attrezzo, simboli delle etichette e l'effetto sul volume settimanale dei muscoli che cambiano (es. "petto alto −1,5 · petto medio +1,5").
- CA2: scegliendo una variante la scheda e il pannello si aggiornano.
- CA3: le varianti escluse da un'etichetta compaiono in fondo, con il motivo; si possono comunque scegliere, previa conferma.

**US-15 — Bloccare un esercizio.**
- CA1: ogni esercizio ha un lucchetto attivabile; lo stato è salvato.
- CA2: un esercizio bloccato non viene cambiato da US-18.

**US-16 — Modificare la scheda a mano.**
- CA1: modificare serie (1-8) e ripetizioni minime e massime.
- CA2: riordinare gli esercizi di un giorno trascinandoli.
- CA3: aggiungere un esercizio a un giorno (scegliendo prima la famiglia, poi l'esercizio) e rimuoverlo.
- CA4: segnare un esercizio come facoltativo: resta nella scheda e nel PDF ma non entra nel volume.
- CA5: cambiare la famiglia di uno slot (es. da "croce orizzontale" a "croce dal basso"): l'app assegna il miglior candidato della nuova famiglia, mantiene serie e ripetizioni e toglie l'eventuale variante della seconda seduta solo se non è più valida.

**US-17 — Variante per la seconda seduta.**
- CA1: nei giorni ripetuti due volte a settimana, ogni esercizio può avere una variante per la seconda seduta. Il menu propone prima gli esercizi della stessa famiglia, ordinati per punteggio, poi tutti gli altri con una ricerca per nome (es. croci ai cavi nella seconda seduta al posto della chest press).
- CA2: il volume tiene conto della variante: la prima seduta conta con l'esercizio principale, la seconda con la variante.

**US-18 — Rigenerare.**
- CA1: "Rigenera" ricalcola gli esercizi non bloccati con le preferenze correnti; quelli bloccati restano identici, comprese serie e ripetizioni.
- CA2: prima di applicare, mostra le differenze e chiede conferma.

**US-19 — Gestire le schede salvate.**
- CA1: elenco delle schede con nome, split, data di modifica, stato attiva.
- CA2: rinominare, duplicare, eliminare (con conferma), segnare come attiva (una sola alla volta).
- CA3: le modifiche si salvano automaticamente; un indicatore mostra lo stato del salvataggio.

**US-21 — Gestire i giorni della scheda.**
- CA1: aggiungere un giorno, con nome e volte a settimana (1-3); nasce senza esercizi e senza stretching.
- CA2: rinominare un giorno e riordinare i giorni.
- CA3: cambiare le volte a settimana di un giorno. Se scende a 1, le varianti della seconda seduta di quel giorno non hanno più senso: l'app le elenca e le rimuove dopo conferma.
- CA4: eliminare un giorno, con conferma se contiene esercizi.
- CA5: volumi, avvisi e PDF si aggiornano come per ogni altra modifica.

**US-20 — Avvisi.**
- CA1: avviso se un muscolo supera il tetto per seduta (default 10 serie frazionarie, impostabile).
- CA2: avviso se la durata stimata di una seduta supera la durata massima delle preferenze. La stima usa serie, tipo di esercizio e recuperi della ricerca (formula nel documento sull'algoritmo).

### 6.3 Esportazione

**US-30 — Scaricare il PDF.**
- CA1: il PDF A4 contiene: intestazione con nome della scheda, split e data; una pagina per giorno con esercizi, simboli delle etichette, serie × ripetizioni, RIR obiettivo, recupero e caselle vuote per 4 settimane di carichi e ripetizioni; sotto la tabella, le note delle etichette degli esercizi del giorno (es. gli accorgimenti per il collo); riscaldamento e stretching del giorno; un'ultima pagina con il riepilogo dei volumi, la legenda dei simboli e il mini-allenamento quotidiano.
- CA2: gli esercizi facoltativi sono marcati come tali; le varianti della seconda seduta sono indicate.
- CA3: il PDF è identico qualunque sia il dispositivo da cui lo si scarica.

**US-31 — Esportare e importare i dati.**
- CA1: esportazione di catalogo e schede in un file JSON versionato.
- CA2: importazione di un file esportato in un'istanza vuota, con risultato identico all'originale (test di andata e ritorno).
- CA3: l'importazione su un'istanza non vuota è rifiutata in fase 1, per evitare fusioni ambigue.

### 6.4 Sistema

**US-40 — Accesso.** L'app è raggiungibile in HTTPS all'indirizzo della tailnet da computer e telefono; non è esposta fuori dalla tailnet.

**US-41 — Persistenza.** I dati sopravvivono a riavvii e aggiornamenti del container; il file del database sta in un volume con backup.

## 7. Split predefiniti della fase 1

La composizione degli slot di PPL e Upper/Lower viene dal documento di ricerca ("Giorni Push, Pull e Legs", "Giorni Upper e Lower"). Push/Pull e Full body sono nuovi: la loro composizione sarà proposta nel documento sui dati iniziali e approvata prima di M1.

| ID | Nome | Giorni a settimana | Composizione |
| --- | --- | --- | --- |
| `ppl-3` | Push/Pull/Legs, 3 giorni | 3 | Push, Pull, Legs × 1 |
| `ppl-6` | Push/Pull/Legs, 6 giorni | 6 | Push, Pull, Legs × 2 |
| `ul-4` | Upper/Lower, 4 giorni | 4 | Upper, Lower × 2 |
| `pplul-5` | Push/Pull/Legs/Upper/Lower | 5 | ognuno × 1 |
| `pp-4` | Push/Pull, 4 giorni | 4 | Push con quadricipiti, Pull con femorali e glutei, × 2 |
| `fb-3` | Full body, 3 giorni | 3 | Full body A, B, C, una volta ciascuno |

## 8. Requisiti non funzionali

| ID | Requisito |
| --- | --- |
| NF1 Prestazioni | Dopo una modifica alla scheda, il pannello volume si aggiorna entro 300 ms in rete locale o tailnet |
| NF2 Interfaccia | Usabile da 380 px di larghezza in su; modalità chiara e scura secondo il sistema |
| NF3 Lingua | Interfaccia e documentazione in italiano |
| NF4 Browser | Ultime due versioni di Firefox, Chrome e Safari (iOS compreso) |
| NF5 Affidabilità | Nessuna perdita di dati per riavvio o aggiornamento; backup giornaliero del database |
| NF6 Manutenibilità | Copertura dei test del modulo di dominio ≥ 90%; CI verde come condizione per il merge |
| NF7 Aggiornabilità | Ogni modifica allo schema passa da una migrazione; un aggiornamento non richiede interventi manuali sul database |
| NF8 Accessibilità | Contrasti leggibili, navigazione da tastiera nei form, stati non comunicati solo dal colore (icona o testo accanto al colore) |

## 9. Rischi

| Rischio | Mitigazione |
| --- | --- |
| Le famiglie di movimento risultano troppo larghe o troppo strette | Revisione della tabella prima di M1; famiglie modificabili dall'app (US-06) |
| La generazione propone schede poco sensate | Test di riferimento sui preset documentati (US-12 CA4); punteggio con pesi configurabili |
| WeasyPrint complica l'immagine Docker | Verificato in M0 con un PDF di prova |
| Il deploy su Tailscale dà problemi | M0 pubblica subito una pagina vuota sull'homelab |

## 10. Domande aperte

1. Composizione degli split Push/Pull e Full body: risolta nel documento sui dati iniziali.
2. Nome del repository e dell'app: risolta, `gym_split_planner` (README).
3. Serve un campo "note personali" per esercizio, oltre alle note delle etichette?
