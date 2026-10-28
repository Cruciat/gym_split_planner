<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, NModal } from 'naive-ui'
import { ref, watch } from 'vue'

import { texts } from '@/texts'

/** Un testo da scrivere: nome della scheda, nota dell'esercizio. */
const props = defineProps<{
  show: boolean
  title: string
  label: string
  value: string
  action: string
  required?: boolean
  multiline?: boolean
  placeholder?: string
  maxlength?: number
}>()
const emit = defineEmits<{ 'update:show': [show: boolean]; submit: [value: string] }>()
const t = texts.editor

const text = ref('')
const error = ref<string | null>(null)

watch(
  () => props.show,
  (show) => {
    if (!show) return
    text.value = props.value
    error.value = null
  },
  { immediate: true },
)

function submit(): void {
  const trimmed = text.value.trim()
  if (props.required && trimmed === '') {
    error.value = t.nameRequired
    return
  }
  emit('submit', trimmed)
}
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    :title="title"
    style="width: min(30rem, calc(100vw - 2rem))"
    data-testid="text-dialog"
    @update:show="(value: boolean) => emit('update:show', value)"
  >
    <NForm @submit.prevent="submit">
      <NFormItem
        :label="label"
        :validation-status="error ? 'error' : undefined"
        :feedback="error ?? undefined"
      >
        <NInput
          v-model:value="text"
          :type="multiline ? 'textarea' : 'text'"
          :autosize="multiline ? { minRows: 2, maxRows: 6 } : undefined"
          :maxlength="maxlength ?? 120"
          :placeholder="placeholder"
          data-testid="text-input"
        />
      </NFormItem>
    </NForm>
    <template #footer>
      <div class="actions">
        <NButton @click="emit('update:show', false)">{{ t.cancel }}</NButton>
        <NButton type="primary" data-testid="text-save" @click="submit">{{ action }}</NButton>
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
