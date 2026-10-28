<script setup lang="ts">
import { NAlert, NH1, NP } from 'naive-ui'
import { onMounted } from 'vue'

import { useHealthStore } from '@/stores/health'
import { texts } from '@/texts'

/** Impostazioni (wireframe, § 5): per ora solo versione e stato del server. */
const store = useHealthStore()
const t = texts.settings

onMounted(() => {
  void store.load()
})
</script>

<template>
  <main class="page">
    <NH1>{{ t.title }}</NH1>
    <NP>{{ t.comingSoon }}</NP>

    <NAlert v-if="store.failed" type="error" data-testid="health-error">
      {{ t.serverDown }}
    </NAlert>
    <NAlert
      v-else-if="store.health"
      :type="store.health.status === 'ok' ? 'success' : 'warning'"
      data-testid="health-ok"
    >
      {{ t.server(store.health.status === 'ok', store.health.version, store.health.database) }}
    </NAlert>
  </main>
</template>
