import { describe, expect, it } from 'vitest'

import { makeCatalog, makePlan, makeVolumes } from '@/test/fixtures'

import {
  barGeometry,
  dayMinutes,
  filterVolumes,
  groupVolumes,
  statusCounts,
  warningItems,
} from './volume'

describe('pannello del volume', () => {
  const volumes = makeVolumes()

  it('filtra prioritari, con obiettivo e tutti', () => {
    expect(filterVolumes(volumes, 'priority').map((v) => v.code)).toEqual([
      'chest-upper',
      'chest-mid',
      'triceps-long',
    ])
    expect(filterVolumes(volumes, 'target').map((v) => v.code)).toEqual([
      'chest-upper',
      'chest-mid',
      'triceps-long',
      'quads',
    ])
  })

  it('raggruppa per gruppo con i nomi del catalogo', () => {
    const groups = groupVolumes(filterVolumes(volumes, 'priority'), makeCatalog())

    expect(groups.map((g) => [g.name, g.volumes.length])).toEqual([
      ['Petto', 2],
      ['Tricipiti', 1],
    ])
  })

  it('disegna la fascia come zona e il valore come segno', () => {
    const upper = volumes[0]
    if (upper === undefined) throw new Error('fixture')
    const bar = barGeometry({ ...upper, volume: 12, weekly_min: 10, weekly_max: 20 })

    expect(bar.zoneStart).toBeCloseTo(41.667, 2)
    expect(bar.zoneStart + bar.zoneWidth).toBeCloseTo(83.333, 2)
    expect(bar.marker).toBe(50)
  })

  it('conta i muscoli sotto e sopra', () => {
    expect(statusCounts(volumes)).toEqual({ below: 1, above: 1 })
  })

  it('traduce gli avvisi e dice dove portano', () => {
    const plan = makePlan({
      analysis: {
        volumes,
        sessions: [
          { day_id: 10, session: 1, minutes: 58.4, max_muscle_volume: null },
          { day_id: 10, session: 2, minutes: 61.6, max_muscle_volume: null },
        ],
        warnings: [
          warning({
            code: 'volume-below',
            muscle_id: 3,
            volume: 8,
            weekly_min: 10,
            weekly_max: 18,
          }),
          warning({ code: 'session-cap', day_id: 10, session: 2, muscle_id: 1, volume: 10.5 }),
          warning({ code: 'session-too-long', day_id: 10, session: 1, minutes: 82.2 }),
          warning({
            code: 'empty-slot',
            day_id: 10,
            slot_id: 100,
            position: 1,
            family_id: 1,
            excluded_by: ['neck-caution'],
          }),
        ],
      },
    })

    const items = warningItems(plan, makeCatalog())

    expect(items.map((i) => i.text)).toEqual([
      'Capo lungo sotto fascia (8 / 10–18)',
      'Push (2ª seduta): Petto alto a 10,5 serie, oltre il tetto per seduta',
      'Push: seduta di ~82 min, oltre i 75 previsti',
      'Push, esercizio 1: nessun esercizio per «Spinta inclinata»: tutti esclusi da «Collo: attenzione»',
    ])
    expect(items.map((i) => i.target)).toEqual([
      { kind: 'muscle', muscleId: 3 },
      { kind: 'day', dayId: 10 },
      { kind: 'day', dayId: 10 },
      { kind: 'slot', dayId: 10, slotId: 100 },
    ])
    expect(dayMinutes(plan, 10)).toEqual([58.4, 61.6])
  })
})

function warning(fields: Partial<ReturnType<typeof makePlan>['analysis']['warnings'][number]>) {
  return {
    code: '',
    day_id: null,
    session: null,
    slot_id: null,
    position: null,
    family_id: null,
    muscle_id: null,
    volume: null,
    weekly_min: null,
    weekly_max: null,
    minutes: null,
    excluded_by: [],
    ...fields,
  }
}
