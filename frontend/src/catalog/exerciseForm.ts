/**
 * Stato e regole della form dell'esercizio (US-03, US-04; wireframe § 4.3).
 *
 * Funzioni pure: la pagina le usa per costruire il corpo di `POST`/`PUT` e per
 * mostrare gli errori accanto ai campi. Il server resta l'arbitro (API, § 3.1): le
 * stesse regole controllate qui servono solo a rispondere subito, senza attendere.
 */

import type {
  Catalog,
  Confidence,
  ExerciseDetail,
  ExerciseInput,
  Kind,
  Level,
  Problem,
  Stretch,
} from '@/api/client'
import { texts } from '@/texts'

export interface MuscleEntry {
  muscle_id: number
  level: Level
  note: string | null
}

export interface TagEntry {
  tag_id: number
  note: string
}

export interface ExerciseForm {
  name: string
  primary_family_id: number | null
  secondary_family_id: number | null
  family_rank: number
  equipment_id: number | null
  equipment_detail: string
  kind: Kind
  stretch: Stretch
  stretch_note: string
  confidence: Confidence
  notes: string
  is_active: boolean
  muscles: MuscleEntry[]
  tags: TagEntry[]
  source_ids: number[]
}

/** Campi della form che possono avere un errore proprio. */
export type FormField =
  | 'name'
  | 'code'
  | 'primary_family_id'
  | 'secondary_family_id'
  | 'family_rank'
  | 'equipment_id'
  | 'equipment_detail'
  | 'stretch_note'
  | 'notes'
  | 'muscles'
  | 'tags'
  | 'source_ids'

export type FormErrors = Partial<Record<FormField, string>>

const FIELDS: readonly FormField[] = [
  'name',
  'code',
  'primary_family_id',
  'secondary_family_id',
  'family_rank',
  'equipment_id',
  'equipment_detail',
  'stretch_note',
  'notes',
  'muscles',
  'tags',
  'source_ids',
]

/**
 * Esercizio nuovo. La confidenza parte da "opinione": un esercizio aggiunto a mano
 * non viene dalla ricerca finché non si indicano fonti.
 */
export function emptyForm(): ExerciseForm {
  return {
    name: '',
    primary_family_id: null,
    secondary_family_id: null,
    family_rank: 1,
    equipment_id: null,
    equipment_detail: '',
    kind: 'compound',
    stretch: 'medium',
    stretch_note: '',
    confidence: 'opinion',
    notes: '',
    is_active: true,
    muscles: [],
    tags: [],
    source_ids: [],
  }
}

export function formFromDetail(detail: ExerciseDetail): ExerciseForm {
  return {
    name: detail.name,
    primary_family_id: detail.primary_family_id,
    secondary_family_id: detail.secondary_family_id,
    family_rank: detail.family_rank,
    equipment_id: detail.equipment_id,
    equipment_detail: detail.equipment_detail ?? '',
    kind: detail.kind,
    stretch: detail.stretch,
    stretch_note: detail.stretch_note ?? '',
    confidence: detail.confidence,
    notes: detail.notes ?? '',
    is_active: detail.is_active,
    muscles: detail.muscles.map((m) => ({ muscle_id: m.muscle_id, level: m.level, note: m.note })),
    tags: detail.tags.map((t) => ({ tag_id: t.tag_id, note: t.note ?? '' })),
    source_ids: detail.sources.map((s) => s.id),
  }
}

const orNull = (text: string): string | null => (text.trim() === '' ? null : text.trim())

/**
 * Corpo della richiesta. Da chiamare solo su una form senza errori (`validateForm`):
 * famiglia e attrezzo mancanti sono un errore di programmazione.
 */
