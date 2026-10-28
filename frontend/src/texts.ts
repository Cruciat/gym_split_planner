/**
 * Testi dell'interfaccia, tutti in un posto (ADR 0013): anche con una lingua sola,
 * niente testi sparsi nei componenti.
 */

import type { Confidence, Kind, Level, Priority, Stretch } from '@/api/client'

const plural = (n: number, one: string, many: string): string =>
  `${String(n)} ${n === 1 ? one : many}`

export const texts = {
  appName: 'Gym Split Planner',

  nav: {
    plans: 'Schede',
    catalog: 'Catalogo',
    settings: 'Impostazioni',
    label: 'Navigazione principale',
  },

  common: {
    retry: 'Riprova',
    loadFailed: 'Impossibile caricare i dati dal server.',
    unexpectedError: 'Errore inatteso dal server',
    none: '—',
  },

  plans: {
    title: 'Schede',
    comingSoon: 'Creazione e modifica delle schede arrivano con la prossima tappa (M4).',
    goToCatalog: 'Intanto puoi consultare il catalogo',
  },

  settings: {
    title: 'Impostazioni',
    comingSoon: 'Impostazioni, esportazione e importazione arrivano con le prossime tappe.',
    serverDown: 'Il server non risponde.',
    server: (ok: boolean, version: string, database: string): string =>
      `Server ${ok ? 'attivo' : 'con problemi'} · versione ${version} · database ${database}`,
  },

  notFound: {
    title: 'Pagina non trovata',
    back: 'Torna alle schede',
  },

  catalog: {
    title: 'Catalogo',
    tabs: { exercises: 'Esercizi' },
    count: (shown: number, total: number): string =>
      shown === total
        ? plural(total, 'esercizio', 'esercizi')
        : `${String(shown)} di ${plural(total, 'esercizio', 'esercizi')}`,
    empty: 'Nessun esercizio corrisponde ai filtri.',
    columns: {
      name: 'Nome',
      group: 'Gruppo',
      family: 'Famiglia',
      equipment: 'Attrezzo',
      confidence: 'Confidenza',
    },
    inactive: 'disattivato',
  },

  filters: {
    title: 'Filtri',
    open: (active: number): string => (active > 0 ? `Filtri (${String(active)})` : 'Filtri'),
    search: 'Cerca per nome',
    group: 'Gruppo',
    muscle: 'Muscolo allenato',
    level: { P: 'Solo come P', S: 'Come P o S' } satisfies Record<Level, string>,
    family: 'Famiglia',
    equipment: 'Attrezzo',
    tag: 'Etichetta',
    tagMode: { with: 'Con', without: 'Senza' },
    confidence: 'Confidenza',
    showInactive: 'Mostra disattivati',
    reset: 'Azzera filtri',
    any: 'Tutti',
    close: 'Mostra risultati',
  },

  exercise: {
    notFound: 'Esercizio non trovato.',
    backToCatalog: 'Torna al catalogo',
    active: 'Attivo',
    inactive: 'Disattivato',
    muscles: 'Muscoli',
    primary: 'P',
    secondary: 'S',
    primaryLong: 'Primario',
    secondaryLong: 'Secondario',
    stretch: 'Allungamento',
    confidence: 'Confidenza',
    equipment: 'Attrezzo',
    families: 'Famiglie',
    primaryFamily: 'principale',
    secondaryFamily: 'secondaria',
    rank: (rank: number): string => `${String(rank)}° nella famiglia`,
    tags: 'Etichette',
    variants: 'Varianti',
    noVariants: 'Nessun altro esercizio attivo nelle sue famiglie.',
    sources: 'Fonti',
    notes: 'Note',
  },

  labels: {
    kind: { compound: 'Multiarticolare', isolation: 'Isolamento' } satisfies Record<Kind, string>,
    stretch: { high: 'Alto', medium: 'Medio', low: 'Basso' } satisfies Record<Stretch, string>,
    confidence: {
      solid: 'Solido',
      limited: 'Limitato',
      opinion: 'Opinione',
    } satisfies Record<Confidence, string>,
    priority: {
      priority: 'Prioritario',
      standard: 'Non prioritario',
      none: 'Nessun obiettivo',
    } satisfies Record<Priority, string>,
  },

  symbols: {
    warning: 'Avviso',
    ban: 'Divieto',
    info: 'Informazione',
    star: 'Stella',
    heart: 'Cuore',
    zap: 'Fulmine',
    flag: 'Bandiera',
    'eye-off': 'Occhio barrato',
  },
} as const
