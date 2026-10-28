import { afterEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse } from '@/test/fixtures'
import { mountAt, setMobile, stubFetch } from '@/test/mount'

describe('SettingsPage', () => {
  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('mostra versione e stato del database', async () => {
    setMobile(false)
    stubFetch({
      '/api/health': () => jsonResponse({ status: 'ok', version: '0.4.0', database: 'ok' }),
    })

    const { wrapper } = await mountAt('/impostazioni')

    const message = wrapper.get('[data-testid="health-ok"]')
    expect(message.text()).toContain('versione 0.4.0')
    expect(message.text()).toContain('database ok')
  })

  it('segnala un server che non risponde', async () => {
    setMobile(false)
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('rete'))),
    )

    const { wrapper } = await mountAt('/impostazioni')

    expect(wrapper.find('[data-testid="health-error"]').exists()).toBe(true)
  })
})
