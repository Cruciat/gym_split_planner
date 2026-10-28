import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, type HealthOut } from '@/api/client'

/** Stato del backend, letto da `GET /api/health`. */
export const useHealthStore = defineStore('health', () => {
  const health = ref<HealthOut | null>(null)
  const failed = ref(false)

  async function load(): Promise<void> {
    failed.value = false
    try {
      const { data } = await api.GET('/api/health')
      health.value = data ?? null
      failed.value = data === undefined
    } catch {
      health.value = null
      failed.value = true
    }
  }

  return { health, failed, load }
})
