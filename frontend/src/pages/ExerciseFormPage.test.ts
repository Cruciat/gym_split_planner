import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makeCatalog, makeDetail } from '@/test/fixtures'
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
  'GET /api/exercises/4': () => jsonResponse(makeDetail()),
  'PUT /api/exercises/4': async (request) =>
    jsonResponse({ ...makeDetail(), ...((await request.json()) as object) }),
  'POST /api/exercises': async (request) =>
    jsonResponse({ ...makeDetail(), ...((await request.json()) as object), id: 7 }, 201),
  'GET /api/exercises/7': () => jsonResponse({ ...makeDetail(), id: 7 }),
  ...extra,
})

describe('ExerciseFormPage', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('modifica: parte dai valori attuali e invia tutti i campi (US-03)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper, router } = await mountAt('/catalogo/esercizi/4/modifica')

    expect(wrapper.get('h1').text()).toBe('Modifica · Estensione sopra la testa ai cavi')
    const name = wrapper.get<HTMLInputElement>('[data-testid="field-name"] input')
    expect(name.element.value).toBe('Estensione sopra la testa ai cavi')
    expect(wrapper.get('[data-testid="muscle-triceps-long"]').attributes('aria-label')).toBe(
      'Tricipite, capo lungo: primario',
    )

    await name.setValue('Estensione ai cavi')
    await wrapper.get('[data-testid="muscle-chest-upper"]').trigger('click')
    await wrapper.get('[data-testid="save"]').trigger('submit')
    await flushPromises()

    const [body] = await requestBodies(fetchMock, 'PUT', '/api/exercises/4')
    expect(body).toMatchObject({
      name: 'Estensione ai cavi',
      primary_family_id: 3,
      equipment_detail: 'barra o corda',
      is_active: true,
      muscles: [
        { muscle_id: 3, level: 'P', note: 'in allungamento' },
        { muscle_id: 1, level: 'S', note: null },
      ],
      tags: [{ tag_id: 2, note: 'Schiena appoggiata' }],
      source_ids: [1],
    })
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/catalogo/esercizi/4')
    })
  })

  it('nuovo: segnala subito i campi mancanti senza chiamare il server', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/esercizi/nuovo')

    expect(wrapper.get('h1').text()).toBe('Nuovo esercizio')
    await wrapper.get('[data-testid="save"]').trigger('submit')
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('Serve un nome.')
    expect(text).toContain('Scegli la famiglia principale.')
    expect(text).toContain('Scegli l’attrezzo.')
    expect(text).toContain('Serve almeno un muscolo P.')
    expect(await requestBodies(fetchMock, 'POST', '/api/exercises')).toEqual([])
  })

  it('nuovo: crea l esercizio in fondo alla sua famiglia (US-04)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper, router } = await mountAt('/catalogo/esercizi/nuovo')

    await wrapper.get('[data-testid="field-name"] input').setValue('Chest press convergente')
    await chooseOption(wrapper, 'field-family', 'Spinta inclinata')
    await chooseOption(wrapper, 'field-equipment', 'Macchina')
    const upper = wrapper.get('[data-testid="muscle-chest-upper"]')
    await upper.trigger('click')
    await upper.trigger('click')
    await wrapper.get('[data-testid="save"]').trigger('submit')
    await flushPromises()

    const [body] = await requestBodies(fetchMock, 'POST', '/api/exercises')
    expect(body).toEqual({
      name: 'Chest press convergente',
      primary_family_id: 1,
      secondary_family_id: null,
      family_rank: 3,
      equipment_id: 1,
      equipment_detail: null,
      kind: 'compound',
      stretch: 'medium',
      stretch_note: null,
      confidence: 'opinion',
      notes: null,
      is_active: true,
      muscles: [{ muscle_id: 1, level: 'P', note: null }],
      tags: [],
      source_ids: [],
    })
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/catalogo/esercizi/7')
    })
  })

  it('mostra le regole violate dal server accanto ai campi (API, § 3.1)', async () => {
    stubFetch(
      routes({
        'PUT /api/exercises/4': () =>
          jsonResponse(
            {
              status: 422,
              code: 'rule-violation',
              title: 'Dati non accettati',
              detail: 'Esiste già.',
              rule: 'name-taken',
              violations: [
                { rule: 'name-taken', field: 'name', message: 'Esiste già un esercizio così.' },
              ],
            },
            422,
          ),
      }),
    )
    const { wrapper, router } = await mountAt('/catalogo/esercizi/4/modifica')

    await wrapper.get('[data-testid="field-name"] input').setValue('Face pull')
    await wrapper.get('[data-testid="save"]').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Esiste già un esercizio così.')
    expect(router.currentRoute.value.path).toBe('/catalogo/esercizi/4/modifica')
  })

  it('aggiunge, annota e toglie le etichette', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/esercizi/4/modifica')

    await chooseOption(wrapper, 'add-tag', 'Collo: accorgimento')
    const rows = wrapper.findAll('[data-testid="tag-row"]')
    expect(rows.map((r) => r.text())).toEqual([
      expect.stringContaining('Collo: attenzione'),
      expect.stringContaining('Collo: accorgimento'),
    ])
    await rows[1]?.get('input').setValue('Testa appoggiata')
    await rows[0]?.get('button').trigger('click')
    await wrapper.get('[data-testid="save"]').trigger('submit')
    await flushPromises()

    const [body] = await requestBodies(fetchMock, 'PUT', '/api/exercises/4')
    expect((body as { tags: unknown }).tags).toEqual([{ tag_id: 1, note: 'Testa appoggiata' }])
  })

  it('crea una fonte nuova e la collega all esercizio', async () => {
    const newSource = {
      id: 9,
      code: 'src-49',
      title: 'Schoenfeld 2010',
      kind: 'Revisione',
      url: null,
      reliability: null,
      used_for: null,
    }
    const fetchMock = stubFetch(
      routes({
        'POST /api/sources': () => jsonResponse(newSource, 201),
        '/api/catalog': () => {
          const catalog = makeCatalog()
          return jsonResponse({ ...catalog, sources: [...catalog.sources, newSource] })
        },
      }),
    )
    const { wrapper } = await mountAt('/catalogo/esercizi/4/modifica')

    await wrapper.get('[data-testid="new-source"]').trigger('click')
    await flushPromises()
    const title = inBody('[data-testid="source-title"] input')[0]
    const kind = inBody('[data-testid="source-kind"] input')[0]
    await title?.setValue('Schoenfeld 2010')
    await kind?.setValue('Revisione')
    await inBody('[data-testid="source-save"]')[0]?.trigger('click')
    await flushPromises()
    await wrapper.get('[data-testid="save"]').trigger('submit')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'POST', '/api/sources')).toEqual([
      { title: 'Schoenfeld 2010', kind: 'Revisione', url: null, reliability: null },
    ])
    const [body] = await requestBodies(fetchMock, 'PUT', '/api/exercises/4')
    expect((body as { source_ids: unknown }).source_ids).toEqual([1, 9])
  })

  it('chiede conferma prima di uscire con modifiche non salvate', async () => {
    stubFetch(routes())
    const { wrapper, router } = await mountAt('/catalogo/esercizi/4/modifica')

    await wrapper.get('[data-testid="field-name"] input').setValue('Altro nome')
    void router.push('/catalogo')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/catalogo/esercizi/4/modifica')

    await dialogButton('Esci senza salvare').trigger('click')
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/catalogo')
    })
  })

  it('esce senza chiedere se nulla è cambiato', async () => {
    stubFetch(routes())
    const { router } = await mountAt('/catalogo/esercizi/4/modifica')

    await router.push('/catalogo')

    expect(router.currentRoute.value.path).toBe('/catalogo')
  })

  it('dice quando l esercizio da modificare non esiste', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/catalogo/esercizi/99/modifica')

    expect(wrapper.find('[data-testid="form-not-found"]').exists()).toBe(true)
  })
})
