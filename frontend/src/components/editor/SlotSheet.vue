<script setup lang="ts">
import { NButton, NDrawer, NDrawerContent, NInputNumber, NSwitch } from 'naive-ui'
import { computed } from 'vue'

import TagBadges from '@/components/TagBadges.vue'
import { type Slot, type SlotPatch, usePlanEditor } from '@/plans/editor'
import { texts } from '@/texts'

/** Sul telefono: campi e azioni di un esercizio in un foglio dal basso (wireframe, § 3.7). */
const props = defineProps<{ item: Slot | null; repeated: boolean }>()
const emit = defineEmits<{
  close: []
  variants: []
  second: []
  family: []
  note: []
  delete: []
}>()
const t = texts.editor
const editor = usePlanEditor()

const name = computed(() => props.item?.exercise?.name ?? props.item?.family.name ?? '')

function patch(body: SlotPatch): void {
  if (props.item !== null) void editor.updateSlot(props.item.id, body)
}

function setNumber(field: 'sets' | 'rep_min' | 'rep_max', value: number | null): void {
  if (props.item === null || value === null || value === props.item[field]) return
  patch({ [field]: value })
}
</script>

<template>
  <NDrawer
    :show="item !== null"
    placement="bottom"
    height="min(36rem, 90vh)"
    :auto-focus="false"
    data-testid="slot-sheet"
    @update:show="(show: boolean) => !show && emit('close')"
  >
    <NDrawerContent v-if="item" closable>
      <template #header>
        <span class="title">
          {{ name }}
          <TagBadges v-if="item.exercise" :links="item.exercise.badges" />
        </span>
        <small class="family">{{ item.family.name }}</small>
      </template>

      <div class="fields">
        <label>
          <span>{{ t.sets }}</span>
          <NInputNumber
            :value="item.sets"
            :min="1"
            :max="8"
            :update-value-on-input="false"
            data-testid="sheet-sets"
            @update:value="(v: number | null) => setNumber('sets', v)"
          />
        </label>
        <label>
          <span>{{ t.repMin }}</span>
          <NInputNumber
            :value="item.rep_min"
            :min="1"
            :max="100"
            :update-value-on-input="false"
            data-testid="sheet-rep-min"
            @update:value="(v: number | null) => setNumber('rep_min', v)"
          />
        </label>
        <label>
          <span>{{ t.repMax }}</span>
          <NInputNumber
            :value="item.rep_max"
            :min="1"
            :max="100"
            :update-value-on-input="false"
            data-testid="sheet-rep-max"
            @update:value="(v: number | null) => setNumber('rep_max', v)"
          />
        </label>
      </div>

      <div class="switches">
        <label>
          <NSwitch
            :value="item.is_optional"
            data-testid="sheet-optional"
            @update:value="(v: boolean) => patch({ is_optional: v })"
          />
          {{ t.optional }}
        </label>
        <label>
          <NSwitch
            :value="item.weekly_weight < 1"
            data-testid="sheet-alternate"
            @update:value="(v: boolean) => patch({ weekly_weight: v ? 0.5 : 1 })"
          />
          {{ t.alternate }}
        </label>
        <label>
          <NSwitch
            :value="item.locked"
            data-testid="sheet-locked"
            @update:value="(v: boolean) => patch({ locked: v })"
          />
          {{ t.lockedHelp }}
        </label>
      </div>

      <p v-if="item.note" class="note">{{ item.note }}</p>

      <div class="buttons">
        <NButton secondary data-testid="sheet-variants" @click="emit('variants')">
          {{ t.slotMenu.variants }}
        </NButton>
        <NButton v-if="repeated" secondary data-testid="sheet-second" @click="emit('second')">
          {{ t.slotMenu.secondSession }}
        </NButton>
        <NButton secondary @click="emit('family')">{{ t.slotMenu.changeFamily }}</NButton>
        <NButton secondary @click="emit('note')">{{ t.slotMenu.note }}</NButton>
        <NButton secondary type="error" data-testid="sheet-delete" @click="emit('delete')">
          {{ t.slotMenu.delete }}
        </NButton>
      </div>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
.title {
  display: inline-flex;
  align-items: center;
}

.family {
  display: block;
  color: var(--muted-color);
  font-weight: normal;
}

.fields {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.fields label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
}

.fields span {
  color: var(--muted-color);
}

.switches {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 1rem;
}

.switches label {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.note {
  color: var(--muted-color);
  font-style: italic;
}

.buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 1.25rem 0 0.5rem;
}
</style>
