<script setup lang="ts">
import { NAlert, NButton, NH1, NInput, NSkeleton, useMessage } from 'naive-ui'
import { FilePlus } from 'lucide-vue-next'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { api, asProblem, type Split } from '@/api/client'
import OverridesEditor from '@/components/OverridesEditor.vue'
import PreferencesBasics from '@/components/PreferencesBasics.vue'
import {
  defaultPlanName,
  defaultPreferences,
  equipmentItems,
  muscleRowsFromCatalog,
  overrideCount,
  preferenceErrors,
  type PreferencesValue,
  tagRowsFromCatalog,
  toInput,
} from '@/plans/preferences'
import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/**
 * Creazione guidata (US-10, US-11; wireframe, § 3.2): da dove parti, preferenze, nome.
 * Il passo 2 ha valori già pronti; le personalizzazioni usano la stessa schermata delle
 * preferenze della scheda, con i valori del catalogo come base.
 */
const t = texts.planNew
const store = useCatalogStore()
const router = useRouter()
const message = useMessage()

const step = ref<1 | 2 | 3>(1)
const splits = ref<Split[] | null>(null)
const failed = ref(false)
/** Lo split scelto, `null` per la scheda vuota; `undefined` finché non si sceglie. */
const choice = ref<Split | null | undefined>(undefined)
const value = ref<PreferencesValue | null>(null)
const customizing = ref(false)
const name = ref('')
const nameEdited = ref(false)
const errors = ref<Record<string, string>>({})
const general = ref<string[]>([])
const creating = ref(false)

onMounted(async () => {
  try {
    const [result] = await Promise.all([api.GET('/api/splits'), store.load()])
    if (result.data === undefined) failed.value = true
    else splits.value = result.data
  } catch {
    failed.value = true
  }
})

watch(
  () => store.catalog,
  (catalog) => {
    if (catalog !== null && value.value === null) value.value = defaultPreferences(catalog)
  },
  { immediate: true },
)

const equipment = computed(() => (store.catalog ? equipmentItems(store.catalog) : []))
const muscles = computed(() => (store.catalog ? muscleRowsFromCatalog(store.catalog) : []))
const tags = computed(() => (store.catalog ? tagRowsFromCatalog(store.catalog) : []))
const ready = computed(() => splits.value !== null && value.value !== null)

function dayNames(split: Split): string {
  return split.days.map((d) => t.dayName(d.name, d.times_per_week)).join(' · ')
}

function choose(split: Split | null): void {
  choice.value = split
  if (!nameEdited.value) name.value = defaultPlanName(split?.name ?? null, t.empty, new Date())
  step.value = 2
}

function updateName(text: string): void {
  name.value = text
  nameEdited.value = true
}

function updateValue(next: PreferencesValue): void {
  value.value = next
  errors.value = {}
}

