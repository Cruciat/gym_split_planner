import { createRouter, createWebHistory, type RouteRecordRaw, type Router } from 'vue-router'

// Pagine caricate al primo accesso: il bundle iniziale resta piccolo anche sul telefono.
const PlansPage = () => import('@/pages/PlansPage.vue')
const CatalogPage = () => import('@/pages/CatalogPage.vue')
const ExerciseDetailPage = () => import('@/pages/ExerciseDetailPage.vue')
const SettingsPage = () => import('@/pages/SettingsPage.vue')
const NotFoundPage = () => import('@/pages/NotFoundPage.vue')

/**
 * Percorsi in italiano come l'interfaccia (wireframe, § 2). Le pagine delle schede
 * arrivano con M4: fino ad allora `/` e `/schede` mostrano un segnaposto.
 */
export const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: PlansPage },
  { path: '/schede', name: 'plans', component: PlansPage },
  { path: '/catalogo', name: 'catalog', component: CatalogPage },
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
