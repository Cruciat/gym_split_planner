# ADR 0015 — Naive UI al posto di PrimeVue come libreria di componenti

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-28 |

## Contesto

L'ADR 0004 ha scelto PrimeVue come libreria di componenti. Installando le dipendenze in M0 (issue #2) è emerso che da luglio 2026, con la versione 5, PrimeVue e le librerie collegate (`@primeuix/themes` 3, `primeicons` 8) non hanno più licenza MIT ma la "PrimeUI License":

- serve una chiave di licenza; senza, l'app mostra un avviso;
- per uso personale la licenza Community è gratuita, ma va rinnovata ogni anno;
- le ultime versioni MIT (PrimeVue 4.5.5, aprile 2026) non ricevono più aggiornamenti.

Il progetto è personale e pensato per durare anni: entrambe le strade con PrimeVue lasciano un debito, una dipendenza ferma oppure una chiave da rinnovare. Al momento della decisione il frontend è una sola pagina, quindi cambiare libreria non costa quasi nulla.

## Decisione

- **Naive UI** (MIT) come libreria di componenti, con tema chiaro e scuro secondo il sistema (`NConfigProvider`, `useOsTheme`) e testi in italiano (`itIT`, `dateItIT`).
- **Lucide** (`lucide-vue-next`, ISC) per le icone, comprese quelle delle etichette (wireframe, § 4.4). Le stesse icone in SVG servono al PDF (ADR 0008).
- Per il riordino trascinando (US-16, US-21), dove Naive UI non ha un componente, una libreria basata su SortableJS con licenza MIT, scelta in M4.
- Il resto dell'ADR 0004 resta valido (Vue 3, TypeScript, Vite, Pinia, Vue Router, tipi generati, Vitest, Playwright).

## Alternative considerate

- **PrimeVue 4.5.5, fermo:** funziona e non costa nulla oggi, ma non riceverà più correzioni e potrebbe rompersi con le prossime versioni di Vue.
- **PrimeVue 5 con licenza Community:** aggiornato, ma con una chiave da rinnovare ogni anno e condizioni di licenza da rispettare per un progetto pubblico.
- **Vuetify (MIT):** completo, ma legato a Material Design e più pesante; Naive UI è scritto in TypeScript e ha una tabella con filtri e ordinamento adatta al catalogo (US-01).

## Conseguenze

- Tutte le dipendenze del frontend hanno licenze permissive (MIT, ISC).
- Componenti importati uno per uno dove servono: il bundle contiene solo ciò che si usa.
- Il riordino trascinando richiede una dipendenza in più in M4.
- Supera la parte dell'ADR 0004 che sceglieva PrimeVue.
