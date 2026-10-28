/**
 * Form delle impostazioni globali (US-20; API, § 6.1; wireframe, § 5).
 *
 * I campi sono descritti una volta sola, con percorso nel JSON, limiti e unità: la
 * pagina li disegna da qui, e gli errori del server si ricollegano ai campi per
 * percorso (`level_weights.S`). I limiti sono gli stessi dello schema del backend.
 */

import type { components } from '@/api/schema'
import type { Problem } from '@/api/client'
import { texts } from '@/texts'

export type Settings = components['schemas']['SettingsIO']
export type GroupKey = keyof typeof texts.settings.groups
export type FieldPath = keyof typeof texts.settings.fields

export interface NumberField {
  kind: 'number'
  path: FieldPath
  min: number
  max: number
  step: number
  /** Il minimo è escluso (es. peso di P maggiore di zero). */
  exclusiveMin?: boolean
  unit?: keyof typeof texts.settings.units
}

export interface OtherField {
  kind: 'text' | 'switch' | 'textarea'
  path: FieldPath
}

export type Field = NumberField | OtherField

const seconds = (path: FieldPath, max: number, exclusiveMin = false): NumberField => ({
  kind: 'number',
  path,
  min: 0,
  max,
  step: 5,
  unit: 'seconds',
  exclusiveMin,
})
const minutes = (path: FieldPath): NumberField => ({
  kind: 'number',
  path,
  min: 0,
  max: 60,
  step: 1,
  unit: 'minutes',
})
const score = (path: FieldPath): NumberField => ({
  kind: 'number',
  path,
  min: 0,
  max: 20,
  step: 0.5,
})

export const GROUPS: { key: GroupKey; fields: Field[] }[] = [
  {
    key: 'volume',
    fields: [
      { kind: 'number', path: 'level_weights.P', min: 0, max: 2, step: 0.1, exclusiveMin: true },
      { kind: 'number', path: 'level_weights.S', min: 0, max: 2, step: 0.1 },
      {
        kind: 'number',
        path: 'session_cap',
        min: 0,
        max: 50,
        step: 0.5,
        exclusiveMin: true,
        unit: 'sets',
      },
    ],
  },
  {
    key: 'score',
    fields: [
      score('score_weights.confidence'),
      score('score_weights.equipment'),
      score('score_weights.stretch'),
      score('score_weights.family'),
      score('score_weights.rank'),
    ],
  },
  {
    key: 'duration',
    fields: [
      seconds('duration_params.set_seconds', 300, true),
      seconds('duration_params.rest_compound_seconds', 600),
      seconds('duration_params.rest_isolation_seconds', 600),
      seconds('duration_params.change_seconds', 600),
      seconds('duration_params.warmup_set_seconds', 300),
      seconds('duration_params.warmup_rest_seconds', 600),
      minutes('duration_params.warmup_minutes'),
      minutes('duration_params.stretching_minutes'),
    ],
  },
  {
    key: 'effort',
    fields: [
      { kind: 'text', path: 'effort.rir' },
      { kind: 'switch', path: 'effort.failure_last_set' },
    ],
  },
  { key: 'warmup', fields: [{ kind: 'textarea', path: 'warmup_text' }] },
]

const FIELDS = new Map(GROUPS.flatMap((g) => g.fields).map((f) => [f.path, f]))

type Value = number | string | boolean | null

/** Valore di un campo per percorso: `level_weights.P`. */
export function getValue(settings: Settings, path: FieldPath): Value {
  let current: unknown = settings
  for (const key of path.split('.')) {
    current = (current as Record<string, unknown>)[key]
  }
  return current as Value
}

/** Copia delle impostazioni con un campo cambiato. */
export function setValue(settings: Settings, path: FieldPath, value: Value): Settings {
  // Copia via JSON: dati semplici, e `structuredClone` rifiuta i proxy reattivi di Vue.
  const copy = JSON.parse(JSON.stringify(settings)) as Settings
  const keys = path.split('.')
  const last = keys.pop()
  let target = copy as unknown as Record<string, unknown>
  for (const key of keys) target = target[key] as Record<string, unknown>
  if (last !== undefined) target[last] = value
  return copy
}

/** Per l'avviso prima di uscire: le impostazioni sono cambiate rispetto a quelle salvate. */
export function sameSettings(a: Settings, b: Settings): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

/**
 * Errori del server per campo. I limiti numerici danno un messaggio con l'intervallo;
 * gli errori dei validatori (es. "S non può superare P") passano con il loro testo.
 */
export function settingsErrors(problem: Problem): {
  fields: Partial<Record<string, string>>
  general: string[]
} {
  const fields: Partial<Record<string, string>> = {}
  const general: string[] = []
  for (const error of problem.errors ?? []) {
    const path = error.loc.slice(1).join('.')
    const field = FIELDS.get(path as FieldPath)
    const own = error.msg.replace(/^Value error, /, '')
    if (field?.kind === 'number') fields[path] ??= texts.settings.range(field.min, field.max)
    else if (field !== undefined) fields[path] ??= texts.settings.invalid
    else if (path !== '' && error.msg.startsWith('Value error, ')) fields[path] ??= own
    else general.push(own)
  }
  if (Object.keys(fields).length === 0 && general.length === 0) {
    general.push(problem.detail ?? problem.title)
  }
  return { fields, general }
}
