<script setup lang="ts">
import {
  NAlert,
  NButton,
  NDrawer,
  NDrawerContent,
  NDropdown,
  NSkeleton,
  useMessage,
} from 'naive-ui'
import {
  ChevronUp,
  EllipsisVertical,
  Pencil,
  Plus,
  RefreshCw,
  SlidersHorizontal,
} from 'lucide-vue-next'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, RouterLink, useRoute, useRouter } from 'vue-router'

import DayDialog from '@/components/editor/DayDialog.vue'
import DayView from '@/components/editor/DayView.vue'
import RegenerateDialog from '@/components/editor/RegenerateDialog.vue'
import TextDialog from '@/components/editor/TextDialog.vue'
import SaveStatus from '@/components/SaveStatus.vue'
import VolumePanel from '@/components/VolumePanel.vue'
import { useConfirm } from '@/composables/useConfirm'
import { NARROW_QUERY, useIsMobile, useMediaQuery } from '@/composables/useIsMobile'
import { useSortable } from '@/composables/useSortable'
import { createPlanEditor, providePlanEditor } from '@/plans/editor'
import { statusCounts, type WarningTarget } from '@/plans/volume'
import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/**
 * Editor della scheda (US-13, US-15, US-16, US-19 CA3, US-20, US-21; wireframe, § 3.3 e
 * § 3.7). Ogni modifica passa dalla coda dell'editor e la risposta del server, con
 * volumi e avvisi ricalcolati, prende il posto della scheda sullo schermo.
 */
const props = defineProps<{ id: number }>()
const t = texts.editor
const message = useMessage()
const confirm = useConfirm()
const route = useRoute()
const router = useRouter()
const catalog = useCatalogStore()
const mobile = useIsMobile()
const narrow = useMediaQuery(NARROW_QUERY)

const editor = createPlanEditor(props.id, {
  warning: (text) => message.warning(text, { duration: 6000 }),
  error: (text) => message.error(text, { duration: 6000 }),
})
providePlanEditor(editor)
const plan = editor.plan

onMounted(() => {
  void editor.load()
  void catalog.load()
})
onBeforeUnmount(editor.dispose)

// --- Giorno attivo, nell'URL (`?giorno=12`) ------------------------------------------

const activeDayId = computed<number | null>(() => {
  const days = plan.value?.days ?? []
  const requested = Number(route.query.giorno)
  return days.find((d) => d.id === requested)?.id ?? days[0]?.id ?? null
})
const activeIndex = computed(() =>
  (plan.value?.days ?? []).findIndex((d) => d.id === activeDayId.value),
)
const activeDay = computed(() => plan.value?.days[activeIndex.value] ?? null)

function selectDay(dayId: number): void {
  void router.replace({ query: { ...route.query, giorno: String(dayId) } })
}

// --- Schede dei giorni, riordinabili trascinandole su schermo largo ---------------------

const tabs = ref<HTMLElement | null>(null)
const tabsDraggable = computed(() => !mobile.value)
useSortable(tabs, {
  enabled: tabsDraggable,
  onMove: (from, to) => {
    const ids = (plan.value?.days ?? []).map((d) => d.id)
    const [id] = ids.splice(from, 1)
    if (id === undefined) return
    ids.splice(to, 0, id)
    void editor.reorderDays(ids)
  },
})

// --- Nuovo giorno, nome della scheda ------------------------------------------------------

const addingDay = ref(false)
const renaming = ref(false)

async function addDay(value: { name: string; times_per_week: number }): Promise<void> {
  addingDay.value = false
  const ok = await editor.addDay(value)
  const last = plan.value?.days.at(-1)
  if (ok && last !== undefined) selectDay(last.id)
}

async function rename(name: string): Promise<void> {
  renaming.value = false
  if (name !== plan.value?.name) await editor.rename(name)
}

const regenerating = ref(false)

const mobileMenu = [
  { key: 'preferences', label: t.preferences },
  { key: 'regenerate', label: t.regenerate },
  { key: 'rename', label: t.rename },
]

function actOnPlan(key: 'preferences' | 'regenerate' | 'rename'): void {
  if (key === 'rename') renaming.value = true
  else if (key === 'regenerate') regenerating.value = true
  else void router.push(`/schede/${String(props.id)}/preferenze`)
}

