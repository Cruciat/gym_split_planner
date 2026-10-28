import { describe, expect, it } from 'vitest'

import { problemMessages } from './problems'

describe('problemMessages', () => {
  it('divide regole violate ed errori di validazione per campo', () => {
    const result = problemMessages(
      {
        status: 422,
        code: 'rule-violation',
        title: 'Dati non accettati',
        violations: [
          { rule: 'band-order', field: 'weekly_max', message: 'Il massimo…' },
          { rule: 'x', field: null, message: 'Generale.' },
        ],
        errors: [{ loc: ['body', 'points'], msg: 'too big', type: 'le' }],
      },
      'Non valido',
    )

    expect(result).toEqual({
      fields: { weekly_max: 'Il massimo…', points: 'Non valido' },
      general: ['Generale.'],
    })
  })

  it('senza dettagli per campo usa il messaggio del problema', () => {
    expect(
      problemMessages({ status: 409, code: 'in-use', title: 'In uso', detail: 'Usata.' }, 'x'),
    ).toEqual({ fields: {}, general: ['Usata.'] })
  })
})
