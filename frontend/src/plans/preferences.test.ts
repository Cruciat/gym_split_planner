import { describe, expect, it } from 'vitest'

import { makeCatalog, makePlanSettings } from '@/test/fixtures'

import {
  defaultPlanName,
  defaultPreferences,
  effectiveMuscle,
  effectiveTag,
  emptyOverrides,
  fromPlanSettings,
  moveItem,
  muscleRowsFromCatalog,
  overrideCount,
  preferenceErrors,
  resetOverride,
  rowErrors,
  setMuscle,
  setTag,
  tagRowsFromCatalog,
  toInput,
} from './preferences'

const catalog = makeCatalog()
const [upper] = muscleRowsFromCatalog(catalog)
const [tip, caution] = tagRowsFromCatalog(catalog)
if (upper === undefined || tip === undefined || caution === undefined) throw new Error('fixture')

describe('preferenze', () => {
  it('parte dagli attrezzi nell’ordine del catalogo, 75 minuti e nessuna personalizzazione', () => {
    expect(toInput(defaultPreferences(catalog))).toEqual({
      version: 2,
      equipment_order: ['machine', 'cable', 'free-weight'],
      max_session_minutes: 75,
      overrides: { muscles: {}, tags: {} },
    })
  })

  it('tiene solo i campi diversi dal catalogo', () => {
    let overrides = setMuscle(emptyOverrides(), upper, { weekly_max: 14 })
    expect(overrides.muscles).toEqual({ 'chest-upper': { weekly_max: 14 } })

    overrides = setMuscle(overrides, upper, { weekly_min: 10, priority: 'standard' })
    expect(overrides.muscles).toEqual({
      'chest-upper': { priority: 'standard', weekly_max: 14 },
    })
    expect(effectiveMuscle(upper, overrides)).toEqual({
      priority: 'standard',
      weekly_min: 10,
      weekly_max: 14,
    })

    // Tornare al valore del catalogo toglie la voce.
    overrides = setMuscle(overrides, upper, { weekly_max: 18, priority: 'priority' })
    expect(overrides.muscles).toEqual({})
  })

  it('con "nessun obiettivo" la fascia non si tiene', () => {
    const overrides = setMuscle(setMuscle(emptyOverrides(), upper, { weekly_max: 12 }), upper, {
      priority: 'none',
    })

    expect(overrides.muscles).toEqual({ 'chest-upper': { priority: 'none' } })
    expect(effectiveMuscle(upper, overrides)).toEqual({
      priority: 'none',
      weekly_min: null,
      weekly_max: null,
    })
  })

  it('i punti delle etichette contano solo per bonus e penalità', () => {
    let overrides = setTag(emptyOverrides(), caution, { points: 1 })
    expect(overrides.tags).toEqual({ 'neck-caution': { points: 1 } })

    overrides = setTag(overrides, caution, { effect: 'exclude' })
    expect(overrides.tags).toEqual({ 'neck-caution': { effect: 'exclude' } })
    expect(effectiveTag(caution, overrides).effect).toBe('exclude')

    overrides = setTag(overrides, tip, { effect: 'bonus', points: 2 })
    expect(overrides.tags['neck-tip']).toEqual({ effect: 'bonus', points: 2 })
    expect(overrideCount(overrides)).toBe(2)
  })

  it('il ripristino toglie la personalizzazione', () => {
    const overrides = setTag(setMuscle(emptyOverrides(), upper, { weekly_max: 14 }), caution, {
      points: 1,
    })

    expect(resetOverride(overrides, 'muscles', 'chest-upper')).toEqual({
      muscles: {},
      tags: { 'neck-caution': { points: 1 } },
    })
  })

  it('legge la vista delle personalizzazioni della scheda', () => {
    const { value, muscles, tags } = fromPlanSettings(makePlanSettings())

    expect(value.overrides).toEqual({
      muscles: { 'chest-mid': { weekly_max: 14 } },
      tags: {},
    })
    expect(value.max_session_minutes).toBe(75)
    expect(muscles.map((m) => m.code)).toEqual(['chest-upper', 'chest-mid', 'triceps-long'])
    expect(tags[1]?.catalog).toEqual({ effect: 'penalty', points: 3 })
  })

  it('sposta gli attrezzi senza uscire dall’elenco', () => {
    expect(moveItem(['a', 'b', 'c'], 2, -1)).toEqual(['a', 'c', 'b'])
    expect(moveItem(['a', 'b', 'c'], 0, -1)).toEqual(['a', 'b', 'c'])
  })

  it('divide gli errori per percorso nel JSON', () => {
    const { fields, general } = preferenceErrors(
      {
        status: 422,
        code: 'rule-violation',
        title: 'Regola violata',
        violations: [
          {
            rule: 'band-order',
            field: 'overrides.muscles.chest-upper.weekly_max',
            message: 'Il massimo deve superare il minimo.',
          },
        ],
        errors: [{ loc: ['body', 'preferences', 'max_session_minutes'], msg: 'x', type: 'y' }],
      },
      'Valore non valido.',
    )

    expect(general).toEqual([])
    expect(fields['max_session_minutes']).toBe('Valore non valido.')
    expect(rowErrors(fields, 'muscles', 'chest-upper')).toEqual({
      weekly_max: 'Il massimo deve superare il minimo.',
    })
  })

  it('propone lo stesso nome del server', () => {
    const date = new Date(2026, 9, 28, 12)
    expect(defaultPlanName('PPL 6', 'Scheda vuota', date)).toBe('PPL 6 — 28/10/2026')
    expect(defaultPlanName(null, 'Scheda vuota', date)).toBe('Scheda vuota — 28/10/2026')
  })
})
