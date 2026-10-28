import createClient from 'openapi-fetch'

import { texts } from '@/texts'

import type { components, paths } from './schema'

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

type Schemas = components['schemas']

export type HealthOut =
  paths['/api/health']['get']['responses']['200']['content']['application/json']

export type Catalog = Schemas['CatalogOut']
export type MuscleGroup = Schemas['MuscleGroupOut']
export type Muscle = Schemas['MuscleOut']
export type Equipment = Schemas['EquipmentOut']
export type Family = Schemas['FamilyOut']
export type Tag = Schemas['TagOut']
export type Source = Schemas['SourceOut']
export type ExerciseSummary = Schemas['ExerciseSummaryOut']
export type ExerciseDetail = Schemas['ExerciseDetailOut']
export type Variant = Schemas['VariantOut']
export type TagLink = Schemas['TagLinkOut']

export type Level = ExerciseSummary['muscles'][number]['level']
export type Kind = ExerciseSummary['kind']
export type Stretch = ExerciseSummary['stretch']
export type Confidence = ExerciseSummary['confidence']
export type Priority = Muscle['priority']
export type TagColor = Tag['color']

/** Errore dell'API in formato Problem Details (API, § 3). */
export interface Problem {
  status: number
  code: string
  title: string
  detail?: string
}

/** Riconosce un Problem Details nella risposta d'errore di `openapi-fetch`. */
export function asProblem(error: unknown, status: number): Problem {
  if (typeof error === 'object' && error !== null && 'code' in error && 'title' in error) {
    const { code, title, detail } = error as { code: unknown; title: unknown; detail?: unknown }
    if (typeof code === 'string' && typeof title === 'string') {
      return { status, code, title, ...(typeof detail === 'string' ? { detail } : {}) }
    }
  }
  return { status, code: 'unknown', title: texts.common.unexpectedError }
}
