import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makeCatalog, makeDetail } from '@/test/fixtures'
import { mountAt, setMobile, stubFetch } from '@/test/mount'

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
})
