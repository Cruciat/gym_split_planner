import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makeCatalog } from '@/test/fixtures'
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
  'PATCH /api/muscles/3': async (request) =>
    jsonResponse({ ...makeCatalog().muscles[2], ...((await request.json()) as object) }),
  ...extra,
})

describe('MusclesPage (US-07)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('elenca i muscoli per gruppo con priorità e fascia', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/muscoli')

    expect(wrapper.findAll('h2').map((h) => h.text())).toEqual(['Petto', 'Tricipiti'])
    expect(wrapper.findAll('[data-testid="muscle-row"]')[0]?.text()).toMatch(
      /Petto alto.*Prioritario.*10–18/,
    )
  })

  it('modifica priorità e fascia (CA1)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/muscoli')

    await wrapper.findAll('[data-testid="muscle-edit-button"]')[2]?.trigger('click')
    await chooseOption(wrapper, 'muscle-priority', 'Non prioritario')
    await wrapper.get('[data-testid="muscle-min"] input').setValue('8')
    await wrapper.get('[data-testid="muscle-min"] input').trigger('blur')
    await wrapper.get('[data-testid="muscle-edit"]').trigger('submit')
    await flushPromises()

    const [body] = await requestBodies(fetchMock, 'PATCH', '/api/muscles/3')
    expect(body).toEqual({
      name: 'Tricipite, capo lungo',
      short_name: 'Capo lungo',
      priority: 'standard',
      weekly_min: 8,
      weekly_max: 18,
      notes: '',
    })
  })

  it('"nessun obiettivo" svuota la fascia', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/muscoli')

    await wrapper.findAll('[data-testid="muscle-edit-button"]')[2]?.trigger('click')
    await chooseOption(wrapper, 'muscle-priority', 'Nessun obiettivo')
    expect(wrapper.get('[data-testid="muscle-min"] input').attributes('disabled')).toBeDefined()
    await wrapper.get('[data-testid="muscle-edit"]').trigger('submit')
    await flushPromises()

    const [body] = await requestBodies(fetchMock, 'PATCH', '/api/muscles/3')
    expect(body).toMatchObject({ priority: 'none', weekly_min: null, weekly_max: null })
  })

  it('spiega quali schede renderebbero invalida la fascia', async () => {
    stubFetch(
      routes({
        'PATCH /api/muscles/3': () =>
          jsonResponse(
            {
              status: 409,
              code: 'invalid-band',
              title: 'Fascia non valida in una scheda',
              plans: [{ id: 1, name: 'PPL autunno' }],
            },
            409,
          ),
      }),
    )
    const { wrapper } = await mountAt('/catalogo/muscoli')

    await wrapper.findAll('[data-testid="muscle-edit-button"]')[2]?.trigger('click')
    await wrapper.get('[data-testid="muscle-edit"]').trigger('submit')
    await flushPromises()

    expect(wrapper.get('[data-testid="muscle-edit"]').text()).toContain(
      'Fascia non valida per la scheda «PPL autunno»',
    )
  })

  it('mostra accanto ai campi le regole della fascia (CA2)', async () => {
    stubFetch(
      routes({
        'PATCH /api/muscles/3': () =>
          jsonResponse(
            {
              status: 422,
              code: 'rule-violation',
              title: 'Dati non accettati',
              violations: [
                {
                  rule: 'band-order',
                  field: 'weekly_max',
                  message: 'Il massimo deve essere maggiore.',
                },
              ],
            },
            422,
          ),
      }),
    )
    const { wrapper } = await mountAt('/catalogo/muscoli')

    await wrapper.findAll('[data-testid="muscle-edit-button"]')[2]?.trigger('click')
    await wrapper.get('[data-testid="muscle-edit"]').trigger('submit')
    await flushPromises()

    expect(wrapper.get('[data-testid="muscle-edit"]').text()).toContain(
      'Il massimo deve essere maggiore.',
    )
  })
})
