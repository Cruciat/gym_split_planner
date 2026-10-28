<script setup lang="ts">
import {
  NAlert,
  NButton,
  NH1,
  NInput,
  NInputNumber,
  NSkeleton,
  NSwitch,
  useMessage,
} from 'naive-ui'
import { RotateCcw } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import { api, asProblem } from '@/api/client'
import { useConfirm } from '@/composables/useConfirm'
import {
  type Field,
  type FieldPath,
  getValue,
  GROUPS,
  sameSettings,
  type Settings,
  setValue,
  settingsErrors,
} from '@/settings/form'
import { useHealthStore } from '@/stores/health'
import { texts } from '@/texts'

/**
 * Impostazioni globali (US-20; wireframe, § 5). È una form con «Salva» esplicito: le
 * impostazioni valgono per tutte le schede, e un salvataggio a ogni tasto ricalcolerebbe
 * le analisi a metà di un numero. Esportazione e importazione arrivano con M6.
 */
const t = texts.settings
const health = useHealthStore()
const message = useMessage()
const confirm = useConfirm()

const form = ref<Settings | null>(null)
const saved = ref<Settings | null>(null)
const failed = ref(false)
const saving = ref(false)
const errors = ref<Partial<Record<string, string>>>({})
const general = ref<string[]>([])

const dirty = computed(
  () => form.value !== null && saved.value !== null && !sameSettings(form.value, saved.value),
)

async function load(): Promise<void> {
  failed.value = false
  try {
    const { data } = await api.GET('/api/settings')
    if (data === undefined) failed.value = true
    else {
      form.value = data
      saved.value = data
    }
  } catch {
    failed.value = true
  }
}

onMounted(() => {
  void load()
  void health.load()
})

function update(path: FieldPath, value: number | string | boolean | null): void {
  if (form.value === null) return
  form.value = setValue(form.value, path, value)
}

const numberValue = (path: FieldPath) => {
  const value = form.value === null ? null : getValue(form.value, path)
  return typeof value === 'number' ? value : null
}
const textValue = (path: FieldPath) => {
  const value = form.value === null ? null : getValue(form.value, path)
  return typeof value === 'string' ? value : ''
}
const boolValue = (path: FieldPath) => form.value !== null && getValue(form.value, path) === true

/** Errori del gruppo che non appartengono a un campo, es. "S non può superare P". */
function groupErrors(fields: Field[]): string[] {
  const prefixes = new Set(fields.map((f) => f.path.split('.')[0]))
  return Object.entries(errors.value).flatMap(([path, text]) =>
    prefixes.has(path) && !fields.some((f) => f.path === path) && text !== undefined ? [text] : [],
  )
}

async function save(): Promise<void> {
  if (form.value === null) return
  saving.value = true
  try {
    const { data, error, response } = await api.PUT('/api/settings', { body: form.value })
    if (data === undefined) {
      const mapped = settingsErrors(asProblem(error, response.status))
      errors.value = mapped.fields
      general.value = mapped.general.length > 0 ? mapped.general : [t.notSaved]
      return
    }
    form.value = data
    saved.value = data
    errors.value = {}
    general.value = []
    message.success(t.saved)
  } catch {
    general.value = [texts.common.loadFailed]
  } finally {
    saving.value = false
  }
}

/** I valori iniziali nella form: si applicano solo salvando. */
async function resetDefaults(): Promise<void> {
  const { data } = await api.GET('/api/settings/defaults')
  if (data === undefined) {
    message.error(texts.common.loadFailed)
    return
  }
  form.value = data
  errors.value = {}
  general.value = []
  message.info(t.resetDone)
}

onBeforeRouteLeave(async () => {
  if (!dirty.value) return true
  return confirm({ title: t.leaveTitle, content: t.leaveText, action: t.leave, cancel: t.stay })
})
</script>

