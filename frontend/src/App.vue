<script setup lang="ts">
import {
  darkTheme,
  dateItIT,
  type GlobalThemeOverrides,
  itIT,
  NConfigProvider,
  NGlobalStyle,
  useOsTheme,
} from 'naive-ui'
import { computed } from 'vue'

import AppShell from '@/components/AppShell.vue'

// Tema chiaro o scuro secondo il sistema (wireframe, § 7); testi dei componenti in italiano.
const osTheme = useOsTheme()
const dark = computed(() => osTheme.value === 'dark')
const theme = computed(() => (dark.value ? darkTheme : null))

// Un solo colore d'accento, un verde petrolio sobrio; il resto resta quello di Naive UI.
const overrides = computed<GlobalThemeOverrides>(() => ({
  common: dark.value
    ? {
        primaryColor: '#4fb8a3',
        primaryColorHover: '#6ccab7',
        primaryColorPressed: '#3a9886',
        primaryColorSuppl: '#3a9886',
      }
    : {
        primaryColor: '#1f7a68',
        primaryColorHover: '#2a917d',
        primaryColorPressed: '#17604f',
        primaryColorSuppl: '#2a917d',
      },
}))
</script>

<template>
  <NConfigProvider
    :theme="theme"
    :theme-overrides="overrides"
    :locale="itIT"
    :date-locale="dateItIT"
  >
    <NGlobalStyle />
    <AppShell />
  </NConfigProvider>
</template>
