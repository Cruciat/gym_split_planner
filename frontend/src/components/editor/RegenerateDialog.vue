<script setup lang="ts">
import { NButton, NCheckbox, NModal, NSkeleton, useMessage } from 'naive-ui'
import { ArrowRight, Lock } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'

import { type RegenerationPreview, usePlanEditor } from '@/plans/editor'
import { deltaEffect, formatDelta } from '@/plans/volume'
import { texts } from '@/texts'

/**
 * Rigenerazione con le preferenze attuali (US-18; wireframe, § 3.6): prima le
 * differenze, tutte scelte; si applicano solo quelle spuntate. Gli esercizi con il
 * lucchetto non compaiono e restano come sono.
 */
const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{ 'update:show': [show: boolean] }>()
const t = texts.regenerate
const editor = usePlanEditor()
const message = useMessage()

const preview = ref<RegenerationPreview | null>(null)
const chosen = ref<Set<number>>(new Set())
const applying = ref(false)

watch(
  () => props.show,
  async (show) => {
    preview.value = null
    if (!show) return
    const result = await editor.previewRegeneration()
    if (result === null) {
      emit('update:show', false)
      return
    }
    preview.value = result
    chosen.value = new Set(result.changes.map((c) => c.slot_id))
  },
  { immediate: true },
)

const volumes = computed(
  () => new Map((editor.plan.value?.analysis.volumes ?? []).map((v) => [v.muscle_id, v])),
)

function toggle(slotId: number, on: boolean): void {
  const next = new Set(chosen.value)
  if (on) next.add(slotId)
  else next.delete(slotId)
  chosen.value = next
}

async function apply(): Promise<void> {
  const current = preview.value
  if (current === null || chosen.value.size === 0) return
  applying.value = true
  try {
    const ids = current.changes.map((c) => c.slot_id).filter((id) => chosen.value.has(id))
    if (await editor.regenerate(ids, current.revision)) message.success(t.applied(ids.length))
    emit('update:show', false)
  } finally {
    applying.value = false
  }
}
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    :title="t.title"
    style="width: min(42rem, calc(100vw - 2rem))"
    data-testid="regenerate-dialog"
    @update:show="(value: boolean) => emit('update:show', value)"
  >
    <NSkeleton v-if="preview === null" text :repeat="4" />
    <template v-else>
      <p v-if="preview.changes.length === 0" data-testid="aligned">{{ t.aligned }}</p>
      <template v-else>
        <p class="intro">{{ t.intro }}</p>
        <ul class="changes">
          <li v-for="change in preview.changes" :key="change.slot_id" data-testid="change">
            <NCheckbox
              :checked="chosen.has(change.slot_id)"
              :aria-label="`${t.position(change.day_name, change.position)}: ${change.proposed.name}`"
              data-testid="change-check"
              @update:checked="(on: boolean) => toggle(change.slot_id, on)"
            />
            <div class="body">
              <span class="where">{{ t.position(change.day_name, change.position) }}</span>
              <span class="what">
                {{ change.current?.name ?? t.none }}
                <ArrowRight :size="14" aria-hidden="true" />
                <strong>{{ change.proposed.name }}</strong>
              </span>
              <span class="chips">
                <span v-if="change.volume_delta.length === 0" class="chip">
                  {{ texts.variants.noChange }}
                </span>
                <span
                  v-for="d in change.volume_delta"
                  :key="d.muscle_id"
                  class="chip"
                  :class="deltaEffect(volumes.get(d.muscle_id), d.delta)"
                >
                  {{ volumes.get(d.muscle_id)?.short_name ?? d.code }} {{ formatDelta(d.delta) }}
                </span>
              </span>
            </div>
          </li>
        </ul>
      </template>
      <p v-if="preview.locked_slots > 0" class="locked" data-testid="locked-note">
        <Lock :size="14" aria-hidden="true" />
        {{ t.locked(preview.locked_slots) }}
      </p>
    </template>

    <template #footer>
      <div class="actions">
        <NButton @click="emit('update:show', false)">
          {{ preview?.changes.length === 0 ? t.close : t.cancel }}
        </NButton>
        <NButton
          v-if="preview && preview.changes.length > 0"
          type="primary"
          :disabled="chosen.size === 0"
          :loading="applying"
          data-testid="apply-regeneration"
          @click="apply"
        >
          {{ t.apply(chosen.size) }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.intro {
  margin: 0 0 0.75rem;
  color: var(--muted-color);
}

.changes {
  max-height: 55vh;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  list-style: none;
}

.changes li {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--border-color);
}

.body {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.where {
  color: var(--muted-color);
  font-size: 0.85rem;
}

.what {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.3rem;
}

.what strong {
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

.locked {
  display: flex;
  gap: 0.35rem;
  align-items: center;
  margin: 0.75rem 0 0;
  color: var(--muted-color);
  font-size: 0.9rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}
</style>
