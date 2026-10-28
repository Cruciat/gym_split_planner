<script setup lang="ts">
import { NButton, NDrawer, NDrawerContent, NInput, NSkeleton } from 'naive-ui'
import { Check } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'

import TagBadges from '@/components/TagBadges.vue'
import { useConfirm } from '@/composables/useConfirm'
import { type Candidate, type Candidates, type Day, type Slot, usePlanEditor } from '@/plans/editor'
import { deltaEffect, formatDelta } from '@/plans/volume'
import { useCatalogStore } from '@/stores/catalog'
import { formatNumber, texts } from '@/texts'

/**
 * Varianti di un esercizio con punteggio ed effetto sul volume (US-14, US-17;
 * wireframe, § 3.4). Scegliere un candidato lo applica subito; il pannello resta
 * aperto e mostra il nuovo attuale, con i cambi ricalcolati.
 */
const props = defineProps<{
  day: Day
  item: Slot | null
  session: 1 | 2
  mobile: boolean
}>()
const emit = defineEmits<{ close: [] }>()
const t = texts.variants
const editor = usePlanEditor()
const catalog = useCatalogStore()
const confirm = useConfirm()

const data = ref<Candidates | null>(null)
const loading = ref(false)
const busy = ref(false)
const search = ref('')
const why = ref<number | null>(null)

async function load(): Promise<void> {
  const slot = props.item
  if (slot === null) return
  loading.value = true
  data.value = await editor.candidates(slot.id, props.session)
  loading.value = false
}

// Si ricarica solo quando cambiano slot o seduta, non a ogni nuova versione della scheda.
watch(
  () => (props.item === null ? null : `${String(props.item.id)}:${String(props.session)}`),
  (key) => {
    data.value = null
    search.value = ''
    why.value = null
    if (key !== null) void load()
  },
  { immediate: true },
)

const volumes = computed(
  () => new Map((editor.plan.value?.analysis.volumes ?? []).map((v) => [v.muscle_id, v])),
)
const equipmentNames = computed(
  () => new Map((catalog.catalog?.equipment ?? []).map((e) => [e.code, e.name])),
)
const tagNames = computed(
  () => new Map((catalog.catalog?.tags ?? []).map((tag) => [tag.code, tag.name])),
)

// Nella seconda seduta l'esercizio principale non si può scegliere: le sedute sarebbero uguali.
const all = computed(() =>
  (data.value?.candidates ?? []).filter(
    (c) => props.session === 1 || c.exercise_id !== props.item?.exercise?.id,
  ),
)
const family = computed(() =>
  all.value.filter((c) => c.excluded_by.length === 0 && c.family_match !== 'other'),
)
const others = computed(() => {
  const query = search.value.trim().toLocaleLowerCase('it')
  return all.value.filter(
    (c) =>
      c.excluded_by.length === 0 &&
      c.family_match === 'other' &&
      (query === '' || c.name.toLocaleLowerCase('it').includes(query)),
  )
})
const excluded = computed(() => all.value.filter((c) => c.excluded_by.length > 0))

const currentId = computed(() => data.value?.current_exercise_id ?? null)
const currentName = computed(() => {
  const slot = props.item
  if (slot === null) return null
  return props.session === 1 ? (slot.exercise?.name ?? null) : (slot.second_exercise?.name ?? null)
})
const title = computed(() => {
  const slot = props.item
  if (slot === null) return ''
  const position = props.day.slots.findIndex((s) => s.id === slot.id) + 1
  return props.session === 1
    ? t.title(props.day.name, position, slot.family.name)
    : t.secondTitle(props.day.name, position)
})

const excludedNames = (c: Candidate) =>
  c.excluded_by.map((code) => tagNames.value.get(code) ?? code)

const chips = (c: Candidate) =>
  c.volume_delta.map((d) => {
    const volume = volumes.value.get(d.muscle_id)
    return {
      key: d.muscle_id,
      text: `${volume?.short_name ?? d.code} ${formatDelta(d.delta)}`,
      effect: deltaEffect(volume, d.delta),
    }
  })

