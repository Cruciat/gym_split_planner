# ADR 0004 — Frontend single-page in Vue 3 e TypeScript

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28); la scelta di PrimeVue è superata da ADR 0015 |
| Data | 2026-10-27 |

## Contesto

L'interfaccia ha parti molto interattive: editor della scheda con trascinamento, menu delle varianti con anteprima, pannello volume che si aggiorna a ogni modifica (US-13, US-14, US-16), tabelle filtrabili (US-01). Deve funzionare bene su telefono (NF2). Lo sviluppatore conosce Vue dal tirocinio.

## Decisione

- **Vue 3** con Composition API e `<script setup>`, **TypeScript** in modalità stretta, build con **Vite**.
- **Vue Router** per le pagine; i filtri del catalogo stanno nei parametri dell'URL (US-01 CA3).
- **Pinia** per lo stato condiviso (scheda aperta, stato del salvataggio).
- ~~**PrimeVue**~~ (superato da ADR 0015: Naive UI) come libreria di componenti (DataTable con filtri, OrderList o drag and drop, Dialog, Menu, Tabs), con tema configurato per modalità chiara e scura.
- Client HTTP con tipi **generati dallo schema OpenAPI** del backend (`openapi-typescript`), così un cambio del contratto rompe la compilazione invece di rompere l'app in esecuzione.
- Test con **Vitest** e **Vue Test Utils**; end-to-end con **Playwright** sui flussi critici.

## Alternative considerate

- **Pagine renderizzate dal server con HTMX:** meno codice e un solo linguaggio, ma l'editor della scheda con trascinamento e aggiornamenti continui diventa scomodo.
- **React:** equivalente per capacità, ma stack non già noto.
- **Naive UI o Vuetify:** valide; PrimeVue ha la DataTable più completa per il catalogo e componenti per il riordino già pronti.
- **Tipi scritti a mano lato client:** rischio di disallineamento silenzioso con il backend.

## Conseguenze

- Build del frontend come passo separato, i cui file statici sono serviti dal backend (ADR 0009).
- Dipendenza da una libreria di componenti con il suo ritmo di aggiornamenti.
- Il contratto delle API diventa un artefatto controllato: generazione dei tipi nella CI.
