# Dati iniziali — Fase 1

| Campo | Valore |
| --- | --- |
| Stato | Bozza v0.2, decisioni prese |
| Data | 2026-10-28 |
| Riferimenti | `banca_dati_esercizi.xlsx`; documento di ricerca; modello dati v0.2; algoritmo v0.2; ADR 0006, 0014 |

Questo documento fissa i dati con cui l'app parte: codici, famiglie di movimento, assegnazione degli esercizi, etichette, composizione degli split e valori dei test di riferimento. Diventa il seed (§ 9) e la base dei test della tappa M1.

Tutti i numeri sono stati verificati con uno script sulla banca dati attuale: la generazione con le famiglie qui proposte riproduce esattamente i volumi dell'Excel per i quattro split del documento di ricerca.

## 1. Cosa viene dall'Excel e cosa è nuovo

| Dato | Origine |
| --- | --- |
| Gruppi, muscoli, priorità, fasce | Excel, invariati; si aggiungono i `code` (§ 2) |
| Esercizi, mappe muscolari, attrezzi, allungamento, confidenza, fonti | Excel, invariati |
| Famiglie di movimento, `family_rank`, `kind` | **Nuovi**, costruiti dalle alternative dell'Excel (§ 3, § 4) |
| Etichette | **Nuove**, ricavate dalla colonna "collo" (§ 5) |
| Split `ppl-3`, `ppl-6`, `ul-4`, `pplul-5` | Excel; gli esercizi fissi diventano famiglie (§ 6.1) |
| Split `pp-4`, `fb-3` | **Nuovi**, da approvare (§ 6.3, § 6.4) |
| Stretching e mini-allenamento | Excel, con gli stretch ripetuti unificati (§ 7) |

## 2. Codici

Gruppi muscolari: `chest`, `shoulders`, `triceps`, `back`, `biceps`, `forearms`, `legs`, `core`, nell'ordine dell'Excel (G1-G8).

Attrezzi: `machine` (M), `cable` (C), `free-weight` (L), `bodyweight` (CL).

Fonti: `src-01` … `src-48`, con la numerazione dell'Excel (F01-F48).

Muscoli:

| Excel | `code` | Nome |
| --- | --- | --- |
| PA | `chest-upper` | Petto alto (fascio clavicolare) |
| PM | `chest-mid` | Petto medio (fascio sternocostale) |
| PB | `chest-lower` | Petto basso (fascio addominale) |
| DA | `delt-front` | Deltoide anteriore |
| DL | `delt-lateral` | Deltoide laterale |
| DP | `delt-rear` | Deltoide posteriore |
| — | `rotator-cuff` | Cuffia dei rotatori (extrarotatori: sottospinato e piccolo rotondo). **Non nell'Excel:** aggiunto perché l'extrarotazione (E023) aveva solo il deltoide posteriore come secondario, e ogni esercizio deve avere un muscolo primario (modello dati, § 7). Nessun obiettivo |
| TLU | `triceps-long` | Tricipite, capo lungo |
| TLA | `triceps-lateral` | Tricipite, capo laterale |
| TME | `triceps-medial` | Tricipite, capo mediale |
| DOR | `lats` | Gran dorsale e grande rotondo |
| TRM | `traps-mid` | Trapezio medio e romboidi |
| TRI | `traps-lower` | Trapezio inferiore |
| TRS | `traps-upper` | Trapezio superiore |
| ERE | `erectors` | Erettori spinali |
| BIC | `biceps` | Bicipite brachiale |
| BRA | `brachialis` | Brachiale |
| BRR | `brachioradialis` | Brachioradiale |
| FLE | `forearm-flexors` | Flessori del polso e delle dita |
| EST | `forearm-extensors` | Estensori del polso e delle dita |
| PRS | `pronators-supinators` | Pronatori e supinatori |
| QUA | `quads` | Quadricipiti (vasti) |
| RFE | `rectus-femoris` | Retto femorale |
| FEM | `hamstrings` | Femorali |
| GGL | `glute-max` | Grande gluteo |
| MGL | `glute-med` | Medio e piccolo gluteo |
| ADD | `adductors` | Adduttori |
| GAS | `gastrocnemius` | Gastrocnemio |
| SOL | `soleus` | Soleo |
| FAN | `hip-flexors` | Flessori dell'anca |
| RET | `rectus-abdominis` | Retto dell'addome |
| OBL | `obliques` | Obliqui |
| STB | `stabilizers` | Stabilizzatori (trasverso, quadrato dei lombi) |

## 3. Famiglie di movimento

### 3.1 Criteri

Una famiglia raccoglie gli esercizi **intercambiabili in uno slot**: stesso schema di movimento e stessi muscoli principali, tanto che sostituire l'uno con l'altro non cambia il senso della scheda (ADR 0006). Le regole usate:

1. **Punto di partenza: la colonna "alternativa" dell'Excel.** Esercizi che l'Excel indica come alternativa l'uno dell'altro stanno nella stessa famiglia, salvo quando l'alternativa cambia di proposito l'enfasi (es. croci dal basso al posto delle croci orizzontali: più petto alto). In quel caso le famiglie restano due.
2. **Una famiglia, un gruppo muscolare.** Il gruppo della famiglia è quello dell'Excel per tutti i suoi esercizi (verificato dallo script).
3. **Famiglia secondaria solo dove serve davvero**: quando un esercizio è un'alternativa sensata anche in un altro schema. Sono 4: dip (anche spinta a presa stretta), back extension (anche cerniera dell'anca), reverse curl (anche curl a martello), wrist roller (anche estensione del polso). Come secondaria, l'esercizio prende 0,5 invece di 1 nella voce "famiglia" del punteggio: compare tra i candidati, con un piccolo svantaggio.
4. **`family_rank` segue l'ordine dell'Excel**, che è l'ordine in cui la ricerca presenta gli esercizi: il primo è quello indicato come scelta di base.
5. **Famiglie anche con un solo esercizio** (es. abduzione, scrollata): così aggiungere un esercizio in futuro non richiede di toccare gli split.

### 3.2 Elenco

40 famiglie: petto 6, spalle 5, tricipiti 3, schiena 6, bicipiti 3, avambracci 4, gambe 9, core 4.

