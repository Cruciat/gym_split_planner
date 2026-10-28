import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Plan } from '@/api/client'
import type { Candidate, Candidates, RegenerationPreview } from '@/plans/editor'
import { jsonResponse, makeCatalog, makeEditorPlan } from '@/test/fixtures'
import {
  dialogButton,
  inBody,
  mountAt,
  requestBodies,
  type Routes,
  setMobile,
  stubFetch,
} from '@/test/mount'

const candidate = (fields: Partial<Candidate> & Pick<Candidate, 'exercise_id' | 'name'>) => ({
  code: `ex-${String(fields.exercise_id)}`,
  equipment: 'machine',
  family_match: 'primary' as const,
  score: 5,
  score_breakdown: {
    confidence: 1.8,
    equipment: 2.667,
    stretch: 0.2,
    family: 1,
    rank: 0.5,
    tags: 0,
  },
  badges: [],
  excluded_by: [],
  volume_delta: [],
  ...fields,
})

/** Candidati dello slot 100 (Chest press inclinata), prima e seconda seduta. */
function candidates(session: number, current: number | null): Candidates {
  const list =
    session === 1
      ? [
          candidate({ exercise_id: 1, name: 'Chest press inclinata', score: 6.17 }),
          candidate({
            exercise_id: 2,
            name: 'Panca inclinata a 30°',
            equipment: 'free-weight',
            score: 4.93,
            volume_delta: [{ muscle_id: 3, code: 'triceps-long', delta: 2 }],
          }),
          candidate({
            exercise_id: 3,
            name: 'Chest press seduta',
            score: 3,
            excluded_by: ['neck-caution'],
            volume_delta: [{ muscle_id: 2, code: 'chest-mid', delta: 1.5 }],
          }),
        ]
      : [
          candidate({ exercise_id: 1, name: 'Chest press inclinata' }),
          candidate({ exercise_id: 2, name: 'Panca inclinata a 30°' }),
          candidate({ exercise_id: 7, name: 'Croci ai cavi', family_match: 'other' }),
          candidate({ exercise_id: 8, name: 'Dip alle parallele', family_match: 'other' }),
        ]
  return { slot_id: 100, session, current_exercise_id: current, candidates: list }
}

function routes(plan: Plan = makeEditorPlan(), extra: Routes = {}): Routes {
  let revision = plan.revision
  const edited = () => {
    revision += 1
    return jsonResponse({ ...plan, revision })
  }
  return {
    '/api/catalog': () => jsonResponse(makeCatalog()),
    'GET /api/plans/1': () => jsonResponse({ ...plan, revision }),
    'GET /api/plans/1/slots/100/candidates': (request) => {
      const session = Number(new URL(request.url).searchParams.get('session'))
      return jsonResponse(candidates(session, session === 1 ? 1 : null))
    },
    'PATCH /api/plans/1/slots/100': edited,
    'POST /api/plans/1/regenerate': edited,
    ...extra,
  }
}

const panel = () => inBody('[data-testid="variants-panel"]').at(-1)
const choose = async (name: string) => {
  const button = inBody(`button[aria-label="Scegli ${name}"]`).at(-1)
  if (button === undefined) throw new Error(`Nessun candidato ${name}`)
  await button.trigger('click')
  await flushPromises()
}

async function openVariants(wrapper: VueWrapper): Promise<void> {
  await wrapper.findAll('[data-testid="open-variants"]')[0]?.trigger('click')
  await flushPromises()
}

async function openSecond(wrapper: VueWrapper): Promise<void> {
  await wrapper.findAll('[data-testid="slot-actions"]')[0]?.trigger('click')
  await flushPromises()
  await inBody('.n-dropdown-option-body')
    .filter((o) => o.text() === 'Variante per la seconda seduta')
    .at(-1)
    ?.trigger('click')
  await flushPromises()
}

