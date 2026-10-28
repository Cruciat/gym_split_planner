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

const unused = { exercises: 0, secondary_exercises: 0, split_slots: 0, plans: [] }

const routes = (extra: Routes = {}): Routes => ({
  '/api/catalog': () => jsonResponse(makeCatalog()),
  'POST /api/families': async (request) =>
    jsonResponse(
      { id: 9, code: 'nuova', sort_order: 4, ...((await request.json()) as object) },
      201,
    ),
  'PATCH /api/families/2': async (request) =>
    jsonResponse({ ...makeCatalog().families[1], ...((await request.json()) as object) }),
  'GET /api/families/1/usage': () =>
    jsonResponse({
      exercises: 2,
      secondary_exercises: 1,
      split_slots: 3,
      plans: [{ id: 1, name: 'PPL autunno', slots: 1 }],
    }),
  'GET /api/families/2/usage': () => jsonResponse({ ...unused, secondary_exercises: 0 }),
  'DELETE /api/families/2': () => new Response(null, { status: 204 }),
  ...extra,
})

describe('FamiliesPage (US-06)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('elenca le famiglie con gruppo ed esercizi', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/famiglie')

    const rows = wrapper.findAll('[data-testid="family-row"]')
    expect(rows).toHaveLength(3)
    expect(rows[0]?.text()).toContain('Spinta inclinata')
    expect(rows[0]?.text()).toContain('Petto')
    expect(rows[0]?.text()).toContain('2 (+1 come secondaria)')
    expect(wrapper.get('[aria-current="page"].tab').text()).toBe('Famiglie')
  })

  it('crea una famiglia (CA1)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/famiglie')

    await wrapper.get('[data-testid="add-family"]').trigger('click')
    await wrapper.get('[data-testid="family-name"] input').setValue('Spinta convergente')
    await chooseOption(wrapper, 'family-group', 'Petto')
    await wrapper.get('[data-testid="family-edit"]').trigger('submit')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'POST', '/api/families')).toEqual([
      { name: 'Spinta convergente', muscle_group_id: 1, description: '' },
    ])
    expect(wrapper.find('[data-testid="family-edit"]').exists()).toBe(false)
  })

  it('rinomina una famiglia e mostra gli errori del server', async () => {
    const fetchMock = stubFetch(
      routes({
        'PATCH /api/families/2': () =>
          jsonResponse(
            {
              status: 422,
              code: 'rule-violation',
              title: 'Dati non accettati',
              violations: [{ rule: 'name-taken', field: 'name', message: 'Esiste già.' }],
            },
            422,
          ),
      }),
    )
    const { wrapper } = await mountAt('/catalogo/famiglie')

    await wrapper.findAll('[data-testid="family-edit-button"]')[1]?.trigger('click')
    const name = wrapper.get<HTMLInputElement>('[data-testid="family-name"] input')
    expect(name.element.value).toBe('Spinta orizzontale')
    await name.setValue('Spinta inclinata')
    await wrapper.get('[data-testid="family-edit"]').trigger('submit')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'PATCH', '/api/families/2')).toHaveLength(1)
    expect(wrapper.get('[data-testid="family-edit"]').text()).toContain('Esiste già.')
  })

  it('una famiglia usata non si elimina e il messaggio dice da cosa (CA2)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/famiglie')

    await wrapper.findAll('[data-testid="family-delete"]')[0]?.trigger('click')
    await flushPromises()

    const text = inBody('.n-dialog')[0]?.text() ?? ''
    expect(text).toContain('2 esercizi la hanno come famiglia principale')
    expect(text).toContain('3 slot degli split predefiniti la chiedono')
    expect(text).toContain('«PPL autunno»')
    expect(fetchMock.mock.calls.some(([r]) => r.method === 'DELETE')).toBe(false)
  })

  it('elimina una famiglia non usata dopo la conferma', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/famiglie')

    await wrapper.findAll('[data-testid="family-delete"]')[1]?.trigger('click')
    await flushPromises()
    await dialogButton('Elimina famiglia').trigger('click')
    await flushPromises()

    expect(fetchMock.mock.calls.filter(([r]) => r.method === 'DELETE')).toHaveLength(1)
  })
})
