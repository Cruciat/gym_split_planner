# Wireframe — Fase 1

| Campo | Valore |
| --- | --- |
| Stato | Bozza v0.1, in revisione |
| Data | 2026-10-28 |
| Riferimenti | Specifica fase 1 v0.2; contratto delle API v0.1; ADR 0004, 0008, 0014 |

Bozze a bassa fedeltà delle schermate: cosa c'è, dove sta, come ci si muove. Non decidono colori, font e spaziature, che si fissano nel tema di Naive UI durante M3 (ADR 0015). Gli schizzi sono in testo, così restano versionati e modificabili insieme agli altri documenti.

Legenda degli schizzi: `[Pulsante]`, `(•)` scelta, `[x]` casella, `▾` menu a tendina, `⋮` menu di azioni, `🔒`/`🔓` lucchetto, `⚠` e `⊘` simboli di etichette, `≡` maniglia per trascinare.

## 1. Principi

1. **La scheda è la schermata principale.** All'apertura l'app mostra la scheda attiva; se non ce n'è nessuna, l'elenco delle schede.
2. **Il volume si vede mentre si modifica.** Su schermo largo il pannello volume sta sempre a destra della scheda; su telefono è a un tocco, con un riassunto sempre visibile (§ 4.2).
3. **Ogni scelta automatica si può spiegare.** Accanto a punteggi e avvisi c'è sempre il perché: voci del punteggio, motivo di esclusione, muscoli che cambiano.
4. **Salvataggio automatico, conferma solo per ciò che distrugge.** Niente pulsanti "Salva" nell'editor; conferma per eliminazioni, rigenerazione e importazione.
5. **Lo stato non si affida al solo colore.** Sotto e sopra fascia hanno anche un'icona e un testo; i simboli delle etichette hanno sempre un nome leggibile al tocco o al passaggio del mouse.

## 2. Struttura e navigazione

| Sezione | Contenuto | Percorso |
| --- | --- | --- |
| Schede | Scheda attiva, elenco, creazione | `/`, `/schede`, `/schede/nuova`, `/schede/:id`, `/schede/:id/preferenze` |
| Catalogo | Esercizi, famiglie, etichette, muscoli | `/catalogo`, `/catalogo/esercizi/:id`, `/catalogo/esercizi/:id/modifica`, `/catalogo/famiglie`, `/catalogo/etichette`, `/catalogo/muscoli` |
| Impostazioni | Impostazioni globali, esportazione e importazione | `/impostazioni` |

Larghezze: **telefono** sotto 768 px, **tablet** 768-1023 px (come il telefono, con più spazio), **desktop** da 1024 px.

```
Desktop: barra in alto                      Telefono: barra in basso
┌──────────────────────────────────────┐    ┌────────────────────────┐
│ Schede   Catalogo   Impostazioni     │    │                        │
├──────────────────────────────────────┤    │       contenuto        │
│                                      │    │                        │
│              contenuto               │    ├────────────────────────┤
│                                      │    │ Schede Catalogo  Impost.│
└──────────────────────────────────────┘    └────────────────────────┘
```

## 3. Schede

### 3.1 Elenco (US-19)

```
┌─────────────────────────────────────────────────────────┐
│ Schede                                 [+ Nuova scheda] │
├─────────────────────────────────────────────────────────┤
│ ● PPL 6 giorni — autunno        PPL 6 · 6 giorni      ⋮ │
│   attiva · modificata il 28/10                          │
│ ○ Upper/Lower prova             UL 4 · 4 giorni       ⋮ │
│   modificata il 20/10                                   │
└─────────────────────────────────────────────────────────┘
⋮ = Apri · Rinomina · Duplica · Rendi attiva · Elimina
```

Vuoto: "Nessuna scheda. [Crea la prima scheda]".

### 3.2 Creazione guidata (US-10, US-11)

Tre passi, con "Indietro" sempre disponibile. Il passo 2 ha valori già pronti: si può andare avanti senza toccare nulla.

