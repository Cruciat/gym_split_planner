# ADR 0010 — Immagini su GHCR e versione fissata nel monorepo dell'homelab

| Campo | Valore |
| --- | --- |
| Stato | Accettato (2026-10-28) |
| Data | 2026-10-27 |

## Contesto

Il codice dell'app sta in un repository separato; l'infrastruttura dell'homelab sta in un monorepo gestito con Terraform, Ansible e Docker Compose secondo un approccio GitOps. Serve un modo ripetibile per portare una nuova versione dall'app all'homelab.

## Decisione

1. **Versioni:** SemVer. Un tag `vX.Y.Z` sul repository dell'app avvia il workflow di rilascio.
2. **Pubblicazione:** GitHub Actions compila l'immagine e la pubblica su **GitHub Container Registry** come `ghcr.io/cruciat/gym_split_planner:X.Y.Z` (più `X.Y` e `latest`). Le pull request compilano l'immagine senza pubblicarla.
3. **Deploy:** nel monorepo dell'homelab, il compose dell'app indica la versione esatta (`:X.Y.Z`). Per aggiornare si cambia il numero con un commit e si applica il ruolo Ansible `compose-deploy`.
4. **Infrastruttura:** un container LXC creato con il modulo Terraform `lxc-container`, con Docker installato dal ruolo `docker`.
5. **Credenziali:** se il pacchetto GHCR è privato, l'homelab usa un token con il solo permesso `read:packages`, conservato in Ansible Vault.
6. **In futuro:** Renovate nel monorepo può aprire automaticamente una pull request quando esce una nuova versione.

## Alternative considerate

- **Watchtower** (aggiornamento automatico all'uscita di una nuova immagine): nessuno sforzo, ma lo stato dell'homelab non è più descritto dal monorepo e un rilascio difettoso arriva in produzione senza decisione.
- **Build direttamente sull'homelab dal codice sorgente:** nessun registry, ma build lente sul nodo e nessuna immagine riutilizzabile.

## Conseguenze

- Ogni versione in produzione corrisponde a un commit nel monorepo; tornare indietro è un commit.
- Aggiornare richiede un passaggio manuale breve, finché non si introduce Renovate.