| Codice | Nome | Gruppo | Descrizione | Esercizi (in ordine di rango) |
| --- | --- | --- | --- | --- |
| `press-horizontal` | Spinta orizzontale | Petto | Spinte a busto orizzontale: petto medio, con petto alto e tricipiti | E001, E003 |
| `press-incline` | Spinta inclinata | Petto | Spinte su panca o seduta inclinata: petto alto | E002, E004 |
| `fly-horizontal` | Croce orizzontale | Petto | Croci con braccia all'altezza del petto: petto medio in allungamento | E005, E006 |
| `fly-low-high` | Croce dal basso | Petto | Croci dal basso verso l'alto o su panca inclinata: petto alto | E007, E008 |
| `fly-high-low` | Croce dall'alto | Petto | Croci dall'alto verso il basso: petto basso in isolamento | E009 |
| `dip-decline` | Dip e declinata | Petto | Spinte verso il basso: petto basso e tricipiti | E010, E011 |
| `press-vertical` | Spinta verticale | Spalle | Spinte sopra la testa: deltoide anteriore | E012, E013 |
| `raise-lateral` | Alzata laterale | Spalle | Abduzione della spalla: deltoide laterale | E014, E015, E016, E017, E021 |
| `rear-delt` | Deltoide posteriore | Spalle | Abduzione orizzontale: deltoide posteriore e trapezio medio | E018, E019, E020 |
| `raise-front` | Alzata frontale | Spalle | Flessione della spalla; in genere superflua | E022 |
| `external-rotation` | Extrarotazione | Spalle | Salute della cuffia dei rotatori | E023 |
| `triceps-overhead` | Estensione sopra la testa | Tricipiti | Gomito sopra la testa: capo lungo in allungamento | E024, E025, E026, E027, E028 |
| `triceps-pushdown` | Estensione a braccio lungo il corpo | Tricipiti | Pushdown e kickback: capi laterale e mediale | E029, E030, E031 |
| `triceps-press` | Spinta a presa stretta | Tricipiti | Multiarticolari con enfasi sui tricipiti | E032, E033; secondaria per E010 |
| `pull-vertical` | Tirata verticale | Schiena | Lat machine e trazioni: gran dorsale | E034, E035, E036, E037 |
| `pull-horizontal` | Tirata orizzontale | Schiena | Rematori: dorsale e trapezio medio | E038, E039, E040, E041 |
| `straight-arm` | Braccia tese | Schiena | Estensione della spalla a gomito fermo: dorsale isolato | E042 |
| `shrug` | Scrollata | Schiena | Elevazione delle scapole: trapezio superiore | E043 |
| `y-raise` | Y-raise | Schiena | Depressione e rotazione verso l'alto delle scapole: trapezio inferiore | E044 |
| `lower-back` | Estensione della schiena | Schiena | Erettori spinali | E045 |
| `curl-front` | Curl con braccio davanti | Bicipiti e flessori del gomito | Curl su panca Scott e in piedi | E046, E047, E051, E052 |
| `curl-behind` | Curl con braccio dietro | Bicipiti e flessori del gomito | Braccio dietro il corpo: bicipite in allungamento | E049, E050 |
| `curl-hammer` | Curl a martello | Bicipiti e flessori del gomito | Presa neutra: brachiale e brachioradiale | E048, E053; secondaria per E056 |
| `wrist-flexion` | Flessione del polso | Avambracci | Flessori del polso e delle dita | E054, E057 |
| `wrist-extension` | Estensione del polso | Avambracci | Estensori e brachioradiale | E055, E056; secondaria per E057 |
| `grip` | Presa statica | Avambracci | Tenute: presa e trapezio | E058 |
| `forearm-rotation` | Prono-supinazione | Avambracci | Pronatori e supinatori | E059 |
| `squat-guided` | Squat guidato e pressa | Gambe | Multiarticolari a ginocchio dominante: quadricipiti | E060, E061, E062 |
| `knee-extension` | Estensione del ginocchio | Gambe | Quadricipiti e retto femorale | E063 |
| `knee-flexion` | Flessione del ginocchio | Gambe | Femorali | E064, E065 |
| `hip-hinge` | Cerniera dell'anca | Gambe | Femorali e glutei in allungamento | E066; secondaria per E045 |
| `hip-thrust` | Spinta dell'anca | Gambe | Grande gluteo; aiuta il controllo del bacino | E067 |
| `abduction` | Abduzione | Gambe | Medio e piccolo gluteo | E068 |
| `adduction` | Adduzione | Gambe | Adduttori | E069 |
| `calf-straight` | Polpacci a gamba tesa | Gambe | Gastrocnemio e soleo | E070 |
| `calf-bent` | Polpacci a ginocchio flesso | Gambe | Soleo | E071 |
| `crunch` | Crunch | Core | Flessione del busto: retto dell'addome | E072, E073, E074, E077 |
| `reverse-crunch` | Reverse crunch | Core | Bacino che si arrotola: retto dell'addome, parte bassa | E075, E076 |
| `anti-rotation` | Anti-rotazione | Core | Obliqui e stabilizzatori | E078, E079 |
| `core-stability` | Controllo del tronco | Core | Stabilità e controllo del bacino | E080, E081 |

## 4. Esercizi

### 4.1 Tipo: multiarticolare o isolamento

`kind = compound` per spinte, tirate, squat, pressa, stacco rumeno, hip thrust, dip, panca stretta e tirate al mento (24 esercizi); `isolation` per tutti gli altri, compresi gli esercizi per il core e la back extension. Il tipo serve solo a recuperi predefiniti, serie di avvicinamento e stima della durata.

### 4.2 Assegnazione completa

Legenda: "multi" multiarticolare, "iso" isolamento. Tra parentesi il `family_rank`.

#### Petto

| Excel | Codice | Nome | Famiglia (rango) | Secondaria | Tipo | Attrezzo | Etichette |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E001 | `chest-press` | Chest press seduta | `press-horizontal` (1) |  | multi | Macchina |  |
| E003 | `bench-press` | Panca piana | `press-horizontal` (2) |  | multi | Pesi liberi | Collo: attenzione |
| E002 | `chest-press-incline` | Chest press inclinata | `press-incline` (1) |  | multi | Macchina |  |
| E004 | `incline-bench-press` | Panca inclinata a 30° | `press-incline` (2) |  | multi | Pesi liberi | Collo: attenzione |
| E005 | `cable-fly-seated` | Croci ai cavi da seduti | `fly-horizontal` (1) |  | iso | Cavi |  |
| E006 | `pec-deck` | Pec deck (chest fly a macchina) | `fly-horizontal` (2) |  | iso | Macchina |  |
| E007 | `cable-fly-low-high` | Croci ai cavi dal basso verso l'alto | `fly-low-high` (1) |  | iso | Cavi | Collo: attenzione |
| E008 | `incline-dumbbell-fly` | Croci su panca inclinata | `fly-low-high` (2) |  | iso | Pesi liberi |  |
| E009 | `cable-fly-high-low` | Croci ai cavi dall'alto verso il basso | `fly-high-low` (1) |  | iso | Cavi |  |
| E010 | `dip` | Dip (parallele, assistite o macchina dip) | `dip-decline` (1) | `triceps-press` | multi | Corpo libero | Collo: attenzione |
| E011 | `decline-press` | Panca o chest press declinata | `dip-decline` (2) |  | multi | Macchina |  |

#### Spalle

| Excel | Codice | Nome | Famiglia (rango) | Secondaria | Tipo | Attrezzo | Etichette |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E012 | `machine-shoulder-press` | Shoulder press a macchina | `press-vertical` (1) |  | multi | Macchina | Collo: attenzione |
| E013 | `dumbbell-shoulder-press` | Lento con manubri da seduti | `press-vertical` (2) |  | multi | Pesi liberi | Collo: attenzione |
| E014 | `cable-lateral-raise` | Alzate laterali ai cavi, un braccio | `raise-lateral` (1) |  | iso | Cavi | Collo: accorgimento |
| E015 | `machine-lateral-raise` | Alzate laterali a macchina | `raise-lateral` (2) |  | iso | Macchina |  |
| E016 | `dumbbell-lateral-raise` | Alzate laterali con manubri | `raise-lateral` (3) |  | iso | Pesi liberi | Collo: attenzione |
| E017 | `lying-lateral-raise` | Alzate laterali sdraiato su un fianco | `raise-lateral` (4) |  | iso | Pesi liberi |  |
| E021 | `wide-upright-row` | Tirate al mento a presa larga (barra o corda) | `raise-lateral` (5) |  | multi | Cavi | Collo: attenzione |
| E018 | `reverse-pec-deck` | Reverse pec deck, presa neutra | `rear-delt` (1) |  | iso | Macchina |  |
| E019 | `cable-reverse-fly` | Croci inverse ai cavi | `rear-delt` (2) |  | iso | Cavi |  |
| E020 | `face-pull` | Face pull | `rear-delt` (3) |  | iso | Cavi | Collo: attenzione |
| E022 | `front-raise` | Alzate frontali | `raise-front` (1) |  | iso | Pesi liberi | Collo: attenzione |
| E023 | `cable-external-rotation` | Extrarotazioni ai cavi o con elastico | `external-rotation` (1) |  | iso | Cavi |  |

