import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makeCatalog } from '@/test/fixtures'
import { chooseOption, inBody, mountAt, requestBodies, setMobile, stubFetch } from '@/test/mount'

const rowNames = (wrapper: Awaited<ReturnType<typeof mountAt>>['wrapper']) =>
  wrapper.findAll('[data-testid="exercise-table"] tbody tr .name-link').map((a) => a.text())

describe('CatalogPage', () => {
  beforeEach(() => {
    setMobile(false)
    stubFetch({ '/api/catalog': () => jsonResponse(makeCatalog()) })
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('mostra gli esercizi attivi con gruppo, famiglia, attrezzo e confidenza (US-01 CA1)', async () => {
    const { wrapper } = await mountAt('/catalogo')

    expect(rowNames(wrapper)).toEqual([
      'Chest press inclinata',
      'Panca inclinata a 30°',
      'Chest press seduta',
      'Estensione sopra la testa ai cavi',
    ])
    const first = wrapper.findAll('[data-testid="exercise-table"] tbody tr')[0]
    expect(first?.text()).toContain('Petto')
    expect(first?.text()).toContain('Spinta inclinata')
    expect(first?.text()).toContain('Macchina')
    expect(first?.text()).toContain('Limitato')
    expect(wrapper.get('[data-testid="catalog-count"]').text()).toBe('4 esercizi')
  })

  it('mostra i simboli delle etichette con nome e nota', async () => {
    const { wrapper } = await mountAt('/catalogo')

    const badges = wrapper.findAll('[data-testid="badge-neck-caution"]')
    expect(badges).toHaveLength(2)
    expect(badges[1]?.attributes('aria-label')).toBe('Collo: attenzione: Schiena appoggiata')
  })

  it("applica i filtri letti dall'URL (US-01 CA3)", async () => {
    const { wrapper } = await mountAt(
      '/catalogo?muscolo=chest-upper&livello=S&etichetta=neck-caution&senza=1',
    )

    expect(rowNames(wrapper)).toEqual(['Chest press inclinata', 'Chest press seduta'])
    expect(wrapper.get('[data-testid="catalog-count"]').text()).toBe('2 di 4 esercizi')
  })

  it("scrive i filtri nell'URL mentre si cerca", async () => {
    const { wrapper, router } = await mountAt('/catalogo')

    await wrapper.get('[data-testid="filter-search"] input').setValue('panca')
    await flushPromises()

    expect(router.currentRoute.value.query).toEqual({ cerca: 'panca' })
    expect(rowNames(wrapper)).toEqual(['Panca inclinata a 30°'])
  })

  it('mostra i disattivati solo con il filtro (US-01 CA4)', async () => {
    const { wrapper, router } = await mountAt('/catalogo')

    await wrapper.get('[data-testid="filter-inactive"]').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.query).toEqual({ disattivati: '1' })
    expect(rowNames(wrapper)).toContain('Estensione katana')
    expect(wrapper.text()).toContain('disattivato')
  })

  it("azzera i filtri e segue l'indietro del browser", async () => {
    const { wrapper, router } = await mountAt('/catalogo?attrezzo=cable')
    expect(rowNames(wrapper)).toEqual(['Estensione sopra la testa ai cavi'])

    await wrapper.get('[data-testid="filter-reset"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.query).toEqual({})
    expect(rowNames(wrapper)).toHaveLength(4)

    await router.push('/catalogo?gruppo=triceps')
    await flushPromises()
    expect(rowNames(wrapper)).toEqual(['Estensione sopra la testa ai cavi'])
  })

  it('dice quando nessun esercizio corrisponde', async () => {
    const { wrapper } = await mountAt('/catalogo?cerca=inesistente')

    expect(wrapper.text()).toContain('Nessun esercizio corrisponde ai filtri.')
  })

  it('apre il dettaglio toccando una riga', async () => {
    const { wrapper, router } = await mountAt('/catalogo')

    await wrapper.findAll('[data-testid="exercise-table"] tbody tr')[3]?.trigger('click')

    // La pagina del dettaglio si carica al primo accesso: si aspetta la navigazione.
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/catalogo/esercizi/4')
    })
  })

  it('sul telefono mostra schede e il numero di filtri attivi (US-01 CA5)', async () => {
    setMobile(true)
    const { wrapper } = await mountAt('/catalogo?gruppo=chest&cerca=chest')

    expect(wrapper.find('[data-testid="exercise-table"]').exists()).toBe(false)
    const cards = wrapper.findAll('[data-testid="exercise-cards"] li')
    expect(cards.map((c) => c.text())).toEqual([
      expect.stringContaining('Chest press inclinata'),
      expect.stringContaining('Chest press seduta'),
    ])
    expect(cards[0]?.find('a').attributes('href')).toBe('/catalogo/esercizi/1')
    expect(wrapper.get('[data-testid="open-filters"]').text()).toBe('Filtri (2)')
  })

  it('Nuovo esercizio apre la form vuota (US-04)', async () => {
    const { wrapper, router } = await mountAt('/catalogo')

    await wrapper.get('[data-testid="new-exercise"]').trigger('click')

    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/catalogo/esercizi/nuovo')
    })
  })

  describe('selezione multipla (US-08 CA2)', () => {
    const usage = () => jsonResponse({ exercises: 3, plans_with_overrides: [] })

    it('assegna un etichetta, con nota, agli esercizi selezionati', async () => {
      const fetchMock = stubFetch({
        '/api/catalog': () => jsonResponse(makeCatalog()),
        'POST /api/tags/1/assign': usage,
      })
      const { wrapper } = await mountAt('/catalogo')

      await wrapper.get('[data-testid="toggle-select"]').trigger('click')
      const rows = wrapper.findAll('[data-testid="exercise-table"] tbody tr')
      await rows[0]?.trigger('click')
      await rows[2]?.trigger('click')
      expect(wrapper.get('[data-testid="selected-count"]').text()).toBe('2 selezionati')

      await wrapper.get('[data-testid="bulk-assign"]').trigger('click')
      await flushPromises()
      await chooseOption(wrapper, 'bulk-tag', 'Collo: accorgimento')
      await inBody('[data-testid="bulk-note"] input')[0]?.setValue('Testa appoggiata')
      await inBody('[data-testid="bulk-submit"]')[0]?.trigger('click')
      await flushPromises()

      expect(await requestBodies(fetchMock, 'POST', '/api/tags/1/assign')).toEqual([
        { exercise_ids: [1, 3], note: 'Testa appoggiata' },
      ])
      expect(wrapper.find('[data-testid="selected-count"]').exists()).toBe(false)
    })

    it('senza nota non la invia, e toglie un etichetta', async () => {
      const fetchMock = stubFetch({
        '/api/catalog': () => jsonResponse(makeCatalog()),
        'POST /api/tags/2/assign': usage,
        'POST /api/tags/2/unassign': usage,
      })
      const { wrapper } = await mountAt('/catalogo')

      await wrapper.get('[data-testid="toggle-select"]').trigger('click')
      await wrapper.findAll('[data-testid="exercise-table"] tbody tr')[1]?.trigger('click')
      await wrapper.get('[data-testid="bulk-unassign"]').trigger('click')
      await flushPromises()
      expect(inBody('[data-testid="bulk-note"]')).toHaveLength(0)
      await chooseOption(wrapper, 'bulk-tag', 'Collo: attenzione')
      await inBody('[data-testid="bulk-submit"]')[0]?.trigger('click')
      await flushPromises()

      expect(await requestBodies(fetchMock, 'POST', '/api/tags/2/unassign')).toEqual([
        { exercise_ids: [2] },
      ])
    })

    it('durante la selezione una riga non apre il dettaglio', async () => {
      const { wrapper, router } = await mountAt('/catalogo')

      await wrapper.get('[data-testid="toggle-select"]').trigger('click')
      await wrapper.findAll('[data-testid="exercise-table"] tbody tr')[0]?.trigger('click')
      await flushPromises()

      expect(router.currentRoute.value.path).toBe('/catalogo')
    })

    it('la selezione segue i filtri', async () => {
      const { wrapper } = await mountAt('/catalogo')

      await wrapper.get('[data-testid="toggle-select"]').trigger('click')
      const rows = wrapper.findAll('[data-testid="exercise-table"] tbody tr')
      await rows[0]?.trigger('click')
      await rows[3]?.trigger('click')
      await wrapper.get('[data-testid="filter-search"] input').setValue('estensione')
      await flushPromises()

      expect(wrapper.get('[data-testid="selected-count"]').text()).toBe('1 selezionato')
    })

    it('sul telefono toccare una scheda la seleziona', async () => {
      setMobile(true)
      const { wrapper, router } = await mountAt('/catalogo')

      await wrapper.get('[data-testid="toggle-select"]').trigger('click')
      await wrapper.findAll('[data-testid="exercise-cards"] a')[1]?.trigger('click')
      await flushPromises()

      expect(router.currentRoute.value.path).toBe('/catalogo')
      expect(wrapper.get('[data-testid="selected-count"]').text()).toBe('1 selezionato')
    })
  })

  it('segnala un catalogo che non si carica', async () => {
    stubFetch({ '/api/catalog': () => jsonResponse({ code: 'internal-error', title: 'x' }, 500) })

    const { wrapper } = await mountAt('/catalogo')

    expect(wrapper.find('[data-testid="catalog-error"]').exists()).toBe(true)
  })
})
