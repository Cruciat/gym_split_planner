import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makeCatalog, makeDetail } from '@/test/fixtures'
import {
  dialogButton,
  inBody,
  mountAt,
  requestBodies,
  type Routes,
  setMobile,
  stubFetch,
} from '@/test/mount'

describe('ExerciseDetailPage', () => {
  beforeEach(() => {
    setMobile(false)
    stubFetch({
      '/api/catalog': () => jsonResponse(makeCatalog()),
      '/api/exercises/4': () => jsonResponse(makeDetail()),
      '/api/exercises/6': () =>
        jsonResponse({ ...makeDetail(), id: 6, name: 'Estensione sopra la testa alla macchina' }),
    })
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('mostra attributi, muscoli, etichette, famiglie e fonti (US-02 CA1)', async () => {
    const { wrapper } = await mountAt('/catalogo/esercizi/4')

    const detail = wrapper.get('[data-testid="exercise-detail"]')
    expect(detail.find('h1').text()).toContain('Estensione sopra la testa ai cavi')
    expect(detail.text()).toContain('Isolamento')
    expect(detail.text()).toContain('Alto')
    expect(detail.text()).toContain('Solido')
    expect(detail.text()).toContain('Cavi')
    expect(detail.text()).toContain('(barra o corda)')
    expect(wrapper.get('[data-testid="detail-status"]').text()).toBe('Attivo')
    expect(wrapper.get('[data-testid="detail-muscles"]').text()).toMatch(
      /^P\s*Capo lungo \(in allungamento\)$/,
    )
    expect(wrapper.get('[data-testid="detail-tags"]').text()).toContain(
      'Collo: attenzione — Schiena appoggiata',
    )
    expect(wrapper.get('[data-testid="detail-families"]').text()).toContain(
      'Estensione sopra la testa (principale, 1° nella famiglia)',
    )
    const source = wrapper.get('[data-testid="detail-sources"] a')
    expect(source.text()).toContain('Haugen et al. 2023')
    expect(source.attributes('href')).toBe('https://example.org/haugen')
    expect(source.attributes('target')).toBe('_blank')
    expect(detail.text()).toContain('Gomito sopra la testa.')
  })

  it('dalle varianti si passa al loro dettaglio (US-02 CA2)', async () => {
    const { wrapper, router } = await mountAt('/catalogo/esercizi/4')

    const link = wrapper.get('[data-testid="detail-variants"] a')
    expect(link.text()).toBe('Estensione sopra la testa alla macchina')
    await link.trigger('click')

    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/catalogo/esercizi/6')
      expect(wrapper.get('h1').text()).toContain('Estensione sopra la testa alla macchina')
    })
  })

  it('dice quando l esercizio non esiste', async () => {
    const { wrapper } = await mountAt('/catalogo/esercizi/999')

    expect(wrapper.find('[data-testid="detail-not-found"]').exists()).toBe(true)
  })

  it('un id non numerico è una pagina inesistente', async () => {
    const { wrapper } = await mountAt('/catalogo/esercizi/abc')

    expect(wrapper.text()).toContain('Pagina non trovata')
  })

  describe('azioni (US-05)', () => {
    const routes = (extra: Routes = {}): Routes => ({
      '/api/catalog': () => jsonResponse(makeCatalog()),
      'GET /api/exercises/4': () => jsonResponse(makeDetail()),
      'PUT /api/exercises/4': async (request) =>
        jsonResponse({ ...makeDetail(), ...((await request.json()) as object) }),
      'GET /api/exercises/4/usage': () => jsonResponse({ plans: [] }),
      'DELETE /api/exercises/4': () => new Response(null, { status: 204 }),
      ...extra,
    })

    it('Modifica apre la form', async () => {
      stubFetch(routes())
      const { wrapper, router } = await mountAt('/catalogo/esercizi/4')

      await wrapper.get('[data-testid="edit-exercise"]').trigger('click')

      await vi.waitFor(() => {
        expect(router.currentRoute.value.path).toBe('/catalogo/esercizi/4/modifica')
      })
    })

    it('disattiva e riattiva con un PUT di tutti i campi', async () => {
      const fetchMock = stubFetch(routes())
      const { wrapper } = await mountAt('/catalogo/esercizi/4')

      await wrapper.get('[data-testid="toggle-active"]').trigger('click')
      await vi.waitFor(() => {
        expect(wrapper.get('[data-testid="detail-status"]').text()).toBe('Disattivato')
      })
      expect(wrapper.get('[data-testid="toggle-active"]').text()).toBe('Riattiva')

      const [body] = await requestBodies(fetchMock, 'PUT', '/api/exercises/4')
      expect(body).toMatchObject({
        name: 'Estensione sopra la testa ai cavi',
        is_active: false,
        muscles: [{ muscle_id: 3, level: 'P', note: 'in allungamento' }],
        source_ids: [1],
      })
    })

    it('elimina un esercizio mai usato dopo la conferma (US-05 CA2)', async () => {
      const fetchMock = stubFetch(routes())
      const { wrapper, router } = await mountAt('/catalogo/esercizi/4')

      await wrapper.get('[data-testid="delete-exercise"]').trigger('click')
      await flushPromises()
      expect(inBody('.n-dialog')[0]?.text()).toContain('non è usato in nessuna scheda')

      await dialogButton('Elimina esercizio').trigger('click')

      await vi.waitFor(() => {
        expect(router.currentRoute.value.path).toBe('/catalogo')
      })
      const deletes = fetchMock.mock.calls.filter(([r]) => r.method === 'DELETE')
      expect(deletes).toHaveLength(1)
    })

    it('un esercizio usato si può solo disattivare (US-05 CA1)', async () => {
      const fetchMock = stubFetch(
        routes({
          'GET /api/exercises/4/usage': () =>
            jsonResponse({ plans: [{ id: 1, name: 'PPL autunno', slots: 2 }] }),
        }),
      )
      const { wrapper, router } = await mountAt('/catalogo/esercizi/4')

      await wrapper.get('[data-testid="delete-exercise"]').trigger('click')
      await flushPromises()
      expect(inBody('.n-dialog')[0]?.text()).toContain('«PPL autunno» lo usa')

      await dialogButton('Disattiva').trigger('click')

      await vi.waitFor(async () => {
        expect(await requestBodies(fetchMock, 'PUT', '/api/exercises/4')).toEqual([
          expect.objectContaining({ is_active: false }),
        ])
      })
      expect(fetchMock.mock.calls.some(([r]) => r.method === 'DELETE')).toBe(false)
      expect(router.currentRoute.value.path).toBe('/catalogo/esercizi/4')
    })
  })
})
