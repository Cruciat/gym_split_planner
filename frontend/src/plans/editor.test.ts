import { afterEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makePlan } from '@/test/fixtures'
import { stubFetch } from '@/test/mount'

import { createPlanEditor } from './editor'

const notifier = () => ({ warning: vi.fn(), error: vi.fn() })

/** Server finto: ogni modifica incrementa la revisione, come quello vero. */
function server() {
  let revision = 4
  const respond = () => {
    revision += 1
    return jsonResponse(makePlan({ revision }))
  }
  return {
    'GET /api/plans/1': () => jsonResponse(makePlan({ revision })),
    'PATCH /api/plans/1/slots/100': respond,
    'PATCH /api/plans/1': respond,
    'PUT /api/plans/1/days/10/slots/order': respond,
  }
}

const ifMatchOf = (fetchMock: ReturnType<typeof stubFetch>, method: string) =>
  fetchMock.mock.calls
    .map(([r]) => r)
    .filter((r) => r.method === method)
    .map((r) => r.headers.get('If-Match'))

describe('coda delle modifiche (API, § 4)', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('invia una modifica alla volta con la revisione della precedente', async () => {
    const fetchMock = stubFetch(server())
    const editor = createPlanEditor(1, notifier())
    await editor.load()

    const results = await Promise.all([
      editor.updateSlot(100, { sets: 4 }),
      editor.updateSlot(100, { locked: true }),
      editor.rename('Nuovo nome'),
    ])

    expect(results).toEqual([true, true, true])
    expect(ifMatchOf(fetchMock, 'PATCH')).toEqual(['"4"', '"5"', '"6"'])
    expect(editor.plan.value?.revision).toBe(7)
    expect(editor.saveState.value).toBe('saved')
  })

  it('con 412 ricarica, avvisa e scarta il resto della coda', async () => {
    const notify = notifier()
    let current = 4
    const fetchMock = stubFetch({
      'GET /api/plans/1': () => jsonResponse(makePlan({ revision: current })),
      'PATCH /api/plans/1/slots/100': () => {
        current = 9
        return jsonResponse(
          { status: 412, code: 'revision-mismatch', title: 'Cambiata', current_revision: 9 },
          412,
        )
      },
    })
    const editor = createPlanEditor(1, notify)
    await editor.load()

    const results = await Promise.all([
      editor.updateSlot(100, { sets: 4 }),
      editor.updateSlot(100, { sets: 5 }),
    ])

    expect(results).toEqual([false, false])
    expect(ifMatchOf(fetchMock, 'PATCH')).toEqual(['"4"'])
    expect(notify.warning).toHaveBeenCalledWith(
      'La scheda è stata modificata da un altro dispositivo ed è stata ricaricata.',
    )
    expect(editor.plan.value?.revision).toBe(9)
  })

  it('un errore di rete ferma la coda; «Riprova» la fa ripartire', async () => {
    const routes = server()
    let offline = true
    stubFetch({
      ...routes,
      'PATCH /api/plans/1/slots/100': () =>
        offline ? Promise.reject(new TypeError('rete')) : routes['PATCH /api/plans/1/slots/100'](),
    })
    const editor = createPlanEditor(1, notifier())
    await editor.load()

    const result = editor.updateSlot(100, { sets: 4 })
    await vi.waitFor(() => {
      expect(editor.saveState.value).toBe('error')
    })
    expect(await editor.settle()).toBe(false)

    offline = false
    editor.retry()

    expect(await result).toBe(true)
    expect(editor.saveState.value).toBe('saved')
    expect(await editor.settle()).toBe(true)
  })

  it('una regola violata dà il messaggio del server e la coda prosegue', async () => {
    const notify = notifier()
    const routes = server()
    stubFetch({
      ...routes,
      'PATCH /api/plans/1/slots/100': async (request) => {
        const body = (await request.json()) as { rep_min?: number }
        return body.rep_min === 20
          ? jsonResponse(
              {
                status: 422,
                code: 'rule-violation',
                title: 'Regola violata',
                violations: [
                  { rule: 'reps-order', field: 'rep_max', message: 'Il minimo supera il massimo.' },
                ],
              },
              422,
            )
          : routes['PATCH /api/plans/1/slots/100']()
      },
    })
    const editor = createPlanEditor(1, notify)
    await editor.load()

    const results = await Promise.all([
      editor.updateSlot(100, { rep_min: 20 }),
      editor.updateSlot(100, { sets: 2 }),
    ])

    expect(results).toEqual([false, true])
    expect(notify.error).toHaveBeenCalledWith('Il minimo supera il massimo.')
  })

  it('il riordino si vede subito, prima della risposta', async () => {
    const base = makePlan()
    const day = base.days[0]
    const slot = day?.slots[0]
    if (day === undefined || slot === undefined) throw new Error('fixture')
    const plan = makePlan({ days: [{ ...day, slots: [slot, { ...slot, id: 101, position: 2 }] }] })
    stubFetch({
      'GET /api/plans/1': () => jsonResponse(plan),
      'PUT /api/plans/1/days/10/slots/order': () => jsonResponse({ ...plan, revision: 5 }),
    })
    const editor = createPlanEditor(1, notifier())
    await editor.load()

    const done = editor.reorderSlots(10, [101, 100])

    expect(editor.plan.value?.days[0]?.slots.map((s) => s.id)).toEqual([101, 100])
    expect(await done).toBe(true)
  })

  it('una scheda che non esiste', async () => {
    stubFetch({})
    const editor = createPlanEditor(1, notifier())

    await editor.load()

    expect(editor.loadState.value).toBe('not-found')
  })
})
