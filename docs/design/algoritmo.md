# Algoritmo — Fase 1

| Campo | Valore |
| --- | --- |
| Stato | Bozza v0.2, in revisione |
| Data | 2026-10-28 |
| Riferimenti | Specifica fase 1 (US-12 → US-20); modello dati; ADR 0005, 0006, 0007, 0014 |
| Modifiche v0.2 | Valori effettivi con personalizzazioni (§ 2.2); voce "collo" del punteggio sostituita dagli effetti delle etichette, penalità 3 (§ 3); esempi ricalcolati |

Tutto ciò che segue vive nel modulo `domain` (ADR 0005): funzioni pure su oggetti in memoria, senza database né HTTP. Ogni sezione termina con i casi di test che la definiscono.

I numeri degli esempi sono stati verificati con uno script sulla banca dati attuale e una bozza delle famiglie di movimento.

## 1. Notazione

| Simbolo | Significato |
| --- | --- |
| `e`, `m` | Esercizio, muscolo |
| `λ(e, m)` | Peso del coinvolgimento: `level_weights[P]` = 1 se `e` allena `m` come primario, `level_weights[S]` = 0,5 se secondario, 0 altrimenti |
| `d` | Giorno della scheda, che si ripete `t_d` volte a settimana (1-3) |
| `s` | Slot di un giorno: esercizio `e_s`, eventuale variante della seconda seduta `e2_s`, serie `n_s`, peso settimanale `w_s` (1 oppure 0,5 per le settimane alterne), facoltativo sì o no |

## 2. Volume settimanale frazionario

### 2.1 Definizione

Per ogni muscolo `m`:

```
V(m) = Σ_d Σ_s∈d, s non facoltativo, e_s non nullo   n_s · w_s · contributo(s, m)

contributo(s, m) =
    t_d · λ(e_s, m)                                   se e2_s è nullo
    (t_d − 1) · λ(e_s, m) + 1 · λ(e2_s, m)            se e2_s è valorizzato (t_d ≥ 2)
```

La variante della seconda seduta sostituisce l'esercizio principale in **una** delle `t_d` sedute settimanali di quel giorno. Con `t_d = 2` le due sedute sono una con l'esercizio principale e una con la variante.

Slot facoltativi e slot vuoti non contano.

### 2.2 Valori effettivi e stato rispetto alla fascia

Priorità e fascia di ogni muscolo sono **effettive**: per ciascun campo (`priority`, `weekly_min`, `weekly_max`) si usa la personalizzazione della scheda se esiste, altrimenti il valore del catalogo (ADR 0014). La risoluzione avviene una volta, all'inizio di ogni calcolo, con `resolve_muscle(muscolo, overrides)`; il resto dell'algoritmo vede solo valori effettivi.

```
resolve_muscle(m, ov):
  o ← ov.muscles.get(m.code, {})
  return (o.priority ?? m.priority, o.weekly_min ?? m.weekly_min, o.weekly_max ?? m.weekly_max)
```

Esempio: il catalogo dà ai quadricipiti priorità `standard` e fascia 6-10; una scheda che personalizza solo `weekly_max = 8` ha fascia effettiva 6-8 e priorità `standard`. Se in seguito il catalogo porta il minimo a 7, quella scheda ha 7-8.

| Priorità effettiva | Stato |
| --- | --- |
| `none` | Nessuno stato: il volume si mostra senza giudizio |
| `priority` o `standard` | `below` se `V < weekly_min`, `above` se `V > weekly_max`, altrimenti `within` |

### 2.3 Volume per seduta

Il tetto per seduta (US-20) si controlla su ogni **seduta concreta**. Un giorno con almeno una variante di seconda seduta genera due composizioni: la prima con gli esercizi principali, la seconda con le varianti al posto dei principali. Per ognuna:

```
V_seduta(m) = Σ_s non facoltativo  n_s · w_s · λ(esercizio usato in quella seduta, m)
```

Avviso se `V_seduta(m) > session_cap` (default 10).

### 2.4 Esempio

