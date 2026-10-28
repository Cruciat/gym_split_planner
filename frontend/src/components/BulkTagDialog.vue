<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, NModal, NSelect, useMessage } from 'naive-ui'
import { computed, ref, watch } from 'vue'

import { api, asProblem } from '@/api/client'
import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/**
 * Assegna o toglie un'etichetta su più esercizi insieme (US-08 CA2; wireframe § 4.1).
 * La nota, facoltativa, vale per tutti: lasciata vuota, chi aveva già l'etichetta
 * conserva la sua (API, § 6.3).
 */
const props = defineProps<{ mode: 'assign' | 'unassign'; exerciseIds: number[] }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ done: [] }>()

const store = useCatalogStore()
const message = useMessage()
const t = texts.bulkTags

const tagId = ref<number | null>(null)
const note = ref('')
const saving = ref(false)
const error = ref<string | null>(null)

watch(show, (open) => {
  if (open) {
    tagId.value = null
    note.value = ''
    error.value = null
  }
})

const tagOptions = computed(
  () => store.catalog?.tags.map((tag) => ({ label: tag.name, value: tag.id })) ?? [],
)
const title = computed(() =>
  props.mode === 'assign'
    ? t.assignTitle(props.exerciseIds.length)
    : t.unassignTitle(props.exerciseIds.length),
)

async function submit(): Promise<void> {
  if (tagId.value === null) return
  const tagName = store.tags.get(tagId.value)?.name ?? ''
  saving.value = true
  error.value = null
  try {
    const params = { path: { tag_id: tagId.value } }
    const result =
      props.mode === 'assign'
        ? await api.POST('/api/tags/{tag_id}/assign', {
            params,
            body: {
              exercise_ids: props.exerciseIds,
              ...(note.value.trim() === '' ? {} : { note: note.value }),
            },
          })
        : await api.POST('/api/tags/{tag_id}/unassign', {
            params,
            body: { exercise_ids: props.exerciseIds },
          })
    if (result.data === undefined) {
      const problem = asProblem(result.error, result.response.status)
      error.value = problem.detail ?? problem.title
      return
    }
    await store.load(true)
    message.success(
      props.mode === 'assign' ? t.assigned(tagName, result.data.exercises) : t.unassigned(tagName),
    )
    show.value = false
    emit('done')
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
    :title="title"
    style="width: min(30rem, calc(100vw - 2rem))"
    data-testid="bulk-tag-dialog"
  >
    <NForm @submit.prevent="submit">
      <NFormItem :label="t.tag" required>
        <NSelect
          v-model:value="tagId"
          :options="tagOptions"
          :virtual-scroll="false"
          :placeholder="t.tagPlaceholder"
          data-testid="bulk-tag"
        />
      </NFormItem>
      <NFormItem v-if="mode === 'assign'" :label="t.note" :feedback="t.noteHelp">
        <NInput v-model:value="note" :maxlength="120" data-testid="bulk-note" />
      </NFormItem>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
    </NForm>
    <template #footer>
      <div class="actions">
        <NButton @click="show = false">{{ t.cancel }}</NButton>
        <NButton
          type="primary"
          :disabled="tagId === null"
          :loading="saving"
          data-testid="bulk-submit"
          @click="submit"
        >
          {{ mode === 'assign' ? t.assign : t.unassign }}
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
