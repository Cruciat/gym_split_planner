<script setup lang="ts">
import {
  type DataTableColumns,
  NAlert,
  NButton,
  NDataTable,
  NDrawer,
  NDrawerContent,
  NEmpty,
  NH1,
  NSkeleton,
  NTag,
} from 'naive-ui'
import { Plus, SlidersHorizontal } from 'lucide-vue-next'
import { computed, h, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import type { ExerciseSummary } from '@/api/client'
import {
  countActiveFilters,
  type ExerciseFilters,
  filterExercises,
  filtersFromQuery,
  filtersToQuery,
} from '@/catalog/filters'
import ExerciseFiltersPanel from '@/components/ExerciseFiltersPanel.vue'
import TagBadges from '@/components/TagBadges.vue'
import { useIsMobile } from '@/composables/useIsMobile'
import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/** Elenco degli esercizi con i filtri (US-01, wireframe § 4.1). */
const store = useCatalogStore()
const route = useRoute()
const router = useRouter()
const isMobile = useIsMobile()
const t = texts.catalog

// Copia locale dei filtri: l'URL è la fonte (CA3), ma i campi non devono aspettare il
// giro del router a ogni tasto. Avanti e indietro del browser aggiornano la copia.
const filters = ref<ExerciseFilters>(filtersFromQuery(route.query))
const showFilters = ref(false)

watch(
  () => route.query,
  (query) => {
    const fromUrl = filtersFromQuery(query)
    const same =
      JSON.stringify(filtersToQuery(fromUrl)) === JSON.stringify(filtersToQuery(filters.value))
    if (!same) filters.value = fromUrl
  },
)

watch(
  filters,
  (value) => {
    void router.replace({ query: filtersToQuery(value) })
  },
  { deep: true },
)

onMounted(() => {
  void store.load()
})

const exercises = computed(() =>
  store.catalog === null ? [] : filterExercises(store.catalog, filters.value),
)
const total = computed(
  () =>
    store.catalog?.exercises.filter((e) => e.is_active || filters.value.showInactive).length ?? 0,
)
const activeFilters = computed(() => countActiveFilters(filters.value))

const familyName = (id: number) => store.families.get(id)?.name ?? ''
const groupName = (familyId: number) => {
  const groupId = store.families.get(familyId)?.muscle_group_id
  return groupId === undefined ? '' : (store.groups.get(groupId)?.name ?? '')
}
const equipmentName = (id: number) => store.equipment.get(id)?.name ?? ''
const detailPath = (id: number) => `/catalogo/esercizi/${String(id)}`

const byText = (pick: (e: ExerciseSummary) => string) => (a: ExerciseSummary, b: ExerciseSummary) =>
  pick(a).localeCompare(pick(b), 'it')

const columns = computed<DataTableColumns<ExerciseSummary>>(() => [
  {
    key: 'name',
    title: t.columns.name,
    sorter: byText((e) => e.name),
    render: (row) => [
      h(RouterLink, { to: detailPath(row.id), class: 'name-link' }, () => row.name),
      h(TagBadges, { links: row.tags }),
      row.is_active
        ? null
        : h(NTag, { size: 'small', bordered: false, class: 'inactive' }, () => t.inactive),
    ],
  },
  {
    key: 'group',
    title: t.columns.group,
    sorter: byText((e) => groupName(e.primary_family_id)),
    render: (row) => groupName(row.primary_family_id),
  },
  {
    key: 'family',
    title: t.columns.family,
    sorter: byText((e) => familyName(e.primary_family_id)),
    render: (row) => familyName(row.primary_family_id),
  },
  {
    key: 'equipment',
    title: t.columns.equipment,
    minWidth: 120,
    sorter: byText((e) => equipmentName(e.equipment_id)),
    render: (row) => equipmentName(row.equipment_id),
  },
  {
    key: 'confidence',
    title: t.columns.confidence,
    minWidth: 130,
    sorter: byText((e) => texts.labels.confidence[e.confidence]),
    render: (row) => texts.labels.confidence[row.confidence],
  },
])

const rowProps = (row: ExerciseSummary) => ({
  class: 'clickable',
  onClick: () => {
    void router.push(detailPath(row.id))
  },
})
</script>

<template>
  <main class="page catalog">
    <header class="header">
      <NH1>{{ t.title }}</NH1>
      <nav class="tabs">
        <RouterLink to="/catalogo" class="tab active">{{ t.tabs.exercises }}</RouterLink>
      </nav>
      <NButton
        type="primary"
        class="new"
        data-testid="new-exercise"
        @click="router.push('/catalogo/esercizi/nuovo')"
      >
        <template #icon><Plus :size="16" /></template>
        {{ t.newExercise }}
      </NButton>
    </header>

    <NAlert v-if="store.failed" type="error" data-testid="catalog-error">
      {{ texts.common.loadFailed }}
      <NButton text type="primary" @click="store.load(true)">{{ texts.common.retry }}</NButton>
    </NAlert>

    <div v-else-if="store.catalog === null" class="loading" aria-busy="true">
      <NSkeleton text :repeat="8" />
    </div>

    <div v-else class="layout">
      <aside v-if="!isMobile" class="sidebar">
        <ExerciseFiltersPanel v-model="filters" :catalog="store.catalog" />
      </aside>

      <section class="results">
        <div class="toolbar">
          <span data-testid="catalog-count">{{ t.count(exercises.length, total) }}</span>
          <NButton v-if="isMobile" secondary data-testid="open-filters" @click="showFilters = true">
            <template #icon><SlidersHorizontal :size="16" /></template>
            {{ texts.filters.open(activeFilters) }}
          </NButton>
        </div>

        <NEmpty v-if="exercises.length === 0" :description="t.empty" />

        <ul v-else-if="isMobile" class="cards" data-testid="exercise-cards">
          <li v-for="exercise in exercises" :key="exercise.id">
            <RouterLink :to="detailPath(exercise.id)" class="card">
              <span class="card-title">
                {{ exercise.name }}
                <TagBadges :links="exercise.tags" />
                <NTag v-if="!exercise.is_active" size="small" :bordered="false" class="inactive">
                  {{ t.inactive }}
                </NTag>
              </span>
              <span class="card-meta">
                {{ familyName(exercise.primary_family_id) }} ·
                {{ equipmentName(exercise.equipment_id) }}
              </span>
            </RouterLink>
          </li>
        </ul>

        <NDataTable
          v-else
          :columns="columns"
          :data="exercises"
          :row-key="(row: ExerciseSummary) => row.id"
          :row-props="rowProps"
          :bordered="false"
          size="small"
          data-testid="exercise-table"
        />
      </section>
    </div>

    <NDrawer v-model:show="showFilters" placement="bottom" height="85%">
      <NDrawerContent :title="texts.filters.title" closable>
        <ExerciseFiltersPanel v-if="store.catalog" v-model="filters" :catalog="store.catalog" />
        <template #footer>
          <NButton type="primary" block @click="showFilters = false">
            {{ texts.filters.close }}
          </NButton>
        </template>
      </NDrawerContent>
    </NDrawer>
  </main>
</template>

<style scoped>
.header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem 1.5rem;
}

