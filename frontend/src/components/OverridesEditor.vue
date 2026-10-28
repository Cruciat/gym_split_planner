<script setup lang="ts">
import { NButton, NCheckbox, NInputNumber, NSelect, useThemeVars } from 'naive-ui'
import { RotateCcw } from 'lucide-vue-next'
import { computed, ref } from 'vue'

import type { Priority, TagEffect } from '@/api/client'
import { COLOR_VARS, symbolIcon } from '@/catalog/symbols'
import {
  effectiveMuscle,
  effectiveTag,
  type MuscleRow,
  type MuscleValues,
  type Overrides,
  resetOverride,
  rowErrors,
  setMuscle,
  setTag,
  type TagRow,
  type TagValues,
  usesPoints,
} from '@/plans/preferences'
import { texts } from '@/texts'

/**
 * Personalizzazioni di muscoli ed etichette (US-11; wireframe, § 3.5). Ogni riga mostra
 * il valore effettivo; se è personalizzata, il segno e il valore del catalogo a cui
 * tornerebbe il ripristino.
 */
const props = defineProps<{
  overrides: Overrides
  muscles: MuscleRow[]
  tags: TagRow[]
  /** Errori per percorso nel JSON, es. `overrides.muscles.quads.weekly_max`. */
  errors?: Record<string, string>
}>()
const emit = defineEmits<{ 'update:overrides': [overrides: Overrides] }>()
const t = texts.preferences
const themeVars = useThemeVars()

const onlyCustomized = ref(false)

const priorityOptions = (Object.keys(texts.labels.priority) as Priority[]).map((p) => ({
  label: texts.labels.priority[p],
  value: p,
}))
const effectOptions = (Object.keys(texts.tags.effects) as TagEffect[]).map((e) => ({
  label: texts.tags.effects[e],
  value: e,
}))

const isMuscleCustom = (code: string) => code in props.overrides.muscles
const isTagCustom = (code: string) => code in props.overrides.tags

const shownMuscles = computed(() =>
  props.muscles.filter((m) => !onlyCustomized.value || isMuscleCustom(m.code)),
)
const shownTags = computed(() =>
  props.tags.filter((tag) => !onlyCustomized.value || isTagCustom(tag.code)),
)

function changeMuscle(row: MuscleRow, change: Partial<MuscleValues>): void {
  emit('update:overrides', setMuscle(props.overrides, row, change))
}

function changeTag(row: TagRow, change: Partial<TagValues>): void {
  emit('update:overrides', setTag(props.overrides, row, change))
}

function reset(kind: 'muscles' | 'tags', code: string): void {
  emit('update:overrides', resetOverride(props.overrides, kind, code))
}

const muscleErrors = (code: string) => rowErrors(props.errors ?? {}, 'muscles', code)
const tagErrors = (code: string) => rowErrors(props.errors ?? {}, 'tags', code)

function catalogMuscle(row: MuscleRow): string {
  const { priority, weekly_min, weekly_max } = row.catalog
  return t.catalogBand(weekly_min, weekly_max, texts.labels.priority[priority])
}

function catalogTag(row: TagRow): string {
  const { effect, points } = row.catalog
  return t.catalogTag(texts.tags.effects[effect], usesPoints(effect) ? points : null)
}
</script>

