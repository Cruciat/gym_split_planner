# Documentazione di progetto

**Gym Split Planner** (`gym_split_planner`): servizio web personale per consultare la banca dati degli esercizi e creare schede di allenamento.

| Cosa | Nome |
| --- | --- |
| Repository | `Cruciat/gym_split_planner` |
| Pacchetto Python | `gym_split_planner` |
| Immagine | `ghcr.io/cruciat/gym_split_planner` |
| Nome macchina nella tailnet | `gym-split-planner` (i nomi DNS non ammettono `_`) |
| Database | `/data/gym_split_planner.db` |
| Prefisso delle variabili d'ambiente | `GSP_` |

## Indice

| Documento | Stato | Contenuto |
| --- | --- | --- |
| [processo.md](processo.md) | Bozza | Come si sviluppa: fasi, tappe, ciclo di lavoro, definizione di fatto |
| [spec/fase-1.md](spec/fase-1.md) | Bozza v0.2 | Specifica funzionale della fase 1: obiettivi, esclusioni, glossario, storie utente, requisiti |
| [adr/](adr/) | Accettati | Decisioni architetturali 0001-0014 |
| [design/modello-dati.md](design/modello-dati.md) | Bozza v0.2 | Tabelle, relazioni, vincoli, regole di cancellazione, punti di estensione |
| [design/algoritmo.md](design/algoritmo.md) | Bozza v0.2 | Volume frazionario, punteggio, generazione, anteprima delle varianti, stima della durata, casi di test |
| [design/dati-iniziali.md](design/dati-iniziali.md) | Bozza v0.2 | Famiglie di movimento, assegnazione degli esercizi, etichette iniziali, composizione degli split, test di riferimento |
| [design/api.md](design/api.md) | Bozza v0.1 | Contratto delle API: convenzioni, errori, concorrenza, endpoint, forme delle risposte |
| [design/wireframe.md](design/wireframe.md) | Bozza v0.1 | Bozze delle schermate: navigazione, editor della scheda, varianti, catalogo, impostazioni, PDF |

## Decisioni architetturali

| ADR | Titolo |
| --- | --- |
| [0001](adr/0001-registrare-le-decisioni.md) | Registrare le decisioni con ADR |
| [0002](adr/0002-backend-fastapi.md) | Backend in Python con FastAPI, SQLAlchemy 2 e Alembic |
| [0003](adr/0003-database-sqlite.md) | Database SQLite su volume persistente |
| [0004](adr/0004-frontend-vue.md) | Frontend single-page in Vue 3 e TypeScript |
| [0005](adr/0005-dominio-isolato.md) | Logica di dominio in un modulo puro |
| [0006](adr/0006-slot-e-famiglie-di-movimento.md) | Schede costruite da slot che chiedono famiglie di movimento |
| [0007](adr/0007-calcoli-lato-server.md) | Volumi e punteggi calcolati solo dal backend |
| [0008](adr/0008-pdf-weasyprint.md) | PDF generati dal server con WeasyPrint |
| [0009](adr/0009-container-unico.md) | Un solo container che serve API e frontend |
| [0010](adr/0010-distribuzione.md) | Immagini su GHCR e versione fissata nel monorepo dell'homelab |
| [0011](adr/0011-accesso-tailscale-senza-login.md) | Accesso tramite Tailscale, senza autenticazione nell'app |
| [0012](adr/0012-convenzioni-di-sviluppo.md) | Convenzioni di sviluppo, qualità e integrazione continua |
| [0013](adr/0013-lingua-e-nomenclatura.md) | Italiano per interfaccia e documenti, inglese per il codice |
| [0014](adr/0014-etichette-e-personalizzazioni.md) | Etichette sugli esercizi e personalizzazioni per scheda |
