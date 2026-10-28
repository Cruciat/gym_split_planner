import { describe, expect, it } from 'vitest'

import { makeSettings } from '@/test/fixtures'

import { GROUPS, getValue, sameSettings, setValue, settingsErrors } from './form'

describe('form delle impostazioni', () => {
  it('descrive tutti i campi dello schema, una volta sola', () => {
    const paths = GROUPS.flatMap((g) => g.fields.map((f) => f.path))
    const settings = makeSettings()

    expect(new Set(paths).size).toBe(paths.length)
    for (const path of paths) expect(getValue(settings, path)).not.toBeUndefined()
    // Né più né meno delle foglie del JSON delle impostazioni.
    const leaves = (value: object, prefix = ''): string[] =>
      Object.entries(value).flatMap(([key, v]) =>
        typeof v === 'object' && v !== null
          ? leaves(v as object, `${prefix}${key}.`)
          : [`${prefix}${key}`],
      )
    expect([...paths].sort()).toEqual(leaves(settings).sort())
  })

  it('legge e cambia un campo senza toccare l’originale', () => {
    const settings = makeSettings()

    const changed = setValue(settings, 'level_weights.S', 0.25)

    expect(getValue(changed, 'level_weights.S')).toBe(0.25)
    expect(getValue(settings, 'level_weights.S')).toBe(0.5)
    expect(sameSettings(settings, changed)).toBe(false)
    expect(sameSettings(settings, setValue(changed, 'level_weights.S', 0.5))).toBe(true)
  })

  it('ricollega gli errori del server ai campi', () => {
    const { fields, general } = settingsErrors({
      status: 422,
      code: 'validation-error',
      title: 'Dati non validi',
      errors: [
        { loc: ['body', 'session_cap'], msg: 'Input should be greater than 0', type: 'x' },
        { loc: ['body', 'effort', 'rir'], msg: 'String should match pattern', type: 'x' },
        {
          loc: ['body', 'level_weights'],
          msg: 'Value error, Il peso di S non può superare quello di P',
          type: 'value_error',
        },
      ],
    })

    expect(fields).toEqual({
      session_cap: 'Un valore tra 0 e 50.',
      'effort.rir': 'Valore non valido.',
      level_weights: 'Il peso di S non può superare quello di P',
    })
    expect(general).toEqual([])
  })

  it('senza dettagli usa il titolo dell’errore', () => {
    expect(settingsErrors({ status: 500, code: 'x', title: 'Errore' }).general).toEqual(['Errore'])
  })
})