async function choose(candidate: Candidate | null): Promise<void> {
  const slot = props.item
  if (slot === null || busy.value) return
  const id = candidate?.exercise_id ?? null
  if (id === currentId.value) return
  if (candidate !== null && candidate.excluded_by.length > 0) {
    const confirmed = await confirm({
      title: t.useExcludedTitle,
      content: t.useExcluded(candidate.name, excludedNames(candidate)),
      action: t.useAnyway,
      cancel: texts.editor.cancel,
    })
    if (!confirmed) return
  }
  busy.value = true
  try {
    const body = props.session === 1 ? { exercise_id: id } : { second_exercise_id: id }
    if (await editor.updateSlot(slot.id, body)) await load()
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <NDrawer
    :show="item !== null"
    :placement="mobile ? 'bottom' : 'right'"
    :width="mobile ? undefined : 'min(34rem, 100vw)'"
    :height="mobile ? '88%' : undefined"
    :auto-focus="false"
    data-testid="variants-panel"
    @update:show="(show: boolean) => !show && emit('close')"
  >
    <NDrawerContent closable :title="title" :native-scrollbar="false">
      <p class="current" data-testid="variants-current">{{ t.current(currentName) }}</p>

      <NSkeleton v-if="loading && data === null" text :repeat="5" />
      <template v-else-if="data">
        <ul class="candidates" role="radiogroup" :aria-label="title">
          <li v-if="session === 2" class="candidate">
            <button
              type="button"
              class="choice"
              role="radio"
              :aria-checked="currentId === null"
              :disabled="busy"
              data-testid="no-variant"
              @click="choose(null)"
            >
              <span class="mark"><Check v-if="currentId === null" :size="16" /></span>
              <span class="body">
                <strong>{{ t.noVariant }}</strong>
                <small class="muted">{{ t.noVariantHelp }}</small>
              </span>
            </button>
          </li>
          <li v-for="c in family" :key="c.exercise_id" class="candidate" data-testid="candidate">
            <button
              type="button"
              class="choice"
              role="radio"
              :aria-checked="c.exercise_id === currentId"
              :aria-label="t.choose(c.name)"
              :disabled="busy"
              @click="choose(c)"
            >
              <span class="mark"><Check v-if="c.exercise_id === currentId" :size="16" /></span>
              <span class="body">
                <span class="name">
                  <strong>{{ c.name }}</strong>
                  <TagBadges :links="c.badges" />
                </span>
                <small class="muted">
                  {{ equipmentNames.get(c.equipment) ?? c.equipment }} · {{ t.score }}
                  {{ formatNumber(c.score) }}
                </small>
                <span class="chips">
                  <span v-if="c.exercise_id === currentId" class="chip">{{ t.currentMark }}</span>
                  <span v-else-if="c.volume_delta.length === 0" class="chip">{{ t.noChange }}</span>
                  <span
                    v-for="chip in chips(c)"
                    :key="chip.key"
                    class="chip"
                    :class="chip.effect"
                    data-testid="delta"
                  >
                    {{ chip.text }}
                  </span>
                </span>
              </span>
            </button>
            <NButton
              text
              size="tiny"
              class="why"
              @click="why = why === c.exercise_id ? null : c.exercise_id"
            >
              {{ why === c.exercise_id ? t.hideWhy : t.why }}
            </NButton>
            <dl v-if="why === c.exercise_id" class="breakdown" data-testid="breakdown">
              <template v-for="(label, key) in t.breakdown" :key="key">
                <dt>{{ label }}</dt>
                <dd>{{ formatNumber(c.score_breakdown[key]) }}</dd>
              </template>
            </dl>
          </li>
        </ul>
        <p v-if="family.length === 0 && session === 1" class="muted">{{ t.empty }}</p>

        <section v-if="session === 2" class="section" data-testid="other-families">
          <h3>{{ t.otherFamilies }}</h3>
          <NInput
            v-model:value="search"
            :placeholder="t.search"
            clearable
            size="small"
            data-testid="variants-search"
          />
          <ul class="candidates">
            <li v-for="c in others" :key="c.exercise_id" class="candidate" data-testid="candidate">
              <button
                type="button"
                class="choice"
                role="radio"
                :aria-checked="c.exercise_id === currentId"
                :aria-label="t.choose(c.name)"
                :disabled="busy"
                @click="choose(c)"
              >
                <span class="mark"><Check v-if="c.exercise_id === currentId" :size="16" /></span>
                <span class="body">
                  <span class="name">
                    <strong>{{ c.name }}</strong>
                    <TagBadges :links="c.badges" />
                  </span>
                  <small class="muted">{{ equipmentNames.get(c.equipment) ?? c.equipment }}</small>
                  <span class="chips">
                    <span
                      v-for="chip in chips(c)"
                      :key="chip.key"
                      class="chip"
                      :class="chip.effect"
                    >
                      {{ chip.text }}
                    </span>
                  </span>
                </span>
              </button>
            </li>
          </ul>
          <p v-if="others.length === 0" class="muted">{{ t.noResults }}</p>
        </section>

        <section v-if="excluded.length > 0" class="section" data-testid="excluded">
          <h3>{{ t.excluded }}</h3>
          <ul class="candidates">
            <li
              v-for="c in excluded"
              :key="c.exercise_id"
              class="candidate excluded"
              data-testid="excluded-candidate"
            >
              <button
                type="button"
                class="choice"
                role="radio"
                :aria-checked="c.exercise_id === currentId"
                :aria-label="t.choose(c.name)"
                :disabled="busy"
                @click="choose(c)"
              >
                <span class="mark"><Check v-if="c.exercise_id === currentId" :size="16" /></span>
                <span class="body">
                  <span class="name">
                    <strong>{{ c.name }}</strong>
                    <TagBadges :links="c.badges" />
                  </span>
                  <small class="reason">{{ t.excludedBy(excludedNames(c)) }}</small>
                </span>
              </button>
            </li>
          </ul>
        </section>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
.current {
  margin: 0 0 0.75rem;
  color: var(--muted-color);
}

.candidates {
  margin: 0;
  padding: 0;
  list-style: none;
}

.candidate {
  position: relative;
  border-bottom: 1px solid var(--border-color);
}

.choice {
  display: flex;
  gap: 0.6rem;
  width: 100%;
  padding: 0.6rem 4.5rem 0.6rem 0.25rem;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.choice:hover:not(:disabled),
.choice:focus-visible {
  background: var(--hover-color);
}

.choice[aria-checked='true'] .name strong {
  color: var(--primary-color);
}

.mark {
  display: inline-flex;
  flex: none;
  width: 1rem;
  padding-top: 0.15rem;
  color: var(--primary-color);
}

.body {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.name strong {
  font-weight: 500;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.chip {
  padding: 0 0.4rem;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  color: var(--muted-color);
  font-size: 0.75rem;
}

.chip.closer {
  border-color: var(--success-color);
  color: var(--success-color);
}

.chip.farther {
  border-color: var(--warning-color);
  color: var(--warning-color);
}

.why {
  position: absolute;
  top: 0.6rem;
  right: 0.25rem;
}

.breakdown {
  display: grid;
  grid-template-columns: max-content max-content;
  gap: 0.1rem 1rem;
  margin: 0 0 0.6rem 1.85rem;
  font-size: 0.85rem;
}

.breakdown dt {
  color: var(--muted-color);
}

.breakdown dd {
  margin: 0;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.section {
  margin-top: 1.25rem;
}

.section h3 {
  margin: 0 0 0.5rem;
  color: var(--muted-color);
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
}

.excluded .name {
  opacity: 0.75;
}

.reason {
  color: var(--warning-color);
}

.muted {
  color: var(--muted-color);
}
</style>