export function toExerciseInput(form: ExerciseForm): ExerciseInput {
  if (form.primary_family_id === null || form.equipment_id === null) {
    throw new Error('Form incompleta: controllare con validateForm prima di inviare')
  }
  return {
    name: form.name.trim(),
    primary_family_id: form.primary_family_id,
    secondary_family_id: form.secondary_family_id,
    family_rank: form.family_rank,
    equipment_id: form.equipment_id,
    equipment_detail: orNull(form.equipment_detail),
    kind: form.kind,
    stretch: form.stretch,
    stretch_note: orNull(form.stretch_note),
    confidence: form.confidence,
    notes: orNull(form.notes),
    is_active: form.is_active,
    muscles: form.muscles.map((m) => ({ muscle_id: m.muscle_id, level: m.level, note: m.note })),
    tags: form.tags.map((t) => ({ tag_id: t.tag_id, note: orNull(t.note) })),
    source_ids: [...form.source_ids],
  }
}

/** Livello di un muscolo nella griglia: `null` se non coinvolto. */
export function levelOf(form: ExerciseForm, muscleId: number): Level | null {
  return form.muscles.find((m) => m.muscle_id === muscleId)?.level ?? null
}

/**
 * Un tocco sul muscolo nella griglia: vuoto → S → P → vuoto (wireframe § 4.3).
 * La nota del coinvolgimento resta finché il muscolo resta nell'esercizio.
 */
export function cycleMuscle(form: ExerciseForm, muscleId: number): ExerciseForm {
  const current = form.muscles.find((m) => m.muscle_id === muscleId)
  if (current === undefined) {
    return { ...form, muscles: [...form.muscles, { muscle_id: muscleId, level: 'S', note: null }] }
  }
  if (current.level === 'S') {
    return {
      ...form,
      muscles: form.muscles.map((m) => (m.muscle_id === muscleId ? { ...m, level: 'P' } : m)),
    }
  }
  return { ...form, muscles: form.muscles.filter((m) => m.muscle_id !== muscleId) }
}

/** Rango proposto per un esercizio nuovo: dopo quelli già presenti nella famiglia. */
export function nextRank(catalog: Catalog, familyId: number): number {
  const ranks = catalog.exercises
    .filter((e) => e.primary_family_id === familyId)
    .map((e) => e.family_rank)
  return Math.max(0, ...ranks) + 1
}

/** Le stesse regole del server, per un riscontro immediato (US-03 CA2). */
export function validateForm(form: ExerciseForm): FormErrors {
  const t = texts.exerciseForm.errors
  const errors: FormErrors = {}
  if (form.name.trim() === '') errors.name = t.nameRequired
  if (form.primary_family_id === null) errors.primary_family_id = t.familyRequired
  if (form.equipment_id === null) errors.equipment_id = t.equipmentRequired
  if (!Number.isInteger(form.family_rank) || form.family_rank < 1) errors.family_rank = t.rank
  if (!form.muscles.some((m) => m.level === 'P')) errors.muscles = t.primaryMuscle
  if (form.secondary_family_id !== null && form.secondary_family_id === form.primary_family_id)
    errors.secondary_family_id = t.secondaryFamily
  return errors
}

function asField(name: unknown): FormField | null {
  return FIELDS.find((field) => field === name) ?? null
}

/**
 * Errori del server accanto ai campi: `violations` di un `rule-violation` e campi
 * di un `validation-error` (`loc` = `["body", campo, …]`). Quello che non ha un
 * campo finisce in `general`, da mostrare sopra la form.
 */
export function errorsFromProblem(problem: Problem): { fields: FormErrors; general: string[] } {
  const fields: FormErrors = {}
  const general: string[] = []
  for (const violation of problem.violations ?? []) {
    const field = asField(violation.field)
    if (field === null) general.push(violation.message)
    else fields[field] ??= violation.message
  }
  for (const error of problem.errors ?? []) {
    const field = asField(error.loc[1])
    if (field === null) general.push(error.msg)
    else fields[field] ??= texts.exerciseForm.errors.invalid
  }
  if (Object.keys(fields).length === 0 && general.length === 0) {
    general.push(problem.detail ?? problem.title)
  }
  return { fields, general }
}
