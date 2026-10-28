<script setup lang="ts">
import {
  NAlert,
  NButton,
  NDropdown,
  NForm,
  NFormItem,
  NH1,
  NInput,
  NModal,
  NSkeleton,
  useMessage,
} from 'naive-ui'
import { CircleDot, EllipsisVertical, Plus } from 'lucide-vue-next'
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { api, asProblem, ifMatch, type PlanSummary } from '@/api/client'
import { useConfirm } from '@/composables/useConfirm'
import { formatDate } from '@/plans/preferences'
import { texts } from '@/texts'

/** Elenco delle schede (US-19; wireframe, § 3.1). */
const t = texts.plans
const message = useMessage()
const confirm = useConfirm()
const router = useRouter()

const plans = ref<PlanSummary[] | null>(null)
const failed = ref(false)
const busy = ref(false)

async function load(): Promise<void> {
  failed.value = false
  try {
    const { data } = await api.GET('/api/plans')
    if (data === undefined) failed.value = true
    else plans.value = data
  } catch {
    failed.value = true
  }
}

onMounted(() => {
  void load()
})

type Action = 'open' | 'rename' | 'duplicate' | 'activate' | 'delete'

const menu = (plan: PlanSummary) => [
  { key: 'open', label: t.open },
  { key: 'rename', label: t.rename },
  { key: 'duplicate', label: t.duplicate },
  { key: 'activate', label: t.activate, disabled: plan.is_active },
  { type: 'divider', key: 'divider' },
  { key: 'delete', label: t.delete },
]

function act(plan: PlanSummary, key: Action): void {
  const actions: Record<Action, () => unknown> = {
    open: () => router.push(`/schede/${String(plan.id)}`),
    rename: () => {
      startRename(plan)
    },
    duplicate: () => duplicate(plan),
    activate: () => activate(plan),
    delete: () => remove(plan),
  }
  void actions[key]()
}

function showError(error: unknown, status: number): void {
  const problem = asProblem(error, status)
  message.error(problem.detail ?? problem.title)
}

// --- Rinomina ----------------------------------------------------------------------

const renaming = ref<PlanSummary | null>(null)
const newName = ref('')
const nameError = ref<string | null>(null)

function startRename(plan: PlanSummary): void {
  renaming.value = plan
  newName.value = plan.name
  nameError.value = null
}

async function rename(): Promise<void> {
  const plan = renaming.value
  if (plan === null) return
  const name = newName.value.trim()
  if (name === '') {
    nameError.value = t.nameRequired
    return
  }
  busy.value = true
  try {
    const { data, error, response } = await api.PATCH('/api/plans/{plan_id}', {
      params: { path: { plan_id: plan.id } },
      body: { name },
      headers: ifMatch(plan.revision),
    })
    if (response.status === 412) {
      message.warning(t.changedElsewhere)
      renaming.value = null
      await load()
      return
    }
    if (data === undefined) {
      const problem = asProblem(error, response.status)
      nameError.value = problem.violations?.[0]?.message ?? problem.detail ?? problem.title
      return
    }
    renaming.value = null
    message.success(t.renamed)
    await load()
  } finally {
    busy.value = false
  }
}

// --- Duplica, rendi attiva, elimina ------------------------------------------------

async function duplicate(plan: PlanSummary): Promise<void> {
  const { data, error, response } = await api.POST('/api/plans/{plan_id}/duplicate', {
    params: { path: { plan_id: plan.id } },
  })
  if (data === undefined) {
    showError(error, response.status)
    return
  }
  message.success(t.duplicated(data.name))
  await load()
}

async function activate(plan: PlanSummary): Promise<void> {
  const { data, error, response } = await api.POST('/api/plans/{plan_id}/activate', {
    params: { path: { plan_id: plan.id } },
  })
  if (data === undefined) {
    showError(error, response.status)
    return
  }
  message.success(t.activated(plan.name))
  await load()
}

async function remove(plan: PlanSummary): Promise<void> {
  const confirmed = await confirm({
    title: t.deleteTitle,
    content: t.deleteConfirm(plan.name),
    action: t.deleteAction,
    cancel: t.cancel,
    type: 'error',
  })
  if (!confirmed) return
  const { error, response } = await api.DELETE('/api/plans/{plan_id}', {
    params: { path: { plan_id: plan.id } },
  })
  if (!response.ok) {
    showError(error, response.status)
    return
  }
  message.success(t.deleted(plan.name))
  await load()
}

