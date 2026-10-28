# Gym Split Planner

Servizio web personale per consultare la banca dati degli esercizi e creare schede di allenamento, con il controllo continuo del volume settimanale per muscolo e l'esportazione in PDF.

Stato: progettazione della fase 1 completata; sviluppo in corso dalla tappa M0.

La documentazione di progetto è in [`docs/`](docs/README.md): processo di sviluppo, specifica, decisioni architetturali (ADR), modello dati, algoritmo, dati iniziali, contratto delle API e bozze delle schermate.

## Sviluppo

Servono [uv](https://docs.astral.sh/uv/) e Node 22.

```bash
make setup          # dipendenze e hook di pre-commit
make dev-backend    # API su http://127.0.0.1:8000 (documentazione su /api/docs)
make dev-frontend   # interfaccia su http://127.0.0.1:5173
make check          # tutti i controlli della CI
```

Convenzioni e struttura del codice: [`CLAUDE.md`](CLAUDE.md).
