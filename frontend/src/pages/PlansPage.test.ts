import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makePlan, makePlanSummaries } from '@/test/fixtures'
import {
  dialogButton,
  inBody,
  mountAt,
  requestBodies,
  type Routes,
  setMobile,
  stubFetch,
} from '@/test/mount'

const routes = (extra: Routes = {}): Routes => ({
  'GET /api/plans': () => jsonResponse(makePlanSummaries()),
  'GET /api/plans/1': () => jsonResponse(makePlan()),
  'PATCH /api/plans/2': async (request) =>
    jsonResponse(makePlan({ id: 2, ...((await request.json()) as object) })),
  'POST /api/plans/2/duplicate': () =>
    jsonResponse(makePlan({ id: 3, name: 'Prova vuota (copia)' }), 201),
  'POST /api/plans/2/activate': () => jsonResponse(makePlan({ id: 2 })),
  'DELETE /api/plans/2': () => new Response(null, { status: 204 }),
  ...extra,
})

/** Apre il menu ⋮ di una scheda e sceglie un'azione. */
async function chooseAction(wrapper: VueWrapper, index: number, label: string): Promise<void> {
  await wrapper.findAll('[data-testid="plan-actions"]')[index]?.trigger('click')
  await flushPromises()
  // L'ultimo menu aperto è in fondo al `body`; il clic è sul corpo dell'opzione.
  const option = inBody('.n-dropdown-option-body')
    .filter((o) => o.text() === label)
    .at(-1)
  if (option === undefined) throw new Error(`Nessuna azione «${label}»`)
  await option.trigger('click')
  await flushPromises()
}

const calls = (fetchMock: ReturnType<typeof stubFetch>, method: string, path: string) =>
  fetchMock.mock.calls.filter(([r]) => r.method === method && new URL(r.url).pathname === path)

