import createClient from 'openapi-fetch'

import type { paths } from './schema'

/**
 * Client HTTP tipizzato sullo schema OpenAPI del backend.
 * I tipi in `schema.d.ts` sono generati (`npm run api:types`): un cambio del contratto
 * rompe la compilazione invece dell'app in esecuzione (ADR 0004).
 */
export const api = createClient<paths>({
  baseUrl: window.location.origin,
  // `fetch` letto a ogni chiamata, non alla creazione: così i test possono sostituirlo.
  fetch: (request) => globalThis.fetch(request),
})

export type HealthOut =
  paths['/api/health']['get']['responses']['200']['content']['application/json']
