/**
 * Catalogo ridotto per i test, con la stessa forma di `GET /api/catalog`.
 * Nomi e codici presi dai dati iniziali, per leggere i test senza tradurre.
 */

import type {
  Catalog,
  ExerciseDetail,
  ExerciseSummary,
  Plan,
  PlanSettings,
  PlanSummary,
  Split,
} from '@/api/client'

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

/** Due split predefiniti, con giorni e slot ridotti. */
export function makeSplits(): Split[] {
  const slot = {
    family: { id: 1, code: 'press-incline', name: 'Spinta inclinata' },
    sets: 3,
    rep_min: 6,
    rep_max: 12,
    is_optional: false,
    weekly_weight: 1,
    note: null,
  }
  return [
    {
      id: 1,
      code: 'ppl-3',
      name: 'Push/Pull/Legs, 3 giorni',
      description: 'Ogni muscolo una volta a settimana.',
      days_per_week: 3,
      days: [
        { name: 'Push', times_per_week: 1, slots: [slot] },
        { name: 'Pull', times_per_week: 1, slots: [] },
        { name: 'Legs', times_per_week: 1, slots: [] },
      ],
    },
    {
      id: 2,
      code: 'ul-4',
      name: 'Upper/Lower, 4 giorni',
      description: null,
      days_per_week: 4,
      days: [
        { name: 'Upper', times_per_week: 2, slots: [slot] },
        { name: 'Lower', times_per_week: 2, slots: [] },
      ],
    },
  ]
}

export function makePlanSummaries(): PlanSummary[] {
  return [
    {
      id: 1,
      name: 'PPL autunno',
      revision: 4,
      split_name: 'Push/Pull/Legs, 3 giorni',
      days_per_week: 3,
      is_active: true,
      updated_at: '2026-10-28T10:00:00Z',
    },
    {
      id: 2,
      name: 'Prova vuota',
      revision: 1,
      split_name: null,
      days_per_week: 1,
      is_active: false,
      updated_at: '2026-10-20T10:00:00Z',
    },
  ]
}

/** Una scheda completa con un giorno e uno slot, senza avvisi. */
export function makePlan(overrides: Partial<Plan> = {}): Plan {
  return {
    id: 1,
    name: 'PPL autunno',
    revision: 4,
    is_active: true,
    split: { id: 1, code: 'ppl-3', name: 'Push/Pull/Legs, 3 giorni' },
    created_at: '2026-10-20T10:00:00Z',
    updated_at: '2026-10-28T10:00:00Z',
    preferences: {
      version: 2,
      equipment_order: ['machine', 'cable', 'free-weight'],
      max_session_minutes: 75,
      overrides: { muscles: {}, tags: {} },
    },
    days: [
      {
        id: 10,
        name: 'Push',
        position: 1,
        times_per_week: 1,
        stretches: [],
        slots: [
          {
            id: 100,
            position: 1,
            family: { id: 1, code: 'press-incline', name: 'Spinta inclinata' },
            exercise: {
              id: 1,
              code: 'chest-press-incline',
              name: 'Chest press inclinata',
              equipment: 'machine',
              kind: 'compound',
              is_active: true,
              badges: [],
            },
            second_exercise: null,
            sets: 3,
            rep_min: 6,
            rep_max: 12,
            is_optional: false,
            weekly_weight: 1,
            locked: false,
            note: null,
            rest_seconds: 150,
            rir: '0-2',
            last_set_to_failure: true,
          },
        ],
      },
    ],
    analysis: { volumes: [], sessions: [], warnings: [] },
    ...overrides,
  }
}

/** Vista delle preferenze della scheda 1, con il petto medio personalizzato. */
export function makePlanSettings(): PlanSettings {
  const catalog = makeCatalog()
  return {
    name: 'PPL autunno',
    revision: 4,
    equipment_order: ['machine', 'cable', 'free-weight'],
    max_session_minutes: 75,
    muscles: catalog.muscles.map((m) => {
      const values = { priority: m.priority, weekly_min: m.weekly_min, weekly_max: m.weekly_max }
      const custom = m.code === 'chest-mid'
      return {
        muscle_id: m.id,
        code: m.code,
        name: m.name,
        short_name: m.short_name,
        group_code: m.muscle_group_id === 1 ? 'chest' : 'triceps',
        catalog: values,
        override: { priority: null, weekly_min: null, weekly_max: custom ? 14 : null },
        effective: custom ? { ...values, weekly_max: 14 } : values,
      }
    }),
    tags: catalog.tags.map((t) => ({
      tag_id: t.id,
      code: t.code,
      name: t.name,
      symbol: t.symbol,
      color: t.color,
      catalog: { effect: t.effect, points: t.points },
      override: { effect: null, points: null },
      effective: { effect: t.effect, points: t.points },
    })),
  }
}

/** Risposta JSON per sostituire `fetch` nei test. */
export function jsonResponse(body: unknown, status = 200): Response {
  const contentType = status >= 400 ? 'application/problem+json' : 'application/json'
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': contentType } })
}
