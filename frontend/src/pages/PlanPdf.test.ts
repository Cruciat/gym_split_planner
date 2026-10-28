import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { filenameFrom } from '@/plans/pdf'
import { jsonResponse, makeCatalog, makeEditorPlan } from '@/test/fixtures'
import { inBody, mountAt, type Routes, setMobile, stubFetch } from '@/test/mount'

const pdfResponse = () =>
  new Response('%PDF-1.7 prova', {
    status: 200,
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': 'attachment; filename="ppl-autunno-2026-10-28.pdf"',
    },
  })

function routes(extra: Routes = {}): Routes {
  const plan = makeEditorPlan()
  return {
    '/api/catalog': () => jsonResponse(makeCatalog()),
    'GET /api/plans/1': () => jsonResponse(plan),
    'PATCH /api/plans/1/slots/100': () => jsonResponse({ ...plan, revision: plan.revision + 1 }),
    'GET /api/plans/1/pdf': pdfResponse,
    ...extra,
  }
}

/** Richieste del PDF, con le settimane chieste. */
const pdfWeeks = (fetchMock: ReturnType<typeof stubFetch>) =>
  fetchMock.mock.calls
    .map(([r]) => new URL(r.url))
    .filter((url) => url.pathname === '/api/plans/1/pdf')
    .map((url) => url.searchParams.get('weeks'))

describe('PDF dall’editor (US-30)', () => {
  let downloads: string[]

  beforeEach(() => {
    setMobile(false)
    downloads = []
    URL.createObjectURL = vi.fn(() => 'blob:prova')
    URL.revokeObjectURL = vi.fn()
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      downloads.push(this.download)
    })
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  async function click(wrapper: VueWrapper, testId: string): Promise<void> {
    await wrapper.get(`[data-testid="${testId}"]`).trigger('click')
    await flushPromises()
  }

  it('scarica il PDF con 4 settimane e il nome del server', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await click(wrapper, 'pdf')

    await vi.waitFor(() => {
      expect(downloads).toEqual(['ppl-autunno-2026-10-28.pdf'])
    })
    expect(pdfWeeks(fetchMock)).toEqual(['4'])
    await vi.waitFor(() => {
      expect(document.body.textContent).toContain('Scaricato «ppl-autunno-2026-10-28.pdf».')
    })
  })

  it('il menu accanto al pulsante sceglie le settimane', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await click(wrapper, 'pdf-weeks-menu')
    await inBody('.n-dropdown-option-body')
      .filter((o) => o.text() === '8 settimane')
      .at(-1)
      ?.trigger('click')
    await flushPromises()
    await click(wrapper, 'pdf')

    expect(pdfWeeks(fetchMock)).toEqual(['8', '8'])
  })

  it('prima invia le modifiche in coda, poi chiede il PDF', async () => {
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await wrapper.findAll('[data-testid="slot-lock"]')[0]?.trigger('click')
    await click(wrapper, 'pdf')

    const order = fetchMock.mock.calls
      .map(([r]) => `${r.method} ${new URL(r.url).pathname}`)
      .filter((call) => !call.startsWith('GET /api/plans/1') || call.endsWith('/pdf'))
      .filter((call) => call.includes('/plans/1/'))
    expect(order).toEqual(['PATCH /api/plans/1/slots/100', 'GET /api/plans/1/pdf'])
  })

  it('un errore del server compare come gli altri', async () => {
    stubFetch(
      routes({
        'GET /api/plans/1/pdf': () =>
          jsonResponse(
            { status: 404, code: 'not-found', title: 'Scheda non trovata', detail: 'Non esiste.' },
            404,
          ),
      }),
    )
    const { wrapper } = await mountAt('/schede/1')

    await click(wrapper, 'pdf')

    expect(downloads).toEqual([])
    expect(document.body.textContent).toContain('Scheda non trovata: Non esiste.')
  })

  it('sul telefono il menu apre la scelta delle settimane', async () => {
    setMobile(true)
    const fetchMock = stubFetch(routes())
    const { wrapper } = await mountAt('/schede/1')

    await click(wrapper, 'plan-menu')
    await inBody('.n-dropdown-option-body')
      .filter((o) => o.text() === 'PDF')
      .at(-1)
      ?.trigger('click')
    await flushPromises()
    await inBody('[data-testid="pdf-weeks"] input[value="2"]')[0]?.setValue(true)
    await inBody('[data-testid="pdf-download"]')[0]?.trigger('click')
    await flushPromises()

    await vi.waitFor(() => {
      expect(downloads).toEqual(['ppl-autunno-2026-10-28.pdf'])
    })
    expect(pdfWeeks(fetchMock)).toEqual(['2'])
  })
})

describe('nome del file', () => {
  it('lo prende da Content-Disposition, altrimenti usa quello di riserva', () => {
    expect(filenameFrom('attachment; filename="a-b.pdf"', 'x.pdf')).toBe('a-b.pdf')
    expect(filenameFrom('attachment; filename=a.pdf', 'x.pdf')).toBe('a.pdf')
    expect(filenameFrom(null, 'x.pdf')).toBe('x.pdf')
  })
})
