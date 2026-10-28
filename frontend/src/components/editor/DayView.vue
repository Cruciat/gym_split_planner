<script setup lang="ts">
import { NButton, NDropdown } from 'naive-ui'
import { EllipsisVertical, Plus } from 'lucide-vue-next'
import { computed, ref, toRef } from 'vue'

import DayDialog from '@/components/editor/DayDialog.vue'
import SlotDialog from '@/components/editor/SlotDialog.vue'
import SlotRow from '@/components/editor/SlotRow.vue'
import SlotSheet from '@/components/editor/SlotSheet.vue'
import TextDialog from '@/components/editor/TextDialog.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useSortable } from '@/composables/useSortable'
import { moveItem } from '@/plans/preferences'
import { type Day, type Slot, usePlanEditor } from '@/plans/editor'
import { dayMinutes } from '@/plans/volume'
import { useCatalogStore } from '@/stores/catalog'
import { texts } from '@/texts'

/** Un giorno della scheda: testata, esercizi e stretching (wireframe, § 3.3 e § 3.7). */
const props = defineProps<{
  day: Day
  dayIndex: number
  dayCount: number
  mobile: boolean
  highlightedSlot: number | null
}>()
const t = texts.editor
const editor = usePlanEditor()
const confirm = useConfirm()
const catalog = useCatalogStore()

const reorder = ref(false)
const dayDialog = ref(false)
const slotDialog = ref<{ mode: 'add' | 'family'; slot: Slot | null } | null>(null)
const noteSlot = ref<Slot | null>(null)
const sheetSlotId = ref<number | null>(null)

const plan = computed(() => editor.plan.value)
const minutes = computed(() => (plan.value === null ? [] : dayMinutes(plan.value, props.day.id)))
const meta = computed(() =>
  [
    t.timesPerWeek(props.day.times_per_week),
    ...(minutes.value.length > 0 ? [t.minutes(minutes.value)] : []),
  ].join(' · '),
)
const sheetSlot = computed(() => props.day.slots.find((s) => s.id === sheetSlotId.value) ?? null)

/** Motivo dello slot vuoto, dagli avvisi `empty-slot`. */
function emptyReason(slot: Slot): string | null {
  if (slot.exercise !== null) return null
  const warning = plan.value?.analysis.warnings.find(
    (w) => w.code === 'empty-slot' && w.slot_id === slot.id,
  )
  if (warning === undefined || warning.excluded_by.length === 0) return null
  const names = warning.excluded_by.map(
    (code) => catalog.catalog?.tags.find((tag) => tag.code === code)?.name ?? code,
  )
  return t.emptySlotExcluded(names)
}

// --- Riordino ------------------------------------------------------------------------

const list = ref<HTMLElement | null>(null)
const draggable = computed(() => !props.mobile || reorder.value)

function moveSlot(from: number, to: number): void {
  const ids = props.day.slots.map((s) => s.id)
  const [id] = ids.splice(from, 1)
  if (id === undefined) return
  ids.splice(to, 0, id)
  void editor.reorderSlots(props.day.id, ids)
}

useSortable(list, {
  handle: '.drag-handle',
  enabled: draggable,
  onMove: moveSlot,
})

// --- Menu del giorno -------------------------------------------------------------------

type DayAction = 'edit' | 'before' | 'after' | 'reorder' | 'delete'

const dayMenu = computed(() => [
  { key: 'edit', label: t.dayMenu.edit },
  { key: 'before', label: t.dayMenu.moveBefore, disabled: props.dayIndex === 0 },
  { key: 'after', label: t.dayMenu.moveAfter, disabled: props.dayIndex === props.dayCount - 1 },
  { key: 'reorder', label: reorder.value ? t.endReorder : t.dayMenu.reorder },
  { type: 'divider', key: 'divider' },
  { key: 'delete', label: t.dayMenu.delete },
])

function actOnDay(key: DayAction): void {
  if (key === 'edit') dayDialog.value = true
  else if (key === 'reorder') reorder.value = !reorder.value
  else if (key === 'delete') void deleteDay()
  else moveDay(key === 'before' ? -1 : 1)
}

function moveDay(delta: -1 | 1): void {
  const days = plan.value?.days ?? []
  const ids = moveItem(
    days.map((d) => d.id),
    props.dayIndex,
    delta,
  )
  void editor.reorderDays(ids)
}

async function saveDay(value: { name: string; times_per_week: number }): Promise<void> {
  const day = props.day
  const variants = day.slots.filter((s) => s.second_exercise !== null)
  // Scendendo a una volta la seconda seduta sparisce: si dice quali varianti si perdono.
  if (value.times_per_week < 2 && day.times_per_week >= 2 && variants.length > 0) {
    const confirmed = await confirm({
      title: t.removeVariantsTitle,
      content: t.removeVariants(
        day.name,
        variants.map((s) =>
          t.variantPair(s.exercise?.name ?? s.family.name, s.second_exercise?.name ?? ''),
        ),
      ),
      action: t.removeVariantsAction,
      cancel: t.cancel,
    })
    if (!confirmed) return
  }
  dayDialog.value = false
  const changes: { name?: string; times_per_week?: number } = {}
  if (value.name !== day.name) changes.name = value.name
  if (value.times_per_week !== day.times_per_week) changes.times_per_week = value.times_per_week
  if (Object.keys(changes).length > 0) await editor.updateDay(day.id, changes)
}

async function deleteDay(): Promise<void> {
  const day = props.day
  if (day.slots.length > 0) {
    const confirmed = await confirm({
      title: t.deleteDayTitle,
      content: t.deleteDayConfirm(day.name, day.slots.length),
      action: t.deleteDayAction,
      cancel: t.cancel,
      type: 'error',
    })
    if (!confirmed) return
  }
  await editor.deleteDay(day.id)
}

