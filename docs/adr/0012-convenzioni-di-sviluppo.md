# ADR 0012 — Convenzioni di sviluppo, qualità e integrazione continua

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

Il processo deve essere disciplinato: niente codice che entra senza test, controlli automatici uguali per ogni modifica, storico leggibile (requisito NF6 e documento di processo).

## Decisione

**Repository e flusso**
- Branch `main` sempre rilasciabile e protetto: si modifica solo tramite pull request con CI verde.
- Un branch per issue: `feat/…`, `fix/…`, `docs/…`, `chore/…`.
- **Conventional Commits** per i messaggi e i titoli delle pull request; merge con squash.
- **SemVer** con `CHANGELOG.md` aggiornato a ogni rilascio.
- Ogni attività parte da una issue con criteri di accettazione, collegata a una tappa (milestone) di GitHub.

**Qualità del backend**
- `ruff` per formattazione e lint, `mypy` in modalità stretta, `import-linter` per i confini degli strati (ADR 0005).
- `pytest` con copertura; soglia del 90% sul modulo `domain` (NF6).

**Qualità del frontend**
- `eslint`, `prettier`, `vue-tsc` per i tipi, `vitest`.
- Playwright per i test end-to-end dei flussi critici, a partire da M4.

**Automazione**
- `pre-commit` esegue formattazione e lint in locale.
- CI su GitHub Actions per ogni pull request: lint, controllo tipi, test di backend e frontend, verifica che i tipi del client siano allineati allo schema OpenAPI, build dell'immagine.
- Workflow di rilascio sui tag (ADR 0010).

**Definizione di fatto** (vale per ogni issue)
1. Criteri di accettazione soddisfatti e verificati.
2. Test nuovi o aggiornati, tutti verdi.
3. Documentazione aggiornata (specifica, ADR, contratto delle API se cambiano).
4. Migrazione presente se lo schema cambia.
5. Versione distribuita sull'homelab, se la issue chiude una tappa.

## Alternative considerate

- **Commit diretti su `main`:** più veloce, ma senza la CI come guardia.
- **Black, isort e flake8 separati:** `ruff` li sostituisce tutti con un solo strumento.

## Conseguenze

- Ogni modifica passa dagli stessi controlli.
- Overhead di processo modesto ma costante, accettato in cambio di affidabilità.