<template>
  <main class="page">
    <NH1>{{ t.title }}</NH1>
    <p class="intro">{{ t.intro }}</p>

    <NAlert v-if="failed" type="error">
      {{ texts.common.loadFailed }}
      <NButton text type="primary" @click="load">{{ texts.common.retry }}</NButton>
    </NAlert>
    <NSkeleton v-else-if="form === null" text :repeat="8" />

    <form v-else class="settings" data-testid="settings-form" @submit.prevent="save">
      <fieldset v-for="group in GROUPS" :key="group.key" class="group" :data-group="group.key">
        <legend>{{ t.groups[group.key] }}</legend>
        <p class="help">{{ t.groupHelp[group.key] }}</p>
        <div class="fields" :class="{ wide: group.key === 'warmup' }">
          <label
            v-for="field in group.fields"
            :key="field.path"
            class="field"
            :class="{ switch: field.kind === 'switch', full: field.kind === 'textarea' }"
          >
            <span class="label">{{ t.fields[field.path] }}</span>
            <NInputNumber
              v-if="field.kind === 'number'"
              :value="numberValue(field.path)"
              :min="field.exclusiveMin ? undefined : field.min"
              :max="field.max"
              :step="field.step"
              :status="errors[field.path] ? 'error' : undefined"
              :data-testid="`setting-${field.path}`"
              @update:value="(v: number | null) => update(field.path, v)"
            >
              <template v-if="field.unit" #suffix>{{ t.units[field.unit] }}</template>
            </NInputNumber>
            <NInput
              v-else-if="field.kind === 'text'"
              :value="textValue(field.path)"
              :placeholder="t.rirPlaceholder"
              :maxlength="5"
              :status="errors[field.path] ? 'error' : undefined"
              :data-testid="`setting-${field.path}`"
              @update:value="(v: string) => update(field.path, v)"
            />
            <NInput
              v-else-if="field.kind === 'textarea'"
              type="textarea"
              :value="textValue(field.path)"
              :autosize="{ minRows: 3, maxRows: 8 }"
              :maxlength="2000"
              show-count
              :status="errors[field.path] ? 'error' : undefined"
              :data-testid="`setting-${field.path}`"
              @update:value="(v: string) => update(field.path, v)"
            />
            <NSwitch
              v-else
              :value="boolValue(field.path)"
              :data-testid="`setting-${field.path}`"
              @update:value="(v: boolean) => update(field.path, v)"
            />
            <small v-if="field.path === 'effort.rir'" class="help">{{ t.rirHelp }}</small>
            <small v-if="errors[field.path]" class="error">{{ errors[field.path] }}</small>
          </label>
        </div>
        <p v-for="text in groupErrors(group.fields)" :key="text" class="error" role="alert">
          {{ text }}
        </p>
      </fieldset>

      <p v-for="text in general" :key="text" class="error" role="alert">{{ text }}</p>

      <div class="buttons">
        <NButton data-testid="reset-defaults" @click="resetDefaults">
          <template #icon><RotateCcw :size="16" /></template>
          {{ t.reset }}
        </NButton>
        <NButton
          type="primary"
          attr-type="submit"
          :disabled="!dirty"
          :loading="saving"
          data-testid="save-settings"
        >
          {{ t.save }}
        </NButton>
      </div>
    </form>

    <section class="system">
      <h2>{{ t.system }}</h2>
      <NAlert v-if="health.failed" type="error" data-testid="health-error">
        {{ t.serverDown }}
      </NAlert>
      <NAlert
        v-else-if="health.health"
        :type="health.health.status === 'ok' ? 'success' : 'warning'"
        data-testid="health-ok"
      >
        {{ t.server(health.health.status === 'ok', health.health.version, health.health.database) }}
      </NAlert>
    </section>
  </main>
</template>

<style scoped>
.intro {
  max-width: 48rem;
  margin: 0.25rem 0 1.25rem;
  color: var(--muted-color);
}

.settings {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 60rem;
}

.group {
  margin: 0;
  padding: 1rem 1.1rem 1.1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

legend {
  padding: 0 0.35rem;
  font-weight: 600;
}

.help {
  margin: 0 0 0.75rem;
  color: var(--muted-color);
  font-size: 0.875rem;
}

.fields {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr));
  gap: 0.85rem 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.field.full {
  grid-column: 1 / -1;
}

.field.switch {
  flex-direction: row-reverse;
  justify-content: flex-end;
  align-items: center;
  gap: 0.6rem;
  grid-column: span 2;
}

.label {
  font-size: 0.9rem;
}

.field .help {
  margin: 0;
}

.error {
  margin: 0;
  color: var(--error-color);
  font-size: 0.875rem;
}

.buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-end;
}

.system {
  max-width: 60rem;
  margin-top: 2rem;
}

.system h2 {
  margin: 0 0 0.5rem;
  font-size: 1.05rem;
}

@media (max-width: 767px) {
  .fields {
    grid-template-columns: minmax(0, 1fr);
  }

  .field.switch {
    grid-column: auto;
  }

  .buttons {
    justify-content: stretch;
  }

  .buttons > * {
    flex: 1;
  }
}
</style>