```
Passo 1 di 3 — Da dove parti?
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Push/Pull/Legs   │ │ Push/Pull/Legs   │ │ Upper/Lower      │
│ 3 giorni         │ │ 6 giorni         │ │ 4 giorni         │
│ Push · Pull ·    │ │ Push · Pull ·    │ │ Upper ×2 ·       │
│ Legs             │ │ Legs, ×2         │ │ Lower ×2         │
└──────────────────┘ └──────────────────┘ └──────────────────┘
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ PPL + UL         │ │ Push/Pull        │ │ Full body        │
│ 5 giorni         │ │ 4 giorni         │ │ 3 giorni         │
└──────────────────┘ └──────────────────┘ └──────────────────┘
┌──────────────────┐
│ Scheda vuota     │
│ crei tu i giorni │
└──────────────────┘

Passo 2 di 3 — Preferenze
  Attrezzi, dal preferito:   ≡ Macchina  ≡ Cavi  ≡ Pesi liberi  ≡ Corpo libero
  Durata massima seduta:     [ 75 ] min
  Muscoli ed etichette:      come nel catalogo · [Personalizza…]

Passo 3 di 3 — Nome
  Nome: [ PPL 6 giorni — 28/10/2026 ]
                                           [Indietro]  [Crea scheda]
```

"Personalizza…" apre la stessa schermata di § 3.5, dentro la procedura. Alla creazione si apre l'editor della nuova scheda.

