<script setup lang="ts">
import { NButton, NInputNumber } from 'naive-ui'
import { ArrowDown, ArrowUp } from 'lucide-vue-next'
import { computed } from 'vue'

import { type EquipmentItem, moveItem, type PreferencesValue } from '@/plans/preferences'
import { texts } from '@/texts'

/**
 * Ordine degli attrezzi e durata massima della seduta (wireframe, § 3.2 passo 2 e
 * § 3.5). L'ordine si cambia con le frecce: funziona allo stesso modo con il mouse,
 * con la tastiera e sul telefono.
 */
const props = defineProps<{
  value: PreferencesValue
  equipment: EquipmentItem[]
  errors?: Record<string, string>
}>()
const emit = defineEmits<{ 'update:value': [value: PreferencesValue] }>()
const t = texts.preferences

const names = computed(() => new Map(props.equipment.map((e) => [e.code, e.name])))

function move(index: number, delta: -1 | 1): void {
  emit('update:value', {
    ...props.value,
    equipment_order: moveItem(props.value.equipment_order, index, delta),
  })
}

function setMinutes(minutes: number | null): void {
  emit('update:value', { ...props.value, max_session_minutes: minutes })
}
</script>

<template>
  <section class="basics">
    <div class="field">
      <h3 id="equipment-label">{{ t.equipment }}</h3>
      <p class="help">{{ t.equipmentHelp }}</p>
      <ol class="equipment" aria-labelledby="equipment-label" data-testid="equipment-order">
        <li v-for="(code, index) in value.equipment_order" :key="code" data-testid="equipment">
          <span class="rank">{{ index + 1 }}</span>
          <span class="name">{{ names.get(code) ?? code }}</span>
          <NButton
            quaternary
            circle
            size="small"
            :disabled="index === 0"
            :aria-label="t.moveUp(names.get(code) ?? code)"
            data-testid="equipment-up"
            @click="move(index, -1)"
          >
            <template #icon><ArrowUp :size="16" /></template>
          </NButton>
          <NButton
            quaternary
            circle
            size="small"
            :disabled="index === value.equipment_order.length - 1"
            :aria-label="t.moveDown(names.get(code) ?? code)"
            data-testid="equipment-down"
            @click="move(index, 1)"
          >
            <template #icon><ArrowDown :size="16" /></template>
          </NButton>
        </li>
      </ol>
      <small v-if="errors?.equipment_order" class="error">{{ errors.equipment_order }}</small>
    </div>

    <label class="field">
      <h3>{{ t.maxMinutes }}</h3>
      <NInputNumber
        :value="value.max_session_minutes"
        :min="15"
        :max="300"
        :step="5"
        clearable
        :placeholder="t.noLimit"
        :status="errors?.max_session_minutes ? 'error' : undefined"
        class="minutes"
        data-testid="max-minutes"
        @update:value="setMinutes"
      >
        <template #suffix>{{ t.minutes }}</template>
      </NInputNumber>
      <small class="help">{{ t.noLimitHelp }}</small>
      <small v-if="errors?.max_session_minutes" class="error">
        {{ errors.max_session_minutes }}
      </small>
    </label>
  </section>
</template>

<style scoped>
.basics {
  display: grid;
  grid-template-columns: minmax(0, 22rem) minmax(0, 16rem);
  gap: 1.5rem 3rem;
  align-items: start;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.help {
  margin: 0;
  color: var(--muted-color);
  font-size: 0.875rem;
}

.equipment {
  margin: 0.25rem 0 0;
  padding: 0;
  list-style: none;
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.equipment li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.4rem 0.3rem 0.75rem;
}

.equipment li + li {
  border-top: 1px solid var(--border-color);
}

.rank {
  width: 1.25rem;
  color: var(--muted-color);
  font-variant-numeric: tabular-nums;
}

.name {
  flex: 1;
}

.minutes {
  max-width: 10rem;
}

.error {
  color: var(--error-color);
}

@media (max-width: 767px) {
  .basics {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
