import { createRouter, createWebHistory } from 'vue-router'

import HomePage from '@/pages/HomePage.vue'

// Percorsi in italiano come l'interfaccia (wireframe, § 2). Le altre pagine arrivano con M3 e M4.
export const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', name: 'home', component: HomePage }],
})
