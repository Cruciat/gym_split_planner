/**
 * Catalogo ridotto per i test, con la stessa forma di `GET /api/catalog`.
 * Nomi e codici presi dai dati iniziali, per leggere i test senza tradurre.
 */

import type { Catalog, ExerciseDetail, ExerciseSummary } from '@/api/client'

const exercise = (
  overrides: Partial<ExerciseSummary> & Pick<ExerciseSummary, 'id' | 'code' | 'name'>,
): ExerciseSummary => ({
  primary_family_id: 1,
  secondary_family_id: null,
  family_rank: 1,
  equipment_id: 1,
  equipment_detail: null,
  kind: 'compound',
  stretch: 'medium',
  confidence: 'solid',
  is_active: true,
  muscles: [],
  tags: [],
  ...overrides,
})

export function makeCatalog(): Catalog {
  return {
    muscle_groups: [
      { id: 1, code: 'chest', name: 'Petto', sort_order: 1 },
      { id: 2, code: 'triceps', name: 'Tricipiti', sort_order: 2 },
    ],
    muscles: [
      {
        id: 1,
        code: 'chest-upper',
        name: 'Petto alto (fascio clavicolare)',
        short_name: 'Petto alto',
        muscle_group_id: 1,
        priority: 'priority',
        weekly_min: 10,
        weekly_max: 18,
        notes: null,
        sort_order: 1,
      },
      {
        id: 2,
        code: 'chest-mid',
        name: 'Petto medio (fascio sternale)',
        short_name: 'Petto medio',
        muscle_group_id: 1,
        priority: 'priority',
        weekly_min: 10,
        weekly_max: 18,
        notes: null,
        sort_order: 2,
      },
      {
        id: 3,
        code: 'triceps-long',
        name: 'Tricipite, capo lungo',
        short_name: 'Capo lungo',
        muscle_group_id: 2,
        priority: 'priority',
        weekly_min: 10,
        weekly_max: 18,
        notes: null,
        sort_order: 3,
      },
    ],
    equipment: [
      { id: 1, code: 'machine', name: 'Macchina', sort_order: 1 },
      { id: 2, code: 'cable', name: 'Cavi', sort_order: 2 },
      { id: 3, code: 'free-weight', name: 'Pesi liberi', sort_order: 3 },
    ],
    families: [
      {
        id: 1,
        code: 'press-incline',
        name: 'Spinta inclinata',
        description: null,
        muscle_group_id: 1,
        sort_order: 1,
      },
      {
        id: 2,
        code: 'press-horizontal',
        name: 'Spinta orizzontale',
        description: null,
        muscle_group_id: 1,
        sort_order: 2,
      },
      {
        id: 3,
        code: 'triceps-overhead',
        name: 'Estensione sopra la testa',
        description: null,
        muscle_group_id: 2,
        sort_order: 3,
      },
    ],
    tags: [
      {
        id: 1,
        code: 'neck-tip',
        name: 'Collo: accorgimento',
        description: null,
        symbol: 'info',
        color: 'info',
        effect: 'none',
        points: 0,
        show_badge: true,
        sort_order: 1,
      },
      {
        id: 2,
        code: 'neck-caution',
        name: 'Collo: attenzione',
        description: null,
        symbol: 'warning',
        color: 'warning',
        effect: 'penalty',
        points: 3,
        show_badge: true,
        sort_order: 2,
      },
    ],
    exercises: [
      exercise({
        id: 1,
        code: 'chest-press-incline',
        name: 'Chest press inclinata',
        primary_family_id: 1,
        muscles: [
          { muscle_id: 1, level: 'P' },
          { muscle_id: 2, level: 'S' },
        ],
        confidence: 'limited',
      }),
      exercise({
        id: 2,
        code: 'incline-bench-press',
        name: 'Panca inclinata a 30°',
        primary_family_id: 1,
        family_rank: 2,
        equipment_id: 3,
        muscles: [
          { muscle_id: 1, level: 'P' },
          { muscle_id: 2, level: 'S' },
        ],
        tags: [{ tag_id: 2, note: null }],
      }),
      exercise({
        id: 3,
        code: 'chest-press',
        name: 'Chest press seduta',
        primary_family_id: 2,
        secondary_family_id: 1,
        muscles: [
          { muscle_id: 1, level: 'S' },
          { muscle_id: 2, level: 'P' },
        ],
      }),
      exercise({
        id: 4,
        code: 'cable-overhead-extension',
        name: 'Estensione sopra la testa ai cavi',
        primary_family_id: 3,
        equipment_id: 2,
        kind: 'isolation',
        stretch: 'high',
        muscles: [{ muscle_id: 3, level: 'P' }],
        tags: [{ tag_id: 2, note: 'Schiena appoggiata' }],
      }),
      exercise({
        id: 5,
        code: 'katana-extension',
        name: 'Estensione katana',
        primary_family_id: 3,
        family_rank: 2,
        equipment_id: 2,
        kind: 'isolation',
        confidence: 'opinion',
        is_active: false,
        muscles: [{ muscle_id: 3, level: 'P' }],
      }),
    ],
    sources: [
      {
        id: 1,
        code: 'src-01',
        title: 'Haugen et al. 2023',
        kind: 'Meta-analisi',
        url: 'https://example.org/haugen',
        reliability: 'Alta',
        used_for: 'Macchine contro pesi liberi',
      },
    ],
    stretches: [],
    daily_routine: [],
  }
}

export function makeDetail(): ExerciseDetail {
  return {
    id: 4,
    code: 'cable-overhead-extension',
    name: 'Estensione sopra la testa ai cavi',
    primary_family_id: 3,
    secondary_family_id: null,
    family_rank: 1,
    equipment_id: 2,
    equipment_detail: 'barra o corda',
    kind: 'isolation',
    stretch: 'high',
    stretch_note: null,
    confidence: 'solid',
    notes: 'Gomito sopra la testa.',
    is_active: true,
    created_at: '2026-10-28T09:15:00Z',
    updated_at: '2026-10-28T09:15:00Z',
    muscles: [{ muscle_id: 3, level: 'P', note: 'in allungamento' }],
    tags: [{ tag_id: 2, note: 'Schiena appoggiata' }],
    sources: [
      {
        id: 1,
        code: 'src-01',
        title: 'Haugen et al. 2023',
        kind: 'Meta-analisi',
        url: 'https://example.org/haugen',
        reliability: 'Alta',
        used_for: null,
      },
    ],
    variants: [
      {
        id: 6,
        code: 'machine-overhead-extension',
        name: 'Estensione sopra la testa alla macchina',
        family_id: 3,
        equipment_id: 1,
        family_rank: 2,
        tags: [],
      },
    ],
  }
}

/** Risposta JSON per sostituire `fetch` nei test. */
export function jsonResponse(body: unknown, status = 200): Response {
  const contentType = status >= 400 ? 'application/problem+json' : 'application/json'
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': contentType } })
}