#### Tricipiti

| Excel | Codice | Nome | Famiglia (rango) | Secondaria | Tipo | Attrezzo | Etichette |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E024 | `cable-overhead-extension` | Estensione sopra la testa ai cavi (barra o corda) | `triceps-overhead` (1) |  | iso | Cavi | Collo: attenzione |
| E025 | `machine-overhead-extension` | Estensione sopra la testa alla macchina | `triceps-overhead` (2) |  | iso | Macchina |  |
| E026 | `dumbbell-overhead-extension` | Estensione a un braccio con manubrio, da seduti con schienale | `triceps-overhead` (3) |  | iso | Pesi liberi |  |
| E027 | `katana-extension` | Estensione katana ai cavi (braccia incrociate) | `triceps-overhead` (4) |  | iso | Cavi |  |
| E028 | `ez-skull-crusher` | Skull crusher con bilanciere EZ, portato dietro la testa | `triceps-overhead` (5) |  | iso | Pesi liberi | Collo: accorgimento |
| E029 | `pushdown-bar` | Pushdown al cavo con barra | `triceps-pushdown` (1) |  | iso | Cavi |  |
| E030 | `pushdown-rope` | Pushdown al cavo con corda | `triceps-pushdown` (2) |  | iso | Cavi |  |
| E031 | `cable-kickback` | Kickback ai cavi | `triceps-pushdown` (3) |  | iso | Cavi |  |
| E032 | `close-grip-bench-press` | Panca a presa stretta (bilanciere o Smith) | `triceps-press` (1) |  | multi | Pesi liberi | Collo: attenzione |
| E033 | `machine-dip` | Dip alla macchina (seduti) o dip a busto verticale | `triceps-press` (2) |  | multi | Macchina |  |

#### Schiena

| Excel | Codice | Nome | Famiglia (rango) | Secondaria | Tipo | Attrezzo | Etichette |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E034 | `lat-pulldown-wide` | Lat machine, presa prona media o larga, al petto | `pull-vertical` (1) |  | multi | Macchina |  |
| E035 | `lat-pulldown-neutral` | Lat machine, presa neutra o supina stretta | `pull-vertical` (2) |  | multi | Macchina |  |
| E036 | `single-arm-pulldown` | Lat machine a un braccio, in ginocchio | `pull-vertical` (3) |  | multi | Cavi |  |
| E037 | `assisted-pull-up` | Trazioni alla macchina assistita, presa neutra | `pull-vertical` (4) |  | multi | Macchina |  |
| E038 | `chest-supported-row` | Rematore con appoggio al petto (macchina o T-bar) | `pull-horizontal` (1) |  | multi | Macchina |  |
| E039 | `cable-row-wide` | Pulley basso, presa larga | `pull-horizontal` (2) |  | multi | Cavi |  |
| E040 | `cable-row-close` | Pulley basso, presa stretta, gomiti vicini al corpo | `pull-horizontal` (3) |  | multi | Cavi |  |
| E041 | `dumbbell-row` | Rematore a un braccio con manubrio su panca | `pull-horizontal` (4) |  | multi | Pesi liberi | Collo: attenzione |
| E042 | `straight-arm-pulldown` | Pullover al cavo o macchina pullover (braccia tese) | `straight-arm` (1) |  | iso | Cavi |  |
| E043 | `shrug-dumbbell-machine` | Scrollate con manubri o alla macchina | `shrug` (1) |  | iso | Macchina | Collo: attenzione |
| E044 | `prone-y-raise` | Y-raise da proni su panca inclinata | `y-raise` (1) |  | iso | Pesi liberi | Collo: attenzione |
| E045 | `back-extension` | Back extension a 45° o macchina lombare | `lower-back` (1) | `hip-hinge` | iso | Macchina |  |

#### Bicipiti e flessori del gomito

| Excel | Codice | Nome | Famiglia (rango) | Secondaria | Tipo | Attrezzo | Etichette |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E046 | `machine-preacher-curl` | Curl alla macchina Scott (preacher) | `curl-front` (1) |  | iso | Macchina |  |
| E047 | `dumbbell-preacher-curl` | Curl con manubrio su panca Scott | `curl-front` (2) |  | iso | Pesi liberi |  |
| E051 | `standing-cable-curl` | Curl al cavo in piedi (barra o EZ) | `curl-front` (3) |  | iso | Cavi | Collo: attenzione |
| E052 | `standing-curl` | Curl con bilanciere EZ o manubri, in piedi | `curl-front` (4) |  | iso | Pesi liberi | Collo: attenzione |
| E049 | `incline-dumbbell-curl` | Curl su panca inclinata con manubri | `curl-behind` (1) |  | iso | Pesi liberi | Collo: accorgimento |
| E050 | `bayesian-curl` | Bayesian curl (di spalle al cavo, braccio dietro il corpo) | `curl-behind` (2) |  | iso | Cavi | Collo: attenzione |
| E048 | `preacher-hammer-curl` | Hammer curl su panca Scott | `curl-hammer` (1) |  | iso | Pesi liberi |  |
| E053 | `hammer-curl` | Hammer curl con manubri o corda al cavo | `curl-hammer` (2) |  | iso | Pesi liberi | Collo: attenzione |

#### Avambracci

| Excel | Codice | Nome | Famiglia (rango) | Secondaria | Tipo | Attrezzo | Etichette |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E054 | `wrist-curl` | Curl del polso, palmi in su, avambraccio appoggiato | `wrist-flexion` (1) |  | iso | Pesi liberi |  |
| E057 | `wrist-roller` | Wrist roller | `wrist-flexion` (2) | `wrist-extension` | iso | Pesi liberi | Collo: attenzione |
| E055 | `reverse-wrist-curl` | Curl del polso inverso, palmi in giù, avambraccio appoggiato | `wrist-extension` (1) |  | iso | Pesi liberi |  |
| E056 | `reverse-curl` | Reverse curl (presa prona, bilanciere EZ o cavo) | `wrist-extension` (2) | `curl-hammer` | iso | Pesi liberi | Collo: attenzione |
| E058 | `static-holds` | Prese statiche (presa al disco, camminata del contadino, sospensione alla sbarra) | `grip` (1) |  | iso | Pesi liberi | Collo: attenzione |
| E059 | `pronation-supination` | Pronazione e supinazione con manubrio sbilanciato | `forearm-rotation` (1) |  | iso | Pesi liberi |  |

#### Gambe

