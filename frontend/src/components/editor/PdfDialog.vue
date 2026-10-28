<script setup lang="ts">
import { NButton, NModal, NRadioButton, NRadioGroup } from 'naive-ui'
import { ref, watch } from 'vue'

import { WEEK_OPTIONS } from '@/plans/pdf'
import { texts } from '@/texts'

/** Sul telefono: quante settimane annotare, poi lo scarico (wireframe, § 3.7). */
const props = defineProps<{ show: boolean; weeks: number; loading: boolean }>()
const emit = defineEmits<{ 'update:show': [show: boolean]; download: [weeks: number] }>()
const t = texts.editor

const chosen = ref(props.weeks)
watch(
  () => props.show,
  (show) => {
    if (show) chosen.value = props.weeks
  },
)
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    :title="t.pdfTitle"
    style="width: min(26rem, calc(100vw - 2rem))"
    data-testid="pdf-dialog"
    @update:show="(value: boolean) => emit('update:show', value)"
  >
    <p class="label">{{ t.pdfChooseWeeks }}</p>
    <NRadioGroup v-model:value="chosen" data-testid="pdf-weeks">
      <NRadioButton v-for="n in WEEK_OPTIONS" :key="n" :value="n" :label="String(n)" />
    </NRadioGroup>
    <p class="help">{{ t.pdfHelp }}</p>
    <template #footer>
      <div class="actions">
        <NButton @click="emit('update:show', false)">{{ t.cancel }}</NButton>
        <NButton
          type="primary"
          :loading="loading"
          data-testid="pdf-download"
          @click="emit('download', chosen)"
        >
          {{ t.pdfDownload }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.label {
  margin: 0 0 0.5rem;
}

.help {
  margin: 0.75rem 0 0;
  color: var(--muted-color);
  font-size: 0.875rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}
</style>
