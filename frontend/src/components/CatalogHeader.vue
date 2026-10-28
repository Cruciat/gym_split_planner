<script setup lang="ts">
import { NH1 } from 'naive-ui'
import { RouterLink, useRoute } from 'vue-router'

import { texts } from '@/texts'

/** Titolo e schede del catalogo (wireframe, § 4.1), con le azioni della sezione a destra. */
const route = useRoute()
const t = texts.catalog

const tabs = [
  { to: '/catalogo', label: t.tabs.exercises },
  { to: '/catalogo/famiglie', label: t.tabs.families },
  { to: '/catalogo/etichette', label: t.tabs.tags },
  { to: '/catalogo/muscoli', label: t.tabs.muscles },
] as const

/** Gli esercizi sono la sezione di partenza: comprendono anche dettaglio e form. */
function isActive(to: string): boolean {
  if (to !== '/catalogo') return route.path === to
  return !tabs.some((tab) => tab.to !== '/catalogo' && route.path === tab.to)
}
</script>

<template>
  <header class="header">
    <NH1>{{ t.title }}</NH1>
    <nav class="tabs" :aria-label="t.tabs.label">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.to"
        :to="tab.to"
        class="tab"
        :class="{ active: isActive(tab.to) }"
        :aria-current="isActive(tab.to) ? 'page' : undefined"
      >
        {{ tab.label }}
      </RouterLink>
    </nav>
    <div class="actions"><slot /></div>
  </header>
</template>

<style scoped>
.header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem 1.5rem;
}

.header :deep(h1) {
  margin: 0;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.tab {
  padding: 0.3rem 0.7rem;
  border-radius: 6px;
  color: var(--muted-color);
  text-decoration: none;
}

.tab:hover {
  color: inherit;
}

.tab.active {
  color: var(--primary-color);
  background: var(--hover-color);
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 0.5rem;
  margin-left: auto;
  align-self: center;
}

@media (max-width: 767px) {
  .tabs {
    order: 3;
    width: 100%;
  }
}
</style>