// --- Esercizi --------------------------------------------------------------------------

async function saveSlot(value: { family_id: number; exercise_id: number | null }): Promise<void> {
  const dialog = slotDialog.value
  slotDialog.value = null
  if (dialog === null) return
  if (dialog.mode === 'add') {
    await editor.addSlot(props.day.id, {
      family_id: value.family_id,
      ...(value.exercise_id === null ? {} : { exercise_id: value.exercise_id }),
    })
  } else if (dialog.slot !== null) {
    await editor.updateSlot(dialog.slot.id, { family_id: value.family_id })
  }
}

async function saveNote(text: string): Promise<void> {
  const slot = noteSlot.value
  noteSlot.value = null
  if (slot !== null) await editor.updateSlot(slot.id, { note: text === '' ? null : text })
}

async function deleteSlot(slot: Slot): Promise<void> {
  const confirmed = await confirm({
    title: t.deleteSlotTitle,
    content: t.deleteSlotConfirm(slot.exercise?.name ?? slot.family.name),
    action: t.deleteSlotAction,
    cancel: t.cancel,
    type: 'error',
  })
  if (!confirmed) return
  sheetSlotId.value = null
  await editor.deleteSlot(slot.id)
}

function fromSheet(action: 'family' | 'note' | 'delete'): void {
  const slot = sheetSlot.value
  if (slot === null) return
  if (action === 'delete') {
    void deleteSlot(slot)
    return
  }
  sheetSlotId.value = null
  if (action === 'family') slotDialog.value = { mode: 'family', slot }
  else noteSlot.value = slot
}

const highlighted = toRef(props, 'highlightedSlot')
</script>

<template>
  <section class="day" :data-day-id="day.id" data-testid="day">
    <header class="day-head">
      <div>
        <h2 data-testid="day-title">{{ day.name }}</h2>
        <span class="meta" data-testid="day-meta">{{ meta }}</span>
      </div>
      <NButton v-if="reorder" size="small" data-testid="end-reorder" @click="reorder = false">
        {{ t.endReorder }}
      </NButton>
      <NDropdown trigger="click" placement="bottom-end" :options="dayMenu" @select="actOnDay">
        <NButton quaternary circle :aria-label="t.dayActions(day.name)" data-testid="day-actions">
          <template #icon><EllipsisVertical :size="18" /></template>
        </NButton>
      </NDropdown>
    </header>

    <p v-if="reorder" class="help">{{ t.reorderHelp }}</p>
    <p v-if="day.slots.length === 0" class="muted" data-testid="empty-day">{{ t.emptyDay }}</p>

    <ol ref="list" class="slots" data-testid="slots">
      <SlotRow
        v-for="(slot, index) in day.slots"
        :key="slot.id"
        :item="slot"
        :index="index"
        :count="day.slots.length"
        :mobile="mobile"
        :reorder="reorder"
        :draggable="draggable"
        :highlighted="highlighted === slot.id"
        :empty-reason="emptyReason(slot)"
        @move="(delta) => moveSlot(index, index + delta)"
        @open="sheetSlotId = slot.id"
        @family="slotDialog = { mode: 'family', slot }"
        @note="noteSlot = slot"
        @delete="deleteSlot(slot)"
      />
    </ol>

    <NButton
      v-if="!reorder"
      dashed
      class="add-slot"
      data-testid="add-slot"
      @click="slotDialog = { mode: 'add', slot: null }"
    >
      <template #icon><Plus :size="16" /></template>
      {{ t.addSlot }}
    </NButton>

    <p v-if="day.stretches.length > 0" class="stretching" data-testid="stretching">
      <strong>{{ t.stretching }}:</strong>
      {{ day.stretches.map((s) => s.name).join(' · ') }}
    </p>

    <DayDialog
      v-model:show="dayDialog"
      :title="t.editDayTitle(day.name)"
      :action="t.save"
      :initial-name="day.name"
      :initial-times="day.times_per_week"
      @submit="saveDay"
    />
    <SlotDialog
      :show="slotDialog !== null"
      :mode="slotDialog?.mode ?? 'add'"
      :current-family-id="slotDialog?.slot?.family.id ?? null"
      @update:show="(show: boolean) => !show && (slotDialog = null)"
      @submit="saveSlot"
    />
    <TextDialog
      :show="noteSlot !== null"
      :title="t.noteTitle"
      :label="t.noteTitle"
      :value="noteSlot?.note ?? ''"
      :action="t.save"
      multiline
      :maxlength="500"
      :placeholder="t.notePlaceholder"
      @update:show="(show: boolean) => !show && (noteSlot = null)"
      @submit="saveNote"
    />
    <SlotSheet
      v-if="mobile"
      :item="sheetSlot"
      @close="sheetSlotId = null"
      @family="fromSheet('family')"
      @note="fromSheet('note')"
      @delete="fromSheet('delete')"
    />
  </section>
</template>

<style scoped>
.day-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-color);
}

.day-head > div {
  flex: 1;
  min-width: 0;
}

h2 {
  display: inline;
  margin: 0 0.5rem 0 0;
  font-size: 1.15rem;
}

.meta {
  color: var(--muted-color);
  font-size: 0.9rem;
}

.slots {
  margin: 0;
  padding: 0;
  list-style: none;
}

.help,
.muted {
  margin: 0.75rem 0;
  color: var(--muted-color);
  font-size: 0.9rem;
}

.add-slot {
  margin-top: 0.75rem;
}

.stretching {
  margin: 1.25rem 0 0;
  color: var(--muted-color);
  font-size: 0.9rem;
}

:deep(.sortable-ghost) {
  opacity: 0.4;
}
</style>
