<script setup lang="ts">
import {
  NAlert,
  NButton,
  NInput,
  NSelect,
  NSkeleton,
  type SelectOption,
  useDialog,
  useMessage,
} from 'naive-ui'
import { Pencil, Plus, Trash2 } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'

import { api, asProblem, type Family } from '@/api/client'
import { problemMessages } from '@/catalog/problems'
import CatalogHeader from '@/components/CatalogHeader.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/** Famiglie di movimento, modificabili in linea (US-06, wireframe § 4.4). */
const store = useCatalogStore()
const message = useMessage()
const dialog = useDialog()
const confirm = useConfirm()
const t = texts.families
const e = texts.editing

interface Draft {
  name: string
  muscle_group_id: number | null
  description: string
}

/** Riga in modifica: l'`id` della famiglia, `'new'` per quella nuova, `null` per nessuna. */
const editing = ref<number | 'new' | null>(null)
const draft = ref<Draft>({ name: '', muscle_group_id: null, description: '' })
const errors = ref<Record<string, string>>({})
const general = ref<string[]>([])
const saving = ref(false)

onMounted(() => {
  void store.load()
})

const families = computed(() =>
  [...(store.catalog?.families ?? [])].sort((a, b) => a.sort_order - b.sort_order),
)
const groupOptions = computed<SelectOption[]>(
  () => store.catalog?.muscle_groups.map((g) => ({ label: g.name, value: g.id })) ?? [],
)
const groupName = (id: number) => store.groups.get(id)?.name ?? ''

function counts(familyId: number): { primary: number; secondary: number } {
  const exercises = store.catalog?.exercises ?? []
  return {
    primary: exercises.filter((x) => x.primary_family_id === familyId).length,
    secondary: exercises.filter((x) => x.secondary_family_id === familyId).length,
  }
}

function startEdit(family: Family | null): void {
  editing.value = family?.id ?? 'new'
  draft.value = {
    name: family?.name ?? '',
    muscle_group_id: family?.muscle_group_id ?? null,
    description: family?.description ?? '',
  }
  errors.value = {}
  general.value = []
}

function cancel(): void {
  editing.value = null
}

async function save(): Promise<void> {
  const local: Record<string, string> = {}
  if (draft.value.name.trim() === '') local.name = texts.exerciseForm.errors.nameRequired
  if (draft.value.muscle_group_id === null) local.muscle_group_id = t.groupPlaceholder
  errors.value = local
  if (Object.keys(local).length > 0 || draft.value.muscle_group_id === null) return

  const body = {
    name: draft.value.name,
    muscle_group_id: draft.value.muscle_group_id,
    description: draft.value.description,
  }
  saving.value = true
  try {
    const result =
      editing.value === 'new'
        ? await api.POST('/api/families', { body })
        : await api.PATCH('/api/families/{family_id}', {
            params: { path: { family_id: editing.value ?? 0 } },
            body,
          })
    if (result.data === undefined) {
      const mapped = problemMessages(
        asProblem(result.error, result.response.status),
        texts.exerciseForm.errors.invalid,
      )
      errors.value = mapped.fields
      general.value = mapped.general
      return
    }
    message.success(editing.value === 'new' ? e.created : e.saved)
    editing.value = null
    await store.load(true)
  } finally {
    saving.value = false
  }
}

/** Elimina solo una famiglia non usata; altrimenti spiega da cosa è usata (US-06 CA2). */
async function remove(family: Family): Promise<void> {
  const {
    data: usage,
    error,
    response,
  } = await api.GET('/api/families/{family_id}/usage', {
    params: { path: { family_id: family.id } },
  })
  if (usage === undefined) {
    const problem = asProblem(error, response.status)
    message.error(problem.detail ?? problem.title)
    return
  }
  if (usage.exercises > 0 || usage.split_slots > 0 || usage.plans.length > 0) {
    dialog.info({
      title: t.inUseTitle,
      content: t.inUse(
        family.name,
        usage.exercises,
        usage.split_slots,
        usage.plans.map((p) => p.name),
      ),
      positiveText: t.close,
    })
    return
  }
  const confirmed = await confirm({
    title: t.deleteTitle,
    content: t.deleteConfirm(family.name, usage.secondary_exercises),
    action: t.deleteAction,
    cancel: e.cancel,
  })
  if (!confirmed) return
  const result = await api.DELETE('/api/families/{family_id}', {
    params: { path: { family_id: family.id } },
  })
  if (!result.response.ok) {
    const problem = asProblem(result.error, result.response.status)
    message.error(problem.detail ?? problem.title)
    return
  }
  message.success(e.deleted)
  await store.load(true)
}
</script>

