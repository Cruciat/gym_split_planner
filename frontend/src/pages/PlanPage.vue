<script setup lang="ts">
import { NAlert, NButton, NH1, NSkeleton } from 'naive-ui'
import { SlidersHorizontal } from 'lucide-vue-next'
import { onMounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { api, type Plan } from '@/api/client'
import { texts } from '@/texts'

/**
 * La scheda in sola lettura: giorni, esercizi, serie e ripetizioni. L'editor con il
 * pannello del volume (US-13 → US-18; wireframe, § 3.3) prende il posto di questa vista.
 */
const props = defineProps<{ id: number }>()
const t = texts.plan
const router = useRouter()

const plan = ref<Plan | null>(null)
const notFound = ref(false)
const failed = ref(false)

async function load(): Promise<void> {
  plan.value = null
  notFound.value = false
  failed.value = false
  try {
    const { data, response } = await api.GET('/api/plans/{plan_id}', {
      params: { path: { plan_id: props.id } },
    })
    if (response.status === 404) notFound.value = true
    else if (data === undefined) failed.value = true
    else plan.value = data
  } catch {
    failed.value = true
  }
}

onMounted(() => {
  void load()
})
watch(
  () => props.id,
  () => {
    void load()
  },
)
</script>

<template>
  <main class="page">
    <template v-if="notFound">
      <NAlert type="warning">{{ t.notFound }}</NAlert>
      <p>
        <RouterLink to="/schede" class="text-link">{{ t.backToPlans }}</RouterLink>
      </p>
    </template>
    <NAlert v-else-if="failed" type="error">
      {{ texts.common.loadFailed }}
      <NButton text type="primary" @click="load">{{ texts.common.retry }}</NButton>
    </NAlert>
    <NSkeleton v-else-if="plan === null" text :repeat="6" />

    <template v-else>
      <header class="header">
        <NH1 data-testid="plan-name">{{ plan.name }}</NH1>
        <NButton
          secondary
          data-testid="open-preferences"
          @click="router.push(`/schede/${plan.id}/preferenze`)"
        >
          <template #icon><SlidersHorizontal :size="16" /></template>
          {{ t.preferences }}
        </NButton>
      </header>

      <p v-if="plan.days.length === 0" class="muted">{{ t.noDays }}</p>
      <section v-for="day in plan.days" :key="day.id" class="day" data-testid="plan-day">
        <h2>
          {{ day.name }} <span class="muted">{{ t.timesPerWeek(day.times_per_week) }}</span>
        </h2>
        <p v-if="day.slots.length === 0" class="muted">{{ t.emptyDay }}</p>
        <ol v-else class="slots">
          <li v-for="slot in day.slots" :key="slot.id">
            <span :class="{ muted: slot.exercise === null }">
              {{ slot.exercise?.name ?? `${slot.family.name}: ${t.emptySlot}` }}
            </span>
            <span class="muted">{{ t.sets(slot.sets, slot.rep_min, slot.rep_max) }}</span>
          </li>
        </ol>
      </section>
    </template>
  </main>
</template>

<style scoped>
.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.header :deep(h1) {
  margin: 0;
}

.day h2 {
  margin: 1.5rem 0 0.5rem;
  font-size: 1.1rem;
}

.slots {
  margin: 0;
  padding-left: 1.5rem;
}

.slots li {
  display: flex;
  flex-wrap: wrap;
  gap: 0 1rem;
  justify-content: space-between;
  max-width: 40rem;
  padding: 0.2rem 0;
}

.muted {
  color: var(--muted-color);
}
</style>
