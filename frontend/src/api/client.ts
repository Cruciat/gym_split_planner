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
export type ExerciseInput = Schemas['ExerciseIn']
export type ExerciseCreateInput = Schemas['ExerciseCreateIn']
export type ExerciseUsage = Schemas['ExerciseUsageOut']
export type SourceInput = Schemas['SourceIn']

export type Level = ExerciseSummary['muscles'][number]['level']
export type Kind = ExerciseSummary['kind']
export type Stretch = ExerciseSummary['stretch']
export type Confidence = ExerciseSummary['confidence']
export type Priority = Muscle['priority']
export type TagColor = Tag['color']

/** Regola violata in un `rule-violation` (API, § 3.1). */
export interface Violation {
  rule: string
  field: string | null
  message: string
}

/** Campo non valido in un `validation-error`, come in Pydantic. */
export interface FieldError {
  loc: (string | number)[]
  msg: string
  type: string
}

/** Errore dell'API in formato Problem Details (API, § 3). */
export interface Problem {
  status: number
  code: string
  title: string
  detail?: string
  violations?: Violation[]
  errors?: FieldError[]
  usage?: unknown
}

/** Riconosce un Problem Details nella risposta d'errore di `openapi-fetch`. */
export function asProblem(error: unknown, status: number): Problem {
  if (typeof error === 'object' && error !== null && 'code' in error && 'title' in error) {
    const body = error as Record<string, unknown>
    const { code, title, detail, violations, errors, usage } = body
    if (typeof code === 'string' && typeof title === 'string') {
      return {
        status,
        code,
        title,
        ...(typeof detail === 'string' ? { detail } : {}),
        ...(Array.isArray(violations) ? { violations: violations as Violation[] } : {}),
        ...(Array.isArray(errors) ? { errors: errors as FieldError[] } : {}),
        ...('usage' in body ? { usage } : {}),
      }
    }
  }
  return { status, code: 'unknown', title: texts.common.unexpectedError }
}