| Excel | Codice | Nome | Famiglia (rango) | Secondaria | Tipo | Attrezzo | Etichette |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E060 | `hack-squat` | Hack squat o pendulum squat, profondo | `squat-guided` (1) |  | multi | Macchina |  |
| E061 | `leg-press` | Pressa a 45°, profonda | `squat-guided` (2) |  | multi | Macchina |  |
| E062 | `smith-squat` | Squat al multipower (Smith), profondo | `squat-guided` (3) |  | multi | Macchina | Collo: attenzione |
| E063 | `leg-extension` | Leg extension, schienale reclinato | `knee-extension` (1) |  | iso | Macchina |  |
| E064 | `seated-leg-curl` | Leg curl da seduti | `knee-flexion` (1) |  | iso | Macchina |  |
| E065 | `lying-leg-curl` | Leg curl sdraiato | `knee-flexion` (2) |  | iso | Macchina |  |
| E066 | `romanian-deadlift` | Stacco rumeno (manubri o bilanciere) | `hip-hinge` (1) |  | multi | Pesi liberi | Collo: attenzione |
| E067 | `hip-thrust-machine` | Hip thrust alla macchina o al multipower | `hip-thrust` (1) |  | multi | Macchina |  |
| E068 | `hip-abduction` | Abduzione dell'anca alla macchina | `abduction` (1) |  | iso | Macchina |  |
| E069 | `hip-adduction` | Adduzione dell'anca alla macchina | `adduction` (1) |  | iso | Macchina |  |
| E070 | `calf-raise-straight` | Calf raise alla pressa o in piedi, gambe tese | `calf-straight` (1) |  | iso | Macchina | Collo: accorgimento |
| E071 | `seated-calf-raise` | Calf raise da seduti | `calf-bent` (1) |  | iso | Macchina |  |

#### Core

| Excel | Codice | Nome | Famiglia (rango) | Secondaria | Tipo | Attrezzo | Etichette |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E072 | `kneeling-cable-crunch` | Crunch al cavo in ginocchio (corda) | `crunch` (1) |  | iso | Cavi | Collo: accorgimento |
| E073 | `seated-cable-crunch` | Crunch al cavo seduto alla lat machine, di spalle | `crunch` (2) |  | iso | Cavi |  |
| E074 | `machine-crunch` | Crunch alla macchina | `crunch` (3) |  | iso | Macchina |  |
| E077 | `floor-crunch` | Crunch a terra o curl-up | `crunch` (4) |  | iso | Corpo libero | Collo: evitare |
| E075 | `bench-reverse-crunch` | Reverse crunch su panca piana o declinata | `reverse-crunch` (1) |  | iso | Corpo libero | Collo: accorgimento |
| E076 | `leg-raise` | Leg raise alla sedia romana o appesi, bacino arrotolato | `reverse-crunch` (2) |  | iso | Corpo libero | Collo: attenzione |
| E078 | `side-plank` | Side plank | `anti-rotation` (1) |  | iso | Corpo libero | Collo: attenzione |
| E079 | `pallof-press` | Pallof press al cavo | `anti-rotation` (2) |  | iso | Cavi |  |
| E080 | `bird-dog` | Bird dog | `core-stability` (1) |  | iso | Corpo libero |  |
| E081 | `dead-bug` | Dead bug | `core-stability` (2) |  | iso | Corpo libero | Collo: accorgimento |

## 5. Etichette iniziali

### 5.1 Definizione

| `code` | Nome | Simbolo | Colore | Effetto | Punti | Visibile |
| --- | --- | --- | --- | --- | --- | --- |
| `neck-tip` | Collo: accorgimento | `info` | `info` | `none` | 0 | sì |
| `neck-caution` | Collo: attenzione | `warning` | `warning` | `penalty` | 3 | sì |
| `neck-avoid` | Collo: evitare | `ban` | `danger` | `exclude` | 0 | sì |

`neck-tip` è un'etichetta senza effetto sul punteggio, che porta con sé l'accorgimento degli esercizi "OK, a patto che…". Senza di essa quelle note (es. "se le spalle non salgono" sulle alzate ai cavi) andrebbero perse, perché un esercizio OK non avrebbe etichette. È anche il primo esempio dell'effetto `none`.

### 5.2 Regole di conversione dalla colonna "collo"

| Valore nell'Excel | Etichetta | Nota |
| --- | --- | --- |
| "OK" | nessuna | |
| "OK" seguito da una condizione, es. "OK se la testa segue il busto", "OK (testa appoggiata)" | `neck-tip` | La condizione |
| "Attenzione" | `neck-caution` | Vuota, o il resto del testo |
| Giudizio che dipende dalla variante, es. "In piedi Attenzione; sdraiato OK" | Quello della variante **peggiore**, salvo che lo split indichi già quella buona | Entrambi i giudizi |
| "Evitare" (anche "Evitare o Attenzione") | `neck-avoid` | Il giudizio originale |

Il caso della variante si presenta 3 volte. Face pull e leg raise prendono `neck-caution`: le varianti sicure (sdraiato, alla sedia romana) non sono quelle di default. Il calf raise prende `neck-tip`, perché gli split indicano già "alla pressa". Il criterio prudente ha anche un effetto pratico: se il leg raise non fosse penalizzato, supererebbe il reverse crunch nello slot del Legs per via della confidenza più alta, cambiando i volumi rispetto all'Excel.

### 5.3 Assegnazioni

34 esercizi su 81 hanno un'etichetta sul collo: 26 `neck-caution`, 7 `neck-tip`, 1 `neck-avoid`.

| Excel | Esercizio | Etichetta | Nota dell'assegnazione |
| --- | --- | --- | --- |
| E003 | Panca piana | Collo: attenzione |  |
| E004 | Panca inclinata a 30° | Collo: attenzione |  |
| E007 | Croci ai cavi dal basso verso l'alto | Collo: attenzione |  |
| E010 | Dip (parallele, assistite o macchina dip) | Collo: attenzione | Attenzione anche per le spalle |
| E012 | Shoulder press a macchina | Collo: attenzione |  |
| E013 | Lento con manubri da seduti | Collo: attenzione |  |
| E014 | Alzate laterali ai cavi, un braccio | Collo: accorgimento | Se le spalle non salgono |
| E016 | Alzate laterali con manubri | Collo: attenzione |  |
| E020 | Face pull | Collo: attenzione | In piedi attenzione; da sdraiati OK |
| E021 | Tirate al mento a presa larga (barra o corda) | Collo: attenzione |  |
| E022 | Alzate frontali | Collo: attenzione |  |
| E024 | Estensione sopra la testa ai cavi (barra o corda) | Collo: attenzione |  |
| E028 | Skull crusher con bilanciere EZ, portato dietro la testa | Collo: accorgimento | Testa appoggiata |
| E032 | Panca a presa stretta (bilanciere o Smith) | Collo: attenzione |  |
| E041 | Rematore a un braccio con manubrio su panca | Collo: attenzione |  |
| E043 | Scrollate con manubri o alla macchina | Collo: attenzione |  |
| E044 | Y-raise da proni su panca inclinata | Collo: attenzione |  |
| E049 | Curl su panca inclinata con manubri | Collo: accorgimento | Testa appoggiata |
| E050 | Bayesian curl (di spalle al cavo, braccio dietro il corpo) | Collo: attenzione |  |
| E051 | Curl al cavo in piedi (barra o EZ) | Collo: attenzione |  |
| E052 | Curl con bilanciere EZ o manubri, in piedi | Collo: attenzione |  |
| E053 | Hammer curl con manubri o corda al cavo | Collo: attenzione |  |
| E056 | Reverse curl (presa prona, bilanciere EZ o cavo) | Collo: attenzione |  |
| E057 | Wrist roller | Collo: attenzione |  |
| E058 | Prese statiche (presa al disco, camminata del contadino, sospensione alla sbarra) | Collo: attenzione | Attenzione nella camminata del contadino; le altre prese OK |
| E062 | Squat al multipower (Smith), profondo | Collo: attenzione |  |
| E066 | Stacco rumeno (manubri o bilanciere) | Collo: attenzione |  |
| E070 | Calf raise alla pressa o in piedi, gambe tese | Collo: accorgimento | Alla pressa OK; in piedi attenzione |
| E072 | Crunch al cavo in ginocchio (corda) | Collo: accorgimento | Se la testa segue il busto |
| E075 | Reverse crunch su panca piana o declinata | Collo: accorgimento | Testa appoggiata |
| E076 | Leg raise alla sedia romana o appesi, bacino arrotolato | Collo: attenzione | Alla sedia romana OK; appesi attenzione |
| E077 | Crunch a terra o curl-up | Collo: evitare | Giudizio della ricerca: evitare, al più attenzione |
| E078 | Side plank | Collo: attenzione |  |
| E081 | Dead bug | Collo: accorgimento | Testa a terra |