<template>
  <div class="overrides">
    <NCheckbox v-model:checked="onlyCustomized" data-testid="only-customized">
      {{ t.onlyCustomized }}
    </NCheckbox>

    <section>
      <h3>{{ t.muscles }}</h3>
      <div class="table muscles" data-testid="muscle-overrides">
        <div class="row head" aria-hidden="true">
          <span>{{ t.muscle }}</span>
          <span>{{ t.priority }}</span>
          <span>{{ t.min }}</span>
          <span>{{ t.max }}</span>
          <span />
        </div>
        <div
          v-for="row in shownMuscles"
          :key="row.code"
          class="row"
          :class="{ custom: isMuscleCustom(row.code) }"
          data-testid="muscle-override"
        >
          <div class="name">
            <strong>{{ row.name }}</strong>
            <span v-if="isMuscleCustom(row.code)" class="mark" :title="t.customizedMark">
              ● <span class="sr-only">{{ t.customizedMark }}</span>
            </span>
            <small v-if="isMuscleCustom(row.code)" class="catalog">{{ catalogMuscle(row) }}</small>
          </div>
          <NSelect
            :value="effectiveMuscle(row, overrides).priority"
            :options="priorityOptions"
            :virtual-scroll="false"
            size="small"
            :aria-label="`${t.priority} ${row.name}`"
            data-testid="muscle-priority"
            @update:value="(priority: Priority) => changeMuscle(row, { priority })"
          />
          <template v-for="field in ['weekly_min', 'weekly_max'] as const" :key="field">
            <div class="number">
              <NInputNumber
                :value="effectiveMuscle(row, overrides)[field]"
                :min="0"
                :max="100"
                :step="1"
                size="small"
                :show-button="false"
                :disabled="effectiveMuscle(row, overrides).priority === 'none'"
                :placeholder="texts.common.none"
                :status="muscleErrors(row.code)[field] ? 'error' : undefined"
                :aria-label="`${field === 'weekly_min' ? t.min : t.max} ${row.name}`"
                :data-testid="`muscle-${field === 'weekly_min' ? 'min' : 'max'}`"
                @update:value="(v: number | null) => changeMuscle(row, { [field]: v })"
              />
            </div>
          </template>
          <div class="reset">
            <NButton
              v-if="isMuscleCustom(row.code)"
              size="tiny"
              quaternary
              :aria-label="t.resetLabel(row.name)"
              data-testid="muscle-reset"
              @click="reset('muscles', row.code)"
            >
              <template #icon><RotateCcw :size="14" /></template>
              {{ t.reset }}
            </NButton>
          </div>
          <small
            v-for="(message, field) in muscleErrors(row.code)"
            :key="field"
            class="error full"
            role="alert"
          >
            {{ message }}
          </small>
        </div>
      </div>
    </section>

    <section>
      <h3>{{ t.tags }}</h3>
      <div class="table tags" data-testid="tag-overrides">
        <div class="row head" aria-hidden="true">
          <span>{{ t.tag }}</span>
          <span>{{ t.effect }}</span>
          <span>{{ t.points }}</span>
          <span />
        </div>
        <div
          v-for="row in shownTags"
          :key="row.code"
          class="row"
          :class="{ custom: isTagCustom(row.code) }"
          data-testid="tag-override"
        >
          <div class="name">
            <component
              :is="symbolIcon(row.symbol)"
              :size="16"
              :style="{ color: themeVars[COLOR_VARS[row.color]] }"
              aria-hidden="true"
            />
            <strong>{{ row.name }}</strong>
            <span v-if="isTagCustom(row.code)" class="mark" :title="t.customizedMark">
              ● <span class="sr-only">{{ t.customizedMark }}</span>
            </span>
            <small v-if="isTagCustom(row.code)" class="catalog">{{ catalogTag(row) }}</small>
          </div>
          <NSelect
            :value="effectiveTag(row, overrides).effect"
            :options="effectOptions"
            :virtual-scroll="false"
            size="small"
            :aria-label="`${t.effect} ${row.name}`"
            data-testid="tag-effect"
            @update:value="(effect: TagEffect) => changeTag(row, { effect })"
          />
          <div class="number">
            <NInputNumber
              :value="
                usesPoints(effectiveTag(row, overrides).effect)
                  ? effectiveTag(row, overrides).points
                  : null
              "
              :min="0"
              :max="100"
              :step="0.5"
              size="small"
              :show-button="false"
              :disabled="!usesPoints(effectiveTag(row, overrides).effect)"
              :placeholder="texts.common.none"
              :status="tagErrors(row.code).points ? 'error' : undefined"
              :aria-label="`${t.points} ${row.name}`"
              data-testid="tag-points"
              @update:value="
                (points: number | null) => points !== null && changeTag(row, { points })
              "
            />
          </div>
          <div class="reset">
            <NButton
              v-if="isTagCustom(row.code)"
              size="tiny"
              quaternary
              :aria-label="t.resetLabel(row.name)"
              data-testid="tag-reset"
              @click="reset('tags', row.code)"
            >
              <template #icon><RotateCcw :size="14" /></template>
              {{ t.reset }}
            </NButton>
          </div>
          <small
            v-for="(message, field) in tagErrors(row.code)"
            :key="field"
            class="error full"
            role="alert"
          >
            {{ message }}
          </small>
        </div>
      </div>
    </section>

    <p v-if="onlyCustomized && shownMuscles.length + shownTags.length === 0" class="muted">
      {{ t.noneCustomized }}
    </p>
  </div>
</template>

<style scoped>
.overrides {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

h3 {
  margin: 0 0 0.4rem;
  font-size: 1rem;
  font-weight: 600;
}

.table {
  display: flex;
  flex-direction: column;
}

.row {
  display: grid;
  gap: 0.3rem 0.75rem;
  align-items: center;
  padding: 0.45rem 0.25rem;
  border-bottom: 1px solid var(--border-color);
}

.muscles .row {
  grid-template-columns: minmax(0, 2.5fr) minmax(9rem, 1.2fr) 4.5rem 4.5rem 6.5rem;
}

.tags .row {
  grid-template-columns: minmax(0, 2.5fr) minmax(9rem, 1.2fr) 4.5rem 6.5rem;
}

.row.head {
  color: var(--muted-color);
  font-size: 0.875rem;
  font-weight: 500;
}

.row.custom {
  background: var(--hover-color);
}

.name {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.1rem 0.4rem;
  min-width: 0;
}

.name strong {
  font-weight: 500;
}

.mark {
  color: var(--primary-color);
  font-size: 0.75rem;
}

.catalog {
  flex-basis: 100%;
  color: var(--muted-color);
}

.reset {
  display: flex;
  justify-content: flex-end;
}

.full {
  grid-column: 1 / -1;
}

.error {
  color: var(--error-color);
}

.muted {
  color: var(--muted-color);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

@media (max-width: 767px) {
  .muscles .row,
  .tags .row {
    grid-template-columns: minmax(0, 1fr) 4.5rem 4.5rem;
  }

  .row.head {
    display: none;
  }

  /* Sul telefono: nome e ripristino sopra, poi priorità (o effetto) e numeri. */
  .name {
    grid-column: 1 / 3;
  }

  .muscles .row > :nth-child(2) {
    grid-column: 1;
    grid-row: 2;
  }

  .tags .row > :nth-child(2) {
    grid-column: 1 / 3;
    grid-row: 2;
  }

  .reset {
    grid-column: 3;
    grid-row: 1;
  }
}
</style>
