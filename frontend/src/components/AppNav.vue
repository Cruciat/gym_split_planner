<script setup lang="ts">
import { ClipboardList, Dumbbell, Settings } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'

import { texts } from '@/texts'

/**
 * Navigazione principale (wireframe, § 2): barra in alto su schermo largo, in basso
 * sotto i 768 px. La sezione attiva si riconosce dal percorso, anche nelle sottopagine.
 */
const sections = [
  { to: '/schede', label: texts.nav.plans, icon: ClipboardList, match: ['/', '/schede'] },
  { to: '/catalogo', label: texts.nav.catalog, icon: Dumbbell, match: ['/catalogo'] },
  { to: '/impostazioni', label: texts.nav.settings, icon: Settings, match: ['/impostazioni'] },
] as const

function isActive(path: string, match: readonly string[]): boolean {
  return match.some((prefix) =>
    prefix === '/' ? path === '/' : path === prefix || path.startsWith(`${prefix}/`),
  )
}
</script>

<template>
  <nav class="app-nav" :aria-label="texts.nav.label">
    <!-- Link "custom": il marchio non deve risultare la pagina corrente (aria-current). -->
    <RouterLink v-slot="{ href, navigate }" to="/" custom>
      <a :href="href" class="brand" @click="navigate">{{ texts.appName }}</a>
    </RouterLink>
    <ul>
      <li v-for="section in sections" :key="section.to">
        <RouterLink
          :to="section.to"
          class="link"
          :class="{ active: isActive($route.path, section.match) }"
          :aria-current="isActive($route.path, section.match) ? 'page' : undefined"
        >
          <component :is="section.icon" :size="20" aria-hidden="true" />
          <span>{{ section.label }}</span>
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.app-nav {
  display: flex;
  align-items: center;
  gap: 2rem;
  height: var(--nav-height);
  padding: 0 1.25rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--surface-color);
}

.brand {
  font-weight: 600;
  color: inherit;
  text-decoration: none;
  white-space: nowrap;
}

ul {
  display: flex;
  gap: 0.25rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.link {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.75rem;
  border-radius: 6px;
  color: var(--muted-color);
  text-decoration: none;
}

.link:hover {
  color: inherit;
  background: var(--hover-color);
}

.link.active {
  color: var(--primary-color);
  font-weight: 600;
}

@media (max-width: 767px) {
  .app-nav {
    position: fixed;
    inset: auto 0 0;
    z-index: 10;
    padding: 0 0 env(safe-area-inset-bottom);
    border-top: 1px solid var(--border-color);
    border-bottom: 0;
  }

  .brand {
    display: none;
  }

  ul {
    flex: 1;
    gap: 0;
  }

  li {
    flex: 1;
  }

  .link {
    flex-direction: column;
    gap: 0.15rem;
    padding: 0.4rem 0;
    font-size: 0.75rem;
    border-radius: 0;
  }
}
</style>
