<script setup lang="ts">
import {
  NAlert,
  NButton,
  NForm,
  NFormItem,
  NH1,
  NInput,
  NInputNumber,
  NRadioButton,
  NRadioGroup,
  NSelect,
  NSkeleton,
  type SelectGroupOption,
  type SelectOption,
  useDialog,
  useMessage,
} from 'naive-ui'
import { ChevronLeft, X } from 'lucide-vue-next'
import { computed, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, RouterLink, useRouter } from 'vue-router'

import { api, asProblem, type Confidence, type Kind, type Source, type Stretch } from '@/api/client'
import {
  emptyForm,
  errorsFromProblem,
  type ExerciseForm,
  type FormErrors,
  type FormField,
  formFromDetail,
  nextRank,
  toExerciseInput,
  validateForm,
} from '@/catalog/exerciseForm'
import { symbolIcon } from '@/catalog/symbols'
import MuscleGrid from '@/components/MuscleGrid.vue'
import SourceDialog from '@/components/SourceDialog.vue'
import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/** Creazione e modifica di un esercizio (US-03, US-04; wireframe § 4.3). */
const props = defineProps<{ id?: number }>()

const store = useCatalogStore()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const t = texts.exerciseForm
const labels = texts.labels

const editing = computed(() => props.id !== undefined)
const form = ref<ExerciseForm>(emptyForm())
const saved = ref('')
/** Nome com'era all'apertura, per il titolo della pagina. */
const originalName = ref('')
const state = ref<'loading' | 'ready' | 'not-found' | 'failed'>('loading')
const saving = ref(false)
const errors = ref<FormErrors>({})
const general = ref<string[]>([])
const showSourceDialog = ref(false)
/** Rango toccato a mano: da lì in poi non segue più la famiglia scelta. */
const rankTouched = ref(false)
/** Dopo un salvataggio riuscito si esce senza chiedere conferma. */
let leaving = false

const snapshot = () => JSON.stringify(form.value)
const dirty = computed(() => state.value === 'ready' && JSON.stringify(form.value) !== saved.value)

async function load(): Promise<void> {
  state.value = 'loading'
  try {
    await store.load()
    if (store.catalog === null) {
      state.value = 'failed'
      return
    }
    if (props.id === undefined) {
      form.value = emptyForm()
    } else {
      const { data, response } = await api.GET('/api/exercises/{exercise_id}', {
        params: { path: { exercise_id: props.id } },
      })
      if (data === undefined) {
        state.value = response.status === 404 ? 'not-found' : 'failed'
        return
      }
      form.value = formFromDetail(data)
      originalName.value = data.name
      rankTouched.value = true
    }
    saved.value = snapshot()
    state.value = 'ready'
  } catch {
    state.value = 'failed'
  }
}

onMounted(load)

// Un esercizio nuovo va in fondo alla sua famiglia, finché il rango non si cambia a mano.
watch(
  () => form.value.primary_family_id,
  (familyId) => {
    if (!rankTouched.value && familyId !== null && store.catalog !== null) {
      form.value = { ...form.value, family_rank: nextRank(store.catalog, familyId) }
    }
  },
)

// Correggendo un campo, il suo errore sparisce.
watch(form, (current, previous) => {
  const changed = (Object.keys(errors.value) as FormField[]).filter((field) => {
    const key = field as keyof ExerciseForm
    return JSON.stringify(current[key]) !== JSON.stringify(previous[key])
  })
  if (changed.length > 0) {
    errors.value = Object.fromEntries(
      Object.entries(errors.value).filter(([field]) => !changed.includes(field as FormField)),
    )
  }
})

function update<K extends keyof ExerciseForm>(key: K, value: ExerciseForm[K]): void {
  form.value = { ...form.value, [key]: value }
}

// --- Opzioni ------------------------------------------------------------------------