describe('varianti (US-14; wireframe, § 3.4)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('elenca i candidati con attrezzo, punteggio ed effetto sul volume', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await openVariants(wrapper)

    const text = panel()?.text() ?? ''
    expect(text).toContain('Push · esercizio 1 · Spinta inclinata')
    expect(text).toContain('Attuale: Chest press inclinata')
    const items = inBody('[data-testid="candidate"]').map((c) => c.text())
    expect(items[0]).toMatch(/Chest press inclinata.*Macchina · Punteggio 6,17.*attuale/)
    expect(items[1]).toMatch(/Panca inclinata a 30°.*Pesi liberi · Punteggio 4,93/)
    // Capo lungo a 8 su 10-18: +2 avvicina alla fascia, quindi verde.
    const delta = inBody('[data-testid="delta"]')[0]
    expect(delta?.text()).toBe('Capo lungo +2')
    expect(delta?.classes()).toContain('closer')
  })

  it('«Perché?» mostra le voci del punteggio', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')
    await openVariants(wrapper)

    await inBody('[data-testid="candidate"] button')
      .filter((b) => b.text() === 'Perché?')[1]
      ?.trigger('click')
    await flushPromises()

    expect(inBody('[data-testid="breakdown"]')[0]?.text()).toMatch(
      /Confidenza1,8Attrezzo2,67Allungamento0,2Famiglia1Rango0,5Etichette0/,
    )
  })

  it('scegliere un candidato lo applica subito e il pannello resta aperto (CA2)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')
    await openVariants(wrapper)

    await choose('Panca inclinata a 30°')

    expect(await requestBodies(fetchMock, 'PATCH', '/api/plans/1/slots/100')).toEqual([
      { exercise_id: 2 },
    ])
    const loads = fetchMock.mock.calls.filter(([r]) => r.url.includes('/candidates'))
    expect(loads).toHaveLength(2)
    expect(panel()?.text()).toContain('Attuale:')
  })

  it('gli esclusi stanno in fondo con il motivo e chiedono conferma (CA3)', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')
    await openVariants(wrapper)

    expect(inBody('[data-testid="excluded"]')[0]?.text()).toContain(
      'Chest press seduta' + 'esclusa da «Collo: attenzione»',
    )
    await choose('Chest press seduta')
    expect(inBody('.n-dialog')[0]?.text()).toContain(
      '«Chest press seduta» è escluso dall’etichetta «Collo: attenzione». Usarlo lo stesso?',
    )
    await dialogButton('Usalo lo stesso').trigger('click')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'PATCH', '/api/plans/1/slots/100')).toEqual([
      { exercise_id: 3 },
    ])
  })
})

describe('seconda seduta (US-17)', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('propone «Nessuna variante», la famiglia senza l’esercizio principale, poi le altre', async () => {
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await openSecond(wrapper)

    expect(panel()?.text()).toContain('Seconda seduta · Push · esercizio 1')
    expect(inBody('[data-testid="no-variant"]')[0]?.attributes('aria-checked')).toBe('true')
    const names = inBody('[data-testid="candidate"] strong').map((n) => n.text())
    expect(names).toEqual(['Panca inclinata a 30°', 'Croci ai cavi', 'Dip alle parallele'])
  })

  it('cerca per nome nelle altre famiglie e sceglie', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')
    await openSecond(wrapper)

    await inBody('[data-testid="variants-search"] input')[0]?.setValue('croci')
    await flushPromises()
    const others = inBody('[data-testid="other-families"] [data-testid="candidate"]')
    expect(others.map((o) => o.text())).toEqual([expect.stringContaining('Croci ai cavi')])
    await choose('Croci ai cavi')

    expect(await requestBodies(fetchMock, 'PATCH', '/api/plans/1/slots/100')).toEqual([
      { second_exercise_id: 7 },
    ])
  })

  it('la voce non c’è nei giorni fatti una volta a settimana', async () => {
    const plan = makeEditorPlan()
    const push = plan.days[0]
    if (push === undefined) throw new Error('fixture')
    stubFetch(routes({ ...plan, days: [{ ...push, times_per_week: 1 }] }))
    const { wrapper } = await mountAt('/schede/1')

    await wrapper.findAll('[data-testid="slot-actions"]')[0]?.trigger('click')
    await flushPromises()

    const labels = inBody('.n-dropdown-option-body').map((o) => o.text())
    expect(labels).not.toContain('Variante per la seconda seduta')
  })

  it('sul telefono il foglio dell’esercizio apre varianti e seconda seduta', async () => {
    setMobile(true)
    stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await wrapper.findAll('[data-testid="slot-main"]')[0]?.trigger('click')
    await flushPromises()
    await inBody('[data-testid="sheet-second"]')[0]?.trigger('click')
    await flushPromises()

    expect(panel()?.text()).toContain('Seconda seduta')
  })
})

