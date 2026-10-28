import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api, type Catalog } from '@/api/client'

/** Indice per `id` di un elenco del catalogo. */
function index<T extends { id: number }>(items: T[] | undefined): Map<number, T> {
  return new Map((items ?? []).map((item) => [item.id, item]))
}

/**
 * Catalogo caricato in blocco da `GET /api/catalog` (API, § 6.2), con indici per `id`.
 * Lo usano l'elenco, i filtri e le pagine che mostrano nomi di muscoli, famiglie ed
 * etichette a partire dagli `id`.
 */
export const useCatalogStore = defineStore('catalog', () => {
  const catalog = ref<Catalog | null>(null)
  const loading = ref(false)
  const failed = ref(false)

  const groups = computed(() => index(catalog.value?.muscle_groups))
  const muscles = computed(() => index(catalog.value?.muscles))
  const equipment = computed(() => index(catalog.value?.equipment))
  const families = computed(() => index(catalog.value?.families))
  const tags = computed(() => index(catalog.value?.tags))

  /** Carica il catalogo; con `force` lo ricarica anche se c'è già. */
  async function load(force = false): Promise<void> {
    if (catalog.value !== null && !force) return
    loading.value = true
    failed.value = false
    try {
      const { data } = await api.GET('/api/catalog')
      if (data === undefined) {
        failed.value = true
      } else {
        catalog.value = data
      }
    } catch {
      failed.value = true
    } finally {
      loading.value = false
    }
  }

  return { catalog, loading, failed, groups, muscles, equipment, families, tags, load }
})
