<script setup lang="ts">
import {
  NAlert,
  NButton,
  NInput,
  NInputNumber,
  NSelect,
  NSkeleton,
  NSwitch,
  type SelectOption,
  useMessage,
  useThemeVars,
} from 'naive-ui'
import { Pencil, Plus, Trash2 } from 'lucide-vue-next'
import { computed, h, onMounted, ref } from 'vue'

import { api, asProblem, type Tag, type TagColor } from '@/api/client'
import { problemMessages } from '@/catalog/problems'
import { COLOR_VARS, SYMBOLS, type SymbolName, symbolIcon } from '@/catalog/symbols'
import CatalogHeader from '@/components/CatalogHeader.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/** Etichette, modificabili in linea (US-08 CA1, CA3; wireframe § 4.4). */
const store = useCatalogStore()
const message = useMessage()
const confirm = useConfirm()
const themeVars = useThemeVars()
const t = texts.tags
const e = texts.editing

type Effect = Tag['effect']

interface Draft {
  name: string
  symbol: SymbolName
  color: TagColor
  effect: Effect
  points: number
  show_badge: boolean
  description: string
}

const emptyDraft = (): Draft => ({
  name: '',
  symbol: 'info',
  color: 'neutral',
  effect: 'none',
  points: 0,
  show_badge: true,
  description: '',
})

const editing = ref<number | 'new' | null>(null)
const draft = ref<Draft>(emptyDraft())
const errors = ref<Record<string, string>>({})
const general = ref<string[]>([])
const saving = ref(false)

onMounted(() => {
  void store.load()
})

const tags = computed(() =>
  [...(store.catalog?.tags ?? [])].sort((a, b) => a.sort_order - b.sort_order),
)
const usesPoints = (effect: Effect) => effect === 'bonus' || effect === 'penalty'
const colorOf = (color: TagColor) => themeVars.value[COLOR_VARS[color]]

const assigned = (tagId: number) =>
  store.catalog?.exercises.filter((x) => x.tags.some((link) => link.tag_id === tagId)).length ?? 0

const symbolOptions = (Object.keys(SYMBOLS) as SymbolName[]).map((symbol) => ({
  label: texts.symbols[symbol],
  value: symbol,
}))
const renderSymbol = (option: SelectOption) =>
  h('span', { class: 'symbol-option' }, [
    h(symbolIcon(String(option.value)), { size: 16, 'aria-hidden': 'true' }),
    String(option.label),
  ])
const colorOptions = (Object.keys(t.colors) as TagColor[]).map((color) => ({
  label: t.colors[color],
  value: color,
}))
const renderColor = (option: SelectOption) =>
  h('span', { class: 'symbol-option' }, [
    h('span', { class: 'swatch', style: { background: colorOf(option.value as TagColor) } }),
    String(option.label),
  ])
const effectOptions = (Object.keys(t.effects) as Effect[]).map((effect) => ({
  label: t.effects[effect],
  value: effect,
}))

function effectText(tag: Tag): string {
  const label = t.effects[tag.effect]
  return usesPoints(tag.effect) ? `${label} ${String(tag.points)}` : label
}

function startEdit(tag: Tag | null): void {
  editing.value = tag?.id ?? 'new'
  draft.value =
    tag === null
      ? emptyDraft()
      : {
          name: tag.name,
          symbol: (Object.keys(SYMBOLS) as SymbolName[]).find((s) => s === tag.symbol) ?? 'info',
          color: tag.color,
          effect: tag.effect,
          points: tag.points,
          show_badge: tag.show_badge,
          description: tag.description ?? '',
        }
  errors.value = {}
  general.value = []
}

