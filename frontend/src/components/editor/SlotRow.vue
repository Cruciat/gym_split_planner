<script setup lang="ts">
import { NButton, NDropdown, NInputNumber } from 'naive-ui'
import { ArrowDown, ArrowUp, EllipsisVertical, GripVertical, Lock, LockOpen } from 'lucide-vue-next'
import { computed } from 'vue'

import TagBadges from '@/components/TagBadges.vue'
import { type Slot, type SlotPatch, usePlanEditor } from '@/plans/editor'
import { texts } from '@/texts'

/**
 * Un esercizio della scheda (wireframe, § 3.3). Su schermo largo serie e ripetizioni
 * si modificano nella riga e si salvano all'uscita dal campo; sul telefono toccare la
 * riga apre il foglio con campi e azioni (`open`).
 */
const props = defineProps<{
  item: Slot
  index: number
  count: number
  mobile: boolean
  reorder: boolean
  /** Sotto i telefoni le maniglie si vedono solo in modalità "Riordina". */
  draggable: boolean
  highlighted: boolean
  emptyReason: string | null
  /** Il giorno si ripete: c'è una seconda seduta e la sua variante. */
  repeated: boolean
}>()
const emit = defineEmits<{
  move: [delta: -1 | 1]
  variants: []
  second: []
  open: []
  family: []
  note: []
  delete: []
}>()
const t = texts.editor
const editor = usePlanEditor()

const name = computed(() => props.item.exercise?.name ?? props.item.family.name)
const alternate = computed(() => props.item.weekly_weight < 1)

function patch(body: SlotPatch): void {
  void editor.updateSlot(props.item.id, body)
}

function setNumber(field: 'sets' | 'rep_min' | 'rep_max', value: number | null): void {
  if (value === null || value === props.item[field]) return
  patch({ [field]: value })
}

type Action = 'second' | 'family' | 'optional' | 'alternate' | 'note' | 'delete'

const menu = computed(() => [
  ...(props.repeated ? [{ key: 'second', label: t.slotMenu.secondSession }] : []),
  { key: 'family', label: t.slotMenu.changeFamily },
  {
    key: 'optional',
    label: props.item.is_optional ? t.slotMenu.optionalOff : t.slotMenu.optionalOn,
  },
  { key: 'alternate', label: alternate.value ? t.slotMenu.alternateOff : t.slotMenu.alternateOn },
  { key: 'note', label: t.slotMenu.note },
  { type: 'divider', key: 'divider' },
  { key: 'delete', label: t.slotMenu.delete },
])

function act(key: Action): void {
  if (key === 'optional') patch({ is_optional: !props.item.is_optional })
  else if (key === 'alternate') patch({ weekly_weight: alternate.value ? 1 : 0.5 })
  else if (key === 'family') emit('family')
  else if (key === 'second') emit('second')
  else if (key === 'note') emit('note')
  else emit('delete')
}

function openSheet(): void {
  if (props.mobile && !props.reorder) emit('open')
}
</script>