describe('PlansPage (US-19)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('elenca le schede con split, giorni, data e scheda attiva (CA1)', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede')

    const rows = wrapper.findAll('[data-testid="plan"]')
    expect(rows).toHaveLength(2)
    expect(rows[0]?.text()).toMatch(
      /PPL autunno.*attiva.*modificata il 28\/10\/2026.*Push\/Pull\/Legs, 3 giorni · 3 giorni/,
    )
    expect(rows[0]?.classes()).toContain('active')
    expect(rows[1]?.text()).toContain('Scheda vuota · 1 giorno')
    expect(rows[1]?.text()).not.toContain('attiva')
    expect(rows[1]?.get('a').attributes('href')).toBe('/schede/2')
  })

  it('senza schede propone di creare la prima', async () => {
    stubFetch(routes({ 'GET /api/plans': () => jsonResponse([]) }))
    const { wrapper, router } = await mountAt('/schede')

    expect(wrapper.get('[data-testid="no-plans"]').text()).toContain('Nessuna scheda.')
    await wrapper.get('[data-testid="create-first"]').trigger('click')
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/schede/nuova')
    })
  })

  it('rinomina con la revisione della scheda (CA2)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede')

    await chooseAction(wrapper, 1, 'Rinomina')
    const input = inBody('[data-testid="rename-input"] input')[0]
    await input?.setValue('Upper/Lower prova')
    await inBody('[data-testid="rename-save"]')[0]?.trigger('click')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'PATCH', '/api/plans/2')).toEqual([
      { name: 'Upper/Lower prova' },
    ])
    expect(calls(fetchMock, 'PATCH', '/api/plans/2')[0]?.[0].headers.get('If-Match')).toBe('"1"')
    expect(calls(fetchMock, 'GET', '/api/plans')).toHaveLength(2)
  })

  it('un nome vuoto non parte', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede')

    await chooseAction(wrapper, 1, 'Rinomina')
    await inBody('[data-testid="rename-input"] input')[0]?.setValue('  ')
    await inBody('[data-testid="rename-save"]')[0]?.trigger('click')
    await flushPromises()

    expect(inBody('[data-testid="rename-dialog"]')[0]?.text()).toContain('Serve un nome.')
    expect(calls(fetchMock, 'PATCH', '/api/plans/2')).toHaveLength(0)
  })

  it('se la scheda è cambiata altrove ricarica l’elenco', async () => {
    const fetchMock = stubFetch(
      routes({
        'PATCH /api/plans/2': () =>
          jsonResponse(
            { status: 412, code: 'precondition-failed', title: 'Cambiata', current_revision: 2 },
            412,
          ),
      }),
    )
    const { wrapper } = await mountAt('/schede')

    await chooseAction(wrapper, 1, 'Rinomina')
    await inBody('[data-testid="rename-input"] input')[0]?.setValue('Altro')
    await inBody('[data-testid="rename-save"]')[0]?.trigger('click')
    await flushPromises()

    expect(document.body.textContent).toContain('La scheda è cambiata su un altro dispositivo')
    expect(calls(fetchMock, 'GET', '/api/plans')).toHaveLength(2)
  })

  it('duplica e rende attiva (CA2)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede')

    await chooseAction(wrapper, 1, 'Duplica')
    expect(document.body.textContent).toContain('Creata «Prova vuota (copia)».')
    await chooseAction(wrapper, 1, 'Rendi attiva')

    expect(calls(fetchMock, 'POST', '/api/plans/2/duplicate')).toHaveLength(1)
    expect(calls(fetchMock, 'POST', '/api/plans/2/activate')).toHaveLength(1)
    expect(calls(fetchMock, 'GET', '/api/plans')).toHaveLength(3)
  })

  it('la scheda già attiva non si può rendere attiva', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede')

    await wrapper.findAll('[data-testid="plan-actions"]')[0]?.trigger('click')
    await flushPromises()

    const option = inBody('.n-dropdown-option-body').find((o) => o.text() === 'Rendi attiva')
    expect(option?.classes()).toContain('n-dropdown-option-body--disabled')
  })

  it('elimina solo dopo la conferma (CA2)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede')

    await chooseAction(wrapper, 1, 'Elimina')
    expect(inBody('.n-dialog')[0]?.text()).toContain('«Prova vuota» verrà eliminata')
    await dialogButton('Annulla').trigger('click')
    await flushPromises()
    expect(calls(fetchMock, 'DELETE', '/api/plans/2')).toHaveLength(0)

    await chooseAction(wrapper, 1, 'Elimina')
    await dialogButton('Elimina scheda').trigger('click')
    await flushPromises()
    expect(calls(fetchMock, 'DELETE', '/api/plans/2')).toHaveLength(1)
  })

  it('su telefono le azioni restano nel menu', async () => {
    setMobile(true)
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede')

    expect(wrapper.findAll('[data-testid="plan-actions"]')).toHaveLength(2)
  })
})

describe('apertura dell’app (wireframe, principio 1)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('/ apre la scheda attiva', async () => {
    stubFetch(routes())
    const { wrapper, router } = await mountAt('/')

    expect(router.currentRoute.value.path).toBe('/schede/1')
    expect(wrapper.get('[data-testid="plan-name"]').text()).toBe('PPL autunno')
  })

  it('/ apre l’elenco se non c’è una scheda attiva', async () => {
    const plans = makePlanSummaries().map((p) => ({ ...p, is_active: false }))
    stubFetch(routes({ 'GET /api/plans': () => jsonResponse(plans) }))
    const { router } = await mountAt('/')

    expect(router.currentRoute.value.path).toBe('/schede')
  })

  it('/ apre l’elenco se il server non risponde', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('rete'))),
    )
    const { wrapper, router } = await mountAt('/')

    expect(router.currentRoute.value.path).toBe('/schede')
    expect(wrapper.text()).toContain('Impossibile caricare i dati dal server.')
  })
})
