/**
 * Pannello del volume e avvisi (US-13 CA2, US-20; wireframe, § 3.3).
 *
 * Le righe arrivano già calcolate dal server (`analysis`): qui si filtrano, si
 * raggruppano e si traducono gli avvisi in testo e in un elemento a cui portare.
 */

import type { Catalog, Plan } from '@/api/client'
import { formatNumber, texts } from '@/texts'

export type Volume = Plan['analysis']['volumes'][number]
export type PlanWarning = Plan['analysis']['warnings'][number]
export type VolumeFilter = 'priority' | 'target' | 'all'

export const hasTarget = (v: Volume): boolean =>
  v.priority !== 'none' && v.weekly_min !== null && v.weekly_max !== null

/** Muscoli con obiettivo da mostrare con il filtro; quelli senza stanno a parte. */
export function filterVolumes(volumes: Volume[], filter: VolumeFilter): Volume[] {
  return volumes.filter((v) => hasTarget(v) && (filter !== 'priority' || v.priority === 'priority'))
}

export interface VolumeGroup {
  code: string
  name: string
  volumes: Volume[]
}

/** Raggruppati per gruppo muscolare, nell'ordine in cui arrivano (quello del catalogo). */
export function groupVolumes(volumes: Volume[], catalog: Catalog | null): VolumeGroup[] {
  const names = new Map((catalog?.muscle_groups ?? []).map((g) => [g.code, g.name]))
  const groups = new Map<string, VolumeGroup>()
  for (const volume of volumes) {
    let group = groups.get(volume.group_code)
    if (group === undefined) {
      group = {
        code: volume.group_code,
        name: names.get(volume.group_code) ?? volume.group_code,
        volumes: [],
      }
      groups.set(volume.group_code, group)
    }
    group.volumes.push(volume)
  }
  return [...groups.values()]
}

/** Posizioni in percentuale: zona della fascia e segno del valore. */
export function barGeometry(v: Volume): { zoneStart: number; zoneWidth: number; marker: number } {
  const top = Math.max(v.weekly_max ?? 0, v.volume) * 1.2 || 1
  const percent = (n: number) => Math.min(100, (n / top) * 100)
  const min = v.weekly_min ?? 0
  const max = v.weekly_max ?? 0
  return {
    zoneStart: percent(min),
    zoneWidth: percent(max) - percent(min),
    marker: percent(v.volume),
  }
}

export function statusCounts(volumes: Volume[]): { below: number; above: number } {
  return {
    below: volumes.filter((v) => v.status === 'below').length,
    above: volumes.filter((v) => v.status === 'above').length,
  }
}

/** Dove porta un avviso: un muscolo nel pannello, un giorno o un esercizio. */
export type WarningTarget =
  | { kind: 'muscle'; muscleId: number }
  | { kind: 'day'; dayId: number }
  | { kind: 'slot'; dayId: number; slotId: number }

export interface WarningItem {
  key: string
  kind: 'below' | 'above' | 'cap' | 'long' | 'empty'
  text: string
  target: WarningTarget | null
}

/** Testo e destinazione di ogni avviso (algoritmo, § 8). */
export function warningItems(plan: Plan, catalog: Catalog | null): WarningItem[] {
  const w = texts.volume.warning
  const muscles = new Map(plan.analysis.volumes.map((v) => [v.muscle_id, v]))
  const days = new Map(plan.days.map((d) => [d.id, d]))
  const families = new Map((catalog?.families ?? []).map((f) => [f.id, f.name]))
  const tags = new Map((catalog?.tags ?? []).map((t) => [t.code, t.name]))

  const muscleName = (id: number | null) =>
    (id === null ? undefined : muscles.get(id)?.short_name) ?? ''
  const dayName = (warning: PlanWarning) => {
    const name = (warning.day_id === null ? undefined : days.get(warning.day_id)?.name) ?? ''
    return warning.session === 2 ? w.secondSession(name) : name
  }

  return plan.analysis.warnings.map((warning, index): WarningItem => {
    const key = `${warning.code}-${String(index)}`
    const volume = warning.volume ?? 0
    const min = warning.weekly_min ?? 0
    const max = warning.weekly_max ?? 0
    const dayTarget: WarningTarget | null =
      warning.day_id === null ? null : { kind: 'day', dayId: warning.day_id }
    switch (warning.code) {
      case 'volume-below':
      case 'volume-above': {
        const below = warning.code === 'volume-below'
        const name = muscleName(warning.muscle_id)
        return {
          key,
          kind: below ? 'below' : 'above',
          text: below ? w.below(name, volume, min, max) : w.above(name, volume, min, max),
          target:
            warning.muscle_id === null ? null : { kind: 'muscle', muscleId: warning.muscle_id },
        }
      }
      case 'session-cap':
        return {
          key,
          kind: 'cap',
          text: w.cap(dayName(warning), muscleName(warning.muscle_id), volume),
          target: dayTarget,
        }
      case 'session-too-long':
        return {
          key,
          kind: 'long',
          text: w.long(
            dayName(warning),
            warning.minutes ?? 0,
            plan.preferences.max_session_minutes,
          ),
          target: dayTarget,
        }
      case 'empty-slot': {
        const family =
          (warning.family_id === null ? undefined : families.get(warning.family_id)) ?? ''
        const excluded = warning.excluded_by.map((code) => tags.get(code) ?? code)
        const base = w.empty(dayName(warning), warning.position ?? 0, family)
        return {
          key,
          kind: 'empty',
          text: excluded.length > 0 ? `${base}: ${texts.editor.emptySlotExcluded(excluded)}` : base,
          target:
            warning.day_id !== null && warning.slot_id !== null
              ? { kind: 'slot', dayId: warning.day_id, slotId: warning.slot_id }
              : dayTarget,
        }
      }
      default:
        return { key, kind: 'cap', text: warning.code, target: dayTarget }
    }
  })
}

/** Durate stimate delle sedute di un giorno: una, o due con la seconda seduta. */
export function dayMinutes(plan: Plan, dayId: number): number[] {
  return plan.analysis.sessions
    .filter((s) => s.day_id === dayId)
    .sort((a, b) => a.session - b.session)
    .map((s) => s.minutes)
}

/** Distanza dalla fascia: zero dentro, altrimenti quanto manca o quanto si eccede. */
function bandDistance(value: number, min: number, max: number): number {
  if (value < min) return min - value
  if (value > max) return value - max
  return 0
}

/**
 * Effetto di un cambio di volume su un muscolo (wireframe, § 3.4): avvicina alla
 * fascia (verde), allontana (arancione) o non cambia la distanza.
 */
export function deltaEffect(
  volume: Volume | undefined,
  delta: number,
): 'closer' | 'farther' | 'neutral' {
  if (volume === undefined || !hasTarget(volume)) return 'neutral'
  const min = volume.weekly_min ?? 0
  const max = volume.weekly_max ?? 0
  const before = bandDistance(volume.volume, min, max)
  const after = bandDistance(volume.volume + delta, min, max)
  if (after < before) return 'closer'
  if (after > before) return 'farther'
  return 'neutral'
}

/** Cambio con il segno: `+2`, `−1,5` (meno tipografico). */
export function formatDelta(delta: number): string {
  const text = formatNumber(Math.abs(delta))
  return delta < 0 ? `−${text}` : `+${text}`
}
