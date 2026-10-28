<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, NModal, NRadioButton, NRadioGroup } from 'naive-ui'
import { ref, watch } from 'vue'

import { texts } from '@/texts'

/** Nome e volte a settimana di un giorno, nuovo o esistente (US-21 CA1-CA3). */
const props = defineProps<{
  show: boolean
  title: string
  action: string
  initialName?: string
  initialTimes?: number
}>()
const emit = defineEmits<{
  'update:show': [show: boolean]
  submit: [value: { name: string; times_per_week: number }]
}>()
const t = texts.editor

const name = ref('')
const times = ref(1)
const error = ref<string | null>(null)

watch(
  () => props.show,
  (show) => {
    if (!show) return
    name.value = props.initialName ?? ''
    times.value = props.initialTimes ?? 1
    error.value = null
  },
  { immediate: true },
)

function submit(): void {
  const trimmed = name.value.trim()
  if (trimmed === '') {
    error.value = t.nameRequired
    return
  }
  emit('submit', { name: trimmed, times_per_week: times.value })
}
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    :title="title"
    style="width: min(26rem, calc(100vw - 2rem))"
    data-testid="day-dialog"
    @update:show="(value: boolean) => emit('update:show', value)"
  >
    <NForm @submit.prevent="submit">
      <NFormItem
        :label="t.dayName"
        :validation-status="error ? 'error' : undefined"
        :feedback="error ?? undefined"
      >
        <NInput
          v-model:value="name"
          :maxlength="80"
          :placeholder="t.dayNamePlaceholder"
          data-testid="day-name"
        />
      </NFormItem>
      <NFormItem :label="t.times">
        <NRadioGroup v-model:value="times" data-testid="day-times">
          <NRadioButton v-for="n in [1, 2, 3]" :key="n" :value="n" :label="String(n)" />
        </NRadioGroup>
      </NFormItem>
    </NForm>
    <template #footer>
      <div class="actions">
        <NButton @click="emit('update:show', false)">{{ t.cancel }}</NButton>
        <NButton type="primary" data-testid="day-save" @click="submit">{{ action }}</NButton>
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
</style>
