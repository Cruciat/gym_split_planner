import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Plan } from '@/api/client'
import { jsonResponse, makeCatalog, makeEditorPlan } from '@/test/fixtures'
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

const EDITS = [
  'PATCH /api/plans/1',
  'PATCH /api/plans/1/slots/100',
  'PATCH /api/plans/1/slots/101',
  'PATCH /api/plans/1/slots/200',
  'DELETE /api/plans/1/slots/101',
  'POST /api/plans/1/days',
  'POST /api/plans/1/days/10/slots',
  'PATCH /api/plans/1/days/10',
  'DELETE /api/plans/1/days/10',
  'PUT /api/plans/1/days/order',
  'PUT /api/plans/1/days/10/slots/order',
]

/** Server finto: ogni modifica restituisce la scheda con la revisione successiva. */
function routes(plan: Plan = makeEditorPlan(), extra: Routes = {}): Routes {
  let revision = plan.revision
  const edited = () => {
    revision += 1
    return jsonResponse({ ...plan, revision })
  }
  return {
    '/api/catalog': () => jsonResponse(makeCatalog()),
    'GET /api/plans/1': () => jsonResponse({ ...plan, revision }),
    ...Object.fromEntries(EDITS.map((key) => [key, edited])),
    ...extra,
  }
}

const calls = (fetchMock: ReturnType<typeof stubFetch>, method: string, path: string) =>
  fetchMock.mock.calls
    .map(([r]) => r)
    .filter((r) => r.method === method && new URL(r.url).pathname === path)

/** Sceglie una voce di un menu ⋮ aperto con il pulsante indicato. */
async function menu(wrapper: VueWrapper, testId: string, label: string, index = 0) {
  await wrapper.findAll(`[data-testid="${testId}"]`)[index]?.trigger('click')
  await flushPromises()
  const option = inBody('.n-dropdown-option-body')
    .filter((o) => o.text() === label)
    .at(-1)
  if (option === undefined) throw new Error(`Nessuna voce «${label}»`)
  await option.trigger('click')
  await flushPromises()
}

const slots = (wrapper: VueWrapper) => wrapper.findAll('[data-testid="slot"]')

