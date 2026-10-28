<script setup lang="ts">
import { NAlert, NButton, NH1, NSkeleton, NTag } from 'naive-ui'
import { ChevronLeft, ExternalLink } from 'lucide-vue-next'
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { api, type ExerciseDetail, type Variant } from '@/api/client'
import TagBadges from '@/components/TagBadges.vue'
import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/** Dettaglio di un esercizio (US-02, wireframe § 4.2). */
const props = defineProps<{ id: number }>()

const store = useCatalogStore()
const t = texts.exercise
const labels = texts.labels

const detail = ref<ExerciseDetail | null>(null)
const state = ref<'loading' | 'ready' | 'not-found' | 'failed'>('loading')

async function load(): Promise<void> {
  state.value = 'loading'
  try {
    const [{ data, response }] = await Promise.all([
      api.GET('/api/exercises/{exercise_id}', { params: { path: { exercise_id: props.id } } }),
      store.load(),
    ])
    if (data !== undefined) {
      detail.value = data
      state.value = 'ready'
    } else {
      state.value = response.status === 404 || response.status === 422 ? 'not-found' : 'failed'
    }
  } catch {
    state.value = 'failed'
  }
}

onMounted(load)
// Dalle varianti si passa a un altro esercizio con la stessa pagina (US-02 CA2).
watch(() => props.id, load)

const muscleName = (id: number) => store.muscles.get(id)?.short_name ?? ''
const muscleFullName = (id: number) => store.muscles.get(id)?.name ?? ''
const familyName = (id: number) => store.families.get(id)?.name ?? ''
const equipmentName = (id: number) => store.equipment.get(id)?.name ?? ''

const primaryMuscles = computed(() => detail.value?.muscles.filter((m) => m.level === 'P') ?? [])
const secondaryMuscles = computed(() => detail.value?.muscles.filter((m) => m.level === 'S') ?? [])

/** Varianti raggruppate per famiglia in comune, nell'ordine ricevuto dal server. */
const variantGroups = computed(() => {
  const groups = new Map<number, Variant[]>()
  for (const variant of detail.value?.variants ?? []) {
    groups.set(variant.family_id, [...(groups.get(variant.family_id) ?? []), variant])
  }
  return [...groups].map(([familyId, variants]) => ({ familyId, variants }))
})

const tagRows = computed(() =>
  (detail.value?.tags ?? []).flatMap((link) => {
    const tag = store.tags.get(link.tag_id)
    return tag === undefined ? [] : [{ tag, note: link.note }]
  }),
)
</script>