const familyOptions = computed<SelectGroupOption[]>(() => {
  const catalog = store.catalog
  if (catalog === null) return []
  return catalog.muscle_groups
    .map((group) => ({
      type: 'group' as const,
      key: group.code,
      label: group.name,
      children: catalog.families
        .filter((f) => f.muscle_group_id === group.id)
        .map((f) => ({ label: f.name, value: f.id })),
    }))
    .filter((group) => group.children.length > 0)
})
const equipmentOptions = computed<SelectOption[]>(
  () => store.catalog?.equipment.map((e) => ({ label: e.name, value: e.id })) ?? [],
)
const stretchOptions = (Object.keys(labels.stretch) as Stretch[]).map((v) => ({
  label: labels.stretch[v],
  value: v,
}))
const confidenceOptions = (Object.keys(labels.confidence) as Confidence[]).map((v) => ({
  label: labels.confidence[v],
  value: v,
}))
const kinds = Object.keys(labels.kind) as Kind[]
const tagOptions = computed<SelectOption[]>(
  () =>
    store.catalog?.tags
      .filter((tag) => !form.value.tags.some((entry) => entry.tag_id === tag.id))
      .map((tag) => ({ label: tag.name, value: tag.id })) ?? [],
)
const sourceOptions = computed<SelectOption[]>(
  () => store.catalog?.sources.map((s) => ({ label: `${s.code} · ${s.title}`, value: s.id })) ?? [],
)

const asId = (value: unknown): number | null => (typeof value === 'number' ? value : null)

// --- Etichette e fonti --------------------------------------------------------------

function addTag(value: unknown): void {
  const tagId = asId(value)
  if (tagId !== null) update('tags', [...form.value.tags, { tag_id: tagId, note: '' }])
}

function setTagNote(tagId: number, note: string): void {
  update(
    'tags',
    form.value.tags.map((entry) => (entry.tag_id === tagId ? { ...entry, note } : entry)),
  )
}

function removeTag(tagId: number): void {
  update(
    'tags',
    form.value.tags.filter((entry) => entry.tag_id !== tagId),
  )
}

async function onSourceCreated(source: Source): Promise<void> {
  await store.load(true)
  update('source_ids', [...form.value.source_ids, source.id])
}

// --- Salvataggio ----------------------------------------------------------------

const fieldStatus = (field: FormField) => (errors.value[field] ? 'error' : undefined)

async function save(): Promise<void> {
  general.value = []
  errors.value = validateForm(form.value)
  if (Object.keys(errors.value).length > 0) return

  saving.value = true
  try {
    const body = toExerciseInput(form.value)
    const result =
      props.id === undefined
        ? await api.POST('/api/exercises', { body })
        : await api.PUT('/api/exercises/{exercise_id}', {
            params: { path: { exercise_id: props.id } },
            body,
          })
    if (result.data === undefined) {
      const problem = asProblem(result.error, result.response.status)
      const mapped = errorsFromProblem(problem)
      errors.value = mapped.fields
      general.value = mapped.general
      return
    }
    await store.load(true)
    message.success(editing.value ? t.saved : t.created)
    leaving = true
    await router.push(`/catalogo/esercizi/${String(result.data.id)}`)
  } catch {
    general.value = [texts.common.loadFailed]
  } finally {
    saving.value = false
  }
}

function cancel(): void {
  void router.push(props.id === undefined ? '/catalogo' : `/catalogo/esercizi/${String(props.id)}`)
}

onBeforeRouteLeave(() => {
  if (leaving || !dirty.value) return true
  return new Promise<boolean>((resolve) => {
    dialog.warning({
      title: t.leaveTitle,
      content: t.leaveText,
      positiveText: t.leave,
      negativeText: t.stay,
      onPositiveClick: () => {
        resolve(true)
      },
      onNegativeClick: () => {
        resolve(false)
      },
      onClose: () => {
        resolve(false)
      },
      onMaskClick: () => {
        resolve(false)
      },
    })
  })
})

const title = computed(() => (editing.value ? t.editTitle(originalName.value) : t.newTitle))
</script>