describe('rigenerazione (US-18; wireframe, § 3.6)', () => {
  const preview: RegenerationPreview = {
    revision: 4,
    locked_slots: 2,
    changes: [
      {
        slot_id: 100,
        day_id: 10,
        day_name: 'Push',
        position: 1,
        current: { exercise_id: 1, name: 'Chest press inclinata' },
        proposed: { exercise_id: 2, name: 'Panca inclinata a 30°' },
        volume_delta: [],
      },
      {
        slot_id: 101,
        day_id: 10,
        day_name: 'Push',
        position: 2,
        current: { exercise_id: 4, name: 'Estensione sopra la testa ai cavi' },
        proposed: { exercise_id: 6, name: 'Estensione sopra la testa alla macchina' },
        volume_delta: [{ muscle_id: 2, code: 'chest-mid', delta: 1 }],
      },
    ],
  }

  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  async function open(wrapper: VueWrapper): Promise<void> {
    await wrapper.get('[data-testid="regenerate"]').trigger('click')
    await flushPromises()
  }

  it('mostra le differenze, tutte scelte, e gli esercizi bloccati (CA1, CA2)', async () => {
    stubFetch(
      routes(undefined, { 'POST /api/plans/1/regenerate/preview': () => jsonResponse(preview) }),
    )
    const { wrapper } = await mountAt('/schede/1')

    await open(wrapper)

    const changes = inBody('[data-testid="change"]').map((c) => c.text())
    expect(changes[0]).toMatch(
      /Push · 1.*Chest press inclinata.*Panca inclinata a 30°.*nessun cambio/,
    )
    // Petto medio a 15 su 10-14: +1 allontana, in arancione.
    expect(inBody('[data-testid="change"] .chip.farther')[0]?.text()).toBe('Petto medio +1')
    expect(inBody('[data-testid="locked-note"]')[0]?.text()).toContain(
      'Gli esercizi con il lucchetto non vengono toccati (2).',
    )
    expect(inBody('[data-testid="apply-regeneration"]')[0]?.text()).toBe('Applica 2 modifiche')
  })

  it('applica solo le differenze spuntate, con la revisione dell’anteprima', async () => {
    const fetchMock = stubFetch(
      routes(undefined, { 'POST /api/plans/1/regenerate/preview': () => jsonResponse(preview) }),
    )
    const { wrapper } = await mountAt('/schede/1')
    await open(wrapper)

    await inBody('[data-testid="change-check"]')[1]?.trigger('click')
    await flushPromises()
    expect(inBody('[data-testid="apply-regeneration"]')[0]?.text()).toBe('Applica 1 modifica')
    await inBody('[data-testid="apply-regeneration"]')[0]?.trigger('click')
    await flushPromises()

    expect(await requestBodies(fetchMock, 'POST', '/api/plans/1/regenerate')).toEqual([
      { slot_ids: [100] },
    ])
    const request = fetchMock.mock.calls
      .map(([r]) => r)
      .find((r) => r.method === 'POST' && r.url.endsWith('/regenerate'))
    expect(request?.headers.get('If-Match')).toBe('"4"')
    expect(document.body.textContent).toContain('Rigenerato 1 esercizio.')
  })

  it('senza differenze lo dice', async () => {
    stubFetch(
      routes(undefined, {
        'POST /api/plans/1/regenerate/preview': () =>
          jsonResponse({ revision: 4, locked_slots: 0, changes: [] }),
      }),
    )
    const { wrapper } = await mountAt('/schede/1')

    await open(wrapper)

    expect(inBody('[data-testid="aligned"]')[0]?.text()).toBe(
      'La scheda è già allineata alle preferenze.',
    )
    expect(inBody('[data-testid="apply-regeneration"]')).toHaveLength(0)
  })
})
