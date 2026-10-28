<script setup lang="ts">
import { NCollapse, NCollapseItem, NSelect, useThemeVars } from 'naive-ui'
import {
  ArrowDown,
  ArrowUp,
  CircleAlert,
  CircleSlash,
  Clock,
  Gauge,
  type LucideIcon,
} from 'lucide-vue-next'
import { computed, nextTick, ref } from 'vue'

import type { Plan } from '@/api/client'
import {
  barGeometry,
  filterVolumes,
  groupVolumes,
  hasTarget,
  type Volume,
  type VolumeFilter,
  type WarningItem,
  warningItems,
  type WarningTarget,
} from '@/plans/volume'
import { useCatalogStore } from '@/stores/catalog'
import { formatNumber, texts } from '@/texts'

/**
 * Volume settimanale per muscolo e avvisi (US-13 CA2, US-20; wireframe, § 3.3). Lo
 * stato non è affidato al solo colore: sotto e sopra fascia hanno anche icona e testo.
 * Un avviso su un muscolo porta alla sua riga; gli altri portano al giorno o
 * all'esercizio, e li gestisce l'editor (`go`).
 */
const props = withDefaults(defineProps<{ plan: Plan; titled?: boolean }>(), { titled: true })
const emit = defineEmits<{ go: [target: WarningTarget] }>()
const t = texts.volume
const store = useCatalogStore()
const themeVars = useThemeVars()

const filter = ref<VolumeFilter>('priority')
const highlighted = ref<number | null>(null)
const filterOptions = (Object.keys(t.filters) as VolumeFilter[]).map((value) => ({
  label: t.filters[value],
  value,
}))

const groups = computed(() =>
  groupVolumes(filterVolumes(props.plan.analysis.volumes, filter.value), store.catalog),
)
const withoutTarget = computed(() => props.plan.analysis.volumes.filter((v) => !hasTarget(v)))
const warnings = computed(() => warningItems(props.plan, store.catalog))

function colorOf(v: Volume): string {
  const vars = themeVars.value
  if (v.status === 'below') return vars.errorColor
  if (v.status === 'above') return vars.warningColor
  if (v.status === 'within') return vars.successColor
  return vars.textColor3
}

const WARNING_ICONS: Record<WarningItem['kind'], LucideIcon> = {
  below: ArrowDown,
  above: ArrowUp,
  cap: Gauge,
  long: Clock,
  empty: CircleSlash,
}

async function go(item: WarningItem): Promise<void> {
  const target = item.target
  if (target === null) return
  if (target.kind !== 'muscle') {
    emit('go', target)
    return
  }
  const volume = props.plan.analysis.volumes.find((v) => v.muscle_id === target.muscleId)
  if (volume !== undefined && volume.priority !== 'priority') filter.value = 'target'
  highlighted.value = target.muscleId
  await nextTick()
  document
    .querySelector(`[data-muscle-id="${String(target.muscleId)}"]`)
    ?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  setTimeout(() => {
    if (highlighted.value === target.muscleId) highlighted.value = null
  }, 2500)
}
</script>

