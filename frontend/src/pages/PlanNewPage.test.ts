import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makeCatalog, makePlan, makeSplits } from '@/test/fixtures'
import {
  chooseOption,
  mountAt,
  requestBodies,
  type Routes,
  setMobile,
  stubFetch,
} from '@/test/mount'

const routes = (extra: Routes = {}): Routes => ({
  '/api/catalog': () => jsonResponse(makeCatalog()),
  'GET /api/splits': () => jsonResponse(makeSplits()),
  'GET /api/plans/7': () => jsonResponse(makePlan({ id: 7, name: 'Upper/Lower, 4 giorni' })),
  'POST /api/plans': async (request) => {
    const body = (await request.json()) as { name: string | null }
    return jsonResponse(makePlan({ id: 7, name: body.name ?? 'Senza nome' }), 201)
  },
  ...extra,
})

const step = (wrapper: VueWrapper) => wrapper.get('[data-testid="step"]').text()

async function click(wrapper: VueWrapper, testId: string, index = 0): Promise<void> {
  await wrapper.findAll(`[data-testid="${testId}"]`)[index]?.trigger('click')
  await flushPromises()
}

describe('PlanNewPage (US-10, US-11)', () => {
  beforeEach(() => {
    setMobile(false)
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 9, 28, 12))
  })

  afterEach(() => {
    vi.useRealTimers()
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('propone gli split con i giorni e la scheda vuota (CA1)', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/nuova')

    expect(step(wrapper)).toBe('Passo 1 di 3 — Da dove parti?')
    const cards = wrapper.findAll('[data-testid="split-choice"]').map((c) => c.text())
    expect(cards[0]).toMatch(/Push\/Pull\/Legs, 3 giorni.*3 giorni.*Push · Pull · Legs/)
    expect(cards[1]).toContain('Upper ×2 · Lower ×2')
    expect(wrapper.get('[data-testid="empty-choice"]').text()).toContain('Scheda vuota')
  })

  it('crea con i valori già pronti e apre la scheda', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper, router } = await mountAt('/schede/nuova')

    await click(wrapper, 'split-choice', 1)
    expect(step(wrapper)).toBe('Passo 2 di 3 — Preferenze')
    expect(wrapper.get('[data-testid="overrides-summary"]').text()).toBe('come nel catalogo')
    await click(wrapper, 'next')
    expect(step(wrapper)).toBe('Passo 3 di 3 — Nome')
    expect((wrapper.get('[data-testid="plan-name"] input').element as HTMLInputElement).value).toBe(
      'Upper/Lower, 4 giorni — 28/10/2026',
    )
    await click(wrapper, 'create')

    expect(await requestBodies(fetchMock, 'POST', '/api/plans')).toEqual([
      {
        split_id: 2,
        name: 'Upper/Lower, 4 giorni — 28/10/2026',
        preferences: {
          version: 2,
          equipment_order: ['machine', 'cable', 'free-weight'],
          max_session_minutes: 75,
          overrides: { muscles: {}, tags: {} },
        },
      },
    ])
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/schede/7')
    })
  })

  it('scheda vuota con preferenze e personalizzazioni (CA2, US-11)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/nuova')

    await click(wrapper, 'empty-choice')
    // Pesi liberi in cima: due volte su.
    await click(wrapper, 'equipment-up', 2)
    await click(wrapper, 'equipment-up', 1)
    await wrapper.get('[data-testid="max-minutes"] input').setValue('60')
    await click(wrapper, 'customize')
    await chooseOption(wrapper, 'muscle-priority', 'Non prioritario')
    expect(wrapper.get('[data-testid="overrides-summary"]').text()).toBe('1 personalizzazione')
    await click(wrapper, 'next')
    await wrapper.get('[data-testid="plan-name"] input').setValue('La mia scheda')
    await click(wrapper, 'create')

    const [body] = await requestBodies(fetchMock, 'POST', '/api/plans')
    expect(body).toEqual({
      split_id: null,
      name: 'La mia scheda',
      preferences: {
        version: 2,
        equipment_order: ['free-weight', 'machine', 'cable'],
        max_session_minutes: 60,
        overrides: { muscles: { 'chest-upper': { priority: 'standard' } }, tags: {} },
      },
    })
  })

  it('il nome proposto segue lo split, finché non lo si cambia', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/nuova')
    const name = () =>
      (wrapper.get('[data-testid="plan-name"] input').element as HTMLInputElement).value

    await click(wrapper, 'empty-choice')
    await click(wrapper, 'next')
    expect(name()).toBe('Scheda vuota — 28/10/2026')

    await click(wrapper, 'back')
    await click(wrapper, 'back')
    await click(wrapper, 'split-choice', 0)
    await click(wrapper, 'next')
    expect(name()).toBe('Push/Pull/Legs, 3 giorni — 28/10/2026')
  })

  it('un errore sulle preferenze riporta al passo 2, accanto al campo', async () => {
    stubFetch(
      routes({
        'POST /api/plans': () =>
          jsonResponse(
            {
              status: 422,
              code: 'rule-violation',
              title: 'Regola violata',
              violations: [
                {
                  rule: 'band-order',
                  field: 'overrides.muscles.chest-upper.weekly_max',
                  message: 'Il massimo deve essere maggiore del minimo.',
                },
              ],
            },
            422,
          ),
      }),
    )
    const { wrapper, router } = await mountAt('/schede/nuova')

    await click(wrapper, 'split-choice', 0)
    await click(wrapper, 'next')
    await click(wrapper, 'create')

    expect(step(wrapper)).toBe('Passo 2 di 3 — Preferenze')
    const row = wrapper.findAll('[data-testid="muscle-override"]')[0]
    expect(row?.text()).toContain('Il massimo deve essere maggiore del minimo.')
    expect(router.currentRoute.value.path).toBe('/schede/nuova')
  })
})