Giorno Push del documento, un solo passaggio a settimana (`t = 1`):

| Esercizio | Serie | Petto alto | Petto medio |
| --- | --- | --- | --- |
| Chest press inclinata (alto P, medio S) | 3 | 3 × 1 = 3 | 3 × 0,5 = 1,5 |
| Chest press seduta (alto S, medio P) | 3 | 1,5 | 3 |
| Croci ai cavi da seduti (alto S, medio P) | 3 | 1,5 | 3 |
| **Totale** | | **6** | **7,5** |

Coincide con il "Totale per seduta" del documento.

### 2.5 Casi di test

| ID | Caso | Atteso |
| --- | --- | --- |
| V1 | Push del documento con `t = 1` | Petto alto 6, petto medio 7,5, deltoide anteriore 4,5, tricipite capo lungo 4 |
| V2 | Slot facoltativo (shoulder press nel Push) | Nessun contributo |
| V3 | Scrollate con `w = 0,5`, 2 serie, `t = 2` | Trapezio superiore +2 (2 · 0,5 · 2 · 1) |
| V4 | Seconda seduta: pushdown con barra principale, kickback come variante, 2 serie, `t = 2` | Capo lungo = 2 · (1 · 0,5 + 1 · 1) = 3 |
| V5 | Slot vuoto | Nessun contributo, nessun errore |
| V6 | Muscolo con priorità `none` | Stato assente |
| V7 | Valori sui bordi della fascia (V = min, V = max) | `within` in entrambi i casi |
| V8 | Tutti gli split della specifica | Volumi identici alla tabella "Volume settimanale" dell'Excel (test di riferimento, § 7) |
| V9 | Personalizzazione del solo `weekly_max` | Fascia effettiva = minimo del catalogo, massimo personalizzato |
| V10 | Personalizzazione della priorità a `none` | Stato assente, anche se il catalogo ha una fascia |
| V11 | Personalizzazione di un muscolo che non esiste più | Ignorata, nessun errore |

## 3. Punteggio dei candidati

### 3.1 Candidati ed esclusioni

I candidati di uno slot con famiglia `F` sono gli esercizi **attivi** con famiglia principale o secondaria `F`.

Gli effetti delle etichette sono **effettivi** come i valori dei muscoli: `resolve_tag(etichetta, overrides)` restituisce `effect` e `points` della personalizzazione della scheda se presenti, altrimenti quelli del catalogo.

Un candidato è **escluso** se ha almeno un'etichetta con effetto effettivo `exclude`. Il motivo è `tag-exclude:<code>` per ogni etichetta che lo esclude (es. `tag-exclude:neck-avoid`); l'interfaccia mostra il nome dell'etichetta.

Gli esclusi non vengono mai assegnati automaticamente, ma compaiono in fondo al menu delle varianti, con il motivo (US-14 CA3). L'utente può comunque sceglierli a mano, previa conferma: la regola vale solo per le operazioni automatiche (generazione, rigenerazione, ribilanciamento della fase 2).

### 3.2 Formula

```
punteggio(e) = base(e) + etichette(e)

base(e)      = 3 · confidenza + 4 · attrezzo + 1 · allungamento + 1 · famiglia + 0,5 · rango
etichette(e) = Σ_t ∈ etichette di e   ( +points_t se effetto bonus · −points_t se effetto penalty · 0 altrimenti )
```

| Componente | Valori |
| --- | --- |
| confidenza | `solid` 1 · `limited` 0,6 · `opinion` 0,3 |
| attrezzo | Posizione dell'attrezzo in `equipment_order`: 1°: 1 · 2°: 0,67 · 3°: 0,33 · 4°: 0 |
| allungamento | `high` 1 · `medium` 0,6 · `low` 0,2 |
| famiglia | 1 se `F` è la famiglia principale dell'esercizio, 0,5 se è la secondaria |
| rango | `1 / family_rank`: piccolo vantaggio all'ordine editoriale della ricerca |
| etichette | Somma dei bonus meno le penalità effettive. Con i dati iniziali: "Collo: attenzione" −3 |