## 6. Split

### 6.1 Split del documento di ricerca

Slot come nell'Excel, con la famiglia al posto dell'esercizio fisso. "Peso" 0,5 indica le settimane alterne. Le note dell'Excel diventano le note degli slot e non sono ripetute qui.

| `code` | Giorni × volte a settimana |
| --- | --- |
| `ppl-6` | Push × 2, Pull × 2, Legs × 2 |
| `ppl-3` | Push, Pull, Legs × 1 |
| `ul-4` | Upper × 2, Lower × 2 |
| `pplul-5` | Push, Pull, Legs, Upper, Lower × 1 |

#### Push

| # | Famiglia | Serie | Ripetizioni | Facoltativo | Peso | Esercizio del documento |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `press-incline` | 3 | 6-12 |  | 1 | Chest press inclinata |
| 2 | `press-horizontal` | 3 | 6-12 |  | 1 | Chest press seduta |
| 3 | `fly-horizontal` | 3 | 10-20 |  | 1 | Croci ai cavi da seduti |
| 4 | `raise-lateral` | 4 | 10-20 |  | 1 | Alzate laterali ai cavi, un braccio |
| 5 | `triceps-overhead` | 3 | 10-15 |  | 1 | Estensione sopra la testa ai cavi (barra o corda) |
| 6 | `triceps-pushdown` | 2 | 10-15 |  | 1 | Pushdown al cavo con barra |
| 7 | `press-vertical` | 2 | 8-12 | sì | 1 | Shoulder press a macchina |

#### Pull

| # | Famiglia | Serie | Ripetizioni | Facoltativo | Peso | Esercizio del documento |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `pull-vertical` | 3 | 6-12 |  | 1 | Lat machine, presa prona media o larga, al petto |
| 2 | `pull-horizontal` | 3 | 6-12 |  | 1 | Rematore con appoggio al petto (macchina o T-bar) |
| 3 | `rear-delt` | 3 | 10-20 |  | 1 | Reverse pec deck, presa neutra |
| 4 | `curl-front` | 3 | 8-15 |  | 1 | Curl alla macchina Scott (preacher) |
| 5 | `curl-behind` | 2 | 10-15 |  | 1 | Curl su panca inclinata con manubri |
| 6 | `shrug` | 2 | 10-15 |  | 0,5 | Scrollate con manubri o alla macchina |
| 7 | `y-raise` | 2 | 10-15 |  | 0,5 | Y-raise da proni su panca inclinata |
| 8 | `wrist-extension` | 2 | 12-20 | sì | 1 | Curl del polso inverso, palmi in giù, avambraccio appoggiato |
| 9 | `straight-arm` | 2 | 10-15 | sì | 1 | Pullover al cavo o macchina pullover (braccia tese) |

#### Legs

| # | Famiglia | Serie | Ripetizioni | Facoltativo | Peso | Esercizio del documento |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `squat-guided` | 3 | 6-12 |  | 1 | Hack squat o pendulum squat, profondo |
| 2 | `knee-flexion` | 3 | 8-15 |  | 1 | Leg curl da seduti |
| 3 | `knee-extension` | 2 | 10-15 |  | 1 | Leg extension, schienale reclinato |
| 4 | `hip-thrust` | 2 | 8-12 |  | 1 | Hip thrust alla macchina o al multipower |
| 5 | `calf-straight` | 3 | 10-15 |  | 1 | Calf raise alla pressa o in piedi, gambe tese |
| 6 | `crunch` | 3 | 10-15 |  | 1 | Crunch al cavo in ginocchio (corda) |
| 7 | `reverse-crunch` | 2 | 10-15 |  | 1 | Reverse crunch su panca piana o declinata |
| 8 | `abduction` | 2 | 12-20 | sì | 1 | Abduzione dell'anca alla macchina |

#### Upper

| # | Famiglia | Serie | Ripetizioni | Facoltativo | Peso | Esercizio del documento |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `press-incline` | 3 | 6-12 |  | 1 | Chest press inclinata |
| 2 | `pull-vertical` | 3 | 6-12 |  | 1 | Lat machine, presa prona media o larga, al petto |
| 3 | `press-horizontal` | 3 | 6-12 |  | 1 | Chest press seduta |
| 4 | `pull-horizontal` | 3 | 6-12 |  | 1 | Rematore con appoggio al petto (macchina o T-bar) |
| 5 | `raise-lateral` | 3 | 10-20 |  | 1 | Alzate laterali ai cavi, un braccio |
| 6 | `rear-delt` | 2 | 10-20 |  | 1 | Reverse pec deck, presa neutra |
| 7 | `curl-front` | 2 | 8-15 |  | 1 | Curl alla macchina Scott (preacher) |
| 8 | `triceps-overhead` | 3 | 10-15 |  | 1 | Estensione sopra la testa ai cavi (barra o corda) |

#### Lower

| # | Famiglia | Serie | Ripetizioni | Facoltativo | Peso | Esercizio del documento |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `squat-guided` | 3 | 6-12 |  | 1 | Pressa a 45°, profonda |
| 2 | `knee-flexion` | 3 | 8-15 |  | 1 | Leg curl da seduti |
| 3 | `knee-extension` | 2 | 10-15 |  | 1 | Leg extension, schienale reclinato |
| 4 | `hip-thrust` | 2 | 8-12 |  | 1 | Hip thrust alla macchina o al multipower |
| 5 | `calf-straight` | 2 | 10-15 |  | 1 | Calf raise alla pressa o in piedi, gambe tese |
| 6 | `crunch` | 3 | 10-15 |  | 1 | Crunch al cavo in ginocchio (corda) |
| 7 | `reverse-crunch` | 2 | 10-15 |  | 1 | Reverse crunch su panca piana o declinata |
| 8 | `abduction` | 2 | 10-20 | sì | 1 | Abduzione dell'anca alla macchina |

