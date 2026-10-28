<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, NModal } from 'naive-ui'
import { computed, ref, watch } from 'vue'

import { api, asProblem, type Source } from '@/api/client'
import { texts } from '@/texts'

/** Finestra per aggiungere una fonte dalla form dell'esercizio (API, § 6.3). */
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ created: [source: Source] }>()

const t = texts.sourceForm
const title = ref('')
const kind = ref('')
const url = ref('')
const reliability = ref('')
const saving = ref(false)
const error = ref<string | null>(null)

watch(show, (open) => {
  if (open) {
    title.value = kind.value = url.value = reliability.value = ''
    error.value = null
  }
})

const urlInvalid = computed(
  () => url.value.trim() !== '' && !/^https?:\/\//i.test(url.value.trim()),
)
const canSave = computed(
  () => title.value.trim() !== '' && kind.value.trim() !== '' && !urlInvalid.value,
)

async function save(): Promise<void> {
  if (!canSave.value) return
  saving.value = true
  error.value = null
  try {
    const {
      data,
      error: problem,
      response,
    } = await api.POST('/api/sources', {
      body: {
        title: title.value,
        kind: kind.value,
        url: url.value.trim() === '' ? null : url.value,
        reliability: reliability.value.trim() === '' ? null : reliability.value,
      },
    })
    if (data === undefined) {
      const p = asProblem(problem, response.status)
      error.value = p.detail ?? p.title
      return
    }
    emit('created', data)
    show.value = false
  } catch {
    error.value = texts.common.loadFailed
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="t.title"
    style="width: min(32rem, calc(100vw - 2rem))"
    data-testid="source-dialog"
  >
    <NForm @submit.prevent="save">
      <NFormItem :label="t.sourceTitle" required>
        <NInput
          v-model:value="title"
          :placeholder="t.titlePlaceholder"
          data-testid="source-title"
        />
      </NFormItem>
      <NFormItem :label="t.kind" required>
        <NInput v-model:value="kind" :placeholder="t.kindPlaceholder" data-testid="source-kind" />
      </NFormItem>
      <NFormItem
        :label="t.url"
        :validation-status="urlInvalid ? 'error' : undefined"
        :feedback="urlInvalid ? t.urlInvalid : undefined"
      >
        <NInput v-model:value="url" placeholder="https://" data-testid="source-url" />
      </NFormItem>
      <NFormItem :label="t.reliability">
        <NInput v-model:value="reliability" :placeholder="t.reliabilityPlaceholder" />
      </NFormItem>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
    </NForm>
    <template #footer>
      <div class="actions">
        <NButton @click="show = false">{{ t.cancel }}</NButton>
        <NButton
          type="primary"
          :disabled="!canSave"
          :loading="saving"
          data-testid="source-save"
          @click="save"
        >
          {{ t.create }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.error {
  margin: 0;
  color: var(--error-color);
}
</style>
