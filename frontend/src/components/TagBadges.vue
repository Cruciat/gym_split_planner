<script setup lang="ts">
import { NPopover, useThemeVars } from 'naive-ui'
import { computed } from 'vue'

import type { TagLink } from '@/api/client'
import { COLOR_VARS, symbolIcon } from '@/catalog/symbols'
import { useIsMobile } from '@/composables/useIsMobile'
import { useCatalogStore } from '@/stores/catalog'

/**
 * Simboli delle etichette di un esercizio (US-13 CA4, wireframe § 1.5): solo quelle
 * con simbolo visibile, nell'ordine delle etichette. Nome e nota si leggono passando
 * sopra con il mouse o, sul telefono, toccando il simbolo.
 */
const props = defineProps<{ links: TagLink[] }>()

const store = useCatalogStore()
const themeVars = useThemeVars()
const isMobile = useIsMobile()

const badges = computed(() =>
  props.links
    .flatMap((link) => {
      const tag = store.tags.get(link.tag_id)
      return tag?.show_badge === true ? [{ tag, note: link.note }] : []
    })
    .sort((a, b) => a.tag.sort_order - b.tag.sort_order),
)

function label(name: string, note: string | null): string {
  return note === null ? name : `${name}: ${note}`
}
</script>

<template>
  <span v-if="badges.length > 0" class="badges">
    <NPopover
      v-for="{ tag, note } in badges"
      :key="tag.id"
      :trigger="isMobile ? 'click' : 'hover'"
      :keep-alive-on-hover="false"
    >
      <template #trigger>
        <span
          class="badge"
          role="img"
          tabindex="0"
          :aria-label="label(tag.name, note)"
          :data-testid="`badge-${tag.code}`"
          :style="{ color: themeVars[COLOR_VARS[tag.color]] }"
          @click.stop.prevent
        >
          <component :is="symbolIcon(tag.symbol)" :size="16" aria-hidden="true" />
        </span>
      </template>
      <strong>{{ tag.name }}</strong>
      <template v-if="note !== null"><br />{{ note }}</template>
    </NPopover>
  </span>
</template>

<style scoped>
.badges {
  display: inline-flex;
  gap: 0.15rem;
  vertical-align: -0.15em;
  margin-left: 0.35rem;
}

.badge {
  display: inline-flex;
  cursor: help;
  border-radius: 3px;
}

.badge:focus-visible {
  outline: 2px solid currentcolor;
  outline-offset: 1px;
}
</style>