Con le preferenze predefinite la generazione sceglie l'esercizio del documento in 34 slot su 40; nei 6 restanti sceglie un esercizio della stessa famiglia con mappa muscolare identica (algoritmo, § 4.3).

### 6.2 La colonna "variante" dell'Excel

L'Excel indica per 19 slot una variante. Si trattano in due modi:

- **Stessa famiglia (13 casi)**, es. lat machine a un braccio al posto della lat machine: non serve migrarle, compaiono già nel menu delle varianti dello slot, ordinate per punteggio.
- **Famiglia diversa (6 casi)**: sono varianti che spostano l'enfasi su un altro muscolo. Non si migrano come dati: restano nella nota dello slot, e l'utente le applica con le due estensioni sotto.

| Giorno · slot | Esercizio | Variante dell'Excel | Effetto cercato |
| --- | --- | --- | --- |
| Push 2 · spinta orizzontale | Chest press seduta | Dip alla macchina | Più petto basso |
| Push 3 · croce orizzontale | Croci ai cavi | Croci dal basso verso l'alto | Più petto alto |
| Upper 3 · spinta orizzontale | Chest press seduta | Croci ai cavi, **nella seconda seduta** | Più petto medio in allungamento |
| Upper 7 · curl con braccio davanti | Curl alla Scott | Curl su panca inclinata | Bicipite in allungamento |
| Legs 7, Lower 7 · reverse crunch | Reverse crunch | Pallof press | Obliqui e stabilità |

Nota sull'Upper 3: con il conteggio frazionario le croci al posto della chest press **non aumentano** il volume del petto, perché i livelli P e S sui tre fasci sono gli stessi; tolgono solo 1,5 serie ai capi laterale e mediale del tricipite. Servono a variare lo stimolo (petto in allungamento), non a portare il petto nella fascia. Per quello, nell'Upper/Lower basta una serie in più sulla chest press inclinata: petto alto da 9 a 11, petto medio da 9 a 10.

Per rendere applicabili tutte queste varianti, la fase 1 include due piccole estensioni, approvate:

1. **Cambiare la famiglia di uno slot** (nuovo criterio US-16 CA5): si sceglie un'altra famiglia, l'app assegna il miglior candidato. Copre i casi Push 2, Push 3, Legs 7, Lower 7.
2. **Variante della seconda seduta di qualunque famiglia** (modifica di US-17 CA1): il menu mostra prima la stessa famiglia, poi le altre. Copre Upper 3 e Upper 7. Il calcolo dei volumi e della durata non cambia, perché usa già l'esercizio effettivo di ogni seduta.

### 6.3 Push/Pull 4 giorni (`pp-4`)

Due giorni ripetuti due volte a settimana. Il Push porta i quadricipiti, il Pull femorali, glutei e polpacci: ogni giorno ha una sola zona delle gambe, a volume ridotto come negli altri split. Hip thrust due volte a settimana, come richiesto dal modulo sull'antiversione del bacino.

#### Push con quadricipiti

| # | Famiglia | Serie | Ripetizioni | Note | Scelta della generazione |
| --- | --- | --- | --- | --- | --- |
| 1 | Spinta inclinata | 3 | 6-12 |  | Chest press inclinata |
| 2 | Spinta orizzontale | 3 | 6-12 |  | Chest press seduta |
| 3 | Croce orizzontale | 2 | 10-20 |  | Pec deck (chest fly a macchina) |
| 4 | Alzata laterale | 4 | 10-20 |  | Alzate laterali ai cavi, un braccio |
| 5 | Estensione sopra la testa | 3 | 10-15 |  | Estensione sopra la testa alla macchina |
| 6 | Squat guidato e pressa | 2 | 6-12 |  | Pressa a 45°, profonda |
| 7 | Estensione del ginocchio | 2 | 10-15 |  | Leg extension, schienale reclinato |
| 8 | Crunch | 2 | 10-15 |  | Crunch alla macchina |

#### Pull con femorali e glutei

| # | Famiglia | Serie | Ripetizioni | Note | Scelta della generazione |
| --- | --- | --- | --- | --- | --- |
| 1 | Tirata verticale | 3 | 6-12 |  | Lat machine, presa prona media o larga, al petto |
| 2 | Tirata orizzontale | 3 | 6-12 |  | Rematore con appoggio al petto (macchina o T-bar) |
| 3 | Deltoide posteriore | 3 | 10-20 |  | Reverse pec deck, presa neutra |
| 4 | Curl con braccio davanti | 3 | 8-15 |  | Curl alla macchina Scott (preacher) |
| 5 | Curl con braccio dietro | 2 | 10-15 |  | Curl su panca inclinata con manubri |
| 6 | Flessione del ginocchio | 3 | 8-15 |  | Leg curl da seduti |
| 7 | Spinta dell'anca | 2 | 8-12 | Bacino in retroversione in cima al movimento | Hip thrust alla macchina o al multipower |
| 8 | Polpacci a gamba tesa | 2 | 10-15 | Alla pressa | Calf raise alla pressa o in piedi, gambe tese |

Durata stimata: 70 min il Push, 67 min il Pull. Tutti i muscoli con obiettivo sono nella fascia, tranne il capo lungo del tricipite (6), sotto fascia come in tutti gli split del documento.

### 6.4 Full body 3 giorni (`fb-3`)

**Tre giorni diversi, A, B e C, una volta ciascuno**, invece dello schema A, B, A alternato previsto dalla specifica. Il motivo è il modello dati: un giorno ha un numero intero di ripetizioni a settimana, e l'alternanza A/B/A – B/A/B darebbe 1,5 ripetizioni ciascuno. Rappresentarla come A × 2 e B × 1 renderebbe i volumi mostrati giusti solo una settimana su due. Con A, B, C ogni settimana è uguale e i volumi sono esatti.

#### Full body A

| # | Famiglia | Serie | Ripetizioni | Note | Scelta della generazione |
| --- | --- | --- | --- | --- | --- |
| 1 | Squat guidato e pressa | 3 | 6-12 |  | Pressa a 45°, profonda |
| 2 | Spinta inclinata | 3 | 6-12 |  | Chest press inclinata |
| 3 | Tirata verticale | 3 | 6-12 |  | Lat machine, presa prona media o larga, al petto |
| 4 | Croce orizzontale | 2 | 10-20 |  | Pec deck (chest fly a macchina) |
| 5 | Alzata laterale | 3 | 10-20 |  | Alzate laterali ai cavi, un braccio |
| 6 | Flessione del ginocchio | 3 | 8-15 |  | Leg curl da seduti |
| 7 | Curl con braccio davanti | 2 | 8-15 |  | Curl alla macchina Scott (preacher) |
| 8 | Estensione sopra la testa | 2 | 10-15 |  | Estensione sopra la testa alla macchina |
| 9 | Crunch | 2 | 10-15 | Facoltativo | Crunch alla macchina |

#### Full body B