describe('PlanEditorPage (US-13, US-15, US-16, US-21)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('mostra i giorni in schede e gli esercizi del primo (US-13 CA1, CA4)', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    expect(wrapper.findAll('[data-testid="day-tab"]').map((t) => t.text())).toEqual([
      'Push ×2',
      'Pull',
    ])
    expect(wrapper.get('[data-testid="day-meta"]').text()).toBe(
      '2 volte a settimana · ~61 / ~63 min',
    )
    const [first, second] = slots(wrapper)
    expect(first?.text()).toContain('Chest press inclinata')
    expect(first?.text()).toContain('Spinta inclinata')
    expect(second?.text()).toContain('2ª seduta: Estensione katana')
    expect(second?.find('[data-testid="badge-neck-caution"]').exists()).toBe(true)
    const sets = second?.get('[data-testid="slot-sets"] input').element as HTMLInputElement
    expect(sets.value).toBe('3')
    expect(wrapper.get('[data-testid="stretching"]').text()).toContain('Stretch allo stipite')
  })

  it('il giorno scelto resta nell’URL; lo slot vuoto dice perché', async () => {
    stubFetch(routes())
    const { wrapper, router } = await mountAt('/schede/1')

    await wrapper.findAll('[data-testid="day-tab"]')[1]?.trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.query.giorno).toBe('11')
    expect(slots(wrapper)[0]?.text()).toContain('nessun esercizio disponibile')
    expect(slots(wrapper)[0]?.text()).toContain('tutti esclusi da «Collo: attenzione»')
  })

  it('serie e ripetizioni si salvano all’uscita dal campo (US-16 CA1)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    const input = slots(wrapper)[0]?.get('[data-testid="slot-sets"] input')
    await input?.setValue('4')
    await input?.trigger('blur')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'PATCH', '/api/plans/1/slots/100')).toEqual([{ sets: 4 }])
    expect(calls(fetchMock, 'PATCH', '/api/plans/1/slots/100')[0]?.headers.get('If-Match')).toBe(
      '"4"',
    )
    expect(wrapper.get('[data-testid="save-status"]').text()).toBe('Salvato')
  })

  it('lucchetto, facoltativo, settimane alterne e nota (US-15, US-16 CA4)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await slots(wrapper)[0]?.get('[data-testid="slot-lock"]').trigger('click')
    await flushPromises()
    await menu(wrapper, 'slot-actions', 'Segna come facoltativo')
    await menu(wrapper, 'slot-actions', 'A settimane alterne')
    await menu(wrapper, 'slot-actions', 'Nota')
    await inBody('[data-testid="text-input"] textarea')[0]?.setValue('Presa stretta')
    await inBody('[data-testid="text-save"]')[0]?.trigger('click')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'PATCH', '/api/plans/1/slots/100')).toEqual([
      { locked: true },
      { is_optional: true },
      { weekly_weight: 0.5 },
      { note: 'Presa stretta' },
    ])
    // Una alla volta, ognuna con la revisione della precedente.
    expect(
      calls(fetchMock, 'PATCH', '/api/plans/1/slots/100').map((r) => r.headers.get('If-Match')),
    ).toEqual(['"4"', '"5"', '"6"', '"7"'])
  })

  it('aggiunge un esercizio scegliendo prima la famiglia (US-16 CA3)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await wrapper.get('[data-testid="add-slot"]').trigger('click')
    await flushPromises()
    await chooseOption(wrapper, 'slot-family', 'Spinta orizzontale')
    await inBody('[data-testid="slot-save"]')[0]?.trigger('click')
    await flushPromises()
    await wrapper.get('[data-testid="add-slot"]').trigger('click')
    await flushPromises()
    await chooseOption(wrapper, 'slot-family', 'Spinta inclinata')
    await chooseOption(wrapper, 'slot-exercise', 'Panca inclinata a 30°')
    await inBody('[data-testid="slot-save"]').at(-1)?.trigger('click')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'POST', '/api/plans/1/days/10/slots')).toEqual([
      { family_id: 2 },
      { family_id: 1, exercise_id: 2 },
    ])
  })

  it('cambia famiglia ed elimina con conferma (US-16 CA3, CA5)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await menu(wrapper, 'slot-actions', 'Cambia famiglia', 1)
    await chooseOption(wrapper, 'slot-family', 'Spinta inclinata')
    await inBody('[data-testid="slot-save"]')[0]?.trigger('click')
    await flushPromises()
    await menu(wrapper, 'slot-actions', 'Elimina', 1)
    expect(inBody('.n-dialog')[0]?.text()).toContain(
      '«Estensione sopra la testa ai cavi» verrà tolto',
    )
    await dialogButton('Elimina esercizio').trigger('click')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'PATCH', '/api/plans/1/slots/101')).toEqual([
      { family_id: 1 },
    ])
    expect(calls(fetchMock, 'DELETE', '/api/plans/1/slots/101')).toHaveLength(1)
  })

  it('riordina gli esercizi con le frecce in modalità «Riordina» (US-16 CA2)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await menu(wrapper, 'day-actions', 'Riordina esercizi')
    await slots(wrapper)[1]?.get('[data-testid="slot-up"]').trigger('click')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'PUT', '/api/plans/1/days/10/slots/order')).toEqual([
      { slot_ids: [101, 100] },
    ])
  })

  it('aggiunge un giorno e sposta i giorni (US-21 CA1, CA2)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await wrapper.get('[data-testid="add-day"]').trigger('click')
    await flushPromises()
    await inBody('[data-testid="day-name"] input')[0]?.setValue('Legs')
    await inBody('[data-testid="day-save"]')[0]?.trigger('click')
    await flushPromises()
    // Il giorno nuovo diventa quello attivo: qui è l'ultimo, Pull, che va prima di Push.
    await menu(wrapper, 'day-actions', 'Sposta prima')

    expect(await requestBodies(fetchMock, 'POST', '/api/plans/1/days')).toEqual([
      { name: 'Legs', times_per_week: 1 },
    ])
    expect(await requestBodies(fetchMock, 'PUT', '/api/plans/1/days/order')).toEqual([
      { day_ids: [11, 10] },
    ])
  })

  it('scendere a una volta chiede conferma e dice quali varianti si perdono (US-21 CA3)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await menu(wrapper, 'day-actions', 'Rinomina e volte a settimana')
    await inBody('[data-testid="day-times"] input[value="1"]')[0]?.setValue(true)
    await inBody('[data-testid="day-save"]')[0]?.trigger('click')
    await flushPromises()

    expect(inBody('.n-dialog')[0]?.text()).toContain(
      '«Estensione katana» al posto di «Estensione sopra la testa ai cavi»',
    )
    await dialogButton('Cambia e togli le varianti').trigger('click')
    await flushPromises()
    expect(await requestBodies(fetchMock, 'PATCH', '/api/plans/1/days/10')).toEqual([
      { times_per_week: 1 },
    ])
  })

  it('elimina un giorno con esercizi solo dopo la conferma (US-21 CA4)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await menu(wrapper, 'day-actions', 'Elimina giorno')
    expect(inBody('.n-dialog')[0]?.text()).toContain('«Push» verrà eliminato con 2 esercizi')
    await dialogButton('Elimina giorno').trigger('click')
    await flushPromises()

    expect(calls(fetchMock, 'DELETE', '/api/plans/1/days/10')).toHaveLength(1)
  })

  it('rinomina la scheda', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await wrapper.get('[data-testid="rename-plan"]').trigger('click')
    await flushPromises()
    await inBody('[data-testid="text-input"] input')[0]?.setValue('PPL inverno')
    await inBody('[data-testid="text-save"]')[0]?.trigger('click')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'PATCH', '/api/plans/1')).toEqual([
      { name: 'PPL inverno' },
    ])
  })

  it('una scheda vuota propone il primo giorno', async () => {
    stubFetch(routes(makeEditorPlan({ days: [] })))
    const { wrapper } = await mountAt('/schede/1')

    expect(wrapper.get('[data-testid="empty-plan"]').text()).toContain(
      'Questa scheda non ha ancora giorni.',
    )
  })

  it('una scheda che non esiste', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/9')

    expect(wrapper.text()).toContain('Scheda non trovata.')
  })
})

