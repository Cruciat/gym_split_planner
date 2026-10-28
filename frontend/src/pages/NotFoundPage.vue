<script setup lang="ts">
import { NH1 } from 'naive-ui'
import { RouterLink } from 'vue-router'

import { texts } from '@/texts'
</script>

<template>
  <main class="page">
    <NH1>{{ texts.notFound.title }}</NH1>
    <RouterLink to="/schede" class="text-link">{{ texts.notFound.back }}</RouterLink>
  </main>
</template>