<template>
  <section class="volume-panel" :aria-label="t.title" data-testid="volume-panel">
    <header class="head">
      <h2 v-if="titled">{{ t.title }}</h2>
      <NSelect
        v-model:value="filter"
        :options="filterOptions"
        :virtual-scroll="false"
        size="small"
        class="filter"
        :aria-label="t.filter"
        data-testid="volume-filter"
      />
    </header>

    <div v-for="group in groups" :key="group.code" class="group">
      <h3>{{ group.name }}</h3>
      <div
        v-for="v in group.volumes"
        :key="v.muscle_id"
        class="row"
        :class="{ highlighted: highlighted === v.muscle_id }"
        :data-muscle-id="v.muscle_id"
        :aria-label="t.row(v.name, v.volume, v.weekly_min, v.weekly_max)"
        role="group"
        data-testid="volume-row"
      >
        <span class="name" :title="v.name">
          <span class="label">{{ v.short_name }}</span>
          <span v-if="v.overridden" class="custom" :title="t.customized">
            ●<span class="sr-only">{{ t.customized }}</span>
          </span>
          <span
            v-if="v.status === 'below' || v.status === 'above'"
            class="status"
            :style="{ color: colorOf(v) }"
            data-testid="volume-status"
          >
            <ArrowDown v-if="v.status === 'below'" :size="14" aria-hidden="true" />
            <ArrowUp v-else :size="14" aria-hidden="true" />
            {{ v.status === 'below' ? t.below : t.above }}
          </span>
        </span>
        <span class="value">{{ formatNumber(v.volume) }}</span>
        <span class="bar" aria-hidden="true">
          <span
            class="zone"
            :style="{
              left: `${barGeometry(v).zoneStart}%`,
              width: `${barGeometry(v).zoneWidth}%`,
            }"
          />
          <span
            class="marker"
            :style="{ left: `${barGeometry(v).marker}%`, background: colorOf(v) }"
          />
        </span>
        <span class="band" :class="{ custom: v.overridden }">
          {{
            v.weekly_min !== null && v.weekly_max !== null ? t.band(v.weekly_min, v.weekly_max) : ''
          }}
        </span>
      </div>
    </div>

    <NCollapse v-if="filter === 'all' && withoutTarget.length > 0" class="no-target">
      <NCollapseItem :title="t.noTarget(withoutTarget.length)" name="none">
        <div
          v-for="v in withoutTarget"
          :key="v.muscle_id"
          class="row plain"
          data-testid="volume-row"
        >
          <span class="name" :title="v.name">{{ v.short_name }}</span>
          <span class="value">{{ formatNumber(v.volume) }}</span>
        </div>
      </NCollapseItem>
    </NCollapse>

    <section class="warnings" data-testid="warnings">
      <h3>{{ t.warnings(warnings.length) }}</h3>
      <p v-if="warnings.length === 0" class="muted">{{ t.noWarnings }}</p>
      <ul v-else>
        <li v-for="item in warnings" :key="item.key">
          <button
            type="button"
            class="warning"
            :class="item.kind"
            :disabled="item.target === null"
            data-testid="warning"
            @click="go(item)"
          >
            <component
              :is="WARNING_ICONS[item.kind] ?? CircleAlert"
              :size="16"
              aria-hidden="true"
            />
            <span>{{ item.text }}</span>
          </button>
        </li>
      </ul>
    </section>
  </section>
</template>

<style scoped>
.volume-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

h2 {
  margin: 0;
  font-size: 1.05rem;
}

h3 {
  margin: 0 0 0.25rem;
  color: var(--muted-color);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.filter {
  width: 9.5rem;
}

.row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 2.2rem 4.5rem 3rem;
  gap: 0.4rem;
  align-items: center;
  padding: 0.15rem 0.25rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.row.plain {
  grid-template-columns: minmax(0, 1fr) 2.4rem;
}

.row.highlighted {
  background: var(--hover-color);
  box-shadow: inset 2px 0 0 var(--primary-color);
}

.name {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  min-width: 0;
}

.label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.custom {
  color: var(--primary-color);
  font-size: 0.7rem;
}

.status {
  display: inline-flex;
  flex: none;
  align-items: center;
  gap: 0.1rem;
  font-size: 0.8rem;
}

.value {
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.bar {
  position: relative;
  height: 0.55rem;
  border-radius: 3px;
  background: var(--border-color);
}

.zone {
  position: absolute;
  top: 0;
  bottom: 0;
  border-radius: 3px;
  background: color-mix(in srgb, var(--primary-color) 30%, transparent);
}

.marker {
  position: absolute;
  top: -0.15rem;
  width: 3px;
  height: 0.85rem;
  border-radius: 1px;
  transform: translateX(-50%);
}

.band {
  color: var(--muted-color);
  font-size: 0.75rem;
  font-variant-numeric: tabular-nums;
}

.band.custom {
  color: var(--primary-color);
}

.warnings ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.warning {
  display: flex;
  gap: 0.4rem;
  align-items: flex-start;
  width: 100%;
  padding: 0.3rem 0.25rem;
  border: 0;
  border-radius: 4px;
  background: none;
  color: inherit;
  font: inherit;
  font-size: 0.875rem;
  text-align: left;
  cursor: pointer;
}

.warning:hover:not(:disabled),
.warning:focus-visible {
  background: var(--hover-color);
}

.warning > :first-child {
  flex: none;
  margin-top: 0.15rem;
}

.warning.below > :first-child {
  color: var(--error-color);
}

.warning.above > :first-child,
.warning.cap > :first-child,
.warning.long > :first-child,
.warning.empty > :first-child {
  color: var(--warning-color);
}

.muted {
  margin: 0;
  color: var(--muted-color);
  font-size: 0.875rem;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}
</style>