.header :deep(h1) {
  margin: 0;
}

.new {
  margin-left: auto;
  align-self: center;
}

.tabs {
  display: flex;
  gap: 0.25rem;
}

.tab {
  padding: 0.3rem 0.7rem;
  border-radius: 6px;
  color: var(--muted-color);
  text-decoration: none;
}

.tab.active {
  color: var(--primary-color);
  background: var(--hover-color);
  font-weight: 600;
}

.loading {
  margin-top: 1.5rem;
}

.layout {
  display: grid;
  grid-template-columns: 16rem minmax(0, 1fr);
  gap: 2rem;
  margin-top: 1.25rem;
}

.sidebar {
  position: sticky;
  top: 1rem;
  align-self: start;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 2.25rem;
  margin-bottom: 0.5rem;
  color: var(--muted-color);
}

:deep(.name-link) {
  color: inherit;
  font-weight: 500;
  text-decoration: none;
}

:deep(.name-link:hover) {
  text-decoration: underline;
}

:deep(.clickable) {
  cursor: pointer;
}

.inactive {
  margin-left: 0.4rem;
}

.cards {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.card {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding: 0.7rem 0.85rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: inherit;
  background: var(--surface-color);
  text-decoration: none;
}

.card-title {
  font-weight: 500;
}

.card-meta {
  color: var(--muted-color);
  font-size: 0.875rem;
}

@media (max-width: 767px) {
  .layout {
    grid-template-columns: minmax(0, 1fr);
    margin-top: 0.75rem;
  }
}
</style>
