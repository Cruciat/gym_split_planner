<script setup lang="ts">
import { NAlert, NH1, NP } from 'naive-ui'
import { onMounted } from 'vue'

import { useHealthStore } from '@/stores/health'

const store = useHealthStore()

onMounted(() => {
  void store.load()
})
</script>

<template>
  <main class="home">
    <NH1>Gym Split Planner</NH1>
    <NP>Banca dati degli esercizi e creazione delle schede. In costruzione.</NP>

    <NAlert v-if="store.failed" type="error" data-testid="health-error">
      Il server non risponde.
    </NAlert>
    <NAlert
      v-else-if="store.health"
      :type="store.health.status === 'ok' ? 'success' : 'warning'"
      data-testid="health-ok"
    >
      Server {{ store.health.status === 'ok' ? 'attivo' : 'con problemi' }} · versione
      {{ store.health.version }} · database {{ store.health.database }}
    </NAlert>
  </main>
</template>

<style scoped>
.home {
  max-width: 40rem;
  margin: 0 auto;
  padding: 2rem 1rem;
}
</style>