<template>
  <li
    class="slot"
    :class="{ optional: item.is_optional, highlighted, mobile, empty: item.exercise === null }"
    :data-slot-id="item.id"
    data-testid="slot"
  >
    <span v-if="draggable" class="drag-handle" :aria-label="t.drag(name)" role="img">
      <GripVertical :size="16" aria-hidden="true" />
    </span>
    <span v-else class="position">{{ index + 1 }}</span>

    <div
      class="main"
      :role="mobile && !reorder ? 'button' : undefined"
      :tabindex="mobile && !reorder ? 0 : undefined"
      data-testid="slot-main"
      @click="openSheet"
      @keydown.enter="openSheet"
    >
      <div class="title">
        <button
          v-if="!mobile && !reorder"
          type="button"
          class="name-button"
          :aria-label="t.openVariants(name)"
          data-testid="open-variants"
          @click="emit('variants')"
        >
          <strong :class="{ muted: item.exercise === null }" data-testid="slot-name">
            {{ item.exercise?.name ?? t.emptySlot }}
          </strong>
        </button>
        <strong v-else :class="{ muted: item.exercise === null }" data-testid="slot-name">
          {{ item.exercise?.name ?? t.emptySlot }}
        </strong>
        <TagBadges v-if="item.exercise" :links="item.exercise.badges" />
        <span v-if="item.is_optional" class="tag">{{ t.optional }}</span>
        <span v-if="alternate" class="tag">{{ t.alternate }}</span>
      </div>
      <div class="sub">
        <span v-if="mobile">{{ item.sets }} × {{ item.rep_min }}-{{ item.rep_max }} · </span>
        <span>{{ item.family.name }}</span>
        <span v-if="item.second_exercise"> · {{ t.secondSession(item.second_exercise.name) }}</span>
        <span v-if="emptyReason" class="reason"> · {{ emptyReason }}</span>
      </div>
      <p v-if="item.note" class="note">{{ item.note }}</p>
    </div>

    <div v-if="!mobile && !reorder" class="prescription">
      <NInputNumber
        :value="item.sets"
        :min="1"
        :max="8"
        size="small"
        :show-button="false"
        :update-value-on-input="false"
        :aria-label="t.setsOf(name)"
        class="number"
        data-testid="slot-sets"
        @update:value="(v: number | null) => setNumber('sets', v)"
      />
      <span aria-hidden="true">×</span>
      <NInputNumber
        :value="item.rep_min"
        :min="1"
        :max="100"
        size="small"
        :show-button="false"
        :update-value-on-input="false"
        :aria-label="t.repMinOf(name)"
        class="number"
        data-testid="slot-rep-min"
        @update:value="(v: number | null) => setNumber('rep_min', v)"
      />
      <span aria-hidden="true">-</span>
      <NInputNumber
        :value="item.rep_max"
        :min="1"
        :max="100"
        size="small"
        :show-button="false"
        :update-value-on-input="false"
        :aria-label="t.repMaxOf(name)"
        class="number"
        data-testid="slot-rep-max"
        @update:value="(v: number | null) => setNumber('rep_max', v)"
      />
    </div>

    <div class="actions">
      <template v-if="reorder">
        <NButton
          quaternary
          circle
          size="small"
          :disabled="index === 0"
          :aria-label="t.moveUp(name)"
          data-testid="slot-up"
          @click="emit('move', -1)"
        >
          <template #icon><ArrowUp :size="16" /></template>
        </NButton>
        <NButton
          quaternary
          circle
          size="small"
          :disabled="index === count - 1"
          :aria-label="t.moveDown(name)"
          data-testid="slot-down"
          @click="emit('move', 1)"
        >
          <template #icon><ArrowDown :size="16" /></template>
        </NButton>
      </template>
      <template v-else>
        <NButton
          quaternary
          circle
          size="small"
          :type="item.locked ? 'primary' : 'default'"
          :aria-pressed="item.locked"
          :aria-label="item.locked ? t.unlock(name) : t.lock(name)"
          :title="item.locked ? t.lockedHelp : undefined"
          data-testid="slot-lock"
          @click="patch({ locked: !item.locked })"
        >
          <template #icon>
            <Lock v-if="item.locked" :size="16" />
            <LockOpen v-else :size="16" />
          </template>
        </NButton>
        <NDropdown
          v-if="!mobile"
          trigger="click"
          placement="bottom-end"
          :options="menu"
          @select="act"
        >
          <NButton
            quaternary
            circle
            size="small"
            :aria-label="t.slotActions(name)"
            data-testid="slot-actions"
          >
            <template #icon><EllipsisVertical :size="16" /></template>
          </NButton>
        </NDropdown>
      </template>
    </div>
  </li>
</template>

<style scoped>
.slot {
  display: grid;
  grid-template-columns: 1.5rem minmax(0, 1fr) auto auto;
  gap: 0.25rem 0.75rem;
  align-items: center;
  padding: 0.55rem 0.25rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--page-color);
}

.item.mobile {
  grid-template-columns: 1.5rem minmax(0, 1fr) auto;
}

.item.optional .main {
  opacity: 0.6;
}

.item.highlighted {
  background: var(--hover-color);
  box-shadow: inset 3px 0 0 var(--primary-color);
}

.position {
  color: var(--muted-color);
  font-variant-numeric: tabular-nums;
  text-align: center;
}

.drag-handle {
  display: inline-flex;
  justify-content: center;
  color: var(--muted-color);
  cursor: grab;
  touch-action: none;
}

.main {
  min-width: 0;
}

.mobile .main[role='button'] {
  cursor: pointer;
}

.title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.15rem 0.4rem;
}

.title strong {
  font-weight: 500;
}

.name-button {
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.name-button:hover strong,
.name-button:focus-visible strong {
  color: var(--primary-color);
  text-decoration: underline;
  text-underline-offset: 0.15em;
}

.tag {
  padding: 0 0.35rem;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  color: var(--muted-color);
  font-size: 0.75rem;
}

.sub {
  color: var(--muted-color);
  font-size: 0.85rem;
}

.reason {
  color: var(--warning-color);
}

.note {
  margin: 0.15rem 0 0;
  color: var(--muted-color);
  font-size: 0.85rem;
  font-style: italic;
}

.muted {
  color: var(--muted-color);
}

.prescription {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--muted-color);
}

.number {
  width: 3.1rem;
}

.number :deep(input) {
  text-align: center;
}

.actions {
  display: flex;
  align-items: center;
  gap: 0.1rem;
}
</style>