async function create(): Promise<void> {
  if (choice.value === undefined || value.value === null) return
  creating.value = true
  general.value = []
  try {
    const trimmed = name.value.trim()
    const { data, error, response } = await api.POST('/api/plans', {
      body: {
        split_id: choice.value?.id ?? null,
        name: trimmed === '' ? null : trimmed,
        preferences: toInput(value.value),
      },
    })
    if (data === undefined) {
      const mapped = preferenceErrors(asProblem(error, response.status), texts.preferences.invalid)
      errors.value = mapped.fields
      general.value = mapped.general
      const fields = Object.keys(mapped.fields)
      // Un errore sulle preferenze si corregge al passo 2, dove c'è il campo.
      if (fields.some((f) => f !== 'name')) {
        step.value = 2
        customizing.value ||= fields.some((f) => f.startsWith('overrides.'))
      }
      return
    }
    message.success(t.created(data.name))
    await router.push(`/schede/${String(data.id)}`)
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <main class="page">
    <NH1>{{ t.title }}</NH1>

    <NAlert v-if="failed || store.failed" type="error">{{ texts.common.loadFailed }}</NAlert>
    <NSkeleton v-else-if="!ready" text :repeat="4" />

    <template v-else>
      <h2 class="step" data-testid="step">{{ t.step(step, t.steps[step - 1] ?? '') }}</h2>

      <!-- Passo 1: split predefinito o scheda vuota -->
      <div v-if="step === 1" class="cards" data-testid="split-choices">
        <button
          v-for="split in splits"
          :key="split.id"
          type="button"
          class="card"
          :aria-pressed="choice?.id === split.id"
          data-testid="split-choice"
          @click="choose(split)"
        >
          <strong>{{ split.name }}</strong>
          <span class="muted">{{ t.days(split.days_per_week) }}</span>
          <span class="days">{{ dayNames(split) }}</span>
          <span v-if="split.description" class="muted description">{{ split.description }}</span>
        </button>
        <button
          type="button"
          class="card empty"
          :aria-pressed="choice === null"
          data-testid="empty-choice"
          @click="choose(null)"
        >
          <FilePlus :size="20" aria-hidden="true" />
          <strong>{{ t.empty }}</strong>
          <span class="muted">{{ t.emptyHelp }}</span>
        </button>
      </div>

      <!-- Passo 2: preferenze, con valori già pronti -->
      <section v-else-if="step === 2 && value" class="preferences">
        <PreferencesBasics
          :value="value"
          :equipment="equipment"
          :errors="errors"
          @update:value="updateValue"
        />
        <div class="overrides-line">
          <strong>{{ t.overrides }}:</strong>
          <span data-testid="overrides-summary">
            {{
              overrideCount(value.overrides) === 0
                ? t.asCatalog
                : t.customized(overrideCount(value.overrides))
            }}
          </span>
          <NButton
            size="small"
            secondary
            data-testid="customize"
            @click="customizing = !customizing"
          >
            {{ customizing ? t.hideCustomize : t.customize }}
          </NButton>
        </div>
        <OverridesEditor
          v-if="customizing"
          :overrides="value.overrides"
          :muscles="muscles"
          :tags="tags"
          :errors="errors"
          @update:overrides="(overrides) => value && updateValue({ ...value, overrides })"
        />
      </section>

      <!-- Passo 3: nome -->
      <form v-else-if="step === 3" class="name-step" @submit.prevent="create">
        <label class="field">
          <span>{{ t.name }}</span>
          <NInput
            :value="name"
            :maxlength="120"
            :status="errors.name ? 'error' : undefined"
            data-testid="plan-name"
            @update:value="updateName"
          />
          <small class="muted">{{ t.nameHelp }}</small>
          <small v-if="errors.name" class="error">{{ errors.name }}</small>
        </label>
      </form>

      <p v-for="text in general" :key="text" class="error" role="alert">{{ text }}</p>

      <div class="buttons">
        <NButton v-if="step === 1" @click="router.push('/schede')">{{ t.cancel }}</NButton>
        <NButton v-else data-testid="back" @click="step = step === 3 ? 2 : 1">
          {{ t.back }}
        </NButton>
        <NButton
          v-if="step === 1 && choice !== undefined"
          type="primary"
          data-testid="next"
          @click="step = 2"
        >
          {{ t.next }}
        </NButton>
        <NButton v-if="step === 2" type="primary" data-testid="next" @click="step = 3">
          {{ t.next }}
        </NButton>
        <NButton
          v-if="step === 3"
          type="primary"
          :loading="creating"
          data-testid="create"
          @click="create"
        >
          {{ t.create }}
        </NButton>
      </div>
    </template>
  </main>
</template>

<style scoped>
.step {
  margin: 0.5rem 0 1rem;
  font-size: 1.1rem;
  font-weight: 600;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr));
  gap: 0.75rem;
}

.card {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--surface-color);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.card:hover,
.card:focus-visible {
  border-color: var(--primary-color);
}

.card[aria-pressed='true'] {
  border-color: var(--primary-color);
  box-shadow: inset 0 0 0 1px var(--primary-color);
}

.card.empty {
  border-style: dashed;
}

.days {
  font-size: 0.9rem;
}

.description {
  font-size: 0.875rem;
}

.preferences {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.overrides-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.name-step {
  max-width: 32rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.buttons {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.muted {
  color: var(--muted-color);
}

.error {
  color: var(--error-color);
}
</style>
