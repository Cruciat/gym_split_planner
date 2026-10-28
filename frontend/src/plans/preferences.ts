/**
 * Preferenze di una scheda nel client (modello dati, § 4.7; API, § 6.6).
 *
 * Le personalizzazioni contengono solo i campi diversi dal catalogo, come le salva il
 * server: così "torna al catalogo" vuol dire togliere la voce, e il segno di
 * personalizzato coincide con la presenza della voce. I valori effettivi seguono le
 * stesse regole del motore (`resolve_muscle`, `resolve_tag`).
 */

import type {
  Catalog,
  PlanSettings,
  PreferencesInput,
  Priority,
  Problem,
  StoredPreferences,
  TagColor,
  TagEffect,
} from '@/api/client'

/** Durata massima predefinita di una seduta, in minuti (modello dati, § 4.7). */
export const DEFAULT_MAX_MINUTES = 75
const PREFERENCES_VERSION = 2

export interface MuscleOverride {
  priority?: Priority
  weekly_min?: number
  weekly_max?: number
}

export interface TagOverride {
  effect?: TagEffect
  points?: number
}

export interface Overrides {
  muscles: Record<string, MuscleOverride>
  tags: Record<string, TagOverride>
}

export interface PreferencesValue {
  equipment_order: string[]
  max_session_minutes: number | null
  overrides: Overrides
}

export interface MuscleValues {
  priority: Priority
  weekly_min: number | null
  weekly_max: number | null
}

export interface TagValues {
  effect: TagEffect
  points: number
}

/** Un muscolo con i valori del catalogo, da cui partono le personalizzazioni. */
export interface MuscleRow {
  code: string
  name: string
  shortName: string
  catalog: MuscleValues
}

export interface TagRow {
  code: string
  name: string
  symbol: string
  color: TagColor
  catalog: TagValues
}

export interface EquipmentItem {
  code: string
  name: string
}

export const emptyOverrides = (): Overrides => ({ muscles: {}, tags: {} })

/** Preferenze di partenza: attrezzi nell'ordine del catalogo, come fa il server. */
export function defaultPreferences(catalog: Catalog): PreferencesValue {
  return {
    equipment_order: equipmentItems(catalog).map((e) => e.code),
    max_session_minutes: DEFAULT_MAX_MINUTES,
    overrides: emptyOverrides(),
  }
}

export function equipmentItems(catalog: Catalog): EquipmentItem[] {
  return [...catalog.equipment]
    .sort((a, b) => a.sort_order - b.sort_order)
    .map(({ code, name }) => ({ code, name }))
}

export function muscleRowsFromCatalog(catalog: Catalog): MuscleRow[] {
  return [...catalog.muscles]
    .sort((a, b) => a.sort_order - b.sort_order)
    .map((m) => ({
      code: m.code,
      name: m.name,
      shortName: m.short_name,
      catalog: { priority: m.priority, weekly_min: m.weekly_min, weekly_max: m.weekly_max },
    }))
}

export function tagRowsFromCatalog(catalog: Catalog): TagRow[] {
  return [...catalog.tags]
    .sort((a, b) => a.sort_order - b.sort_order)
    .map((t) => ({
      code: t.code,
      name: t.name,
      symbol: t.symbol,
      color: t.color,
      catalog: { effect: t.effect, points: t.points },
    }))
}