async function save(): Promise<void> {
  const local: Record<string, string> = {}
  if (draft.value.name.trim() === '') local.name = texts.exerciseForm.errors.nameRequired
  errors.value = local
  if (Object.keys(local).length > 0) return

  const body = {
    ...draft.value,
    // Per nessun effetto ed esclusione i punti non contano: si salvano a zero.
    points: usesPoints(draft.value.effect) ? draft.value.points : 0,
  }
  saving.value = true
  try {
    const result =
      editing.value === 'new'
        ? await api.POST('/api/tags', { body })
        : await api.PATCH('/api/tags/{tag_id}', {
            params: { path: { tag_id: editing.value ?? 0 } },
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

/** Conferma con i numeri giusti, poi elimina con assegnazioni e personalizzazioni (CA3). */
async function remove(tag: Tag): Promise<void> {
  const {
    data: usage,
    error,
    response,
  } = await api.GET('/api/tags/{tag_id}/usage', {
    params: { path: { tag_id: tag.id } },
  })
  if (usage === undefined) {
    const problem = asProblem(error, response.status)
    message.error(problem.detail ?? problem.title)
    return
  }
  const confirmed = await confirm({
    title: t.deleteTitle,
    content: t.deleteConfirm(tag.name, usage.exercises, usage.plans_with_overrides.length),
    action: t.deleteAction,
    cancel: e.cancel,
  })
  if (!confirmed) return
  const result = await api.DELETE('/api/tags/{tag_id}', { params: { path: { tag_id: tag.id } } })
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
        data-testid="add-tag"
        @click="startEdit(null)"
      >
        <template #icon><Plus :size="16" /></template>
        {{ t.add }}
      </NButton>
    </CatalogHeader>
    <p class="intro">{{ t.intro }}</p>

    <NAlert v-if="store.failed" type="error">{{ texts.common.loadFailed }}</NAlert>
    <NSkeleton v-else-if="store.catalog === null" text :repeat="5" />

    <div v-else class="rows" data-testid="tag-rows">
      <div class="row head" aria-hidden="true">
        <span>{{ t.symbol }}</span>
        <span>{{ t.name }}</span>
        <span>{{ t.effect }}</span>
        <span>{{ t.visible }}</span>
        <span>{{ t.exercises }}</span>
        <span />
      </div>

      <template v-for="tag in editing === 'new' ? [null, ...tags] : tags" :key="tag?.id ?? 'new'">
        <form
          v-if="(tag === null && editing === 'new') || (tag !== null && editing === tag.id)"
          class="edit"
          data-testid="tag-edit"
          @submit.prevent="save"
        >
          <label class="field wide">
            <span>{{ t.name }}</span>
            <NInput
              v-model:value="draft.name"
              :maxlength="120"
              :placeholder="t.namePlaceholder"
              :status="errors.name ? 'error' : undefined"
              data-testid="tag-name"
            />
            <small v-if="errors.name" class="error">{{ errors.name }}</small>
          </label>
          <label class="field">
            <span>{{ t.symbol }}</span>
            <NSelect
              v-model:value="draft.symbol"
              :options="symbolOptions"
              :render-label="renderSymbol"
              :virtual-scroll="false"
              data-testid="tag-symbol"
            />
          </label>
          <label class="field">
            <span>{{ t.color }}</span>
            <NSelect
              v-model:value="draft.color"
              :options="colorOptions"
              :render-label="renderColor"
              :virtual-scroll="false"
            />
          </label>
          <label class="field">
            <span>{{ t.effect }}</span>
            <NSelect
              v-model:value="draft.effect"
              :options="effectOptions"
              :virtual-scroll="false"
              data-testid="tag-effect"
            />
          </label>
          <label class="field">
            <span>{{ t.points }}</span>
            <NInputNumber
              v-model:value="draft.points"
              :min="0"
              :max="100"
              :step="0.5"
              :disabled="!usesPoints(draft.effect)"
              :status="errors.points ? 'error' : undefined"
              :title="t.pointsHelp"
              data-testid="tag-points"
            />
            <small v-if="errors.points" class="error">{{ errors.points }}</small>
          </label>
          <label class="field switch">
            <span>{{ t.visible }}</span>
            <NSwitch v-model:value="draft.show_badge" />
          </label>
          <label class="field wide">
            <span>{{ t.description }}</span>
            <NInput
              v-model:value="draft.description"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 4 }"
              :placeholder="t.descriptionPlaceholder"
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
              data-testid="tag-save"
            >
              {{ e.save }}
            </NButton>
          </div>
        </form>

        <div v-else-if="tag" class="row" data-testid="tag-row">
          <span class="symbol" :style="{ color: colorOf(tag.color) }">
            <component :is="symbolIcon(tag.symbol)" :size="18" aria-hidden="true" />
          </span>
          <div>
            <strong>{{ tag.name }}</strong>
            <p v-if="tag.description" class="muted description">{{ tag.description }}</p>
          </div>
          <span>{{ effectText(tag) }}</span>
          <span>{{ tag.show_badge ? t.yes : t.no }}</span>
          <span>{{ assigned(tag.id) }}</span>
          <div class="buttons">
            <NButton
              quaternary
              circle
              size="small"
              :disabled="editing !== null"
              :aria-label="`${e.edit} ${tag.name}`"
              data-testid="tag-edit-button"
              @click="startEdit(tag)"
            >
              <template #icon><Pencil :size="16" /></template>
            </NButton>
            <NButton
              quaternary
              circle
              size="small"
              type="error"
              :disabled="editing !== null"
              :aria-label="`${e.delete} ${tag.name}`"
              data-testid="tag-delete"
              @click="remove(tag)"
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
  grid-template-columns: 4.5rem minmax(0, 2.5fr) minmax(0, 1fr) 8rem 5rem 5rem;
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

.symbol {
  display: inline-flex;
  padding-top: 0.1rem;
}

.description {
  margin: 0.15rem 0 0;
  font-size: 0.875rem;
}

.edit {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) auto;
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

.field.switch {
  align-items: flex-start;
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

:deep(.symbol-option) {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}

:deep(.swatch) {
  display: inline-block;
  width: 0.8rem;
  height: 0.8rem;
  border-radius: 50%;
}

@media (max-width: 767px) {
  .row {
    grid-template-columns: 2rem minmax(0, 1fr) 5rem;
  }

  .row.head {
    display: none;
  }

  /* Sul telefono resta l'effetto, sotto il nome; visibilità e conteggio si vedono in modifica. */
  .row > :nth-child(3) {
    grid-column: 2;
    color: var(--muted-color);
    font-size: 0.875rem;
  }

  .row > :nth-child(4),
  .row > :nth-child(5) {
    display: none;
  }

  .row > .buttons {
    grid-column: 3;
    grid-row: 1;
  }

  .edit {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
