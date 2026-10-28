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
    newExercise: 'Nuovo esercizio',
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
    edit: 'Modifica',
    moreActions: 'Altre azioni',
    deactivate: 'Disattiva',
    reactivate: 'Riattiva',
    delete: 'Elimina',
    deactivated: 'Esercizio disattivato: non verrà più proposto nelle schede.',
    reactivated: 'Esercizio riattivato.',
    deleted: (name: string): string => `«${name}» eliminato.`,
    deleteTitle: 'Eliminare l’esercizio?',
    deleteConfirm: (name: string): string =>
      `«${name}» non è usato in nessuna scheda. L’eliminazione non si può annullare.`,
    deleteAction: 'Elimina esercizio',
    inUseTitle: 'Esercizio usato nelle schede',
    inUse: (plans: string[]): string =>
      `«${plans.join('», «')}» ${plans.length === 1 ? 'lo usa' : 'lo usano'}: per non rompere ${
        plans.length === 1 ? 'la scheda' : 'le schede'
      } si può solo disattivare. Resterà dov’è, ma non verrà più proposto.`,
    inUseInactive: 'È già disattivato.',
    cancel: 'Annulla',
    close: 'Chiudi',
  },

  exerciseForm: {
    newTitle: 'Nuovo esercizio',
    editTitle: (name: string): string => `Modifica · ${name}`,
    general: 'Esercizio',
    name: 'Nome',
    family: 'Famiglia',
    rank: 'Rango (1 = preferito)',
    rankHelp: 'Ordine nella famiglia: 1 è il preferito dalla ricerca.',
    namePlaceholder: 'es. Chest press convergente',
    familyPlaceholder: 'Scegli la famiglia',
    equipmentPlaceholder: 'Scegli l’attrezzo',
    notesPlaceholder: 'Note della ricerca o personali',
    secondaryFamily: 'Famiglia secondaria',
    none: 'Nessuna',
    equipment: 'Attrezzo',
    equipmentDetail: 'Dettaglio',
    equipmentDetailPlaceholder: 'es. barra o corda',
    kind: 'Tipo',
    stretch: 'Allungamento',
    stretchNote: 'Nota',
    stretchNotePlaceholder: 'es. dipende dalla macchina',
    confidence: 'Confidenza',
    muscles: 'Muscoli',
    musclesHelp: 'Tocca un muscolo: vuoto → S (secondario) → P (primario) → vuoto.',
    muscleState: (name: string, level: Level | null): string =>
      `${name}: ${level === 'P' ? 'primario' : level === 'S' ? 'secondario' : 'non coinvolto'}`,
    tags: 'Etichette',
    addTag: 'Aggiungi etichetta',
    tagNote: 'Nota',
    tagNotePlaceholder: 'es. testa appoggiata',
    removeTag: (name: string): string => `Togli ${name}`,
    sources: 'Fonti',
    sourcesPlaceholder: 'Scegli le fonti',
    newSource: 'Nuova fonte…',
    notes: 'Note',
    save: 'Salva',
    cancel: 'Annulla',
    saved: 'Esercizio salvato.',
    created: 'Esercizio creato.',
    leaveTitle: 'Uscire senza salvare?',
    leaveText: 'Le modifiche a questo esercizio andranno perse.',
    leave: 'Esci senza salvare',
    stay: 'Resta',
    errors: {
      nameRequired: 'Serve un nome.',
      familyRequired: 'Scegli la famiglia principale.',
      equipmentRequired: 'Scegli l’attrezzo.',
      rank: 'Il rango è un numero da 1 in su.',
      primaryMuscle: 'Serve almeno un muscolo P.',
      secondaryFamily: 'La famiglia secondaria deve essere diversa dalla principale.',
      invalid: 'Valore non valido.',
      notSaved: 'L’esercizio non è stato salvato.',
    },
  },

  sourceForm: {
    title: 'Nuova fonte',
    sourceTitle: 'Titolo',
    titlePlaceholder: 'es. Schoenfeld 2010',
    kind: 'Tipo',
    kindPlaceholder: 'es. meta-analisi, studio EMG, opinione esperta',
    url: 'Indirizzo',
    reliability: 'Affidabilità',
    reliabilityPlaceholder: 'es. alta, media',
    create: 'Aggiungi fonte',
    cancel: 'Annulla',
    required: 'Campo obbligatorio.',
    urlInvalid: 'Deve iniziare con http:// o https://',
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
