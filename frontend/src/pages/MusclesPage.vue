<script setup lang="ts">
import { NAlert, NButton, NInput, NInputNumber, NSelect, NSkeleton, useMessage } from 'naive-ui'
import { Pencil } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'

import { api, asProblem, type Muscle, type Priority } from '@/api/client'
import { problemMessages } from '@/catalog/problems'
import CatalogHeader from '@/components/CatalogHeader.vue'
import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/** Muscoli: nomi, priorità e fascia del catalogo, modificabili in linea (US-07). */
const store = useCatalogStore()
const message = useMessage()
const t = texts.muscles
const e = texts.editing
const priorities = texts.labels.priority

interface Draft {
  name: string
  short_name: string
  priority: Priority
  weekly_min: number | null
  weekly_max: number | null
  notes: string
}

const editing = ref<number | null>(null)
const draft = ref<Draft | null>(null)
const errors = ref<Record<string, string>>({})
const general = ref<string[]>([])
const saving = ref(false)

onMounted(() => {
  void store.load()
})

const sections = computed(() => {
  const catalog = store.catalog
  if (catalog === null) return []
  return catalog.muscle_groups
    .map((group) => ({
      group,
      muscles: catalog.muscles.filter((m) => m.muscle_group_id === group.id),
    }))
    .filter((section) => section.muscles.length > 0)
})

const priorityOptions = (Object.keys(priorities) as Priority[]).map((p) => ({
  label: priorities[p],
  value: p,
}))

function startEdit(muscle: Muscle): void {
  editing.value = muscle.id
  draft.value = {
    name: muscle.name,
    short_name: muscle.short_name,
    priority: muscle.priority,
    weekly_min: muscle.weekly_min,
    weekly_max: muscle.weekly_max,
    notes: muscle.notes ?? '',
  }
  errors.value = {}
  general.value = []
}

function setPriority(priority: Priority): void {
  if (draft.value === null) return
  draft.value = { ...draft.value, priority }
}