### 3.3 Editor della scheda, desktop (US-13 → US-18, US-21)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ PPL 6 giorni — autunno ✎         ✓ Salvato    [Preferenze] [Rigenera] [PDF] [⋮]   │
├─────────────────────────────────────────────────────────────┬───────────────────────┤
│ [Push ×2] [Pull ×2] [Legs ×2] [+ Giorno]                    │ Volume settimanale    │
├─────────────────────────────────────────────────────────────┤ [Prioritari ▾]        │
│ Push · 2 volte a settimana · ~60 min                      ⋮ │                       │
│                                                             │ Petto                 │
│ ≡ 1 Chest press inclinata               3 × 6-12   🔓   ⋮  │  Alto   12 ▕██████░▏  │
│     Spinta inclinata                                        │  Medio  15 ▕███████▏  │
│ ≡ 2 Chest press seduta                  3 × 6-12   🔓   ⋮  │ Spalle                │
│     Spinta orizzontale                                      │  Lat.   11 ▕█████░░▏  │
│ ≡ 3 Pec deck                            3 × 10-20  🔓   ⋮  │  Post.  13 ▕██████░▏  │
│     Croce orizzontale                                       │ Tricipiti             │
│ ≡ 4 Alzate laterali ai cavi ⓘ           4 × 10-20  🔓   ⋮  │  Lungo ↓ 8 ▕████··│▏ │
│     Alzata laterale                                         │  Lat.   16 ▕███████▏  │
│ ≡ 5 Estensione ai cavi ⚠                3 × 10-15  🔒   ⋮  │ …                     │
│     Estensione sopra la testa · 2ª seduta: alla macchina    │                       │
│ ≡ 6 Pushdown con barra                  2 × 10-15  🔓   ⋮  │ Avvisi (1)            │
│     Estensione a braccio lungo il corpo                     │  ↓ Capo lungo sotto   │
│ ≡ 7 Shoulder press a macchina ⚠  facoltativo  2 × 8-12  ⋮  │    fascia (8 / 10-18) │
│                                                             │                       │
│ [+ Aggiungi esercizio]                                      │                       │
│                                                             │                       │
│ Stretching: stipite · braccio incrociato · tricipite        │                       │
└─────────────────────────────────────────────────────────────┴───────────────────────┘
```

**Riga dell'esercizio**

- Nome dell'esercizio con i simboli delle etichette visibili; sotto, la famiglia e l'eventuale variante della seconda seduta.
- Toccare il nome apre il menu delle varianti (§ 3.4).
- Serie e ripetizioni si modificano toccandole: piccoli campi numerici, salvati all'uscita dal campo.
- Lucchetto: un tocco lo apre e lo chiude.
- `⋮` = Variante per la seconda seduta · Cambia famiglia · Facoltativo sì/no · Settimane alterne sì/no · Nota · Elimina.
- Gli esercizi facoltativi sono in grigio con l'etichetta "facoltativo".

**Testata del giorno**: nome, volte a settimana, durata stimata; `⋮` = Rinomina · Volte a settimana · Elimina giorno. Se il giorno ha una seconda seduta diversa, la durata mostra le due stime ("~60 / ~62 min"). Le schede dei giorni si riordinano trascinandole.

**Pannello volume**

- Muscoli raggruppati per gruppo; filtro `▾` tra prioritari (predefinito), con obiettivo, tutti.
- Barra con la fascia evidenziata come zona; un segno per il valore. Stato con icona e testo: `↓` sotto, `↑` sopra, nessun segno se dentro la fascia.
- Muscoli personalizzati nella scheda marcati con un punto (●) e la fascia effettiva.
- Gli avvisi (sotto fascia, sopra fascia, tetto per seduta, durata, slot vuoti) stanno sotto i volumi. Toccandone uno si va all'elemento che lo causa.

**Salvataggio**: indicatore "Salvataggio…", "✓ Salvato", oppure "Non salvato · [Riprova]" in caso di errore di rete. Con risposta `412` (API, § 4): avviso "La scheda è stata modificata da un altro dispositivo ed è stata ricaricata".

**Scheda vuota**: "Questa scheda non ha ancora giorni. [+ Aggiungi il primo giorno]".

### 3.4 Varianti e anteprima del volume (US-14, US-17)

Pannello laterale su desktop, foglio dal basso su telefono.

```
┌───────────────────────────────────────────────────────────┐
│ Push · slot 6 · Estensione a braccio lungo il corpo   ✕   │
│ Attuale: Pushdown con barra                               │
├───────────────────────────────────────────────────────────┤
│ (•) Pushdown con barra            6,17   attuale          │
│ ( ) Pushdown con corda            5,02   nessun cambio    │
│ ( ) Kickback ai cavi              4,93   Capo lungo +2    │
│                                                    [Perché?] │
├─ Escluse dalle etichette ─────────────────────────────────┤
│ ( ) …                     ⊘ Collo: evitare                 │
└───────────────────────────────────────────────────────────┘
```

- Ogni candidato: nome, simboli delle etichette, attrezzo, punteggio, muscoli che cambiano come chip (`Capo lungo +2`, `Petto alto −1,5`), in verde se avvicinano alla fascia e in arancione se allontanano.
- "Perché?" apre le voci del punteggio (confidenza, attrezzo, allungamento, famiglia, rango, etichette).
- Scegliere un candidato lo applica subito; il pannello resta aperto per confrontare, e mostra il nuovo "attuale".
- Esclusi: in fondo, con il motivo. Sceglierli chiede conferma ("Escluso dall'etichetta 'Collo: evitare'. Usarlo lo stesso?").
- Variante della seconda seduta: stesso pannello, con il titolo "Seconda seduta", la voce "Nessuna variante" in cima e, dopo i candidati della famiglia, la sezione "Altre famiglie" con una ricerca per nome.

### 3.5 Preferenze e personalizzazioni (US-11)

```
Preferenze di "PPL 6 giorni — autunno"
  Attrezzi, dal preferito:  ≡ Macchina ≡ Cavi ≡ Pesi liberi ≡ Corpo libero
  Durata massima seduta:    [ 75 ] min

  Muscoli                                         [Solo personalizzati ☐]
  ┌─────────────────────┬─────────────────┬──────┬──────┬────────────┐
  │ Muscolo             │ Priorità        │ Min  │ Max  │            │
  ├─────────────────────┼─────────────────┼──────┼──────┼────────────┤
  │ Petto alto          │ Prioritario ▾   │ 10   │ 18   │            │
  │ Quadricipiti      ● │ Non priorit. ▾  │  6   │ [8]● │ [↺ Catalogo]│
  │ Petto basso         │ Nessun obiet. ▾ │  —   │  —   │            │
  └─────────────────────┴─────────────────┴──────┴──────┴────────────┘

  Etichette
  ┌───────────────────────┬────────────────┬──────┬────────────┐
  │ ⚠ Collo: attenzione   │ Penalità ▾     │ [3]  │            │
  │ ⊘ Collo: evitare      │ Esclusione ▾   │  —   │            │
  │ ⓘ Collo: accorgimento │ Nessun effetto │  —   │            │
  └───────────────────────┴────────────────┴──────┴────────────┘

  Le modifiche aggiornano subito volumi e avvisi. Per applicarle anche
  agli esercizi scelti: [Rigenera…]