// --- Pannello volume e avvisi -----------------------------------------------------------

const panelOpen = ref(false)
const highlightedSlot = ref<number | null>(null)
const counts = computed(() => statusCounts(plan.value?.analysis.volumes ?? []))
const warningCount = computed(() => plan.value?.analysis.warnings.length ?? 0)

async function go(target: WarningTarget): Promise<void> {
  if (target.kind === 'muscle') return
  panelOpen.value = false
  selectDay(target.dayId)
  await nextTick()
  await nextTick()
  if (target.kind === 'slot') {
    highlightedSlot.value = target.slotId
    document
      .querySelector(`[data-slot-id="${String(target.slotId)}"]`)
      ?.scrollIntoView({ block: 'center', behavior: 'smooth' })
    setTimeout(() => {
      if (highlightedSlot.value === target.slotId) highlightedSlot.value = null
    }, 2500)
  } else {
    document.querySelector('[data-testid="day"]')?.scrollIntoView({ behavior: 'smooth' })
  }
}

// Il giorno chiesto nell'URL non c'è più (eliminato): si torna al primo.
watch(
  () => plan.value?.days.map((d) => d.id).join(','),
  () => {
    const requested = route.query.giorno
    if (requested !== undefined && activeDayId.value !== Number(requested)) {
      const query = { ...route.query }
      delete query.giorno
      void router.replace({ query })
    }
  },
)

// --- Uscita: le modifiche in coda partono prima di lasciare la pagina ---------------------

onBeforeRouteLeave(async () => {
  if (await editor.settle()) return true
  return confirm({ title: t.leaveTitle, content: t.leaveText, action: t.leave, cancel: t.stay })
})
</script>

<template>
  <main class="page editor" :class="{ narrow }">
    <template v-if="editor.loadState.value === 'not-found'">
      <NAlert type="warning">{{ texts.plan.notFound }}</NAlert>
      <p>
        <RouterLink to="/schede" class="text-link">{{ texts.plan.backToPlans }}</RouterLink>
      </p>
    </template>
    <NAlert v-else-if="editor.loadState.value === 'failed'" type="error">
      {{ texts.common.loadFailed }}
      <NButton text type="primary" @click="editor.load">{{ texts.common.retry }}</NButton>
    </NAlert>
    <NSkeleton v-else-if="plan === null" text :repeat="8" />

    <template v-else>
      <header class="head">
        <div class="name">
          <h1 data-testid="plan-name">{{ plan.name }}</h1>
          <NButton
            v-if="!mobile"
            quaternary
            circle
            size="small"
            :aria-label="t.renameLabel(plan.name)"
            data-testid="rename-plan"
            @click="renaming = true"
          >
            <template #icon><Pencil :size="16" /></template>
          </NButton>
        </div>
        <div class="status">
          <SaveStatus :state="editor.saveState.value" />
          <NButton
            v-if="editor.saveState.value === 'error'"
            size="tiny"
            type="primary"
            secondary
            data-testid="retry"
            @click="editor.retry"
          >
            {{ t.retry }}
          </NButton>
        </div>
        <div class="tools">
          <NButton
            v-if="!mobile"
            secondary
            data-testid="open-preferences"
            @click="router.push(`/schede/${plan.id}/preferenze`)"
          >
            <template #icon><SlidersHorizontal :size="16" /></template>
            {{ t.preferences }}
          </NButton>
          <NButton
            v-if="!mobile"
            secondary
            :disabled="plan.days.length === 0"
            data-testid="regenerate"
            @click="regenerating = true"
          >
            <template #icon><RefreshCw :size="16" /></template>
            {{ t.regenerate }}
          </NButton>
          <NDropdown
            v-else
            trigger="click"
            placement="bottom-end"
            :options="mobileMenu"
            @select="actOnPlan"
          >
            <NButton quaternary circle :aria-label="t.more" data-testid="plan-menu">
              <template #icon><EllipsisVertical :size="18" /></template>
            </NButton>
          </NDropdown>
        </div>
      </header>

      <div class="layout">
        <div class="content">
          <div v-if="plan.days.length === 0" class="empty" data-testid="empty-plan">
            <p>{{ t.emptyPlan }}</p>
            <NButton type="primary" data-testid="add-first-day" @click="addingDay = true">
              <template #icon><Plus :size="16" /></template>
              {{ t.addFirstDay }}
            </NButton>
          </div>

          <template v-else>
            <nav class="tabs-bar" :aria-label="t.days">
              <div ref="tabs" class="tabs" role="tablist">
                <button
                  v-for="day in plan.days"
                  :key="day.id"
                  type="button"
                  role="tab"
                  class="tab"
                  :aria-selected="day.id === activeDayId"
                  data-testid="day-tab"
                  @click="selectDay(day.id)"
                >
                  {{ t.dayTab(day.name, day.times_per_week) }}
                </button>
              </div>
              <NButton
                quaternary
                size="small"
                :aria-label="t.addDayLabel"
                data-testid="add-day"
                @click="addingDay = true"
              >
                <template #icon><Plus :size="16" /></template>
                {{ t.addDay }}
              </NButton>
            </nav>

            <DayView
              v-if="activeDay"
              :key="activeDay.id"
              :day="activeDay"
              :day-index="activeIndex"
              :day-count="plan.days.length"
              :mobile="mobile"
              :highlighted-slot="highlightedSlot"
            />
          </template>
        </div>

        <aside v-if="!narrow" class="panel">
          <VolumePanel :plan="plan" @go="go" />
        </aside>
      </div>

      <button
        v-if="narrow"
        type="button"
        class="summary-bar"
        :aria-label="texts.volume.open"
        data-testid="volume-summary"
        @click="panelOpen = true"
      >
        <span>
          {{ texts.volume.summary(counts.below, counts.above)
          }}{{ texts.volume.summaryWarnings(warningCount) }}
        </span>
        <ChevronUp :size="18" aria-hidden="true" />
      </button>

      <NDrawer
        v-if="narrow"
        v-model:show="panelOpen"
        placement="bottom"
        height="100%"
        data-testid="volume-drawer"
      >
        <NDrawerContent closable :title="texts.volume.title">
          <VolumePanel :plan="plan" :titled="false" @go="go" />
        </NDrawerContent>
      </NDrawer>

      <DayDialog v-model:show="addingDay" :title="t.addDayTitle" :action="t.add" @submit="addDay" />
      <RegenerateDialog v-model:show="regenerating" />
      <TextDialog
        v-model:show="renaming"
        :title="t.renameTitle"
        :label="t.name"
        :value="plan.name"
        :action="t.save"
        required
        @submit="rename"
      />
    </template>
  </main>