describe('pannello del volume e avvisi (US-13 CA2, US-20)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('mostra i prioritari con stato a parole e personalizzazioni segnate', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    const rows = wrapper.findAll('[data-testid="volume-row"]').map((r) => r.text())
    expect(rows).toHaveLength(3)
    expect(rows[1]).toMatch(/Petto medio.*personalizzato.*sopra.*15.*10–14/)
    expect(rows[2]).toMatch(/Capo lungo.*sotto.*8/)
    expect(rows[0]).not.toMatch(/sotto|sopra/)
  })

  it('«Tutti» aggiunge i muscoli con obiettivo e quelli senza, a parte', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await chooseOption(wrapper, 'volume-filter', 'Tutti')

    expect(wrapper.text()).toContain('Quadricipiti')
    expect(wrapper.text()).toContain('Senza obiettivo (1)')
  })

  it('un avviso porta all’esercizio che lo causa', async () => {
    stubFetch(routes())
    const { wrapper, router } = await mountAt('/schede/1')

    const warnings = wrapper.findAll('[data-testid="warning"]')
    expect(warnings.map((w) => w.text())).toEqual([
      'Capo lungo sotto fascia (8 / 10–18)',
      'Pull, esercizio 1: nessun esercizio per «Spinta orizzontale»: tutti esclusi da «Collo: attenzione»',
    ])
    await warnings[1]?.trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.query.giorno).toBe('11')
    expect(slots(wrapper)[0]?.classes()).toContain('highlighted')
  })

  it('un avviso su un muscolo evidenzia la sua riga', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await wrapper.findAll('[data-testid="warning"]')[0]?.trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-muscle-id="3"]').classes()).toContain('highlighted')
  })
})