```

- `●` = personalizzato nella scheda; il valore del catalogo compare al passaggio del mouse o al tocco ("Catalogo: 6-10").
- `↺ Catalogo` toglie la personalizzazione della riga.
- Fascia non valida (minimo ≥ massimo, o priorità con obiettivo senza fascia): campo in errore, salvataggio bloccato con il messaggio del server.

### 3.6 Rigenerazione (US-18)

```
┌──────────────────────────────────────────────────────────────┐
│ Rigenera con le preferenze attuali                       ✕   │
├──────────────────────────────────────────────────────────────┤
│ [x] Pull · 2   Pulley basso, presa larga → Rematore con      │
│                appoggio al petto          Dorsale +3         │
│ [x] Legs · 6   Crunch al cavo in ginocchio → Crunch alla     │
│                macchina                   nessun cambio      │
│ Gli esercizi con il lucchetto non vengono toccati (3).       │
├──────────────────────────────────────────────────────────────┤
│                              [Annulla]  [Applica 2 modifiche] │
└──────────────────────────────────────────────────────────────┘
```

Nessuna differenza: "La scheda è già allineata alle preferenze".

### 3.7 Editor della scheda, telefono

```
┌────────────────────────┐   ┌────────────────────────┐
│ PPL 6 — autunno   ✓  ⋮ │   │ Volume            ✕    │
│ [Push][Pull][Legs][+]  │   │ [Prioritari ▾]         │
├────────────────────────┤   │ Petto alto   12 ███░   │
│ Push ×2 · ~60 min    ⋮ │   │ Petto medio  15 ████   │
│                        │   │ Capo lungo ↓  8 ██··   │
│ Chest press incl.   🔓 │   │ …                      │
│ 3 × 6-12 · Spinta incl.│   │ Avvisi (1)             │
│ Chest press seduta  🔓 │   │ ↓ Capo lungo sotto…    │
│ 3 × 6-12 · Spinta orz. │   │                        │
│ Estensione cavi ⚠   🔒 │   │                        │
│ 3 × 10-15 · Sopra testa│   │                        │
│ …                      │   │                        │
├────────────────────────┤   │                        │
│ ↓1 sotto · ↑0 sopra  ▲ │   │                        │
└────────────────────────┘   └────────────────────────┘
```

- Barra in fondo sempre visibile con il riassunto degli stati; toccandola si apre il pannello volume a tutto schermo.
- `⋮` in alto = Preferenze · Rigenera · PDF · Rinomina.
- Riordino: tenere premuto e trascinare (maniglia visibile solo in modalità "Riordina", attivabile dal menu del giorno, per evitare trascinamenti accidentali mentre si scorre).
- Serie e ripetizioni: toccando la riga si apre un foglio con i campi e le azioni del menu `⋮` del desktop.

## 4. Catalogo

### 4.1 Elenco degli esercizi (US-01)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Catalogo   [Esercizi] [Famiglie] [Etichette] [Muscoli]  [+ Nuovo esercizio]│
├───────────────────┬──────────────────────────────────────────────────────┤
│ Cerca [_______]   │ 81 esercizi                       [Seleziona]        │
│                   │ Nome                    Famiglia        Attr.  Conf. │
│ Gruppo        ▾   │ Chest press inclinata   Spinta inclin.  Macch. Lim.  │
│ Muscolo       ▾   │ Panca inclinata 30° ⚠   Spinta inclin.  P. lib Lim.  │
│  livello (•)P ( )P/S                                                     │
│ Famiglia      ▾   │ …                                                    │
│ Attrezzo      ▾   │                                                      │
│ Etichetta     ▾   │                                                      │
│  (•)con ( )senza  │                                                      │
│ Confidenza    ▾   │                                                      │
│ [x] Solo attivi   │                                                      │
│ [Azzera filtri]   │                                                      │
└───────────────────┴──────────────────────────────────────────────────────┘
```