<template>
  <main class="page exercise-form">
    <RouterLink
      :to="id === undefined ? '/catalogo' : `/catalogo/esercizi/${String(id)}`"
      class="back"
    >
      <ChevronLeft :size="18" aria-hidden="true" />{{
        id === undefined ? texts.exercise.backToCatalog : t.cancel
      }}
    </RouterLink>

    <div v-if="state === 'loading'" aria-busy="true">
      <NSkeleton text style="width: 50%; height: 2rem" />
      <NSkeleton text :repeat="8" />
    </div>

    <NAlert v-else-if="state === 'not-found'" type="warning" data-testid="form-not-found">
      {{ texts.exercise.notFound }}
    </NAlert>

    <NAlert v-else-if="state === 'failed'" type="error">
      {{ texts.common.loadFailed }}
      <NButton text type="primary" @click="load">{{ texts.common.retry }}</NButton>
    </NAlert>

    <template v-else-if="store.catalog">
      <NH1 class="title">{{ title }}</NH1>

      <NAlert
        v-if="general.length > 0"
        type="error"
        :title="t.errors.notSaved"
        class="general"
        data-testid="form-general-error"
      >
        <p v-for="text in general" :key="text">{{ text }}</p>
      </NAlert>

      <NForm class="form" label-placement="top" @submit.prevent="save">
        <section class="section">
          <NFormItem
            :label="t.name"
            required
            :validation-status="fieldStatus('name')"
            :feedback="errors.name"
            class="wide"
          >
            <NInput
              :value="form.name"
              :maxlength="160"
              :placeholder="t.namePlaceholder"
              :input-props="{ 'aria-label': t.name }"
              data-testid="field-name"
              @update:value="(v: string) => update('name', v)"
            />
          </NFormItem>

          <div class="two">
            <NFormItem
              :label="t.family"
              required
              :validation-status="fieldStatus('primary_family_id')"
              :feedback="errors.primary_family_id"
            >
              <NSelect
                :virtual-scroll="false"
                :value="form.primary_family_id"
                :options="familyOptions"
                filterable
                :placeholder="t.familyPlaceholder"
                data-testid="field-family"
                @update:value="(v: unknown) => update('primary_family_id', asId(v))"
              />
            </NFormItem>
            <NFormItem
              :label="t.rank"
              :validation-status="fieldStatus('family_rank')"
              :feedback="errors.family_rank"
            >
              <NInputNumber
                :value="form.family_rank"
                :min="1"
                :max="999"
                :precision="0"
                :title="t.rankHelp"
                data-testid="field-rank"
                @update:value="
                  (v: number | null) => {
                    rankTouched = true
                    update('family_rank', v ?? 0)
                  }
                "
              />
            </NFormItem>
          </div>

          <NFormItem
            :label="t.secondaryFamily"
            :validation-status="fieldStatus('secondary_family_id')"
            :feedback="errors.secondary_family_id"
          >
            <NSelect
              :virtual-scroll="false"
              :value="form.secondary_family_id"
              :options="familyOptions"
              :placeholder="t.none"
              clearable
              filterable
              data-testid="field-secondary-family"
              @update:value="(v: unknown) => update('secondary_family_id', asId(v))"
            />
          </NFormItem>

          <div class="two">
            <NFormItem
              :label="t.equipment"
              required
              :validation-status="fieldStatus('equipment_id')"
              :feedback="errors.equipment_id"
            >
              <NSelect
                :virtual-scroll="false"
                :value="form.equipment_id"
                :options="equipmentOptions"
                :placeholder="t.equipmentPlaceholder"
                data-testid="field-equipment"
                @update:value="(v: unknown) => update('equipment_id', asId(v))"
              />
            </NFormItem>
            <NFormItem
              :label="t.equipmentDetail"
              :validation-status="fieldStatus('equipment_detail')"
              :feedback="errors.equipment_detail"
            >
              <NInput
                :value="form.equipment_detail"
                :maxlength="120"
                :placeholder="t.equipmentDetailPlaceholder"
                @update:value="(v: string) => update('equipment_detail', v)"
              />
            </NFormItem>
          </div>

          <NFormItem :label="t.kind">
            <NRadioGroup :value="form.kind" @update:value="(v: Kind) => update('kind', v)">
              <NRadioButton v-for="kind in kinds" :key="kind" :value="kind">
                {{ labels.kind[kind] }}
              </NRadioButton>
            </NRadioGroup>
          </NFormItem>

          <div class="two">
            <NFormItem :label="t.stretch">
              <NSelect
                :virtual-scroll="false"
                :value="form.stretch"
                :options="stretchOptions"
                @update:value="(v: Stretch) => update('stretch', v)"
              />
            </NFormItem>
            <NFormItem
              :label="t.stretchNote"
              :validation-status="fieldStatus('stretch_note')"
              :feedback="errors.stretch_note"
            >
              <NInput
                :value="form.stretch_note"
                :maxlength="120"
                :placeholder="t.stretchNotePlaceholder"
                @update:value="(v: string) => update('stretch_note', v)"
              />
            </NFormItem>
          </div>

          <NFormItem :label="t.confidence">
            <NSelect
              :virtual-scroll="false"
              :value="form.confidence"
              :options="confidenceOptions"
              @update:value="(v: Confidence) => update('confidence', v)"
            />
          </NFormItem>
        </section>

        <section class="section">
          <NFormItem
            :label="t.muscles"
            required
            :validation-status="fieldStatus('muscles')"
            :feedback="errors.muscles ?? t.musclesHelp"
            data-testid="field-muscles"
          >
            <MuscleGrid
              v-model="form"
              :catalog="store.catalog"
              :invalid="errors.muscles !== undefined"
            />
          </NFormItem>
        </section>

        <section class="section">
          <NFormItem
            :label="t.tags"
            :validation-status="fieldStatus('tags')"
            :feedback="errors.tags"
          >
            <div class="tags">
              <div
                v-for="entry in form.tags"
                :key="entry.tag_id"
                class="tag-row"
                data-testid="tag-row"
              >
                <span class="tag-name">
                  <component
                    :is="symbolIcon(store.tags.get(entry.tag_id)?.symbol ?? 'info')"
                    :size="16"
                    aria-hidden="true"
                  />
                  {{ store.tags.get(entry.tag_id)?.name }}
                </span>
                <NInput
                  :value="entry.note"
                  :maxlength="120"
                  :placeholder="t.tagNotePlaceholder"
                  :input-props="{ 'aria-label': t.tagNote }"
                  @update:value="(v: string) => setTagNote(entry.tag_id, v)"
                />
                <NButton
                  quaternary
                  circle
                  :aria-label="t.removeTag(store.tags.get(entry.tag_id)?.name ?? '')"
                  @click="removeTag(entry.tag_id)"
                >
                  <template #icon><X :size="16" /></template>
                </NButton>
              </div>
              <NSelect
                v-if="tagOptions.length > 0"
                :virtual-scroll="false"
                :value="null"
                :options="tagOptions"
                :placeholder="t.addTag"
                class="add-tag"
                data-testid="add-tag"
                @update:value="addTag"
              />
            </div>
          </NFormItem>

          <NFormItem
            :label="t.sources"
            :validation-status="fieldStatus('source_ids')"
            :feedback="errors.source_ids"
          >
            <div class="sources">
              <NSelect
                :virtual-scroll="false"
                :value="form.source_ids"
                :options="sourceOptions"
                multiple
                filterable
                :placeholder="t.sourcesPlaceholder"
                data-testid="field-sources"
                @update:value="(v: number[]) => update('source_ids', v)"
              />
              <NButton secondary data-testid="new-source" @click="showSourceDialog = true">
                {{ t.newSource }}
              </NButton>
            </div>
          </NFormItem>

          <NFormItem
            :label="t.notes"
            :validation-status="fieldStatus('notes')"
            :feedback="errors.notes"
          >
            <NInput
              type="textarea"
              :value="form.notes"
              :placeholder="t.notesPlaceholder"
              :autosize="{ minRows: 3, maxRows: 10 }"
              @update:value="(v: string) => update('notes', v)"
            />
          </NFormItem>
        </section>

        <div class="actions">
          <NButton @click="cancel">{{ t.cancel }}</NButton>
          <NButton type="primary" attr-type="submit" :loading="saving" data-testid="save">
            {{ t.save }}
          </NButton>
        </div>
      </NForm>

      <SourceDialog v-model:show="showSourceDialog" @created="onSourceCreated" />
    </template>
  </main>