I pesi della base (3, 4, 1, 1, 0,5) stanno in `app_setting.score_weights`; i punti delle etichette stanno nelle etichette stesse. Tutto si cambia senza toccare il codice.

Più etichette sullo stesso esercizio si sommano: due penalità da 3 tolgono 6 punti. È voluto: due problemi pesano più di uno.

**Perché questi pesi.** L'ordine di precedenza è quello che hai scelto: prima le tue preferenze (attrezzo e collo), poi la confidenza delle fonti.

- L'attrezzo vale fino a 4 punti; la distanza tra un posto e il successivo in `equipment_order` è 1,33.
- La penalità del collo vale 3: più di due posti di attrezzo (2,67), meno di tre (4). Quindi, a parità del resto, un esercizio "Attenzione" vince su uno senza etichette solo se quest'ultimo usa un attrezzo tre posti più in basso, oppure due posti più in basso con anche una confidenza peggiore.
- La confidenza vale fino a 2,1 punti di scarto (da `solid` a `opinion`): conta, ma non scavalca le preferenze.
- L'allungamento pesa poco perché la ricerca lo tratta come criterio di spareggio, non come regola. Il rango serve a rompere le parità a favore dell'esercizio indicato per primo dalla ricerca.

Il punteggio può essere negativo: conta solo l'ordine tra i candidati.

**Il volume non entra nel punteggio.** Il punteggio dice quanto un esercizio ti si adatta; correggere i volumi è compito del ribilanciamento della fase 2, che userà questo stesso punteggio come penalità.

### 3.3 Ordinamento e determinismo

Candidati ordinati per punteggio decrescente; a parità per `family_rank` crescente; a parità ancora per `code` alfabetico. Con gli stessi dati il risultato è sempre identico (US-12 CA3).

### 3.4 Esempio

Slot "spinta inclinata" con le preferenze predefinite:

| Componente | Chest press inclinata | Panca inclinata a 30° |
| --- | --- | --- |
| confidenza | 3 · 0,6 = 1,8 | 3 · 0,6 = 1,8 |
| attrezzo | 4 · 1 (macchina) = 4 | 4 · 0,33 (pesi liberi) = 1,33 |
| allungamento | 1 · 0,6 = 0,6 | 1 · 1 = 1 |
| famiglia | 1 | 1 |
| rango | 0,5 · 1 = 0,5 | 0,5 · 1/2 = 0,25 |
| etichette | nessuna = 0 | "Collo: attenzione" = −3 |
| **Punteggio** | **7,90** | **2,38** |

Un secondo esempio mostra il limite della penalità. Slot "estensione sopra la testa": l'estensione ai cavi ha "Collo: attenzione" e ottiene 3,97; l'estensione con manubrio, senza etichette ma a pesi liberi, ottiene 4,40 e la supera. Vince comunque l'estensione alla macchina con 7,15.

### 3.5 Casi di test

| ID | Caso | Atteso |
| --- | --- | --- |
| P1 | Esempio § 3.4 | 7,90 e 2,38 |
| P2 | Esercizio con "Collo: evitare" | Escluso con motivo `tag-exclude:neck-avoid` |
| P3 | Scheda che personalizza "Collo: attenzione" con effetto `exclude` | Esercizio escluso con motivo `tag-exclude:neck-caution`; le altre schede non cambiano |
| P4 | `equipment_order` = pesi liberi, corpo libero, cavi, macchina | La panca inclinata (5,05) supera la chest press inclinata (3,90) |
| P4b | `equipment_order` = pesi liberi, cavi, macchina, corpo libero | Vince ancora la chest press inclinata (5,23 contro 5,05): con due posti di attrezzo a sfavore, la penalità del collo pesa ancora di più |
| P5 | Due candidati con punteggio identico | Vince il `family_rank` minore |
| P6 | Pesi modificati in `app_setting` | Il punteggio cambia di conseguenza |
| P7 | Esercizio con la famiglia dello slot come secondaria | Componente famiglia 0,5 |
| P8 | Esercizio con due etichette di penalità da 3 | Etichette = −6 |
| P9 | Etichetta con effetto `bonus` e 2 punti | +2 |
| P10 | Etichetta con effetto `none` | Nessun effetto sul punteggio; simbolo comunque restituito se `show_badge` |
| P11 | Scheda che personalizza i punti di "Collo: attenzione" a 1 | Penalità −1 in quella scheda, −3 nelle altre |
| P12 | Candidato escluso scelto a mano | Assegnazione accettata; nessun avviso di esclusione sulla scheda, simbolo visibile |