| # | Famiglia | Serie | Ripetizioni | Note | Scelta della generazione |
| --- | --- | --- | --- | --- | --- |
| 1 | Spinta dell'anca | 2 | 8-12 | Bacino in retroversione in cima al movimento | Hip thrust alla macchina o al multipower |
| 2 | Spinta orizzontale | 3 | 6-12 |  | Chest press seduta |
| 3 | Tirata orizzontale | 3 | 6-12 |  | Rematore con appoggio al petto (macchina o T-bar) |
| 4 | Croce dal basso | 2 | 10-20 |  | Croci su panca inclinata |
| 5 | Alzata laterale | 3 | 10-20 |  | Alzate laterali ai cavi, un braccio |
| 6 | Deltoide posteriore | 3 | 10-20 |  | Reverse pec deck, presa neutra |
| 7 | Estensione del ginocchio | 2 | 10-15 |  | Leg extension, schienale reclinato |
| 8 | Curl con braccio dietro | 2 | 10-15 |  | Curl su panca inclinata con manubri |
| 9 | Estensione a braccio lungo il corpo | 2 | 10-15 |  | Pushdown al cavo con barra |

#### Full body C

| # | Famiglia | Serie | Ripetizioni | Note | Scelta della generazione |
| --- | --- | --- | --- | --- | --- |
| 1 | Spinta inclinata | 3 | 6-12 |  | Chest press inclinata |
| 2 | Tirata verticale | 2 | 6-12 |  | Lat machine, presa prona media o larga, al petto |
| 3 | Tirata orizzontale | 2 | 6-12 |  | Rematore con appoggio al petto (macchina o T-bar) |
| 4 | Croce orizzontale | 2 | 10-20 |  | Pec deck (chest fly a macchina) |
| 5 | Alzata laterale | 3 | 10-20 |  | Alzate laterali ai cavi, un braccio |
| 6 | Deltoide posteriore | 2 | 10-20 |  | Reverse pec deck, presa neutra |
| 7 | Flessione del ginocchio | 3 | 8-15 |  | Leg curl da seduti |
| 8 | Curl con braccio davanti | 2 | 8-15 |  | Curl alla macchina Scott (preacher) |
| 9 | Estensione sopra la testa | 2 | 10-15 |  | Estensione sopra la testa alla macchina |
| 10 | Reverse crunch | 2 | 10-15 |  | Reverse crunch su panca piana o declinata |

Durata stimata: 74, 75 e 73 min, al limite della durata massima predefinita: tre sedute a settimana devono coprire tutti i prioritari. Tutti i muscoli con obiettivo sono nella fascia, tranne il capo lungo del tricipite (5). Quadricipiti e femorali sono al minimo della fascia (6). Non ci sono polpacci, e gli addominali sono ridotti (reverse crunch nel C, crunch facoltativo nell'A): il mini-allenamento quotidiano copre il controllo del tronco.

### 6.5 Tetto per seduta

In nessuna seduta di nessuno split un muscolo supera il tetto di 10 serie frazionarie. Il massimo è 8 (capo laterale del tricipite nel Push, bicipite nel Pull e nel Pull di `pp-4`).

## 7. Stretching e mini-allenamento

### 7.1 Stretch

Gli stretch che l'Excel ripete in più giorni diventano una sola voce; dove la dose differiva si tiene la più lunga.

| `code` | Nome | Allunga | Dose |
| --- | --- | --- | --- |
| `pec-doorway` | Stretch del petto allo stipite, braccio a 90° e braccio alto | Fascio medio e basso del petto, piccolo pettorale | 30 s, ripetuto fino a circa 60 s |
| `cross-body` | Braccio incrociato davanti al petto | Deltoide posteriore | 30 s × 3 |
| `triceps-overhead` | Stretch del tricipite sopra la testa | Tricipite, capo lungo | 30 s, ripetuto fino a circa 60 s |
| `lat-kneeling` | Stretch del dorsale in ginocchio | Gran dorsale | 30 s, ripetuto fino a circa 60 s |
| `biceps-wall` | Stretch del bicipite a parete | Bicipite | 30 s, ripetuto fino a circa 60 s |
| `upper-trap` | Stretch del trapezio superiore | Trapezio superiore | 30 s per lato |
| `forearm-flexors` | Stretch dei flessori dell'avambraccio | Flessori del polso | 30 s |
| `hamstrings` | Stretch dei femorali | Femorali | 30 s |
| `hip-flexors-kneeling` | Stretch dei flessori dell'anca in ginocchio | Flessori dell'anca | 30 s per lato |
| `quads-standing` | Stretch del quadricipite in piedi | Quadricipite | 30 s per lato |
| `calf-wall` | Stretch del polpaccio al muro | Polpacci | 30 s per lato |

### 7.2 Stretch per giorno

| Giorno | Stretch |
| --- | --- |
| Push | `pec-doorway`, `cross-body`, `triceps-overhead` |
| Pull | `lat-kneeling`, `biceps-wall`, `upper-trap`, `forearm-flexors` |
| Legs, Lower | `hamstrings`, `hip-flexors-kneeling`, `quads-standing`, `calf-wall` |
| Upper | `pec-doorway`, `lat-kneeling`, `cross-body`, `upper-trap` |
| Push con quadricipiti (`pp-4`) | `pec-doorway`, `triceps-overhead`, `quads-standing`, `hip-flexors-kneeling` |
| Pull con femorali e glutei (`pp-4`) | `lat-kneeling`, `biceps-wall`, `upper-trap`, `hamstrings` |
| Full body A | `pec-doorway`, `lat-kneeling`, `hamstrings`, `hip-flexors-kneeling` |
| Full body B | `cross-body`, `upper-trap`, `quads-standing`, `calf-wall` |
| Full body C | `pec-doorway`, `triceps-overhead`, `biceps-wall`, `hip-flexors-kneeling` |

### 7.3 Mini-allenamento quotidiano

Le 8 voci dell'Excel, invariate: blocco `neck` (chin tuck, rotazione toracica, Y-raise a terra, stretch del trapezio superiore) e blocco `pelvis` (retroversione da sdraiati, ponte in retroversione, dead bug, stretch dei flessori dell'anca con gluteo contratto).

## 8. Test di riferimento

### 8.1 Volumi settimanali

Volumi della generazione con le preferenze predefinite, in serie frazionarie a settimana. In grassetto i valori fuori fascia. Le prime quattro colonne coincidono con il foglio "Volume_settimanale" dell'Excel; `pp-4` e `fb-3` sono calcolate dalla composizione di § 6.3 e § 6.4.

