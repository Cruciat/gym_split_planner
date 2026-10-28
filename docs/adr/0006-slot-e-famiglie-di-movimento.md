# ADR 0006 — Schede costruite da slot che chiedono famiglie di movimento

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

Nell'Excel un giorno è un elenco di esercizi fissi; le alternative sono testo libero. Questo rende impossibili le varianti con anteprima (US-14), la generazione automatica (US-12), la rigenerazione con lucchetto (US-18) e il ribilanciamento della fase 2. Serve un concetto che dica "in questo posto va qualcosa che svolga questa funzione".

## Decisione

1. Si introduce la **famiglia di movimento**: un insieme di esercizi intercambiabili ai fini della scheda. Il criterio è "si può mettere uno al posto dell'altro senza perdere nulla di importante", non "allenano lo stesso muscolo". Esempio: curl su panca Scott e curl su panca inclinata appartengono a famiglie diverse, perché la ricerca indica che vanno fatti entrambi.
2. Ogni esercizio ha **una famiglia principale** e **al massimo una secondaria**. È tra le varianti di entrambe; la principale determina dove compare nel catalogo.
3. Gli **split** sono modelli: giorni → **slot**. Ogni slot chiede una famiglia, con serie e ripetizioni predefinite e un'indicazione obbligatorio o facoltativo.
4. Una **scheda** è un'istanza: copia la struttura dello split e assegna a ogni slot un esercizio concreto, con serie e ripetizioni proprie, stato del lucchetto e variante per la seconda seduta. Dopo la creazione, la scheda non dipende più dallo split: modificare un preset non cambia le schede già create.
5. Si possono aggiungere a una scheda esercizi fuori dagli slot del preset: diventano slot della scheda con la famiglia dell'esercizio scelto.
6. Le tabelle per la registrazione degli allenamenti (fase 3) saranno collegate agli esercizi della scheda; non si creano ora, ma nulla nel modello le impedisce.

## Alternative considerate

- **Alternative come relazione esercizio-esercizio** (come nell'Excel): non transitive e incoerenti (A ha B come alternativa, B ha C), difficili da mantenere con 80 e più esercizi.
- **Raggruppare per muscolo primario:** metterebbe insieme esercizi che la ricerca vuole complementari (piana e inclinata, Scott e inclinata).
- **Molte famiglie per esercizio:** più flessibile, ma il catalogo diventa ambiguo; due famiglie coprono i casi limite noti (skull crusher, panca declinata, back extension).

## Conseguenze

- La tabella delle famiglie va preparata nel seed e rivista prima di M1.
- Varianti, generazione, rigenerazione e ribilanciamento si basano tutti sullo stesso concetto.
- Le schede salvate restano stabili anche se si modificano i preset.
