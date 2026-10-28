<script setup lang="ts">
import { NH1, NP } from 'naive-ui'
import { RouterLink } from 'vue-router'

import { texts } from '@/texts'

/** Segnaposto della sezione Schede fino a M4 (wireframe, § 3). */
const t = texts.plans
</script>

<template>
  <main class="page">
    <NH1>{{ t.title }}</NH1>
    <NP>{{ t.comingSoon }}</NP>
    <NP>
      <RouterLink to="/catalogo" class="text-link">{{ t.goToCatalog }}</RouterLink>
    </NP>
  </main>
</template>