/** Righe e preferenze dalla vista `GET /api/plans/{id}/settings` (API, § 8.1). */
export function fromPlanSettings(settings: PlanSettings): {
  value: PreferencesValue
  muscles: MuscleRow[]
  tags: TagRow[]
} {
  const overrides = emptyOverrides()
  for (const m of settings.muscles) {
    const entry = withoutNulls(m.override)
    if (Object.keys(entry).length > 0) overrides.muscles[m.code] = entry
  }
  for (const t of settings.tags) {
    const entry = withoutNulls(t.override)
    if (Object.keys(entry).length > 0) overrides.tags[t.code] = entry
  }
  return {
    value: {
      equipment_order: [...settings.equipment_order],
      max_session_minutes: settings.max_session_minutes,
      overrides,
    },
    muscles: settings.muscles.map((m) => ({
      code: m.code,
      name: m.name,
      shortName: m.short_name,
      catalog: {
        priority: m.catalog.priority ?? 'none',
        weekly_min: m.catalog.weekly_min,
        weekly_max: m.catalog.weekly_max,
      },
    })),
    tags: settings.tags.map((t) => ({
      code: t.code,
      name: t.name,
      symbol: t.symbol,
      color: t.color,
      catalog: { effect: t.catalog.effect ?? 'none', points: t.catalog.points ?? 0 },
    })),
  }
}

/** Le preferenze salvate in una scheda (`PlanOut.preferences`). */
export function fromStored(stored: StoredPreferences): PreferencesValue {
  const overrides = emptyOverrides()
  for (const [code, entry] of Object.entries(stored.overrides.muscles)) {
    overrides.muscles[code] = withoutNulls(entry)
  }
  for (const [code, entry] of Object.entries(stored.overrides.tags)) {
    overrides.tags[code] = withoutNulls(entry)
  }
  return {
    equipment_order: [...stored.equipment_order],
    max_session_minutes: stored.max_session_minutes,
    overrides,
  }
}

/** Il corpo per `PUT …/preferences` e per la creazione della scheda. */
export function toInput(value: PreferencesValue): PreferencesInput {
  return {
    version: PREFERENCES_VERSION,
    equipment_order: value.equipment_order,
    max_session_minutes: value.max_session_minutes,
    overrides: value.overrides,
  }
}

function withoutNulls<T extends object>(values: T): { [K in keyof T]?: NonNullable<T[K]> } {
  return Object.fromEntries(
    Object.entries(values).filter(([, v]) => v !== null && v !== undefined),
  ) as { [K in keyof T]?: NonNullable<T[K]> }
}

// --- Valori effettivi e modifiche --------------------------------------------------

export function effectiveMuscle(row: MuscleRow, overrides: Overrides): MuscleValues {
  const own = overrides.muscles[row.code]
  if (own === undefined) return row.catalog
  const priority = own.priority ?? row.catalog.priority
  if (priority === 'none') return { priority, weekly_min: null, weekly_max: null }
  return {
    priority,
    weekly_min: own.weekly_min ?? row.catalog.weekly_min,
    weekly_max: own.weekly_max ?? row.catalog.weekly_max,
  }
}

export function effectiveTag(row: TagRow, overrides: Overrides): TagValues {
  const own = overrides.tags[row.code]
  if (own === undefined) return row.catalog
  return { effect: own.effect ?? row.catalog.effect, points: own.points ?? row.catalog.points }
}

export const usesPoints = (effect: TagEffect): boolean => effect === 'bonus' || effect === 'penalty'

/**
 * Cambia uno o più valori di un muscolo. I campi uguali al catalogo si tolgono, la
 * fascia non si tiene con "nessun obiettivo", la voce vuota sparisce.
 */
export function setMuscle(
  overrides: Overrides,
  row: MuscleRow,
  change: Partial<MuscleValues>,
): Overrides {
  const merged = { ...effectiveMuscle(row, overrides), ...change }
  const entry: MuscleOverride = {}
  if (merged.priority !== row.catalog.priority) entry.priority = merged.priority
  if (merged.priority !== 'none') {
    if (merged.weekly_min !== null && merged.weekly_min !== row.catalog.weekly_min)
      entry.weekly_min = merged.weekly_min
    if (merged.weekly_max !== null && merged.weekly_max !== row.catalog.weekly_max)
      entry.weekly_max = merged.weekly_max
  }
  return { ...overrides, muscles: withEntry(overrides.muscles, row.code, entry) }
}

