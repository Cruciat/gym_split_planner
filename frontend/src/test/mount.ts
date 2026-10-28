/** Montaggio di una pagina con router in memoria, Pinia, provider di Naive UI e `fetch` finto. */

import { DOMWrapper, flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { NDialogProvider, NMessageProvider } from 'naive-ui'
import { createPinia } from 'pinia'
import { vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { createMemoryHistory, RouterView, type Router } from 'vue-router'

import { makeRouter } from '@/router'

import { jsonResponse } from './fixtures'

type Handler = (request: Request) => Response | Promise<Response>

/**
 * Risposte per percorso: la chiave è `/api/catalog` (qualunque metodo) oppure
 * `PUT /api/exercises/4`. I percorsi senza risposta danno 404.
 */
export type Routes = Record<string, Handler>

export function stubFetch(routes: Routes) {
  const fetchMock = vi.fn(async (request: Request) => {
    const path = new URL(request.url).pathname
    const handler = routes[`${request.method} ${path}`] ?? routes[path]
    return handler === undefined
      ? jsonResponse({ status: 404, code: 'not-found', title: 'Risorsa non trovata' }, 404)
      : handler(request.clone())
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

/** Corpi JSON delle chiamate fatte con un metodo a un percorso. */
export async function requestBodies(
  fetchMock: ReturnType<typeof stubFetch>,
  method: string,
  path: string,
): Promise<unknown[]> {
  const requests = fetchMock.mock.calls
    .map(([request]) => request)
    .filter((r) => r.method === method && new URL(r.url).pathname === path)
  return Promise.all(requests.map((r) => r.clone().json() as Promise<unknown>))
}

/** Simula la larghezza del telefono (sotto 768 px) o del desktop. */
export function setMobile(mobile: boolean): void {
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query: string) => ({
      matches: mobile,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  )
}

export async function mountAt(path: string): Promise<{ wrapper: VueWrapper; router: Router }> {
  const router = makeRouter(createMemoryHistory())
  await router.push(path)
  await router.isReady()
  const Root = defineComponent({
    render: () => h(NDialogProvider, () => h(NMessageProvider, () => h(RouterView))),
  })
  const wrapper = mount(Root, {
    global: { plugins: [createPinia(), router] },
    attachTo: document.body,
  })
  await flushPromises()
  return { wrapper, router }
}

/** Elementi fuori dalla pagina (finestre, menu a tendina): sono nel `body`. */
export function inBody(selector: string): DOMWrapper<Element>[] {
  return [...document.body.querySelectorAll(selector)].map((el) => new DOMWrapper(el))
}

/**
 * Pulsante di una finestra di dialogo aperta, per testo. Se ce n'è più d'una (quella
 * chiusa può restare nel `body` durante la transizione), vale l'ultima aperta.
 */
export function dialogButton(text: string): DOMWrapper<Element> {
  const button = inBody('.n-dialog button')
    .filter((b) => b.text() === text)
    .at(-1)
  if (button === undefined) throw new Error(`Nessun pulsante «${text}» in una finestra aperta`)
  return button
}

/** Sceglie un'opzione in un `NSelect` con il `data-testid` indicato. */
export async function chooseOption(
  wrapper: VueWrapper,
  testId: string,
  label: string,
): Promise<void> {
  // Il menu può stare nella pagina o in una finestra, che Naive UI mette nel `body`.
  const selector = `[data-testid="${testId}"] .n-base-selection`
  const trigger = wrapper.find(selector).exists() ? wrapper.get(selector) : inBody(selector)[0]
  if (trigger === undefined) throw new Error(`Nessun menu ${testId}`)
  // In jsdom la trappola del focus delle finestre richiude subito i menu con ricerca
  // (`filterable`): il focus non serve a scegliere, e qui si salta.
  const focus = vi.spyOn(HTMLElement.prototype, 'focus').mockImplementation(() => undefined)
  try {
    await trigger.trigger('click')
    await flushPromises()
  } finally {
    focus.mockRestore()
  }
  const option = inBody('.n-base-select-option').find((o) => o.text() === label)
  if (option === undefined) throw new Error(`Nessuna opzione «${label}» in ${testId}`)
  await option.trigger('click')
  await flushPromises()
}
