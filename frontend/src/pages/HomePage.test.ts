import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import PrimeVue from 'primevue/config'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import HomePage from './HomePage.vue'

function mountPage() {
  return mount(HomePage, { global: { plugins: [PrimeVue] } })
}

describe('HomePage', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('mostra versione e stato del database', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ status: 'ok', version: '0.1.0', database: 'ok' }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          }),
        ),
      ),
    )

    const wrapper = mountPage()
    await flushPromises()

    const message = wrapper.get('[data-testid="health-ok"]')
    expect(message.text()).toContain('versione 0.1.0')
    expect(message.text()).toContain('database ok')
  })

  it('segnala un server che non risponde', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('rete'))),
    )

    const wrapper = mountPage()
    await flushPromises()

    expect(wrapper.find('[data-testid="health-error"]').exists()).toBe(true)
  })
})