</template>

<style scoped>
.head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 1rem;
  margin-bottom: 1rem;
}

.name {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  min-width: 0;
}

h1 {
  margin: 0;
  overflow: hidden;
  font-size: 1.6rem;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status {
  display: flex;
  flex: 1;
  align-items: center;
  gap: 0.5rem;
}

.tools {
  display: flex;
  gap: 0.5rem;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 23rem;
  gap: 2rem;
  align-items: start;
}

.narrow .layout {
  grid-template-columns: minmax(0, 1fr);
}

.panel {
  position: sticky;
  top: 1rem;
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.tabs-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  overflow-x: auto;
}

.tabs {
  display: flex;
  gap: 0.35rem;
}

.tab {
  padding: 0.35rem 0.85rem;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: none;
  color: inherit;
  font: inherit;
  white-space: nowrap;
  cursor: pointer;
}

.tab[aria-selected='true'] {
  border-color: var(--primary-color);
  background: var(--primary-color);
  color: var(--on-primary-color);
}

.tab:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

.empty {
  padding: 2rem 0;
}

.summary-bar {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.7rem 1.25rem;
  border: 0;
  border-top: 1px solid var(--border-color);
  background: var(--surface-color);
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.narrow {
  padding-bottom: 4rem;
}

@media (max-width: 767px) {
  /* Sul telefono la navigazione è in basso: la barra del volume le sta sopra. */
  .summary-bar {
    bottom: calc(var(--nav-height) + env(safe-area-inset-bottom));
  }

  h1 {
    font-size: 1.25rem;
  }

  /* Sul telefono la testata resta su una riga: il nome si accorcia. */
  .head {
    flex-wrap: nowrap;
  }

  .name {
    flex: 1;
  }

  .status {
    flex: none;
  }
}
</style>
