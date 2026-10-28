import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makeCatalog, makePlan, makePlanSettings } from '@/test/fixtures'
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

const PAGE = '/schede/1/preferenze'
const PUT = '/api/plans/1/preferences'

const routes = (extra: Routes = {}): Routes => ({
  '/api/catalog': () => jsonResponse(makeCatalog()),
  'GET /api/plans/1/settings': () => jsonResponse(makePlanSettings()),
  'GET /api/plans/1': () => jsonResponse(makePlan()),
  'PUT /api/plans/1/preferences': () => jsonResponse(makePlan({ revision: 5 })),
  ...extra,
})

const muscleRows = (wrapper: VueWrapper) => wrapper.findAll('[data-testid="muscle-override"]')

/** Esce dalla pagina: il salvataggio in attesa parte subito (wireframe, principio 4). */
async function leave(wrapper: VueWrapper, router: { push: (to: string) => Promise<unknown> }) {
  await router.push('/schede/1')
  await flushPromises()
  return wrapper
}

const putHeaders = (fetchMock: ReturnType<typeof stubFetch>) =>
  fetchMock.mock.calls
    .map(([r]) => r)
    .filter((r) => r.method === 'PUT')
    .map((r) => r.headers.get('If-Match'))

describe('PlanPreferencesPage (US-11)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    vi.useRealTimers()
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('mostra attrezzi, durata e i valori effettivi, con le personalizzazioni segnate', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt(PAGE)

    expect(wrapper.text()).toContain('Preferenze di «PPL autunno»')
    expect(wrapper.findAll('[data-testid="equipment"]').map((e) => e.text())).toEqual([
      '1Macchina',
      '2Cavi',
      '3Pesi liberi',
    ])
    const [upper, mid] = muscleRows(wrapper)
    expect(upper?.classes()).not.toContain('custom')
    expect(mid?.classes()).toContain('custom')
    expect(mid?.text()).toContain('Catalogo: Prioritario, 10–18')
    const max = mid?.get('[data-testid="muscle-max"] input').element as HTMLInputElement
    expect(max.value).toBe('14')
  })

  it('salva da solo dopo una pausa, con la revisione della vista', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt(PAGE)

    await wrapper.findAll('[data-testid="equipment-down"]')[0]?.trigger('click')
    expect(wrapper.get('[data-testid="save-status"]').text()).toBe('Modifiche in attesa…')
    await vi.advanceTimersByTimeAsync(700)
    await flushPromises()

    expect(await requestBodies(fetchMock, 'PUT', PUT)).toEqual([
      {
        version: 2,
        equipment_order: ['cable', 'machine', 'free-weight'],
        max_session_minutes: 75,
        overrides: { muscles: { 'chest-mid': { weekly_max: 14 } }, tags: {} },
      },
    ])
    expect(putHeaders(fetchMock)).toEqual(['"4"'])
    expect(wrapper.get('[data-testid="save-status"]').text()).toBe('Salvato')
  })

  it('le modifiche successive usano la nuova revisione', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt(PAGE)

    await wrapper.findAll('[data-testid="equipment-down"]')[0]?.trigger('click')
    await vi.advanceTimersByTimeAsync(700)
    await wrapper.findAll('[data-testid="equipment-down"]')[0]?.trigger('click')
    await vi.advanceTimersByTimeAsync(700)
    await flushPromises()

    expect(putHeaders(fetchMock)).toEqual(['"4"', '"5"'])
  })

  it('personalizza e ripristina un muscolo; uscendo salva subito', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper, router } = await mountAt(PAGE)

    await chooseOption(wrapper, 'muscle-priority', 'Nessun obiettivo')
    expect(
      muscleRows(wrapper)[0]?.get('[data-testid="muscle-min"] input').attributes(),
    ).toHaveProperty('disabled')
    await muscleRows(wrapper)[1]?.get('[data-testid="muscle-reset"]').trigger('click')
    await leave(wrapper, router)

    const [body] = await requestBodies(fetchMock, 'PUT', PUT)
    expect(body).toMatchObject({
      overrides: { muscles: { 'chest-upper': { priority: 'none' } }, tags: {} },
    })
  })

  it('i punti dell’etichetta valgono solo con bonus e penalità', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper, router } = await mountAt(PAGE)

    const caution = wrapper.findAll('[data-testid="tag-override"]')[1]
    await caution?.get('[data-testid="tag-points"] input').setValue('1')
    await flushPromises()
    expect(caution?.classes()).toContain('custom')
    expect(caution?.text()).toContain('Catalogo: Penalità 3')
    await leave(wrapper, router)

    const [body] = await requestBodies(fetchMock, 'PUT', PUT)
    expect(body).toMatchObject({ overrides: { tags: { 'neck-caution': { points: 1 } } } })
  })

  it('mostra l’errore del server accanto al campo e chiede prima di uscire', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    stubFetch(
      routes({
        'PUT /api/plans/1/preferences': () =>
          jsonResponse(
            {
              status: 422,
              code: 'rule-violation',
              title: 'Regola violata',
              violations: [
                {
                  rule: 'band-order',
                  field: 'overrides.muscles.chest-mid.weekly_max',
                  message: 'Il massimo deve essere maggiore del minimo.',
                },
              ],
            },
            422,
          ),
      }),
    )
    const { wrapper, router } = await mountAt(PAGE)

    await muscleRows(wrapper)[1]?.get('[data-testid="muscle-max"] input').setValue('8')
    await vi.advanceTimersByTimeAsync(700)
    await flushPromises()

    expect(muscleRows(wrapper)[1]?.text()).toContain('Il massimo deve essere maggiore del minimo.')
    expect(wrapper.get('[data-testid="save-status"]').text()).toBe('Non salvato')

    const leaving = router.push('/schede/1')
    await flushPromises()
    expect(inBody('.n-dialog')[0]?.text()).toContain('Uscire senza salvare?')
    await dialogButton('Resta').trigger('click')
    await leaving
    expect(router.currentRoute.value.path).toBe(PAGE)
  })

  it('se la scheda è cambiata altrove ricarica i valori del server', async () => {
    const fetchMock = stubFetch(
      routes({
        'PUT /api/plans/1/preferences': () =>
          jsonResponse(
            { status: 412, code: 'precondition-failed', title: 'Cambiata', current_revision: 6 },
            412,
          ),
      }),
    )
    const { wrapper, router } = await mountAt(PAGE)

    await wrapper.findAll('[data-testid="equipment-down"]')[0]?.trigger('click')
    await router.push('/schede/1')
    await flushPromises()

    expect(document.body.textContent).toContain('La scheda è cambiata su un altro dispositivo')
    expect(router.currentRoute.value.path).toBe('/schede/1')
    const loads = fetchMock.mock.calls.filter(
      ([r]) => r.method === 'GET' && new URL(r.url).pathname === '/api/plans/1/settings',
    )
    expect(loads).toHaveLength(2)
  })

  it('«Solo personalizzati» lascia le righe personalizzate', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt(PAGE)

    await wrapper.get('[data-testid="only-customized"]').trigger('click')

    expect(muscleRows(wrapper)).toHaveLength(1)
    expect(wrapper.findAll('[data-testid="tag-override"]')).toHaveLength(0)
  })

  it('una scheda che non esiste', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/9/preferenze')

    expect(wrapper.text()).toContain('Scheda non trovata.')
  })
})
