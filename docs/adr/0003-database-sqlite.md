# ADR 0003 — Database SQLite su volume persistente

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

Un solo utente, poche centinaia di righe di catalogo, poche schede, scritture rare e mai concorrenti. In fase 3 si aggiungeranno le serie registrate: anche in anni di allenamenti restano nell'ordine delle decine di migliaia di righe. Requisiti: persistenza tra aggiornamenti (US-41), backup giornaliero (NF5), manutenzione minima.

## Decisione

- **SQLite** in un file su un volume Docker dedicato (`/data/gym_split_planner.db`).
- Modalità **WAL** e `foreign_keys = ON` impostate a ogni connessione.
- Backup giornaliero con `sqlite3 .backup` (copia coerente anche ad applicazione attiva) in una cartella inclusa nei backup dell'homelab; conservazione degli ultimi 14.
- Nota (2026-10-28, issue #15): il backup lo fa l'app stessa, senza cron: all'avvio e poi ogni ora controlla se c'è il backup del giorno e, se manca, lo crea con l'API di backup di SQLite (equivalente a `.backup`) in `/data/backups/gym_split_planner-AAAA-MM-GG.db`, poi elimina i più vecchi oltre i 14. Un riavvio non fa perdere il backup del giorno. `/data` sta nei dati applicativi dell'homelab, quindi i backup seguono il backup dell'host. Configurabile con `GSP_BACKUP_*`.
- Il codice usa solo funzioni SQL portabili tramite SQLAlchemy, così un passaggio a PostgreSQL resta una modifica di configurazione e migrazioni.

## Alternative considerate

- **PostgreSQL:** robusto e già standard, ma richiede un secondo container, credenziali, aggiornamenti di versione e backup dedicati, senza benefici per questo carico.
- **File JSON o YAML:** semplici da leggere, ma senza vincoli d'integrità, transazioni né query.

## Conseguenze

- Un file da salvare; zero servizi aggiuntivi.
- Nessuna scalabilità a più utenti in scrittura concorrente: non è un requisito (ADR 0011).
- Alcune migrazioni su SQLite richiedono la modalità batch di Alembic (ricreazione della tabella): da tenere presente.