/** Cambia effetto o punti di un'etichetta; i punti contano solo per bonus e penalità. */
export function setTag(overrides: Overrides, row: TagRow, change: Partial<TagValues>): Overrides {
  const merged = { ...effectiveTag(row, overrides), ...change }
  const entry: TagOverride = {}
  if (merged.effect !== row.catalog.effect) entry.effect = merged.effect
  if (usesPoints(merged.effect) && merged.points !== row.catalog.points)
    entry.points = merged.points
  return { ...overrides, tags: withEntry(overrides.tags, row.code, entry) }
}

/** "Torna al catalogo": toglie la personalizzazione di un muscolo o di un'etichetta. */
export function resetOverride(
  overrides: Overrides,
  kind: 'muscles' | 'tags',
  code: string,
): Overrides {
  return kind === 'muscles'
    ? { ...overrides, muscles: withEntry(overrides.muscles, code, {}) }
    : { ...overrides, tags: withEntry(overrides.tags, code, {}) }
}

/** Copia con la voce `code` sostituita, o tolta se è vuota. */
function withEntry<T extends object>(
  entries: Record<string, T>,
  code: string,
  entry: T,
): Record<string, T> {
  const rest = Object.fromEntries(Object.entries(entries).filter(([key]) => key !== code))
  return Object.keys(entry).length > 0 ? { ...rest, [code]: entry } : rest
}

export function overrideCount(overrides: Overrides): number {
  return Object.keys(overrides.muscles).length + Object.keys(overrides.tags).length
}

/** Sposta un elemento di una posizione, in su (`-1`) o in giù (`1`). */
export function moveItem<T>(items: readonly T[], index: number, delta: -1 | 1): T[] {
  const target = index + delta
  const result = [...items]
  if (target < 0 || target >= items.length) return result
  const [item] = result.splice(index, 1)
  if (item !== undefined) result.splice(target, 0, item)
  return result
}

// --- Errori ------------------------------------------------------------------------

/**
 * Messaggi di un errore sulle preferenze per percorso nel JSON, es.
 * `overrides.muscles.quads.weekly_max` (API, § 6.6). Gli errori di validazione di
 * Pydantic hanno il percorso in `loc`, dopo `body` e, alla creazione, `preferences`.
 */
export function preferenceErrors(
  problem: Problem,
  invalidValue: string,
): { fields: Record<string, string>; general: string[] } {
  const fields: Record<string, string> = {}
  const general: string[] = []
  for (const violation of problem.violations ?? []) {
    if (violation.field === null) general.push(violation.message)
    else fields[violation.field] ??= violation.message
  }
  for (const error of problem.errors ?? []) {
    const path = error.loc.slice(1)
    if (path[0] === 'preferences') path.shift()
    if (path.length > 0) fields[path.join('.')] ??= invalidValue
    else general.push(error.msg)
  }
  if (Object.keys(fields).length === 0 && general.length === 0) {
    general.push(problem.detail ?? problem.title)
  }
  return { fields, general }
}

/** Errori di un muscolo o di un'etichetta: `{weekly_max: "…"}`. */
export function rowErrors(
  fields: Record<string, string>,
  kind: 'muscles' | 'tags',
  code: string,
): Record<string, string> {
  const prefix = `overrides.${kind}.${code}.`
  return Object.fromEntries(
    Object.entries(fields)
      .filter(([path]) => path.startsWith(prefix))
      .map(([path, message]) => [path.slice(prefix.length), message]),
  )
}

// --- Nomi e date -------------------------------------------------------------------

/** Data come `28/10/2026`, nel fuso del dispositivo. */
export function formatDate(value: string | Date): string {
  return new Date(value).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/** Il nome che darebbe il server: "<split> — gg/mm/aaaa" (API, § 6.5). */
export function defaultPlanName(splitName: string | null, emptyName: string, date: Date): string {
  return `${splitName ?? emptyName} — ${formatDate(date)}`
}
