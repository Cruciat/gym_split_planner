import { describe, expect, it } from 'vitest'

import { makeCatalog, makeDetail } from '@/test/fixtures'

import {
  cycleMuscle,
  emptyForm,
  errorsFromProblem,
  type ExerciseForm,
  formFromDetail,
  levelOf,
  nextRank,
  toExerciseInput,
  validateForm,
} from './exerciseForm'

const validForm = (): ExerciseForm => ({
  ...emptyForm(),
  name: ' Chest press convergente ',
  primary_family_id: 2,
  equipment_id: 1,
  equipment_detail: '   ',
  muscles: [{ muscle_id: 2, level: 'P', note: null }],
  tags: [{ tag_id: 1, note: ' ' }],
})

describe('form e corpo della richiesta', () => {
  it('dal dettaglio alla form e ritorno, senza perdere nulla', () => {
    const detail = makeDetail()

    const input = toExerciseInput(formFromDetail(detail))

    expect(input).toEqual({
      name: detail.name,
      primary_family_id: 3,
      secondary_family_id: null,
      family_rank: 1,
      equipment_id: 2,
      equipment_detail: 'barra o corda',
      kind: 'isolation',
      stretch: 'high',
      stretch_note: null,
      confidence: 'solid',
      notes: 'Gomito sopra la testa.',
      is_active: true,
      muscles: [{ muscle_id: 3, level: 'P', note: 'in allungamento' }],
      tags: [{ tag_id: 2, note: 'Schiena appoggiata' }],
      source_ids: [1],
    })
  })

  it('i testi vuoti diventano null e gli spazi ai bordi spariscono', () => {
    const input = toExerciseInput(validForm())

    expect(input.name).toBe('Chest press convergente')
    expect(input.equipment_detail).toBeNull()
    expect(input.tags).toEqual([{ tag_id: 1, note: null }])
  })

  it('una form incompleta non diventa un corpo', () => {
    expect(() => toExerciseInput(emptyForm())).toThrow()
  })
})

describe('griglia dei muscoli', () => {
  it('vuoto → S → P → vuoto', () => {
    let form = emptyForm()
    expect(levelOf(form, 1)).toBeNull()

    form = cycleMuscle(form, 1)
    expect(levelOf(form, 1)).toBe('S')
    form = cycleMuscle(form, 1)
    expect(levelOf(form, 1)).toBe('P')
    form = cycleMuscle(form, 1)
    expect(levelOf(form, 1)).toBeNull()
  })

  it('la nota resta finché il muscolo resta', () => {
    const form: ExerciseForm = {
      ...emptyForm(),
      muscles: [{ muscle_id: 3, level: 'S', note: 'poco' }],
    }

    expect(cycleMuscle(form, 3).muscles).toEqual([{ muscle_id: 3, level: 'P', note: 'poco' }])
  })
})

describe('validateForm', () => {
  it('una form completa non ha errori', () => {
    expect(validateForm(validForm())).toEqual({})
  })

  it('segnala i campi mancanti e le regole del server (US-03 CA2)', () => {
    expect(validateForm(emptyForm())).toEqual({
      name: 'Serve un nome.',
      primary_family_id: 'Scegli la famiglia principale.',
      equipment_id: 'Scegli l’attrezzo.',
      muscles: 'Serve almeno un muscolo P.',
    })
    const sameFamily = { ...validForm(), secondary_family_id: 2, family_rank: 0 }
    expect(Object.keys(validateForm(sameFamily))).toEqual(['family_rank', 'secondary_family_id'])
  })
})

describe('nextRank', () => {
  it('dopo il rango più alto della famiglia', () => {
    expect(nextRank(makeCatalog(), 1)).toBe(3)
    expect(nextRank(makeCatalog(), 99)).toBe(1)
  })
})

describe('errorsFromProblem', () => {
  it('mette le regole violate accanto ai campi', () => {
    const result = errorsFromProblem({
      status: 422,
      code: 'rule-violation',
      title: 'Dati non accettati',
      violations: [
        {
          rule: 'primary-muscle-required',
          field: 'muscles',
          message: 'Serve almeno un muscolo P.',
        },
        { rule: 'name-taken', field: 'name', message: 'Esiste già.' },
        { rule: 'altro', field: null, message: 'Senza campo.' },
      ],
    })

    expect(result).toEqual({
      fields: { muscles: 'Serve almeno un muscolo P.', name: 'Esiste già.' },
      general: ['Senza campo.'],
    })
  })

  it('riconosce i campi di un errore di validazione', () => {
    const result = errorsFromProblem({
      status: 422,
      code: 'validation-error',
      title: 'Dati non validi',
      errors: [
        { loc: ['body', 'family_rank'], msg: 'too small', type: 'greater_than_equal' },
        { loc: ['body'], msg: 'Field required', type: 'missing' },
      ],
    })

    expect(result).toEqual({
      fields: { family_rank: 'Valore non valido.' },
      general: ['Field required'],
    })
  })

  it('senza dettagli usa il messaggio del problema', () => {
    expect(
      errorsFromProblem({ status: 500, code: 'internal-error', title: 'Errore interno' }),
    ).toEqual({ fields: {}, general: ['Errore interno'] })
  })
})
