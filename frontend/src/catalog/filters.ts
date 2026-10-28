/**
 * Filtri dell'elenco degli esercizi (US-01 CA2-CA4).
 *
 * I filtri si applicano nel client sul catalogo caricato in blocco (API, § 1.4) e
 * stanno nell'URL (CA3), con i `code` e non gli `id`: un link salvato resta valido
 * anche dopo un'esportazione e reimportazione.
 */

import type { LocationQuery, LocationQueryRaw } from 'vue-router'

import type { Catalog, Confidence, ExerciseSummary, Level } from '@/api/client'

export interface ExerciseFilters {
  /** Ricerca sul nome, senza distinguere maiuscole e accenti. */
  search: string
  group: string | null
  muscle: string | null
  /** Livello minimo per il muscolo: `P` solo primario, `S` primario o secondario. */
  level: Level
  family: string | null
  equipment: string | null
  tag: string | null
  /** Con `true`, esercizi **senza** l'etichetta scelta. */
  withoutTag: boolean
  confidence: Confidence | null
  showInactive: boolean
}

export const emptyFilters: Readonly<ExerciseFilters> = Object.freeze({
  search: '',
  group: null,
  muscle: null,
  level: 'P',
  family: null,
  equipment: null,
  tag: null,
  withoutTag: false,
  confidence: null,
  showInactive: false,
})

/** Nomi dei parametri nell'URL, in italiano come i percorsi (wireframe, § 2). */
const KEYS = {
  search: 'cerca',
  group: 'gruppo',
  muscle: 'muscolo',
  level: 'livello',
  family: 'famiglia',
  equipment: 'attrezzo',
  tag: 'etichetta',
  withoutTag: 'senza',
  confidence: 'confidenza',
  showInactive: 'disattivati',
} as const satisfies Record<keyof ExerciseFilters, string>

const CONFIDENCES: readonly Confidence[] = ['solid', 'limited', 'opinion']

function single(query: LocationQuery, key: string): string | null {
  const value = query[key]
  const first = Array.isArray(value) ? value[0] : value
  return typeof first === 'string' && first !== '' ? first : null
}

/** Legge i filtri dall'URL; valori sconosciuti o malformati tornano al valore vuoto. */
export function filtersFromQuery(query: LocationQuery): ExerciseFilters {
  const confidence = single(query, KEYS.confidence)
  return {
    search: single(query, KEYS.search) ?? '',
    group: single(query, KEYS.group),
    muscle: single(query, KEYS.muscle),
    level: single(query, KEYS.level) === 'S' ? 'S' : 'P',
    family: single(query, KEYS.family),
    equipment: single(query, KEYS.equipment),
    tag: single(query, KEYS.tag),
    withoutTag: single(query, KEYS.withoutTag) === '1',
    confidence: CONFIDENCES.find((c) => c === confidence) ?? null,
    showInactive: single(query, KEYS.showInactive) === '1',
  }
}

/** Scrive solo i filtri attivi: l'URL senza filtri resta `/catalogo`. */
export function filtersToQuery(filters: ExerciseFilters): LocationQueryRaw {
  const query: LocationQueryRaw = {}
  const search = filters.search.trim()
  if (search !== '') query[KEYS.search] = search
  if (filters.group !== null) query[KEYS.group] = filters.group
  if (filters.muscle !== null) {
    query[KEYS.muscle] = filters.muscle
    if (filters.level === 'S') query[KEYS.level] = 'S'
  }
  if (filters.family !== null) query[KEYS.family] = filters.family
  if (filters.equipment !== null) query[KEYS.equipment] = filters.equipment
  if (filters.tag !== null) {
    query[KEYS.tag] = filters.tag
    if (filters.withoutTag) query[KEYS.withoutTag] = '1'
  }
  if (filters.confidence !== null) query[KEYS.confidence] = filters.confidence
  if (filters.showInactive) query[KEYS.showInactive] = '1'
  return query
}

/** Quanti filtri sono attivi (per il pulsante "Filtri (n)" sul telefono). */
export function countActiveFilters(filters: ExerciseFilters): number {
  return [
    filters.search.trim() !== '',
    filters.group !== null,
    filters.muscle !== null,
    filters.family !== null,
    filters.equipment !== null,
    filters.tag !== null,
    filters.confidence !== null,
    filters.showInactive,
  ].filter(Boolean).length
}

/** Minuscole e senza accenti: "Croci" trova "cróci", "panca" trova "Panca". */
export function normalize(text: string): string {
  return text.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()
}

/**
 * Esercizi che soddisfano tutti i filtri insieme, nell'ordine del catalogo.
 *
 * - gruppo: quello della famiglia principale (modello dati, § 3.4);
 * - famiglia: principale o secondaria;
 * - muscolo: con il livello minimo richiesto;
 * - un codice che non esiste nel catalogo (link vecchio) non trova nulla.
 */
export function filterExercises(catalog: Catalog, filters: ExerciseFilters): ExerciseSummary[] {
  const idOf = (items: { id: number; code: string }[], code: string | null) =>
    code === null ? null : (items.find((item) => item.code === code)?.id ?? -1)

  const familyGroup = new Map(catalog.families.map((f) => [f.id, f.muscle_group_id]))
  const groupId = idOf(catalog.muscle_groups, filters.group)
  const muscleId = idOf(catalog.muscles, filters.muscle)
  const familyId = idOf(catalog.families, filters.family)
  const equipmentId = idOf(catalog.equipment, filters.equipment)
  const tagId = idOf(catalog.tags, filters.tag)
  const search = normalize(filters.search.trim())

  return catalog.exercises.filter((exercise) => {
    if (!filters.showInactive && !exercise.is_active) return false
    if (search !== '' && !normalize(exercise.name).includes(search)) return false
    if (groupId !== null && familyGroup.get(exercise.primary_family_id) !== groupId) return false
    if (
      familyId !== null &&
      exercise.primary_family_id !== familyId &&
      exercise.secondary_family_id !== familyId
    )
      return false
    if (equipmentId !== null && exercise.equipment_id !== equipmentId) return false
    if (filters.confidence !== null && exercise.confidence !== filters.confidence) return false
    if (muscleId !== null) {
      const link = exercise.muscles.find((m) => m.muscle_id === muscleId)
      if (link === undefined) return false
      if (filters.level === 'P' && link.level !== 'P') return false
    }
    if (tagId !== null) {
      const hasTag = exercise.tags.some((t) => t.tag_id === tagId)
      if (hasTag === filters.withoutTag) return false
    }
    return true
  })
}
