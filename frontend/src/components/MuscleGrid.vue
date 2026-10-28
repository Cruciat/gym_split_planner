<script setup lang="ts">
import { computed } from 'vue'

import type { Catalog } from '@/api/client'
import { cycleMuscle, type ExerciseForm, levelOf } from '@/catalog/exerciseForm'
import { texts } from '@/texts'

/**
 * Griglia dei muscoli della form (wireframe § 4.3): una riga per gruppo, un pulsante
 * a tre stati per muscolo. La lettera P o S è sempre scritta, non affidata al colore.
 */
const props = defineProps<{ catalog: Catalog; invalid?: boolean }>()
const form = defineModel<ExerciseForm>({ required: true })

const rows = computed(() =>
  props.catalog.muscle_groups
    .map((group) => ({
      group,
      muscles: props.catalog.muscles.filter((m) => m.muscle_group_id === group.id),
    }))
    .filter((row) => row.muscles.length > 0),
)

function toggle(muscleId: number): void {
  form.value = cycleMuscle(form.value, muscleId)
}
</script>

<template>
  <div class="grid" :class="{ invalid }" data-testid="muscle-grid">
    <div v-for="row in rows" :key="row.group.id" class="row">
      <span class="group">{{ row.group.name }}</span>
      <div class="muscles">
        <button
          v-for="muscle in row.muscles"
          :key="muscle.id"
          type="button"
          class="muscle"
          :class="`level-${levelOf(form, muscle.id) ?? 'none'}`"
          :title="muscle.name"
          :aria-label="texts.exerciseForm.muscleState(muscle.name, levelOf(form, muscle.id))"
          :data-testid="`muscle-${muscle.code}`"
          @click="toggle(muscle.id)"
        >
          <span class="letter" aria-hidden="true">{{ levelOf(form, muscle.id) ?? '' }}</span>
          {{ muscle.short_name }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  width: 100%;
}

.row {
  display: grid;
  grid-template-columns: 9rem minmax(0, 1fr);
  gap: 0.75rem;
  align-items: baseline;
}

.group {
  color: var(--muted-color);
  font-size: 0.875rem;
}

.muscles {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.muscle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 2rem;
  padding: 0.2rem 0.6rem 0.2rem 0.3rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: inherit;
  background: transparent;
  font: inherit;
  font-size: 0.875rem;
  cursor: pointer;
}

.muscle:hover {
  background: var(--hover-color);
}

.muscle:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 1px;
}

.letter {
  display: inline-block;
  width: 1.3rem;
  border-radius: 4px;
  font-weight: 700;
  text-align: center;
}

.level-S {
  border-color: var(--primary-color);
}

.level-S .letter {
  color: var(--primary-color);
  background: var(--hover-color);
}

.level-P {
  border-color: var(--primary-color);
  color: var(--primary-color);
  font-weight: 600;
}

.level-P .letter {
  color: var(--on-primary-color);
  background: var(--primary-color);
}

.invalid .muscle {
  border-color: var(--error-color);
}

@media (max-width: 767px) {
  .row {
    grid-template-columns: minmax(0, 1fr);
    gap: 0.3rem;
  }
}
</style>
