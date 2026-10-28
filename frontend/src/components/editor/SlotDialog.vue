<script setup lang="ts">
import { NButton, NForm, NFormItem, NModal, NSelect, type SelectOption } from 'naive-ui'
import { computed, ref, watch } from 'vue'

import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/**
 * Famiglia, poi esercizio (US-16 CA3, CA5). Per aggiungere uno slot si sceglie la
 * famiglia e, se si vuole, l'esercizio; senza, il server mette il migliore. Per
 * cambiare famiglia basta la famiglia: l'esercizio lo sceglie il server.
 */
const props = defineProps<{
  show: boolean
  mode: 'add' | 'family'
  currentFamilyId?: number | null
}>()
const emit = defineEmits<{
  'update:show': [show: boolean]
  submit: [value: { family_id: number; exercise_id: number | null }]
}>()
const t = texts.editor
const store = useCatalogStore()

const familyId = ref<number | null>(null)
const exerciseId = ref<number | null>(null)

watch(
  () => props.show,
  (show) => {
    if (!show) return
    void store.load()
    familyId.value = props.mode === 'family' ? null : (props.currentFamilyId ?? null)
    exerciseId.value = null
  },
  { immediate: true },
)

watch(familyId, () => {
  exerciseId.value = null
})

/** Famiglie raggruppate per gruppo muscolare, nell'ordine del catalogo. */
const familyOptions = computed<SelectOption[]>(() => {
  const catalog = store.catalog
  if (catalog === null) return []
  const groups = [...catalog.muscle_groups].sort((a, b) => a.sort_order - b.sort_order)
  return groups.flatMap((group) => {
    const families = catalog.families
      .filter((f) => f.muscle_group_id === group.id && f.id !== props.currentFamilyId)
      .sort((a, b) => a.sort_order - b.sort_order)
    return families.length === 0
      ? []
      : [
          {
            type: 'group',
            label: group.name,
            key: `group-${String(group.id)}`,
            children: families.map((f) => ({ label: f.name, value: f.id })),
          },
        ]
  })
})

/** Esercizi attivi della famiglia, come principale o secondaria, dal preferito. */
const exerciseOptions = computed<SelectOption[]>(() => {
  const id = familyId.value
  const catalog = store.catalog
  if (id === null || catalog === null) return []
  const exercises = catalog.exercises
    .filter((e) => e.is_active && (e.primary_family_id === id || e.secondary_family_id === id))
    .sort((a, b) => a.family_rank - b.family_rank || a.name.localeCompare(b.name, 'it'))
  return [
    { label: t.bestCandidate, value: -1 },
    ...exercises.map((e) => ({ label: e.name, value: e.id })),
  ]
})

function submit(): void {
  if (familyId.value === null) return
  emit('submit', {
    family_id: familyId.value,
    exercise_id: exerciseId.value === null || exerciseId.value < 0 ? null : exerciseId.value,
  })
}
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    :title="mode === 'add' ? t.addSlotTitle : t.changeFamilyTitle"
    style="width: min(30rem, calc(100vw - 2rem))"
    data-testid="slot-dialog"
    @update:show="(value: boolean) => emit('update:show', value)"
  >
    <NForm @submit.prevent="submit">
      <NFormItem :label="t.family">
        <NSelect
          v-model:value="familyId"
          :options="familyOptions"
          :placeholder="t.familyPlaceholder"
          :virtual-scroll="false"
          filterable
          data-testid="slot-family"
        />
      </NFormItem>
      <NFormItem v-if="mode === 'add'" :label="t.exercise">
        <NSelect
          :value="exerciseId ?? -1"
          :options="exerciseOptions"
          :disabled="familyId === null"
          :virtual-scroll="false"
          filterable
          data-testid="slot-exercise"
          @update:value="(value: number) => (exerciseId = value)"
        />
      </NFormItem>
      <p v-else class="help">{{ t.changeFamilyHelp }}</p>
    </NForm>
    <template #footer>
      <div class="actions">
        <NButton @click="emit('update:show', false)">{{ t.cancel }}</NButton>
        <NButton
          type="primary"
          :disabled="familyId === null"
          data-testid="slot-save"
          @click="submit"
        >
          {{ mode === 'add' ? t.add : t.change }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.help {
  margin: 0;
  color: var(--muted-color);
  font-size: 0.875rem;
}
</style>
