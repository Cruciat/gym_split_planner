import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, makeCatalog, makePlan, makePlanSettings } from '@/test/fixtures'
import { mountAt, setMobile, stubFetch } from '@/test/mount'

describe('PlanPage', () => {
  beforeEach(() => {
    setMobile(false)
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('mostra giorni, esercizi, serie e ripetizioni', async () => {
    stubFetch({ 'GET /api/plans/1': () => jsonResponse(makePlan()) })
    const { wrapper } = await mountAt('/schede/1')

    const day = wrapper.get('[data-testid="plan-day"]')
    expect(day.text()).toContain('Push')
    expect(day.text()).toMatch(/Chest press inclinata.*3 × 6-12/)
  })

  it('apre le preferenze', async () => {
    stubFetch({
      'GET /api/plans/1': () => jsonResponse(makePlan()),
      'GET /api/plans/1/settings': () => jsonResponse(makePlanSettings()),
      '/api/catalog': () => jsonResponse(makeCatalog()),
    })
    const { wrapper, router } = await mountAt('/schede/1')

    await wrapper.get('[data-testid="open-preferences"]').trigger('click')

    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/schede/1/preferenze')
    })
  })

  it('una scheda che non esiste', async () => {
    stubFetch({})
    const { wrapper } = await mountAt('/schede/9')

    expect(wrapper.text()).toContain('Scheda non trovata.')
  })
})