/** Il server controlla la fascia e le schede che personalizzano il muscolo (CA2, CA3). */
async function save(muscle: Muscle): Promise<void> {
  if (draft.value === null) return
  const body = { ...draft.value }
  if (body.priority === 'none') {
    body.weekly_min = null
    body.weekly_max = null
  }
  saving.value = true
  try {
    const { data, error, response } = await api.PATCH('/api/muscles/{muscle_id}', {
      params: { path: { muscle_id: muscle.id } },
      body,
    })
    if (data === undefined) {
      const problem = asProblem(error, response.status)
      if (problem.code === 'invalid-band') {
        const plans = (problem.plans ?? []).map((plan) => plan.name)
        errors.value = {}
        general.value = [t.invalidBand(plans)]
        return
      }
      const mapped = problemMessages(problem, texts.exerciseForm.errors.invalid)
      errors.value = mapped.fields
      general.value = mapped.general
      return
    }
    message.success(e.saved)
    editing.value = null
    await store.load(true)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <main class="page">
    <CatalogHeader />
    <p class="intro">{{ t.intro }}</p>

    <NAlert v-if="store.failed" type="error">{{ texts.common.loadFailed }}</NAlert>
    <NSkeleton v-else-if="store.catalog === null" text :repeat="10" />

    <template v-else>
      <section v-for="{ group, muscles } in sections" :key="group.id" class="section">
        <h2>{{ group.name }}</h2>
        <div class="row head" aria-hidden="true">
          <span>{{ t.name }}</span>
          <span>{{ t.priority }}</span>
          <span>{{ t.min }}–{{ t.max }}</span>
          <span />
        </div>

        <template v-for="muscle in muscles" :key="muscle.id">
          <form
            v-if="editing === muscle.id && draft"
            class="edit"
            data-testid="muscle-edit"
            @submit.prevent="save(muscle)"
          >
            <label class="field wide">
              <span>{{ t.name }}</span>
              <NInput
                v-model:value="draft.name"
                :maxlength="120"
                :status="errors.name ? 'error' : undefined"
              />
              <small v-if="errors.name" class="error">{{ errors.name }}</small>
            </label>
            <label class="field">
              <span>{{ t.shortName }}</span>
              <NInput
                v-model:value="draft.short_name"
                :maxlength="40"
                :status="errors.short_name ? 'error' : undefined"
              />
            </label>
            <label class="field">
              <span>{{ t.priority }}</span>
              <NSelect
                :value="draft.priority"
                :options="priorityOptions"
                :virtual-scroll="false"
                data-testid="muscle-priority"
                @update:value="setPriority"
              />
            </label>
            <label class="field">
              <span>{{ t.min }}</span>
              <NInputNumber
                v-model:value="draft.weekly_min"
                :min="0"
                :max="100"
                :step="1"
                :disabled="draft.priority === 'none'"
                :status="errors.weekly_min ? 'error' : undefined"
                data-testid="muscle-min"
              />
              <small v-if="errors.weekly_min" class="error">{{ errors.weekly_min }}</small>
            </label>
            <label class="field">
              <span>{{ t.max }}</span>
              <NInputNumber
                v-model:value="draft.weekly_max"
                :min="0"
                :max="100"
                :step="1"
                :disabled="draft.priority === 'none'"
                :status="errors.weekly_max ? 'error' : undefined"
                data-testid="muscle-max"
              />
              <small v-if="errors.weekly_max" class="error">{{ errors.weekly_max }}</small>
            </label>
            <label class="field wide">
              <span>{{ t.notes }}</span>
              <NInput
                v-model:value="draft.notes"
                type="textarea"
                :autosize="{ minRows: 1, maxRows: 4 }"
                :placeholder="t.notesPlaceholder"
              />
            </label>
            <p v-for="text in general" :key="text" class="error wide" role="alert">{{ text }}</p>
            <div class="buttons wide">
              <NButton size="small" @click="editing = null">{{ e.cancel }}</NButton>
              <NButton
                size="small"
                type="primary"
                attr-type="submit"
                :loading="saving"
                data-testid="muscle-save"
              >
                {{ e.save }}
              </NButton>
            </div>
          </form>

          <div v-else class="row" data-testid="muscle-row">
            <div>
              <strong>{{ muscle.short_name }}</strong>
              <p class="muted small">{{ muscle.name }}</p>
            </div>
            <span :class="{ muted: muscle.priority === 'none' }">
              {{ priorities[muscle.priority] }}
            </span>
            <span>{{ t.band(muscle.weekly_min, muscle.weekly_max) }}</span>
            <NButton
              quaternary
              circle
              size="small"
              :disabled="editing !== null"
              :aria-label="`${e.edit} ${muscle.short_name}`"
              data-testid="muscle-edit-button"
              @click="startEdit(muscle)"
            >
              <template #icon><Pencil :size="16" /></template>
            </NButton>
          </div>
        </template>
      </section>
    </template>
  </main>
</template>

<style scoped>
.intro {
  max-width: 48rem;
  margin: 0.75rem 0 1rem;
  color: var(--muted-color);
}

.section h2 {
  margin: 1.5rem 0 0.25rem;
  font-size: 1.05rem;
}

.row {
  display: grid;
  grid-template-columns: minmax(0, 2.5fr) minmax(0, 1fr) 6rem 3rem;
  gap: 0.35rem 1rem;
  align-items: start;
  padding: 0.55rem 0.25rem;
  border-bottom: 1px solid var(--border-color);
}

.row.head {
  color: var(--muted-color);
  font-size: 0.875rem;
  font-weight: 500;
}

.small {
  margin: 0.1rem 0 0;
  font-size: 0.85rem;
}

.edit {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem 1rem;
  margin: 0.25rem 0;
  padding: 0.85rem;
  border-radius: 6px;
  background: var(--hover-color);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.875rem;
}

.field > span {
  color: var(--muted-color);
}

.wide {
  grid-column: 1 / -1;
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
  margin: 0;
  color: var(--error-color);
}

@media (max-width: 767px) {
  .row {
    grid-template-columns: minmax(0, 1fr) auto 3rem;
  }

  .row.head {
    display: none;
  }

  .row > :nth-child(2) {
    grid-column: 1;
    grid-row: 2;
    font-size: 0.875rem;
  }

  .row > :nth-child(3) {
    grid-column: 2;
    grid-row: 1;
  }

  .row > :nth-child(4) {
    grid-column: 3;
    grid-row: 1;
  }

  .edit {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
