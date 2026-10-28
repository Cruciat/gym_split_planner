# ADR 0001 — Registrare le decisioni architetturali con ADR

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

Il progetto sarà sviluppato a fasi nell'arco di mesi, con interruzioni. Senza una traccia scritta, le ragioni delle scelte (stack, modello dati, deploy) si perdono, e ogni ripresa rischia di rimettere in discussione decisioni già prese.

## Decisione

Ogni decisione che riguarda architettura, tecnologie, modello dati o processo si registra in un ADR in `docs/adr/`, numerato in ordine (`NNNN-titolo-in-kebab-case.md`), con il modello `0000-template.md`.

- Un ADR nasce con stato **Proposto** e diventa **Accettato** dopo la revisione del proprietario del progetto.
- Un ADR accettato non si modifica nel merito: se la decisione cambia, si scrive un nuovo ADR che lo **supera**, e il vecchio riporta il riferimento.
- Nessuno sviluppo che dipende da una decisione parte prima che l'ADR relativo sia accettato.

## Alternative considerate

- **Nessuna documentazione delle decisioni:** più veloce all'inizio, costosa alla prima ripresa dopo una pausa.
- **Un unico documento di architettura:** si aggiorna sovrascrivendo e perde lo storico delle ragioni.

## Conseguenze

- Ogni decisione ha una data, un contesto e le alternative scartate.
- Piccolo costo di scrittura per ogni scelta rilevante.
- Coerente con il metodo già usato nel monorepo dell'homelab.