</template>

<style scoped>
.exercise-form {
  max-width: 52rem;
}

.back {
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
  margin-bottom: 0.75rem;
  color: var(--muted-color);
  text-decoration: none;
}

.title {
  margin: 0 0 1rem;
}

.general {
  margin-bottom: 1rem;
}

.general p {
  margin: 0;
}

.section {
  padding: 0.5rem 0 0.75rem;
  border-bottom: 1px solid var(--border-color);
}

.section + .section {
  padding-top: 1rem;
}

.two {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: 0 1rem;
}

.tags {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

.tag-row {
  display: grid;
  grid-template-columns: 12rem minmax(0, 1fr) auto;
  gap: 0.5rem;
  align-items: center;
}

.tag-name {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.add-tag {
  max-width: 16rem;
}

.sources {
  display: flex;
  gap: 0.5rem;
  width: 100%;
}

.actions {
  position: sticky;
  bottom: 0;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 0.75rem 0;
  background: var(--page-color);
}

@media (max-width: 767px) {
  .two {
    grid-template-columns: minmax(0, 1fr);
  }

  .tag-row {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .tag-row :deep(.n-input) {
    grid-column: 1 / -1;
    grid-row: 2;
  }

  .sources {
    flex-direction: column;
  }

  .actions {
    bottom: calc(var(--nav-height) + env(safe-area-inset-bottom));
  }
}
</style>
