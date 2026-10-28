import { describe, expect, it } from 'vitest'

import { makeCatalog } from '@/test/fixtures'

import {
  countActiveFilters,
  emptyFilters,
  type ExerciseFilters,
  filterExercises,
  filtersFromQuery,
  filtersToQuery,
  normalize,
} from './filters'

const codes = (filters: Partial<ExerciseFilters>): string[] =>
  filterExercises(makeCatalog(), { ...emptyFilters, ...filters }).map((e) => e.code)

describe('filterExercises', () => {
  it('senza filtri nasconde solo i disattivati (US-01 CA4)', () => {
    expect(codes({})).toEqual([
      'chest-press-incline',
      'incline-bench-press',
      'chest-press',
      'cable-overhead-extension',
    ])
    expect(codes({ showInactive: true })).toContain('katana-extension')
  })

  it('cerca nel nome senza distinguere maiuscole e accenti', () => {
    expect(codes({ search: 'CHEST' })).toEqual(['chest-press-incline', 'chest-press'])
    expect(codes({ search: '30' })).toEqual(['incline-bench-press'])
    expect(codes({ search: '  inclinàta ' })).toEqual([
      'chest-press-incline',
      'incline-bench-press',
    ])
  })

  it('filtra per gruppo della famiglia principale', () => {
    expect(codes({ group: 'triceps' })).toEqual(['cable-overhead-extension'])
  })

  it('filtra per famiglia principale o secondaria', () => {
    expect(codes({ family: 'press-incline' })).toEqual([
      'chest-press-incline',
      'incline-bench-press',
      'chest-press',
    ])
  })

  it('filtra per muscolo con il livello minimo', () => {
    expect(codes({ muscle: 'chest-upper' })).toEqual(['chest-press-incline', 'incline-bench-press'])
    expect(codes({ muscle: 'chest-upper', level: 'S' })).toEqual([
      'chest-press-incline',
      'incline-bench-press',
      'chest-press',
    ])
  })

  it('filtra per attrezzo e confidenza', () => {
    expect(codes({ equipment: 'cable' })).toEqual(['cable-overhead-extension'])
    expect(codes({ confidence: 'limited' })).toEqual(['chest-press-incline'])
  })

  it("filtra con o senza un'etichetta", () => {
    expect(codes({ tag: 'neck-caution' })).toEqual([
      'incline-bench-press',
      'cable-overhead-extension',
    ])
    expect(codes({ tag: 'neck-caution', withoutTag: true })).toEqual([
      'chest-press-incline',
      'chest-press',
    ])
  })

  it('combina i filtri (US-01 CA2)', () => {
    expect(
      codes({ group: 'chest', tag: 'neck-caution', withoutTag: true, equipment: 'machine' }),
    ).toEqual(['chest-press-incline', 'chest-press'])
    // La chest press seduta ha la spinta inclinata come famiglia secondaria.
    expect(codes({ family: 'press-incline', muscle: 'chest-mid', search: 'seduta' })).toEqual([
      'chest-press',
    ])
    expect(codes({ family: 'press-incline', muscle: 'triceps-long' })).toEqual([])
  })

  it('un codice che non esiste più non trova nulla', () => {
    expect(codes({ family: 'famiglia-eliminata' })).toEqual([])
  })
})

describe('filtri nell URL (US-01 CA3)', () => {
  it('senza filtri la query è vuota', () => {
    expect(filtersToQuery({ ...emptyFilters })).toEqual({})
    expect(filtersFromQuery({})).toEqual(emptyFilters)
  })

  it('andata e ritorno', () => {
    const filters: ExerciseFilters = {
      search: 'panca',
      group: 'chest',
      muscle: 'chest-upper',
      level: 'S',
      family: 'press-incline',
      equipment: 'free-weight',
      tag: 'neck-caution',
      withoutTag: true,
      confidence: 'solid',
      showInactive: true,
    }
    const query = filtersToQuery(filters)

    expect(query).toEqual({
      cerca: 'panca',
      gruppo: 'chest',
      muscolo: 'chest-upper',
      livello: 'S',
      famiglia: 'press-incline',
      attrezzo: 'free-weight',
      etichetta: 'neck-caution',
      senza: '1',
      confidenza: 'solid',
      disattivati: '1',
    })
    expect(filtersFromQuery(query as Record<string, string>)).toEqual(filters)
  })

  it('livello e "senza" contano solo con muscolo ed etichetta', () => {
    expect(filtersToQuery({ ...emptyFilters, level: 'S', withoutTag: true })).toEqual({})
  })

  it('ignora valori sconosciuti', () => {
    const filters = filtersFromQuery({ confidenza: 'altissima', livello: 'X', cerca: ['a', 'b'] })

    expect(filters.confidence).toBeNull()
    expect(filters.level).toBe('P')
    expect(filters.search).toBe('a')
  })
})

describe('countActiveFilters', () => {
  it('conta i filtri attivi, non il livello', () => {
    expect(countActiveFilters({ ...emptyFilters })).toBe(0)
    expect(countActiveFilters({ ...emptyFilters, search: ' ', level: 'S' })).toBe(0)
    expect(
      countActiveFilters({
        ...emptyFilters,
        search: 'x',
        muscle: 'chest-upper',
        showInactive: true,
      }),
    ).toBe(3)
  })
})

describe('normalize', () => {
  it('toglie accenti e maiuscole', () => {
    expect(normalize('Àlzate Laterali')).toBe('alzate laterali')
  })
})
