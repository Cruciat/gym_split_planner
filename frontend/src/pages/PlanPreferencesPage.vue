<script setup lang="ts">
import { NAlert, NButton, NH1, NSkeleton, useMessage } from 'naive-ui'
import { ChevronLeft } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { onBeforeRouteLeave, RouterLink } from 'vue-router'

import { api, asProblem, ifMatch } from '@/api/client'
import OverridesEditor from '@/components/OverridesEditor.vue'
import PreferencesBasics from '@/components/PreferencesBasics.vue'
import SaveStatus from '@/components/SaveStatus.vue'
import { useAutosave } from '@/composables/useAutosave'
import { useConfirm } from '@/composables/useConfirm'
import {
  fromPlanSettings,
  type MuscleRow,
  preferenceErrors,
  type PreferencesValue,
  type TagRow,
  toInput,
} from '@/plans/preferences'
import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/**
 * Preferenze e personalizzazioni di una scheda (US-11; wireframe, § 3.5). Si salvano da
 * sole poco dopo l'ultima modifica; il server normalizza e valida, e i suoi errori
 * compaiono accanto ai campi.
 */
const props = defineProps<{ id: number }>()
const t = texts.preferences
const store = useCatalogStore()
const message = useMessage()
const confirm = useConfirm()

const name = ref('')
const revision = ref(0)
const value = ref<PreferencesValue | null>(null)
const muscles = ref<MuscleRow[]>([])
const tags = ref<TagRow[]>([])
const notFound = ref(false)
const failed = ref(false)
const errors = ref<Record<string, string>>({})
const general = ref<string[]>([])

async function load(): Promise<void> {
  failed.value = false
  try {
    const [{ data, response }] = await Promise.all([
      api.GET('/api/plans/{plan_id}/settings', { params: { path: { plan_id: props.id } } }),
      store.load(),
    ])
    if (response.status === 404) {
      notFound.value = true
      return
    }
    if (data === undefined) {
      failed.value = true
      return
    }
    const view = fromPlanSettings(data)
    name.value = data.name
    revision.value = data.revision
    value.value = view.value
    muscles.value = view.muscles
    tags.value = view.tags
  } catch {
    failed.value = true
  }
}

onMounted(() => {
  void load()
})

async function save(): Promise<boolean> {
  if (value.value === null) return true
  const { data, error, response } = await api.PUT('/api/plans/{plan_id}/preferences', {
    params: { path: { plan_id: props.id } },
    body: toInput(value.value),
    headers: ifMatch(revision.value),
  })
  if (response.status === 412) {
    // Cambiata altrove: si riparte dai valori del server, senza sovrascriverli.
    message.warning(texts.plans.changedElsewhere)
    errors.value = {}
    general.value = []
    await load()
    // Ora la pagina mostra ciò che c'è sul server: non resta nulla da salvare.
    return true
  }
  if (data === undefined) {
    const mapped = preferenceErrors(asProblem(error, response.status), t.invalid)
    errors.value = mapped.fields
    general.value = mapped.general
    return false
  }
  revision.value = data.revision
  errors.value = {}
  general.value = []
  return true
}

const autosave = useAutosave(save)

function update(next: PreferencesValue): void {
  value.value = next
  autosave.schedule()
}

// Uscendo dalla pagina si salva subito ciò che è in attesa; se il server rifiuta, si
// chiede prima di perdere la modifica.
onBeforeRouteLeave(async () => {
  await autosave.flush()
  if (autosave.state.value !== 'error') return true
  return confirm({
    title: t.leaveTitle,
    content: t.leaveText,
    action: t.leave,
    cancel: t.stay,
  })
})

const equipment = computed(() =>
  (store.catalog?.equipment ?? []).map(({ code, name: label }) => ({ code, name: label })),
)
</script>

<template>
  <main class="page">
    <template v-if="notFound">
      <NAlert type="warning">{{ t.notFound }}</NAlert>
      <p>
        <RouterLink to="/schede" class="text-link">{{ t.backToPlans }}</RouterLink>
      </p>
    </template>

    <NAlert v-else-if="failed || store.failed" type="error">
      {{ texts.common.loadFailed }}
      <NButton text type="primary" @click="load">{{ texts.common.retry }}</NButton>
    </NAlert>

    <NSkeleton v-else-if="value === null" text :repeat="6" />

    <template v-else>
      <RouterLink :to="`/schede/${id}`" class="back text-link">
        <ChevronLeft :size="16" aria-hidden="true" />
        {{ t.backToPlan }}
      </RouterLink>
      <header class="header">
        <NH1>{{ t.title(name) }}</NH1>
        <SaveStatus :state="autosave.state.value" />
      </header>

      <p v-for="text in general" :key="text" class="error" role="alert">{{ text }}</p>

      <PreferencesBasics
        :value="value"
        :equipment="equipment"
        :errors="errors"
        @update:value="update"
      />

      <OverridesEditor
        class="overrides"
        :overrides="value.overrides"
        :muscles="muscles"
        :tags="tags"
        :errors="errors"
        @update:overrides="(overrides) => value && update({ ...value, overrides })"
      />

      <p class="note">{{ t.regenerateNote }}</p>
    </template>
  </main>
</template>

<style scoped>
.back {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.9rem;
}

.header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.25rem 1rem;
  margin-bottom: 1rem;
}

.header :deep(h1) {
  margin: 0.25rem 0 0;
}

.overrides {
  margin-top: 2rem;
}

.note {
  max-width: 48rem;
  margin-top: 1.5rem;
  color: var(--muted-color);
  font-size: 0.9rem;
}

.error {
  color: var(--error-color);
}
</style>
