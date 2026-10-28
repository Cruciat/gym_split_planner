<script setup lang="ts">
import {
  NButton,
  NCheckbox,
  NFormItem,
  NInput,
  NRadioButton,
  NRadioGroup,
  NSelect,
  type SelectGroupOption,
  type SelectOption,
} from 'naive-ui'
import { computed } from 'vue'

import type { Catalog, Confidence } from '@/api/client'
import { emptyFilters, type ExerciseFilters } from '@/catalog/filters'
import { texts } from '@/texts'

/** Filtri dell'elenco degli esercizi (US-01 CA2, wireframe § 4.1). */
const props = defineProps<{ catalog: Catalog }>()
const filters = defineModel<ExerciseFilters>({ required: true })

const t = texts.filters

function update<K extends keyof ExerciseFilters>(key: K, value: ExerciseFilters[K]): void {
  filters.value = { ...filters.value, [key]: value }
}

/** Opzioni raggruppate per gruppo muscolare, nell'ordine del catalogo. */
function byGroup(items: { code: string; name: string; muscle_group_id: number }[]) {
  return props.catalog.muscle_groups
    .map((group): SelectGroupOption => ({
      type: 'group',
      key: group.code,
      label: group.name,
      children: items
        .filter((item) => item.muscle_group_id === group.id)
        .map((item) => ({ label: item.name, value: item.code })),
    }))
    .filter((group) => group.children?.length !== 0)
}

const groupOptions = computed<SelectOption[]>(() =>
  props.catalog.muscle_groups.map((g) => ({ label: g.name, value: g.code })),
)
const muscleOptions = computed(() => byGroup(props.catalog.muscles))
const familyOptions = computed(() => byGroup(props.catalog.families))
const equipmentOptions = computed<SelectOption[]>(() =>
  props.catalog.equipment.map((e) => ({ label: e.name, value: e.code })),
)
const tagOptions = computed<SelectOption[]>(() =>
  props.catalog.tags.map((tag) => ({ label: tag.name, value: tag.code })),
)
const confidenceOptions = (Object.keys(texts.labels.confidence) as Confidence[]).map((c) => ({
  label: texts.labels.confidence[c],
  value: c,
}))

function asCode(value: unknown): string | null {
  return typeof value === 'string' ? value : null
}

function asConfidence(value: unknown): Confidence | null {
  return confidenceOptions.find((option) => option.value === value)?.value ?? null
}
</script>

<template>
  <div class="filters">
    <NFormItem :label="t.search" :show-feedback="false">
      <NInput
        :value="filters.search"
        clearable
        :placeholder="t.search"
        :input-props="{ 'aria-label': t.search }"
        data-testid="filter-search"
        @update:value="(v: string) => update('search', v)"
      />
    </NFormItem>

    <NFormItem :label="t.group" :show-feedback="false">
      <NSelect
        :value="filters.group"
        :options="groupOptions"
        clearable
        :placeholder="t.any"
        data-testid="filter-group"
        @update:value="(v: unknown) => update('group', asCode(v))"
      />
    </NFormItem>

    <NFormItem :label="t.muscle" :show-feedback="false">
      <div class="stack">
        <NSelect
          :value="filters.muscle"
          :options="muscleOptions"
          clearable
          filterable
          :placeholder="t.any"
          data-testid="filter-muscle"
          @update:value="(v: unknown) => update('muscle', asCode(v))"
        />
        <NRadioGroup
          v-if="filters.muscle !== null"
          :value="filters.level"
          size="small"
          @update:value="(v: 'P' | 'S') => update('level', v)"
        >
          <NRadioButton value="P">{{ t.level.P }}</NRadioButton>
          <NRadioButton value="S">{{ t.level.S }}</NRadioButton>
        </NRadioGroup>
      </div>
    </NFormItem>

    <NFormItem :label="t.family" :show-feedback="false">
      <NSelect
        :value="filters.family"
        :options="familyOptions"
        clearable
        filterable
        :placeholder="t.any"
        data-testid="filter-family"
        @update:value="(v: unknown) => update('family', asCode(v))"
      />
    </NFormItem>

    <NFormItem :label="t.equipment" :show-feedback="false">
      <NSelect
        :value="filters.equipment"
        :options="equipmentOptions"
        clearable
        :placeholder="t.any"
        data-testid="filter-equipment"
        @update:value="(v: unknown) => update('equipment', asCode(v))"
      />
    </NFormItem>

    <NFormItem :label="t.tag" :show-feedback="false">
      <div class="stack">
        <NSelect
          :value="filters.tag"
          :options="tagOptions"
          clearable
          :placeholder="t.any"
          data-testid="filter-tag"
          @update:value="(v: unknown) => update('tag', asCode(v))"
        />
        <NRadioGroup
          v-if="filters.tag !== null"
          :value="filters.withoutTag ? 'without' : 'with'"
          size="small"
          @update:value="(v: 'with' | 'without') => update('withoutTag', v === 'without')"
        >
          <NRadioButton value="with">{{ t.tagMode.with }}</NRadioButton>
          <NRadioButton value="without">{{ t.tagMode.without }}</NRadioButton>
        </NRadioGroup>
      </div>
    </NFormItem>

    <NFormItem :label="t.confidence" :show-feedback="false">
      <NSelect
        :value="filters.confidence"
        :options="confidenceOptions"
        clearable
        :placeholder="t.any"
        data-testid="filter-confidence"
        @update:value="(v: unknown) => update('confidence', asConfidence(v))"
      />
    </NFormItem>

    <NCheckbox
      :checked="filters.showInactive"
      data-testid="filter-inactive"
      @update:checked="(v: boolean) => update('showInactive', v)"
    >
      {{ t.showInactive }}
    </NCheckbox>

    <NButton secondary block data-testid="filter-reset" @click="filters = { ...emptyFilters }">
      {{ t.reset }}
    </NButton>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.stack {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  width: 100%;
}
</style>
