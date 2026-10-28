<script setup lang="ts">
import { darkTheme, dateItIT, itIT, NConfigProvider, NGlobalStyle, useOsTheme } from 'naive-ui'
import { computed } from 'vue'
import { RouterView } from 'vue-router'

// Tema chiaro o scuro secondo il sistema (wireframe, § 7); testi dei componenti in italiano.
const osTheme = useOsTheme()
const theme = computed(() => (osTheme.value === 'dark' ? darkTheme : null))
</script>

<template>
  <NConfigProvider :theme="theme" :locale="itIT" :date-locale="dateItIT">
    <NGlobalStyle />
    <RouterView />
  </NConfigProvider>
</template>