## 4. Generazione e rigenerazione

### 4.1 Generazione (US-12)

```
genera(split, preferenze, catalogo) → scheda
  per ogni giorno dello split, nell'ordine:
    copia nome, posizione, volte a settimana
    per ogni slot del giorno, nell'ordine:
      copia famiglia, serie, ripetizioni, facoltativo, peso settimanale, nota
      candidati ← validi della famiglia (§ 3.1), ordinati (§ 3.3)
      se ci sono candidati: esercizio ← il primo
      altrimenti: esercizio ← nullo; avviso "slot vuoto" con i motivi di esclusione
    copia gli stretch del giorno
  variante della seconda seduta: nulla (la sceglie l'utente)
  lucchetti: tutti aperti
```

### 4.2 Rigenerazione (US-18)

```
rigenera(scheda, preferenze, catalogo) → elenco di differenze
  per ogni slot non bloccato:
    migliore ← primo candidato valido della sua famiglia
    se migliore ≠ esercizio attuale: aggiungi differenza (slot, attuale → migliore, effetto sul volume)
  gli slot bloccati non cambiano in niente: esercizio, serie, ripetizioni, variante
```

La rigenerazione **non** cambia serie e ripetizioni degli slot non bloccati: l'utente potrebbe averle modificate di proposito. Restituisce solo le differenze; il servizio le applica dopo la conferma dell'utente.

### 4.3 Esito sui preset del documento

Con le preferenze predefinite la generazione sceglie gli esercizi del documento in 34 slot su 40. Nei 6 restanti sceglie un esercizio diverso della stessa famiglia, con **mappa muscolare identica** e quindi volumi identici:

| Slot | Documento | Generazione | Motivo |
| --- | --- | --- | --- |
| Push · croce orizzontale | Croci ai cavi da seduti | Pec deck | Macchina prima dei cavi |
| Push e Upper · estensione sopra la testa | Ai cavi | Alla macchina | Macchina prima dei cavi; in più i cavi hanno "Collo: attenzione" |
| Legs · squat guidato | Hack squat | Pressa a 45° | Confidenza "Limitato" contro "Opinione" |
| Legs e Lower · crunch | Crunch al cavo in ginocchio | Crunch alla macchina | Macchina prima dei cavi |

È il comportamento voluto: la generazione applica in modo coerente la preferenza per le macchine, mentre nel documento alcune scelte erano libere tra alternative equivalenti. Il test di riferimento confronta quindi i **volumi**, non i singoli esercizi.

### 4.4 Casi di test

| ID | Caso | Atteso |
| --- | --- | --- |
| G1 | Generazione di `ppl-6` con preferenze predefinite | Volumi identici all'Excel per tutti i muscoli |
| G2 | Generazione di `ul-4`, `ppl-3`, `pplul-5` | Come G1 |
| G3 | Stessa generazione eseguita due volte | Schede identiche |
| G4 | Famiglia senza candidati validi | Slot vuoto, avviso con motivi |
| G5 | Rigenerazione con uno slot bloccato e preferenze cambiate | Lo slot bloccato resta identico; gli altri seguono le nuove preferenze |
| G6 | Rigenerazione senza cambiamenti | Elenco di differenze vuoto |
| G7 | Rigenerazione dopo aver modificato a mano le serie di uno slot non bloccato | Le serie restano quelle modificate |

## 5. Anteprima delle varianti (US-14)

Per lo slot `s` e ogni candidato `e'` della sua famiglia:

