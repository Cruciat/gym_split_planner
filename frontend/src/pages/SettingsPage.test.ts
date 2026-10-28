import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makeSettings } from '@/test/fixtures'
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
  '/api/health': () => jsonResponse({ status: 'ok', version: '0.5.0', database: 'ok' }),
  'GET /api/settings': () => jsonResponse(makeSettings()),
  'GET /api/settings/defaults': () => jsonResponse(makeSettings()),
  'PUT /api/settings': async (request) => jsonResponse(await request.json()),
  ...extra,
})

const input = (wrapper: VueWrapper, path: string, tag = 'input') =>
  wrapper.get(`[data-testid="setting-${path}"] ${tag}`)

async function type(wrapper: VueWrapper, path: string, value: string): Promise<void> {
  await input(wrapper, path).setValue(value)
  await input(wrapper, path).trigger('blur')
  await flushPromises()
}

const saveButton = (wrapper: VueWrapper) => wrapper.get('[data-testid="save-settings"]')

describe('SettingsPage (US-20; wireframe, § 5)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('mostra le impostazioni per gruppi, con i valori salvati', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/impostazioni')

    const legends = wrapper.findAll('legend').map((l) => l.text())
    expect(legends).toEqual(['Volume', 'Punteggio', 'Durata', 'Intensità', 'Riscaldamento'])
    expect((input(wrapper, 'level_weights.S').element as HTMLInputElement).value).toBe('0.5')
    expect((input(wrapper, 'session_cap').element as HTMLInputElement).value).toBe('10')
    expect((input(wrapper, 'effort.rir').element as HTMLInputElement).value).toBe('0-2')
    expect((input(wrapper, 'warmup_text', 'textarea').element as HTMLTextAreaElement).value).toBe(
      '5-10 minuti di cardio leggero',
    )
    expect(saveButton(wrapper).attributes('disabled')).toBeDefined()
  })

  it('salva tutte le impostazioni con il campo cambiato', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/impostazioni')

    await type(wrapper, 'session_cap', '12')
    await wrapper.get('[data-testid="setting-effort.failure_last_set"]').trigger('click')
    await wrapper.get('[data-testid="settings-form"]').trigger('submit')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'PUT', '/api/settings')).toEqual([
      { ...makeSettings(), session_cap: 12, effort: { rir: '0-2', failure_last_set: false } },
    ])
    expect(document.body.textContent).toContain('Impostazioni salvate.')
    expect(saveButton(wrapper).attributes('disabled')).toBeDefined()
  })

  it('mostra gli errori del server accanto ai campi e nel gruppo', async () => {
    stubFetch(
      routes({
        'PUT /api/settings': () =>
          jsonResponse(
            {
              status: 422,
              code: 'validation-error',
              title: 'Dati non validi',
              errors: [
                {
                  loc: ['body', 'level_weights'],
                  msg: 'Value error, Il peso di S non può superare quello di P',
                  type: 'value_error',
                },
                { loc: ['body', 'effort', 'rir'], msg: 'String should match', type: 'x' },
              ],
            },
            422,
          ),
      }),
    )
    const { wrapper } = await mountAt('/impostazioni')

    await type(wrapper, 'level_weights.S', '1.5')
    await wrapper.get('[data-testid="settings-form"]').trigger('submit')
    await flushPromises()

    expect(wrapper.get('[data-group="volume"]').text()).toContain(
      'Il peso di S non può superare quello di P',
    )
    expect(wrapper.get('[data-group="effort"]').text()).toContain('Valore non valido.')
  })

  it('«Ripristina predefiniti» porta i valori iniziali nella form, da salvare', async () => {
    const changed = { ...makeSettings(), session_cap: 6 }
    const fetchMock = stubFetch(routes({ 'GET /api/settings': () => jsonResponse(changed) }))
    const { wrapper } = await mountAt('/impostazioni')

    await wrapper.get('[data-testid="reset-defaults"]').trigger('click')
    await flushPromises()

    expect((input(wrapper, 'session_cap').element as HTMLInputElement).value).toBe('10')
    expect(fetchMock.mock.calls.some(([r]) => r.method === 'PUT')).toBe(false)
    expect(saveButton(wrapper).attributes('disabled')).toBeUndefined()
  })

  it('chiede prima di uscire con modifiche non salvate', async () => {
    stubFetch(routes())
    const { wrapper, router } = await mountAt('/impostazioni')

    await type(wrapper, 'session_cap', '12')
    const leaving = router.push('/catalogo')
    await flushPromises()
    expect(inBody('.n-dialog')[0]?.text()).toContain('Uscire senza salvare?')
    await dialogButton('Resta').trigger('click')
    await leaving

    expect(router.currentRoute.value.path).toBe('/impostazioni')
  })

  it('mostra versione e stato del database', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/impostazioni')

    const message = wrapper.get('[data-testid="health-ok"]')
    expect(message.text()).toContain('versione 0.5.0')
    expect(message.text()).toContain('database ok')
  })

  it('segnala un server che non risponde', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('rete'))),
    )

    const { wrapper } = await mountAt('/impostazioni')

    expect(wrapper.find('[data-testid="health-error"]').exists()).toBe(true)
  })
})