describe('salvataggio (US-19 CA3; API, § 4)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('con 412 ricarica e avvisa', async () => {
    const plan = makeEditorPlan()
    const fetchMock = stubFetch(
      routes(plan, {
        'PATCH /api/plans/1/slots/100': () =>
          jsonResponse(
            { status: 412, code: 'revision-mismatch', title: 'Cambiata', current_revision: 9 },
            412,
          ),
      }),
    )
    const { wrapper } = await mountAt('/schede/1')

    await slots(wrapper)[0]?.get('[data-testid="slot-lock"]').trigger('click')
    await flushPromises()

    expect(document.body.textContent).toContain(
      'La scheda è stata modificata da un altro dispositivo ed è stata ricaricata.',
    )
    expect(calls(fetchMock, 'GET', '/api/plans/1')).toHaveLength(2)
  })

  it('senza rete: «Non salvato» e «Riprova» rimanda la modifica', async () => {
    let offline = true
    const base = routes()
    const online = base['PATCH /api/plans/1/slots/100']
    if (online === undefined) throw new Error('percorso')
    const fetchMock = stubFetch({
      ...base,
      'PATCH /api/plans/1/slots/100': (request) =>
        offline ? Promise.reject(new TypeError('rete')) : online(request),
    })
    const { wrapper } = await mountAt('/schede/1')

    await slots(wrapper)[0]?.get('[data-testid="slot-lock"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('[data-testid="save-status"]').text()).toBe('Non salvato')

    offline = false
    await wrapper.get('[data-testid="retry"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="save-status"]').text()).toBe('Salvato')
    expect(await requestBodies(fetchMock, 'PATCH', '/api/plans/1/slots/100')).toEqual([
      { locked: true },
      { locked: true },
    ])
  })

  it('uscire con modifiche non inviate chiede conferma', async () => {
    stubFetch({
      ...routes(),
      'PATCH /api/plans/1/slots/100': () => Promise.reject(new TypeError('rete')),
    })
    const { wrapper, router } = await mountAt('/schede/1')

    await slots(wrapper)[0]?.get('[data-testid="slot-lock"]').trigger('click')
    await flushPromises()
    const leaving = router.push('/schede')
    await flushPromises()
    expect(inBody('.n-dialog')[0]?.text()).toContain('Uscire con modifiche non salvate?')
    await dialogButton('Resta').trigger('click')
    await leaving

    expect(router.currentRoute.value.path).toBe('/schede/1')
  })
})

describe('editor sul telefono (wireframe, § 3.7)', () => {
  beforeEach(() => {
    setMobile(true)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('barra del riassunto che apre il pannello a tutto schermo', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    expect(wrapper.find('aside').exists()).toBe(false)
    const bar = wrapper.get('[data-testid="volume-summary"]')
    expect(bar.text()).toBe('↓1 sotto · ↑1 sopra · 2 avvisi')
    await bar.trigger('click')
    await flushPromises()

    expect(inBody('[data-testid="volume-panel"]')).toHaveLength(1)
  })

  it('toccare un esercizio apre il foglio con campi e azioni', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    expect(slots(wrapper)[0]?.find('[data-testid="slot-sets"]').exists()).toBe(false)
    await slots(wrapper)[0]?.get('[data-testid="slot-main"]').trigger('click')
    await flushPromises()
    const input = inBody('[data-testid="sheet-sets"] input')[0]
    await input?.setValue('5')
    await input?.trigger('blur')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'PATCH', '/api/plans/1/slots/100')).toEqual([{ sets: 5 }])
  })

  it('le maniglie per trascinare compaiono solo in modalità «Riordina»', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    expect(wrapper.find('.drag-handle').exists()).toBe(false)
    await menu(wrapper, 'day-actions', 'Riordina esercizi')

    expect(wrapper.findAll('.drag-handle')).toHaveLength(2)
    expect(wrapper.find('[data-testid="slot-up"]').exists()).toBe(true)
  })
})