- Filtri nell'URL (US-01 CA3): un link riapre la stessa vista.
- Ordinamento per colonna; raggruppamento per gruppo muscolare attivabile.
- "Seleziona" attiva le caselle sulle righe e la barra "Assegna etichetta… / Togli etichetta…" (US-08 CA2).
- Telefono: lista a schede (nome, simboli, famiglia, attrezzo); filtri in un foglio dal basso con il numero di filtri attivi sul pulsante.

### 4.2 Dettaglio dell'esercizio (US-02)

```
Chest press inclinata                                 [Modifica] [⋮]
Spinta inclinata · Macchina · Multiarticolare · Attivo

Muscoli      P  Petto alto
             S  Petto medio · Deltoide anteriore · Tricipite laterale ·
                Tricipite mediale
Allungamento Medio
Confidenza   Limitato
Etichette    —
Varianti     Panca inclinata a 30° ⚠   (stessa famiglia)
Fonti        titolo della fonte ↗ · …
Note         …
```

`⋮` = Disattiva · Elimina (solo se mai usato; altrimenti spiega dove è usato e propone di disattivarlo).

### 4.3 Modifica e creazione dell'esercizio (US-03, US-04)

```
Nome            [ Chest press inclinata          ]
Famiglia        [ Spinta inclinata ▾ ]   Rango [1]
Secondaria      [ nessuna ▾ ]
Attrezzo        [ Macchina ▾ ]   dettaglio [            ]
Tipo            (•) Multiarticolare  ( ) Isolamento
Allungamento    [ Medio ▾ ]      nota [ dipende dalla macchina ]
Confidenza      [ Limitato ▾ ]

Muscoli (tocca: vuoto → S → P → vuoto)
  Petto     [P Alto] [S Medio] [  Basso]
  Spalle    [S Ant.] [  Lat. ] [  Post.]
  Tricipiti [  Lungo] [S Lat.] [S Med.]
  …

Etichette   [+ Aggiungi ▾]
  ⚠ Collo: attenzione   nota [ testa appoggiata allo schienale ]   ✕

Fonti       [ fonte ✕ ] [ + Aggiungi ▾ ]
Note        [ ………………………………………………………………… ]
                                                   [Annulla] [Salva]
```

- La griglia dei muscoli ha una riga per gruppo; ogni muscolo è un pulsante a tre stati con la lettera ben visibile.
- Errori di validazione accanto al campo (es. "Serve almeno un muscolo P").
- Qui c'è un pulsante Salva: è una form, non l'editor.

### 4.4 Famiglie, etichette, muscoli (US-06, US-07, US-08)

Tre tabelle modificabili in linea, con lo stesso schema:

```
Famiglie                                              [+ Nuova famiglia]
Nome                  Gruppo     Esercizi   Usata in       
Spinta inclinata      Petto      2          2 split, 1 scheda    ✎ 🗑
…

Etichette                                             [+ Nuova etichetta]
Simbolo  Nome                  Effetto      Punti  Visibile  Esercizi
⚠        Collo: attenzione     Penalità     3      sì        26        ✎ 🗑
…

Muscoli
Nome          Gruppo   Priorità        Min   Max
Petto alto    Petto    Prioritario ▾   10    18      ✎
…
```

- Etichetta: il simbolo si sceglie da un insieme chiuso di icone (avviso, divieto, informazione, stella, cuore, fulmine, bandiera, occhio barrato). Le stesse icone, in SVG, sono usate dal PDF (§ 6).
- Eliminazione di un'etichetta: "Assegnata a 26 esercizi e personalizzata in 1 scheda. Eliminarla toglie anche queste assegnazioni".
- Cambio di fascia di un muscolo che invaliderebbe una scheda: messaggio con l'elenco delle schede (API, `409 invalid-band`).

