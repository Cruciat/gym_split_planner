<script setup lang="ts">
import Message from 'primevue/message'
import { onMounted } from 'vue'

import { useHealthStore } from '@/stores/health'

const store = useHealthStore()

onMounted(() => {
  void store.load()
})
</script>

<template>
  <main class="home">
    <h1>Gym Split Planner</h1>
    <p>Banca dati degli esercizi e creazione delle schede. In costruzione.</p>

    <Message v-if="store.failed" severity="error" data-testid="health-error">
      Il server non risponde.
    </Message>
    <Message
      v-else-if="store.health"
      :severity="store.health.status === 'ok' ? 'success' : 'warn'"
      data-testid="health-ok"
    >
      Server {{ store.health.status === 'ok' ? 'attivo' : 'con problemi' }} · versione
      {{ store.health.version }} · database {{ store.health.database }}
    </Message>
  </main>
</template>

<style scoped>
.home {
  max-width: 40rem;
  margin: 0 auto;
  padding: 2rem 1rem;
}
</style>