<template>
  <main class="page">
    <CatalogHeader>
      <NButton
        type="primary"
        :disabled="editing !== null"
        data-testid="add-family"
        @click="startEdit(null)"
      >
        <template #icon><Plus :size="16" /></template>
        {{ t.add }}
      </NButton>
    </CatalogHeader>
    <p class="intro">{{ t.intro }}</p>

    <NAlert v-if="store.failed" type="error">{{ texts.common.loadFailed }}</NAlert>
    <NSkeleton v-else-if="store.catalog === null" text :repeat="8" />

    <div v-else class="rows" data-testid="family-rows">
      <div class="row head" aria-hidden="true">
        <span>{{ t.name }}</span>
        <span>{{ t.group }}</span>
        <span>{{ t.exercises }}</span>
        <span />
      </div>

      <template
        v-for="family in editing === 'new' ? [null, ...families] : families"
        :key="family?.id ?? 'new'"
      >
        <form
          v-if="
            (family === null && editing === 'new') || (family !== null && editing === family.id)
          "
          class="row editing"
          data-testid="family-edit"
          @submit.prevent="save"
        >
          <div class="field">
            <NInput
              v-model:value="draft.name"
              :maxlength="120"
              :placeholder="t.namePlaceholder"
              :status="errors.name ? 'error' : undefined"
              :input-props="{ 'aria-label': t.name }"
              data-testid="family-name"
            />
            <small v-if="errors.name" class="error">{{ errors.name }}</small>
            <NInput
              v-model:value="draft.description"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 4 }"
              :placeholder="t.description"
              :input-props="{ 'aria-label': t.description }"
            />
          </div>
          <div class="field">
            <NSelect
              v-model:value="draft.muscle_group_id"
              :options="groupOptions"
              :virtual-scroll="false"
              :placeholder="t.groupPlaceholder"
              :status="errors.muscle_group_id ? 'error' : undefined"
              data-testid="family-group"
            />
          </div>
          <span class="muted">
            {{
              family ? t.exerciseCount(counts(family.id).primary, counts(family.id).secondary) : ''
            }}
          </span>
          <div class="buttons">
            <NButton size="small" @click="cancel">{{ e.cancel }}</NButton>
            <NButton
              size="small"
              type="primary"
              attr-type="submit"
              :loading="saving"
              data-testid="family-save"
            >
              {{ e.save }}
            </NButton>
          </div>
          <p v-for="text in general" :key="text" class="error general" role="alert">{{ text }}</p>
        </form>

        <div v-else-if="family" class="row" data-testid="family-row">
          <div>
            <strong>{{ family.name }}</strong>
            <p v-if="family.description" class="muted description">{{ family.description }}</p>
          </div>
          <span>{{ groupName(family.muscle_group_id) }}</span>
          <span>{{ t.exerciseCount(counts(family.id).primary, counts(family.id).secondary) }}</span>
          <div class="buttons">
            <NButton
              quaternary
              circle
              size="small"
              :disabled="editing !== null"
              :aria-label="`${e.edit} ${family.name}`"
              data-testid="family-edit-button"
              @click="startEdit(family)"
            >
              <template #icon><Pencil :size="16" /></template>
            </NButton>
            <NButton
              quaternary
              circle
              size="small"
              type="error"
              :disabled="editing !== null"
              :aria-label="`${e.delete} ${family.name}`"
              data-testid="family-delete"
              @click="remove(family)"
            >
              <template #icon><Trash2 :size="16" /></template>
            </NButton>
          </div>
        </div>
      </template>
    </div>
  </main>
</template>

<style scoped>
.intro {
  max-width: 48rem;
  margin: 0.75rem 0 1.25rem;
  color: var(--muted-color);
}

.rows {
  display: flex;
  flex-direction: column;
}

.row {
  display: grid;
  grid-template-columns: minmax(0, 2.2fr) minmax(0, 1fr) minmax(0, 1fr) 5rem;
  gap: 0.35rem 1rem;
  align-items: start;
  padding: 0.6rem 0.25rem;
  border-bottom: 1px solid var(--border-color);
}

.row.head {
  color: var(--muted-color);
  font-size: 0.875rem;
  font-weight: 500;
}

.row.editing {
  background: var(--hover-color);
  border-radius: 6px;
  padding: 0.75rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.description {
  margin: 0.15rem 0 0;
  font-size: 0.875rem;
}

.buttons {
  display: flex;
  gap: 0.35rem;
  justify-content: flex-end;
}

.muted {
  color: var(--muted-color);
}

.error {
  color: var(--error-color);
}

.general {
  grid-column: 1 / -1;
  margin: 0;
}

@media (max-width: 767px) {
  .row {
    grid-template-columns: minmax(0, 1fr) 5rem;
  }

  .row.head {
    display: none;
  }

  .row > :nth-child(2),
  .row > :nth-child(3) {
    grid-column: 1;
    color: var(--muted-color);
    font-size: 0.875rem;
  }

  .row > .buttons {
    grid-column: 2;
    grid-row: 1;
  }

  .row.editing > .field,
  .row.editing > .buttons {
    grid-column: 1 / -1;
    grid-row: auto;
  }
}
</style>