## 5. Impostazioni (US-20, US-31)

```
Impostazioni
  Volume       Peso P [1]   Peso S [0,5]   Tetto per seduta [10]
  Punteggio    Confidenza [3]  Attrezzo [4]  Allungamento [1]  Famiglia [1]  Rango [0,5]
  Durata       Serie [45] s  Recupero multi [150] s  Recupero iso [90] s  Cambio [60] s
               Riscaldamento [10] min  Stretching [6] min
  Intensità    RIR [0-2]   [x] Ultima serie a cedimento su macchine e isolamento
  Riscaldamento (testo per il PDF) [ ……………… ]
                                              [Ripristina predefiniti] [Salva]

Dati
  [Esporta tutto (JSON)]
  Importa: possibile solo su un'installazione vuota.  [Scegli file…]
  Versione 1.0.0
```

## 6. PDF (US-30)

A4 verticale, una pagina per giorno, poi una pagina di riepilogo. Un giorno con varianti della seconda seduta resta su una pagina sola: la variante è indicata sotto l'esercizio.

```
┌──────────────────────────────────────────────────────────────┐
│ PPL 6 giorni — autunno · Push/Pull/Legs, 6 giorni · 28/10/2026│
│ PUSH · 2 volte a settimana · ~60 min                          │
│ Riscaldamento: 5-10 min cardio leggero, mobilità spalle…      │
├────────────────────────────┬──────┬─────┬──────┬────┬────┬────┬────┤
│ Esercizio                  │Serie │ RIR │ Rec. │ S1 │ S2 │ S3 │ S4 │
├────────────────────────────┼──────┼─────┼──────┼────┼────┼────┼────┤
│ Chest press inclinata      │3×6-12│ 0-2 │2-3′  │    │    │    │    │
│ Estensione ai cavi ⚠¹      │3×10-15│0-2* │90″  │    │    │    │    │
│   2ª seduta: alla macchina │      │     │      │    │    │    │    │
│ Shoulder press (facolt.) ⚠ │2×8-12│ 0-2 │2-3′  │    │    │    │    │
├────────────────────────────┴──────┴─────┴──────┴────┴────┴────┴────┤
│ ¹ Collo: attenzione.  * ultima serie a cedimento                    │
│ Stretching: stipite 30″→60″ · braccio incrociato 30″×3 · …          │
└──────────────────────────────────────────────────────────────────────┘

Pagina finale: volume settimanale per muscolo con fascia e stato,
legenda dei simboli, mini-allenamento quotidiano (collo e bacino).
```

- Caselle S1-S4: una colonna per settimana (`weeks`, default 4), ciascuna con spazio per "kg × ripetizioni" di ogni serie.
- Le note delle etichette sono richiami numerati sotto la tabella, così la riga resta corta.
- Il PDF usa le stesse icone dell'interfaccia, in bianco e nero leggibile (stampa senza colori).

## 7. Stati comuni

| Stato | Comportamento |
| --- | --- |
| Caricamento | Scheletri grigi della forma del contenuto, non spinner a tutto schermo |
| Errore di rete | Messaggio in alto "Connessione persa" con [Riprova]; le modifiche non inviate restano nella coda e ripartono |
| Errore dal server | Il `title` e il `detail` del Problem Details, così come sono |
| Conferme | Dialog con il verbo dell'azione sul pulsante ("Elimina giorno"), mai "OK" |
| Annulla | Non c'è un annulla generale in fase 1; le azioni distruttive chiedono conferma |
| Tema | Chiaro e scuro secondo il sistema |

## 8. Domande aperte

1. Nessuna bloccante. I dettagli visivi (colori, spaziature, dimensione dei caratteri sul telefono) si decidono in M3 sulle prime schermate vere, che sono più utili di qualunque bozza.