<template>
  <main class="page detail">
    <RouterLink to="/catalogo" class="back">
      <ChevronLeft :size="18" aria-hidden="true" />{{ t.backToCatalog }}
    </RouterLink>

    <div v-if="state === 'loading'" aria-busy="true">
      <NSkeleton text style="width: 60%; height: 2rem" />
      <NSkeleton text :repeat="6" />
    </div>

    <NAlert v-else-if="state === 'not-found'" type="warning" data-testid="detail-not-found">
      {{ t.notFound }}
    </NAlert>

    <NAlert v-else-if="state === 'failed'" type="error" data-testid="detail-error">
      {{ texts.common.loadFailed }}
      <NButton text type="primary" @click="load">{{ texts.common.retry }}</NButton>
    </NAlert>

    <article v-else-if="detail" data-testid="exercise-detail">
      <header>
        <NH1 class="title">
          {{ detail.name }}
          <TagBadges :links="detail.tags" />
        </NH1>
        <p class="summary">
          {{ familyName(detail.primary_family_id) }} · {{ equipmentName(detail.equipment_id) }} ·
          {{ labels.kind[detail.kind] }} ·
          <NTag
            size="small"
            :bordered="false"
            :type="detail.is_active ? 'success' : 'default'"
            data-testid="detail-status"
          >
            {{ detail.is_active ? t.active : t.inactive }}
          </NTag>
        </p>
      </header>

      <dl class="fields">
        <dt>{{ t.muscles }}</dt>
        <dd data-testid="detail-muscles">
          <p v-if="primaryMuscles.length > 0" class="muscle-line">
            <abbr class="level level-p" :title="t.primaryLong">{{ t.primary }}</abbr>
            <span v-for="(m, i) in primaryMuscles" :key="m.muscle_id">
              <span :title="muscleFullName(m.muscle_id)">{{ muscleName(m.muscle_id) }}</span>
              <span v-if="m.note" class="muted"> ({{ m.note }})</span>
              <span v-if="i < primaryMuscles.length - 1"> · </span>
            </span>
          </p>
          <p v-if="secondaryMuscles.length > 0" class="muscle-line">
            <abbr class="level" :title="t.secondaryLong">{{ t.secondary }}</abbr>
            <span v-for="(m, i) in secondaryMuscles" :key="m.muscle_id">
              <span :title="muscleFullName(m.muscle_id)">{{ muscleName(m.muscle_id) }}</span>
              <span v-if="m.note" class="muted"> ({{ m.note }})</span>
              <span v-if="i < secondaryMuscles.length - 1"> · </span>
            </span>
          </p>
        </dd>

        <dt>{{ t.equipment }}</dt>
        <dd>
          {{ equipmentName(detail.equipment_id) }}
          <span v-if="detail.equipment_detail" class="muted">({{ detail.equipment_detail }})</span>
        </dd>

        <dt>{{ t.stretch }}</dt>
        <dd>
          {{ labels.stretch[detail.stretch] }}
          <span v-if="detail.stretch_note" class="muted">({{ detail.stretch_note }})</span>
        </dd>

        <dt>{{ t.confidence }}</dt>
        <dd>{{ labels.confidence[detail.confidence] }}</dd>

        <dt>{{ t.families }}</dt>
        <dd data-testid="detail-families">
          {{ familyName(detail.primary_family_id) }}
          <span class="muted">({{ t.primaryFamily }}, {{ t.rank(detail.family_rank) }})</span>
          <template v-if="detail.secondary_family_id !== null">
            <br />
            {{ familyName(detail.secondary_family_id) }}
            <span class="muted">({{ t.secondaryFamily }})</span>
          </template>
        </dd>

        <dt>{{ t.tags }}</dt>
        <dd data-testid="detail-tags">
          <template v-if="tagRows.length === 0">{{ texts.common.none }}</template>
          <p v-for="{ tag, note } in tagRows" :key="tag.id" class="tag-line">
            <TagBadges :links="[{ tag_id: tag.id, note }]" />
            <span>{{ tag.name }}</span>
            <span v-if="note" class="muted"> — {{ note }}</span>
          </p>
        </dd>

        <dt>{{ t.variants }}</dt>
        <dd data-testid="detail-variants">
          <template v-if="variantGroups.length === 0">{{ t.noVariants }}</template>
          <div v-for="group in variantGroups" :key="group.familyId" class="variant-group">
            <span class="muted">{{ familyName(group.familyId) }}</span>
            <ul>
              <li v-for="variant in group.variants" :key="variant.id">
                <RouterLink :to="`/catalogo/esercizi/${String(variant.id)}`" class="text-link">
                  {{ variant.name }}
                </RouterLink>
                <TagBadges :links="variant.tags" />
                <span class="muted"> · {{ equipmentName(variant.equipment_id) }}</span>
              </li>
            </ul>
          </div>
        </dd>

        <dt>{{ t.sources }}</dt>
        <dd data-testid="detail-sources">
          <template v-if="detail.sources.length === 0">{{ texts.common.none }}</template>
          <ul>
            <li v-for="source in detail.sources" :key="source.id">
              <a
                v-if="source.url"
                :href="source.url"
                class="text-link"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ source.title }}
                <ExternalLink :size="13" aria-hidden="true" />
              </a>
              <span v-else>{{ source.title }}</span>
              <span class="muted">
                · {{ source.kind
                }}<template v-if="source.reliability"> · {{ source.reliability }}</template>
              </span>
            </li>
          </ul>
        </dd>

        <template v-if="detail.notes">
          <dt>{{ t.notes }}</dt>
          <dd class="notes">{{ detail.notes }}</dd>
        </template>
      </dl>
    </article>
  </main>
</template>

<style scoped>
.detail {
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

.back:hover {
  color: inherit;
}

.title {
  margin: 0;
}

.summary {
  margin: 0.35rem 0 1.25rem;
  color: var(--muted-color);
}

.fields {
  display: grid;
  grid-template-columns: 9rem minmax(0, 1fr);
  gap: 0.85rem 1.25rem;
  margin: 0;
}

dt {
  color: var(--muted-color);
  font-weight: 500;
}

dd {
  margin: 0;
}

dd p,
dd ul {
  margin: 0;
}

dd ul {
  padding-left: 1.1rem;
}

.muscle-line + .muscle-line,
.tag-line + .tag-line,
.variant-group + .variant-group {
  margin-top: 0.35rem;
}

.level {
  display: inline-block;
  width: 1.4rem;
  margin-right: 0.35rem;
  border-radius: 4px;
  background: var(--hover-color);
  font-weight: 700;
  text-align: center;
  text-decoration: none;
}

.level-p {
  color: var(--primary-color);
}

.tag-line :deep(.badges) {
  margin: 0 0.35rem 0 0;
}

.muted {
  color: var(--muted-color);
}

.notes {
  white-space: pre-line;
}

@media (max-width: 767px) {
  .fields {
    grid-template-columns: minmax(0, 1fr);
    gap: 0.2rem;
  }

  dd {
    margin-bottom: 0.75rem;
  }
}
</style>
