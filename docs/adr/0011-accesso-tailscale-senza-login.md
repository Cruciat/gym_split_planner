# ADR 0011 — Accesso tramite Tailscale, senza autenticazione nell'app

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

L'app ha un solo utente, che vi accede dai propri dispositivi già collegati alla tailnet. Non deve essere esposta su internet (US-40).

## Decisione

- Un container **sidecar `tailscale/tailscale`** nello stesso compose dell'app, con nome macchina `gym-split-planner`, autenticato con una auth key conservata in Ansible Vault e stato persistente in un volume.
- **`tailscale serve`** espone l'app in HTTPS all'indirizzo `https://gym-split-planner.<tailnet>.ts.net`, con certificato gestito da Tailscale.
- Nessuna porta dell'app pubblicata sull'host; nessuna esposizione su internet (niente Funnel).
- Nessun login nell'app. Chiunque sia nella tailnet ha accesso completo; le ACL di Tailscale possono restringere l'accesso ai soli dispositivi personali.

## Alternative considerate

- **Dietro Traefik con certificati propri:** coerente con lo stack previsto dell'homelab, ma il proxy non è ancora pronto; si potrà passare a Traefik con un nuovo ADR senza modificare l'app.
- **Tailscale installato nel container LXC invece che come sidecar:** richiede il dispositivo TUN nell'LXC; il sidecar resta tutto descritto nel compose.
- **Login nell'app:** inutile per un utente su rete privata; complessità e attrito su telefono.

## Conseguenze

- Zero codice di autenticazione in fase 1.
- Se in futuro servissero più utenti o accesso esterno, servirà un nuovo ADR (autenticazione o intestazioni d'identità di Tailscale).
- Tutte le operazioni distruttive dell'app chiedono comunque conferma (US-05, US-19).