```
ΔV(m) = n_s · w_s · occorrenze · (λ(e', m) − λ(e_s, m))
```

dove `occorrenze` è il numero di sedute settimanali in cui l'esercizio principale viene usato (`t_d`, oppure `t_d − 1` se c'è una variante di seconda seduta). Si restituiscono solo i muscoli con `ΔV ≠ 0`, insieme al punteggio, agli attributi e agli eventuali motivi di esclusione.

Il calcolo riguarda solo il contributo dello slot, quindi non richiede di ricalcolare l'intera scheda per ogni candidato.

**Variante della seconda seduta** (US-17). I candidati sono tutti gli esercizi attivi: prima quelli della famiglia dello slot, poi gli altri. Il confronto è con l'esercizio usato oggi nella seconda seduta (la variante, se c'è, altrimenti il principale), con `occorrenze = 1`:

```
ΔV₂(m) = n_s · w_s · 1 · (λ(e', m) − λ(e2_s oppure e_s, m))
```

**Esempio.** PPL 6 giorni, Push, slot "estensione a braccio lungo il corpo", 2 serie, `t = 2`. Passando da pushdown con barra (capo lungo S) a kickback ai cavi (capo lungo P):

```
ΔV(capo lungo) = 2 · 1 · 2 · (1 − 0,5) = +2
```

È esattamente il tipo di informazione che serve a correggere il capo lungo, oggi sotto fascia in tutti gli split.

| ID | Caso | Atteso |
| --- | --- | --- |
| A1 | Esempio sopra | Capo lungo +2; nessun altro muscolo cambia |
| A2 | Candidato con mappa identica | Nessuna differenza |
| A3 | Slot con variante di seconda seduta e `t = 2` | Le differenze usano `occorrenze = 1` |
| A4 | Candidato escluso | Presente nella risposta, in fondo, con motivo e senza essere assegnato |
| A5 | Candidato con etichette visibili | La risposta include simboli e note delle etichette |
| A6 | Upper di `ul-4`, slot spinta orizzontale (3 serie, `t = 2`): croci ai cavi come seconda seduta al posto della chest press | Capo laterale e capo mediale del tricipite −1,5; petto invariato (stessi livelli P e S) |

## 6. Stima della durata della seduta (US-20)

### 6.1 Formula

Per ogni seduta concreta:

```
durata = riscaldamento + stretching
       + Σ_s non facoltativo  w_s · ( n_s · T_serie + (n_s − 1) · R(s) + T_cambio )
       + Σ_g  2 · (T_avvicinamento + R_avvicinamento)
```

- `R(s)` è il recupero: `R_multi` se l'esercizio è multiarticolare, `R_iso` se è di isolamento.
- L'ultima somma conta 2 serie di avvicinamento per ogni gruppo muscolare `g` il cui **primo** esercizio nella seduta è multiarticolare. È la regola del documento: avvicinamento sul primo esercizio di ogni muscolo.

| Parametro | Default | Fonte |
| --- | --- | --- |
| `T_serie` | 45 s | Stima: 8-15 ripetizioni a 2-3 s l'una |
| `R_multi` | 150 s | Parametri: 2-3 minuti sui multiarticolari |
| `R_iso` | 90 s | Parametri: almeno 90 secondi |
| `T_cambio` | 60 s | Stima: preparare la macchina successiva |
| `T_avvicinamento`, `R_avvicinamento` | 30 s, 60 s | Stima |
| riscaldamento | 10 min | Parametri: cardio 5-10 minuti più mobilità |
| stretching | 6 min | Composizione dei giorni: 5-8 minuti |

Tutti in `app_setting.duration_params`.

### 6.2 Verifica sui giorni del documento

| Giorno | Stima | Indicazione del documento |
| --- | --- | --- |
| Push | 60,5 min | 60-75 min |
| Pull | 56 min | 60-75 min (ampia; il Pull ha più isolamento) |
| Legs | 59 min | 60-75 min |
| Upper | 75,5 min | 75-80 min |
| Lower | 57 min | non indicata |

