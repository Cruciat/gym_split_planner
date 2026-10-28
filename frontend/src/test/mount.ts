/** Montaggio di una pagina con router in memoria, Pinia e `fetch` sostituito. */

import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { createMemoryHistory, RouterView, type Router } from 'vue-router'

import { makeRouter } from '@/router'

import { jsonResponse } from './fixtures'

/** Risposte per percorso (`/api/catalog`); gli altri percorsi rispondono 404. */
export type Routes = Record<string, () => Response>

export function stubFetch(routes: Routes) {
  const fetchMock = vi.fn((request: Request) => {
    const path = new URL(request.url).pathname
    const handler = routes[path]
    return Promise.resolve(
      handler === undefined
        ? jsonResponse({ status: 404, code: 'not-found', title: 'Risorsa non trovata' }, 404)
        : handler(),
    )
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
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
  const Root = defineComponent({ render: () => h(RouterView) })
  const wrapper = mount(Root, {
    global: { plugins: [createPinia(), router] },
    attachTo: document.body,
  })
  await flushPromises()
  return { wrapper, router }
}
