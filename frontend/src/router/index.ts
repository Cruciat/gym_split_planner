import {
  createRouter,
  createWebHistory,
  type RouteLocationRaw,
  type RouteRecordRaw,
  type Router,
} from 'vue-router'

import { api } from '@/api/client'

// Pagine caricate al primo accesso: il bundle iniziale resta piccolo anche sul telefono.
const PlansPage = () => import('@/pages/PlansPage.vue')
const PlanNewPage = () => import('@/pages/PlanNewPage.vue')
const PlanPage = () => import('@/pages/PlanPage.vue')
const PlanPreferencesPage = () => import('@/pages/PlanPreferencesPage.vue')
const CatalogPage = () => import('@/pages/CatalogPage.vue')
const ExerciseDetailPage = () => import('@/pages/ExerciseDetailPage.vue')
const ExerciseFormPage = () => import('@/pages/ExerciseFormPage.vue')
const FamiliesPage = () => import('@/pages/FamiliesPage.vue')
const TagsPage = () => import('@/pages/TagsPage.vue')
const MusclesPage = () => import('@/pages/MusclesPage.vue')
const SettingsPage = () => import('@/pages/SettingsPage.vue')
const NotFoundPage = () => import('@/pages/NotFoundPage.vue')

const planId = (route: { params: Record<string, unknown> }) => ({ id: Number(route.params.id) })

/** `/` apre la scheda attiva, o l'elenco se non ce n'è (wireframe, principio 1). */
async function openActivePlan(): Promise<RouteLocationRaw> {
  try {
    const { data } = await api.GET('/api/plans')
    const active = data?.find((plan) => plan.is_active)
    if (active !== undefined) return { name: 'plan', params: { id: String(active.id) } }
  } catch {
    // Senza risposta del server si mostra l'elenco, che sa dire cosa non va.
  }
  return { name: 'plans' }
}

/** Percorsi in italiano come l'interfaccia (wireframe, § 2). */
export const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: PlansPage, beforeEnter: openActivePlan },
  { path: '/schede', name: 'plans', component: PlansPage },
  { path: '/schede/nuova', name: 'plan-new', component: PlanNewPage },
  { path: '/schede/:id(\\d+)', name: 'plan', component: PlanPage, props: planId },
  {
    path: '/schede/:id(\\d+)/preferenze',
    name: 'plan-preferences',
    component: PlanPreferencesPage,
    props: planId,
  },
  { path: '/catalogo', name: 'catalog', component: CatalogPage },
  { path: '/catalogo/famiglie', name: 'families', component: FamiliesPage },
  { path: '/catalogo/etichette', name: 'tags', component: TagsPage },
  { path: '/catalogo/muscoli', name: 'muscles', component: MusclesPage },
  { path: '/catalogo/esercizi/nuovo', name: 'exercise-new', component: ExerciseFormPage },
  {
    path: '/catalogo/esercizi/:id(\\d+)/modifica',
    name: 'exercise-edit',
    component: ExerciseFormPage,
    props: (route) => ({ id: Number(route.params.id) }),
  },
  {
    path: '/catalogo/esercizi/:id(\\d+)',
    name: 'exercise',
    component: ExerciseDetailPage,
    props: (route) => ({ id: Number(route.params.id) }),
  },
  { path: '/impostazioni', name: 'settings', component: SettingsPage },
  { path: '/:path(.*)*', name: 'not-found', component: NotFoundPage },
]

export function makeRouter(history = createWebHistory()): Router {
  return createRouter({ history, routes })
}

export const router = makeRouter()