L'ordine di grandezza coincide; il valore resta indicativo.

| ID | Caso | Atteso |
| --- | --- | --- |
| D1 | Push del documento | 60,5 min con i parametri predefiniti |
| D2 | Slot facoltativo | Non conta |
| D3 | Due esercizi multiarticolari dello stesso gruppo | Avvicinamento contato una sola volta |
| D4 | Durata oltre `max_session_minutes` | Avviso |

## 7. Test di riferimento

I volumi settimanali della tabella dell'Excel (foglio "Volume_settimanale") diventano un file di dati di test versionato: per ogni split e ogni muscolo, il valore atteso. Il test genera ogni split con le preferenze predefinite e confronta muscolo per muscolo, con tolleranza zero.

Estratto:

| Muscolo | PPL 6 | PPL 3 | UL 4 | PPLUL 5 |
| --- | --- | --- | --- | --- |
| Petto alto | 12 | 6 | 9 | 10,5 |
| Petto medio | 15 | 7,5 | 9 | 12 |
| Deltoide laterale | 11 | 5,5 | 8 | 9,5 |
| Tricipite, capo lungo | 8 | 4 | 6 | 7 |
| Gran dorsale | 12 | 6 | 12 | 12 |
| Bicipite | 16 | 8 | 10 | 13 |
| Quadricipiti | 12 | 6 | 12 | 12 |
| Femorali | 6 | 3 | 6 | 6 |

Verifica preliminare: con le famiglie del documento sui dati iniziali, la generazione riproduce tutti i volumi di tutti e quattro gli split senza differenze. La tabella completa, con i valori di `pp-4` e `fb-3` (calcolati, non presi dall'Excel), è nel documento sui dati iniziali.

Quando un valore atteso cambia di proposito (per esempio perché si modifica la mappa muscolare di un esercizio), il file si aggiorna nella stessa pull request, con il motivo nella descrizione.

## 8. Avvisi restituiti con la scheda

| Codice | Quando | Dati |
| --- | --- | --- |
| `volume-below` | Muscolo con fascia sotto il minimo | muscolo, volume, fascia |
| `volume-above` | Muscolo con fascia sopra il massimo | muscolo, volume, fascia |
| `session-cap` | Muscolo oltre il tetto in una seduta | giorno, seduta (1 o 2), muscolo, volume |
| `session-too-long` | Durata stimata oltre `max_session_minutes` | giorno, seduta, durata |
| `empty-slot` | Slot senza esercizio | giorno, posizione, famiglia, motivi |

## 9. Prestazioni

Per una scheda di 40 slot, 32 muscoli e una decina di candidati per famiglia, ogni operazione richiede al massimo qualche migliaio di operazioni aritmetiche: microsecondi o pochi millisecondi. Il limite di 300 ms (NF1) dipende solo da rete e database. Un test di prestazioni in M4 misura il ciclo completo di modifica.

## 10. Verso la fase 2: il ribilanciamento

Non si implementa ora, ma il disegno della fase 1 lo rende un'aggiunta:

```
penalità(scheda) = Σ_m distanza(V(m), fascia(m))²
                 − α · Σ_s punteggio(e_s)
                 + β · Σ_sedute max(0, durata − massimo)
```

Una ricerca locale sugli slot non bloccati prova a cambiare esercizio dentro la famiglia e a spostare le serie di ±1 entro limiti, accetta le mosse che riducono la penalità e si ferma quando nessuna migliora. Usa le funzioni di questo documento (volume, punteggio, durata) senza modificarle.

## 11. Domande risolte

1. Precedenza nel punteggio: prima le preferenze personali (attrezzo, collo), poi la confidenza. Risolta nella v0.2.
2. Esercizi "Attenzione": penalizzati di 3 punti e segnalati con un simbolo, non esclusi; il meccanismo è generale (etichette, ADR 0014). Risolta nella v0.2.
3. Priorità e fasce personalizzabili per scheda: sì, entrambe, con ereditarietà dal catalogo. Risolta nella v0.2.
