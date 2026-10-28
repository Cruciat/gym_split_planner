import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makeCatalog } from '@/test/fixtures'
import {
  chooseOption,
  dialogButton,
  inBody,
  mountAt,
  requestBodies,
  type Routes,
  setMobile,
  stubFetch,
} from '@/test/mount'

const routes = (extra: Routes = {}): Routes => ({
  '/api/catalog': () => jsonResponse(makeCatalog()),
  'POST /api/tags': async (request) =>
    jsonResponse(
      { id: 9, code: 'preferito', sort_order: 3, ...((await request.json()) as object) },
      201,
    ),
  'PATCH /api/tags/2': async (request) =>
    jsonResponse({ ...makeCatalog().tags[1], ...((await request.json()) as object) }),
  'GET /api/tags/2/usage': () =>
    jsonResponse({ exercises: 2, plans_with_overrides: [{ id: 1, name: 'PPL autunno' }] }),
  'DELETE /api/tags/2': () => new Response(null, { status: 204 }),
  ...extra,
})

describe('TagsPage (US-08)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('elenca le etichette con effetto, visibilità ed esercizi', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/etichette')

    const rows = wrapper.findAll('[data-testid="tag-row"]')
    expect(rows.map((r) => r.text())).toEqual([
      expect.stringMatching(/Collo: accorgimento.*Nessun effetto.*sì.*0/),
      expect.stringMatching(/Collo: attenzione.*Penalità 3.*sì.*2/),
    ])
  })

  it('crea un etichetta con bonus (CA1)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/etichette')

    await wrapper.get('[data-testid="add-tag"]').trigger('click')
    await wrapper.get('[data-testid="tag-name"] input').setValue('Preferito')
    await chooseOption(wrapper, 'tag-symbol', 'Stella')
    await chooseOption(wrapper, 'tag-effect', 'Bonus')
    await wrapper.get('[data-testid="tag-points"] input').setValue('2')
    await wrapper.get('[data-testid="tag-points"] input').trigger('blur')
    await wrapper.get('[data-testid="tag-edit"]').trigger('submit')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'POST', '/api/tags')).toEqual([
      {
        name: 'Preferito',
        symbol: 'star',
        color: 'neutral',
        effect: 'bonus',
        points: 2,
        show_badge: true,
        description: '',
      },
    ])
  })

  it('i punti contano solo per bonus e penalità', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/etichette')

    await wrapper.findAll('[data-testid="tag-edit-button"]')[1]?.trigger('click')
    await chooseOption(wrapper, 'tag-effect', 'Esclusione')
    expect(wrapper.get('[data-testid="tag-points"] input').attributes('disabled')).toBeDefined()
    await wrapper.get('[data-testid="tag-edit"]').trigger('submit')
    await flushPromises()

    const [body] = await requestBodies(fetchMock, 'PATCH', '/api/tags/2')
    expect(body).toMatchObject({ effect: 'exclude', points: 0 })
  })

  it('chiede conferma con i numeri degli utilizzi prima di eliminare (CA3)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/etichette')

    await wrapper.findAll('[data-testid="tag-delete"]')[1]?.trigger('click')
    await flushPromises()

    expect(inBody('.n-dialog')[0]?.text()).toContain(
      '«Collo: attenzione» è assegnata a 2 esercizi e personalizzata in 1 scheda.',
    )
    await dialogButton('Elimina etichetta').trigger('click')
    await flushPromises()
    expect(fetchMock.mock.calls.filter(([r]) => r.method === 'DELETE')).toHaveLength(1)
  })

  it('annullare la conferma non elimina', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/etichette')

    await wrapper.findAll('[data-testid="tag-delete"]')[1]?.trigger('click')
    await flushPromises()
    await dialogButton('Annulla').trigger('click')
    await flushPromises()

    expect(fetchMock.mock.calls.some(([r]) => r.method === 'DELETE')).toBe(false)
  })
})