| Muscolo | `code` | Priorità · fascia | ppl-6 | ppl-3 | ul-4 | pplul-5 | pp-4 | fb-3 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Petto alto (fascio clavicolare) | `chest-upper` | prioritario · 10-18 | 12 | **6** | **9** | 10,5 | 11 | 11,5 |
| Petto medio (fascio sternocostale) | `chest-mid` | prioritario · 10-18 | 15 | **7,5** | **9** | 12 | 13 | 11 |
| Petto basso (fascio addominale) | `chest-lower` | — | 6 | 3 | 3 | 4,5 | 5 | 3,5 |
| Deltoide anteriore | `delt-front` | — | 9 | 4,5 | 6 | 7,5 | 8 | 7,5 |
| Deltoide laterale | `delt-lateral` | prioritario · 10-18 | 11 | **5,5** | **8** | **9,5** | 11 | 11,5 |
| Deltoide posteriore | `delt-rear` | prioritario · 10-18 | 13 | **6,5** | 10 | 11,5 | 12 | 10 |
| Cuffia dei rotatori | `rotator-cuff` | — | 0 | 0 | 0 | 0 | 0 | 0 |
| Tricipite, capo lungo | `triceps-long` | prioritario · 10-18 | **8** | **4** | **6** | **7** | **6** | **5** |
| Tricipite, capo laterale | `triceps-lateral` | prioritario · 10-18 | 16 | **8** | 12 | 14 | 12 | 10,5 |
| Tricipite, capo mediale | `triceps-medial` | prioritario · 10-18 | 16 | **8** | 12 | 14 | 12 | 10,5 |
| Gran dorsale e grande rotondo | `lats` | prioritario · 10-18 | 12 | **6** | 12 | 12 | 12 | 10 |
| Trapezio medio e romboidi | `traps-mid` | prioritario · 10-18 | 14 | **7** | 11 | 12,5 | 12 | 10 |
| Trapezio inferiore | `traps-lower` | — | 11 | 5,5 | 8 | 9,5 | 9 | 7,5 |
| Trapezio superiore | `traps-upper` | — | 6 | 3 | 3 | 4,5 | 4 | 4,5 |
| Erettori spinali | `erectors` | — | 0 | 0 | 0 | 0 | 0 | 0 |
| Bicipite brachiale | `biceps` | prioritario · 10-18 | 16 | **8** | 10 | 13 | 16 | 11 |
| Brachiale | `brachialis` | — | 14 | 7 | 10 | 12 | 14 | 10 |
| Brachioradiale | `brachioradialis` | — | 11 | 5,5 | 8 | 9,5 | 11 | 8 |
| Flessori del polso e delle dita | `forearm-flexors` | — | 12 | 6 | 8 | 10 | 11 | 8 |
| Estensori del polso e delle dita | `forearm-extensors` | — | 0 | 0 | 0 | 0 | 0 | 0 |
| Pronatori e supinatori | `pronators-supinators` | — | 0 | 0 | 0 | 0 | 0 | 0 |
| Quadricipiti (vasti) | `quads` | non prioritario · 6-10 | **12** | 6 | **12** | **12** | 10 | 6 |
| Retto femorale | `rectus-femoris` | — | 4 | 2 | 4 | 4 | 4 | 2 |
| Femorali | `hamstrings` | non prioritario · 6-10 | 6 | **3** | 6 | 6 | 6 | 6 |
| Grande gluteo | `glute-max` | — | 7 | 3,5 | 7 | 7 | 6 | 3,5 |
| Medio e piccolo gluteo | `glute-med` | — | 0 | 0 | 0 | 0 | 0 | 0 |
| Adduttori | `adductors` | — | 5 | 2,5 | 5 | 5 | 4 | 2,5 |
| Gastrocnemio | `gastrocnemius` | — | 9 | 4,5 | 7 | 8 | 7 | 3 |
| Soleo | `soleus` | — | 6 | 3 | 4 | 5 | 4 | 0 |
| Flessori dell'anca | `hip-flexors` | — | 2 | 1 | 2 | 2 | 0 | 1 |
| Retto dell'addome | `rectus-abdominis` | — | 10 | 5 | 10 | 10 | 4 | 2 |
| Obliqui | `obliques` | — | 5 | 2,5 | 5 | 5 | 2 | 1 |
| Stabilizzatori (trasverso, quadrato dei lombi) | `stabilizers` | — | 0 | 0 | 0 | 0 | 0 | 0 |

Cosa dice la tabella:

- **Capo lungo del tricipite sotto fascia ovunque.** È un limite già noto del documento di ricerca: il capo lungo lavora come primario solo nell'estensione sopra la testa. È il caso tipico in cui serve l'anteprima delle varianti (algoritmo, § 5: nel Push di `ppl-6`, passare dal pushdown al kickback dà +2).
- **PPL 3 giorni sotto fascia per tutti i muscoli prioritari.** Atteso: con un passaggio a settimana non si arriva a 10 serie senza sedute troppo lunghe.
- **Quadricipiti sopra fascia** (12 contro 10) in `ppl-6`, `ul-4` e `pplul-5`, come nell'Excel. L'app lo segnala; si corregge nella scheda, per esempio con una serie in meno di squat o di leg extension.

### 8.2 Durate

| Giorno | Durata stimata |
| --- | --- |
| Push | 60,5 min |
| Pull | 56 min |
| Legs | 59 min |
| Upper | 75,5 min |
| Lower | 57 min |
| Push con quadricipiti | 70 min |
| Pull con femorali e glutei | 67 min |
| Full body A, B, C | 74, 75, 73 min |

### 8.3 Forma dei file di test

`tests/data/golden_volumes.csv`, una riga per coppia split-muscolo: `split_code,muscle_code,expected`. Tolleranza zero, valori con al più un decimale (multipli di 0,5). `tests/data/golden_durations.csv` per le durate, con tolleranza di 0,1 minuti.

## 9. Seed

- I dati di questo documento sono file YAML in `backend/src/gym_split_planner/db/seed/data/`: `anatomy.yaml` (gruppi, muscoli, attrezzi), `sources.yaml`, `tags.yaml`, `families.yaml`, `exercises.yaml`, `routines.yaml` (stretching e mini-allenamento), `splits.yaml`, `settings.yaml`. Si usano i `code`, mai gli `id`; `excel_id` negli esercizi serve solo a ritrovare la riga dell'Excel e non si salva.
- La forma dei file è validata (campi sconosciuti compresi) prima di scrivere: un refuso o un riferimento inesistente fermano il caricamento con un messaggio che dice file e voce. Il caricamento è una sola transazione.
- Il container esegue `python -m gym_split_planner migrate` e poi `python -m gym_split_planner seed`.
- Il seed si esegue **solo su un database vuoto**, al primo avvio dopo le migrazioni. Non si riesegue agli avvii successivi: altrimenti rimetterebbe nel catalogo ciò che hai eliminato dall'interfaccia. Con `GSP_SKIP_SEED=1` non si esegue nemmeno la prima volta, per importare un'esportazione su un'istanza nuova (API, § 6.11). Correzioni ai dati iniziali in versioni successive dell'app passano da migrazioni di dati Alembic, scritte caso per caso.
- I test di validità (`tests/db/test_seed.py`) controllano sul seed: conteggi; ogni esercizio ha almeno un muscolo P; ranghi consecutivi in ogni famiglia; ogni famiglia ha un esercizio principale; ogni slot di ogni split ha almeno un candidato attivo non escluso; giorni a settimana degli split; fasce; etichette sul collo; file di riferimento completi. La coerenza del gruppo delle famiglie con l'Excel è stata verificata generando i file.
- I valori attesi di § 8 sono in `backend/tests/data/golden_volumes.csv` e `golden_durations.csv`; il confronto con la generazione arriva in M2.

## 10. Domande aperte

Risolte:

- Cambio di famiglia di uno slot e variante della seconda seduta di qualunque famiglia (§ 6.2; nella specifica US-16 CA5 e US-17 CA1).
- Etichetta `neck-tip` (§ 5.1).
- Composizione di `pp-4` approvata così com'è, con gli addominali solo nel Push (§ 6.3).
- `fb-3` come A, B, C (§ 6.4).
- Famiglie: "Petto basso" divisa in "Croce dall'alto" e "Dip e declinata", perché raccoglieva movimenti diversi; le tirate al mento restano nell'alzata laterale. Volumi di riferimento invariati.

Nessuna domanda aperta su questo documento.
