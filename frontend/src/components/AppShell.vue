<script setup lang="ts">
import { NDialogProvider, NMessageProvider, useThemeVars } from 'naive-ui'
import { computed } from 'vue'
import { RouterView } from 'vue-router'

import AppNav from '@/components/AppNav.vue'

/**
 * Struttura comune delle pagine: navigazione e contenuto. Espone alcuni colori del
 * tema di Naive UI come variabili CSS, così anche gli stili delle pagine seguono il
 * tema chiaro o scuro.
 */
const vars = useThemeVars()
const style = computed(() => ({
  '--primary-color': vars.value.primaryColor,
  '--border-color': vars.value.dividerColor,
  '--surface-color': vars.value.cardColor,
  '--hover-color': vars.value.hoverColor,
  '--muted-color': vars.value.textColor3,
  '--error-color': vars.value.errorColor,
  '--on-primary-color': vars.value.baseColor,
  '--page-color': vars.value.bodyColor,
}))
</script>

<template>
  <div class="shell" :style="style">
    <AppNav />
    <NDialogProvider>
      <NMessageProvider>
        <RouterView />
      </NMessageProvider>
    </NDialogProvider>
  </div>
</template>

<style scoped>
.shell {
  --nav-height: 3.5rem;

  min-height: 100vh;
}

@media (max-width: 767px) {
  .shell {
    padding-bottom: calc(var(--nav-height) + env(safe-area-inset-bottom));
  }
}
</style>
