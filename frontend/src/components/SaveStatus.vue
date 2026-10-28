<script setup lang="ts">
import { Check, CircleAlert, LoaderCircle } from 'lucide-vue-next'

import type { SaveState } from '@/composables/useAutosave'
import { texts } from '@/texts'

/** Stato del salvataggio automatico, accanto al titolo (wireframe, § 3.3). */
defineProps<{ state: SaveState }>()
</script>

<template>
  <span
    class="save-status"
    :class="state"
    role="status"
    aria-live="polite"
    data-testid="save-status"
  >
    <Check v-if="state === 'saved'" :size="16" aria-hidden="true" />
    <LoaderCircle
      v-else-if="state === 'saving' || state === 'pending'"
      :size="16"
      class="spin"
      aria-hidden="true"
    />
    <CircleAlert v-else-if="state === 'error'" :size="16" aria-hidden="true" />
    {{ texts.saveState[state] }}
  </span>
</template>

<style scoped>
.save-status {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  min-height: 1.5rem;
  color: var(--muted-color);
  font-size: 0.875rem;
}

.save-status.error {
  color: var(--error-color);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .spin {
    animation: none;
  }
}
</style>
