# ADR 0016 — Accesso per indirizzo e porta, tramite la rete di casa e il subnet router Tailscale

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-28 |

## Contesto

L'ADR 0011 prevedeva un container `tailscale/tailscale` accanto all'app, con `tailscale serve` per un indirizzo HTTPS proprio nella tailnet e la auth key in Ansible Vault.

Preparando il deploy (issue #5) si è letto il monorepo dell'homelab, che nel frattempo ha fissato convenzioni diverse:

- tutti i servizi si raggiungono per **indirizzo IP e porta** del loro container, dalla rete di casa e da fuori tramite il **subnet router Tailscale** già attivo sul nodo Proxmox (ADR-032 del monorepo); HTTPS arriverà per tutti con Traefik e un dominio;
- i segreti degli stack stanno nel `.env` dello stack, gitignored, non in Ansible Vault (ADR-026 del monorepo);
- dati applicativi in `/srv/appdata/<container>` sull'host, montati nel container come `/opt/appdata` (ADR-035 del monorepo).

In fase 1 l'app non ha bisogno di HTTPS: servirà in fase 3, per l'installazione come app sul telefono (PWA), quando Traefik dovrebbe già esserci.

## Decisione

- L'app si raggiunge a **`http://192.168.1.206:8000`**, dalla rete di casa o con Tailscale attivo, come gli altri servizi dell'homelab. Nessun container Tailscale dedicato e nessuna auth key.
- Il deploy segue le convenzioni del monorepo: container LXC CT 206, dati in `/srv/appdata/gym-split-planner`, versione dell'immagine fissata nel Compose, deploy con il ruolo `compose-deploy`. I dettagli stanno nell'ADR-041 del monorepo.
- Nessun segreto in fase 1, quindi nessun `.env`.
- Restano validi gli altri punti dell'ADR 0011: nessun login nell'app, nessuna esposizione su internet, conferma per le operazioni distruttive.

## Alternative considerate

- **Container Tailscale dedicato (ADR 0011):** HTTPS e un nome da subito, ma unico servizio dell'homelab fatto in modo diverso, con un secondo container e una chiave da generare e rinnovare.
- **Traefik subito:** richiede il dominio, non ancora acquistato; è un lavoro dell'homelab, non dell'app.

## Conseguenze

- Deploy identico a quello degli altri stack: nessuna conoscenza nuova da mantenere.
- Solo HTTP in fase 1; il traffico da fuori casa viaggia comunque cifrato dentro Tailscale.
- Con Traefik l'app avrà un nome e HTTPS senza modifiche al codice, purché continui a rispettare le intestazioni del proxy (Uvicorn è già avviato con `--proxy-headers`).
- Supera la parte dell'ADR 0011 sul container Tailscale e sulla auth key in Ansible Vault.
