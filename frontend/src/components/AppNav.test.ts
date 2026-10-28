import { afterEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createMemoryHistory } from 'vue-router'

import { makeRouter } from '@/router'

import AppNav from './AppNav.vue'

async function mountAt(path: string) {
  const router = makeRouter(createMemoryHistory())
  await router.push(path)
  await router.isReady()
  const wrapper = mount(AppNav, { global: { plugins: [router] } })
  await flushPromises()
  return wrapper
}

describe('AppNav', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('ha le tre sezioni', async () => {
    const wrapper = await mountAt('/')

    expect(wrapper.findAll('li').map((li) => li.text())).toEqual([
      'Schede',
      'Catalogo',
      'Impostazioni',
    ])
  })

  it('segna la sezione attiva anche nelle sottopagine', async () => {
    const wrapper = await mountAt('/catalogo/esercizi/4')

    const current = wrapper.findAll('[aria-current="page"]')
    expect(current.map((a) => a.text())).toEqual(['Catalogo'])
  })

  it('la home appartiene alle schede', async () => {
    const wrapper = await mountAt('/')

    expect(wrapper.get('[aria-current="page"]').text()).toBe('Schede')
  })
})