function details(plan: PlanSummary): string {
  return `${plan.split_name ?? t.emptySplit} · ${t.days(plan.days_per_week)}`
}
</script>

<template>
  <main class="page">
    <header class="header">
      <NH1>{{ t.title }}</NH1>
      <NButton
        v-if="plans?.length"
        type="primary"
        data-testid="new-plan"
        @click="router.push('/schede/nuova')"
      >
        <template #icon><Plus :size="16" /></template>
        {{ t.add }}
      </NButton>
    </header>

    <NAlert v-if="failed" type="error">
      {{ texts.common.loadFailed }}
      <NButton text type="primary" @click="load">{{ texts.common.retry }}</NButton>
    </NAlert>
    <NSkeleton v-else-if="plans === null" text :repeat="3" />

    <div v-else-if="plans.length === 0" class="empty" data-testid="no-plans">
      <p>{{ t.empty }}</p>
      <NButton type="primary" data-testid="create-first" @click="router.push('/schede/nuova')">
        {{ t.createFirst }}
      </NButton>
    </div>

    <ul v-else class="plans" data-testid="plans">
      <li
        v-for="plan in plans"
        :key="plan.id"
        class="plan"
        :class="{ active: plan.is_active }"
        data-testid="plan"
      >
        <span class="marker" aria-hidden="true">
          <CircleDot v-if="plan.is_active" :size="18" />
        </span>
        <div class="main">
          <RouterLink :to="`/schede/${plan.id}`" class="name">{{ plan.name }}</RouterLink>
          <span class="meta">
            <template v-if="plan.is_active">
              <strong class="badge">{{ t.active }}</strong> ·
            </template>
            {{ t.modified(formatDate(plan.updated_at)) }}
          </span>
        </div>
        <span class="details">{{ details(plan) }}</span>
        <NDropdown
          trigger="click"
          placement="bottom-end"
          :options="menu(plan)"
          @select="(key: Action) => act(plan, key)"
        >
          <NButton
            quaternary
            circle
            :aria-label="t.actions(plan.name)"
            :disabled="busy"
            data-testid="plan-actions"
          >
            <template #icon><EllipsisVertical :size="18" /></template>
          </NButton>
        </NDropdown>
      </li>
    </ul>

    <NModal
      :show="renaming !== null"
      preset="card"
      :title="t.renameTitle"
      style="width: min(28rem, calc(100vw - 2rem))"
      data-testid="rename-dialog"
      @update:show="(show: boolean) => !show && (renaming = null)"
    >
      <NForm @submit.prevent="rename">
        <NFormItem
          :label="t.name"
          :validation-status="nameError ? 'error' : undefined"
          :feedback="nameError ?? undefined"
        >
          <NInput v-model:value="newName" :maxlength="120" data-testid="rename-input" />
        </NFormItem>
      </NForm>
      <template #footer>
        <div class="dialog-actions">
          <NButton @click="renaming = null">{{ t.cancel }}</NButton>
          <NButton type="primary" :loading="busy" data-testid="rename-save" @click="rename">
            {{ t.save }}
          </NButton>
        </div>
      </template>
    </NModal>
  </main>
</template>

<style scoped>
.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.header :deep(h1) {
  margin: 0;
}

.empty {
  padding: 2rem 0;
}

.plans {
  margin: 1rem 0 0;
  padding: 0;
  list-style: none;
  border-top: 1px solid var(--border-color);
}

.plan {
  display: grid;
  grid-template-columns: 1.5rem minmax(0, 1fr) auto auto;
  gap: 0.25rem 1rem;
  align-items: center;
  padding: 0.75rem 0.25rem;
  border-bottom: 1px solid var(--border-color);
}

.marker {
  display: inline-flex;
  color: var(--primary-color);
}

.main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.name {
  overflow: hidden;
  color: inherit;
  font-weight: 600;
  text-decoration: none;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.name:hover,
.name:focus-visible {
  color: var(--primary-color);
  text-decoration: underline;
}

.meta,
.details {
  color: var(--muted-color);
  font-size: 0.875rem;
}

.badge {
  color: var(--primary-color);
  font-weight: 500;
}

.dialog-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

@media (max-width: 767px) {
  .plan {
    grid-template-columns: 1.5rem minmax(0, 1fr) auto;
  }

  /* Sul telefono split e giorni vanno sotto, con la data. */
  .details {
    grid-column: 2;
    grid-row: 2;
  }

  .plan > :last-child {
    grid-column: 3;
    grid-row: 1 / 3;
  }
}
</style>
