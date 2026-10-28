/**
 * Testi dell'interfaccia, tutti in un posto (ADR 0013): anche con una lingua sola,
 * niente testi sparsi nei componenti.
 */

import type { Confidence, Kind, Level, Priority, Stretch } from '@/api/client'

const plural = (n: number, one: string, many: string): string =>
  `${String(n)} ${n === 1 ? one : many}`

/** Numero all'italiana, con al più due decimali: 12,5 serie. */
export const formatNumber = (n: number): string =>
  n.toLocaleString('it-IT', { maximumFractionDigits: 2 })

const quoted = (names: string[]): string => `«${names.join('», «')}»`

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
    add: 'Nuova scheda',
    empty: 'Nessuna scheda.',
    createFirst: 'Crea la prima scheda',
    emptySplit: 'Scheda vuota',
    days: (n: number): string => plural(n, 'giorno', 'giorni'),
    active: 'attiva',
    modified: (date: string): string => `modificata il ${date}`,
    actions: (name: string): string => `Azioni per ${name}`,
    open: 'Apri',
    rename: 'Rinomina',
    duplicate: 'Duplica',
    activate: 'Rendi attiva',
    delete: 'Elimina',
    renameTitle: 'Rinomina la scheda',
    name: 'Nome',
    save: 'Salva',
    cancel: 'Annulla',
    nameRequired: 'Serve un nome.',
    renamed: 'Scheda rinominata.',
    duplicated: (name: string): string => `Creata «${name}».`,
    activated: (name: string): string => `«${name}» è la scheda attiva.`,
    deleteTitle: 'Eliminare la scheda?',
    deleteConfirm: (name: string): string =>
      `«${name}» verrà eliminata con tutti i giorni e gli esercizi. L’eliminazione non si può annullare.`,
    deleteAction: 'Elimina scheda',
    deleted: (name: string): string => `«${name}» eliminata.`,
    changedElsewhere: 'La scheda è cambiata su un altro dispositivo: ho ricaricato i dati.',
  },

  planNew: {
    title: 'Nuova scheda',
    step: (n: number, title: string): string => `Passo ${String(n)} di 3 — ${title}`,
    steps: ['Da dove parti?', 'Preferenze', 'Nome'],
    days: (n: number): string => plural(n, 'giorno', 'giorni'),
    dayName: (name: string, times: number): string =>
      times > 1 ? `${name} ×${String(times)}` : name,
    empty: 'Scheda vuota',
    emptyHelp: 'Crei tu i giorni e gli esercizi.',
    overrides: 'Muscoli ed etichette',
    asCatalog: 'come nel catalogo',
    customized: (n: number): string =>
      n === 1 ? '1 personalizzazione' : `${String(n)} personalizzazioni`,
    customize: 'Personalizza…',
    hideCustomize: 'Nascondi',
    name: 'Nome',
    nameHelp: 'Puoi cambiarlo quando vuoi dall’elenco delle schede.',
    back: 'Indietro',
    next: 'Avanti',
    create: 'Crea scheda',
    created: (name: string): string => `«${name}» creata.`,
    cancel: 'Annulla',
  },

  preferences: {
    title: (name: string): string => `Preferenze di «${name}»`,
    backToPlan: 'Torna alla scheda',
    notFound: 'Scheda non trovata.',
    backToPlans: 'Torna alle schede',
    equipment: 'Attrezzi, dal preferito',
    equipmentHelp: 'A parità di efficacia la scelta automatica preferisce gli attrezzi in cima.',
    moveUp: (name: string): string => `Sposta ${name} più in alto`,
    moveDown: (name: string): string => `Sposta ${name} più in basso`,
    maxMinutes: 'Durata massima della seduta',
    minutes: 'min',
    noLimit: 'Senza limite',
    noLimitHelp: 'Lascia vuoto per non avere avvisi sulla durata.',
    muscles: 'Muscoli',
    tags: 'Etichette',
    onlyCustomized: 'Solo personalizzati',
    muscle: 'Muscolo',
    priority: 'Priorità',
    min: 'Min',
    max: 'Max',
    tag: 'Etichetta',
    effect: 'Effetto',
    points: 'Punti',
    customizedMark: 'personalizzato',
    catalogBand: (min: number | null, max: number | null, priority: string): string =>
      min === null || max === null
        ? `Catalogo: ${priority}`
        : `Catalogo: ${priority}, ${String(min)}–${String(max)}`,
    catalogTag: (effect: string, points: number | null): string =>
      points === null ? `Catalogo: ${effect}` : `Catalogo: ${effect} ${String(points)}`,
    reset: 'Catalogo',
    resetLabel: (name: string): string => `Riporta ${name} ai valori del catalogo`,
    noneCustomized: 'Nessuna personalizzazione: tutto come nel catalogo.',
    regenerateNote:
      'Le modifiche aggiornano subito volumi e avvisi. Per applicarle anche agli esercizi già scelti serve la rigenerazione, dall’editor della scheda.',
    invalid: 'Valore non valido.',
    leaveTitle: 'Uscire senza salvare?',
    leaveText: 'L’ultima modifica non è stata salvata: correggi i campi segnati o esci e la perdi.',
    leave: 'Esci senza salvare',
    stay: 'Resta',
  },

  plan: {
    notFound: 'Scheda non trovata.',
    backToPlans: 'Torna alle schede',
  },

  editor: {
    reloaded: 'La scheda è stata modificata da un altro dispositivo ed è stata ricaricata.',
    retry: 'Riprova',
    preferences: 'Preferenze',
    more: 'Altre azioni',
    rename: 'Rinomina',
    renameTitle: 'Rinomina la scheda',
    renameLabel: (name: string): string => `Rinomina ${name}`,
    name: 'Nome',
    save: 'Salva',
    cancel: 'Annulla',
    nameRequired: 'Serve un nome.',
    days: 'Giorni della scheda',
    addDay: 'Giorno',
    addDayLabel: 'Aggiungi un giorno',
    addDayTitle: 'Nuovo giorno',
    editDayTitle: (name: string): string => `Modifica «${name}»`,
    dayName: 'Nome',
    dayNamePlaceholder: 'es. Push',
    times: 'Volte a settimana',
    add: 'Aggiungi',
    emptyPlan: 'Questa scheda non ha ancora giorni.',
    addFirstDay: 'Aggiungi il primo giorno',
    dayTab: (name: string, times: number): string =>
      times > 1 ? `${name} ×${String(times)}` : name,
    timesPerWeek: (n: number): string =>
      n === 1 ? '1 volta a settimana' : `${String(n)} volte a settimana`,
    minutes: (values: number[]): string =>
      `${values.map((v) => `~${String(Math.round(v))}`).join(' / ')} min`,
    dayActions: (name: string): string => `Azioni per il giorno ${name}`,
    dayMenu: {
      edit: 'Rinomina e volte a settimana',
      moveBefore: 'Sposta prima',
      moveAfter: 'Sposta dopo',
      reorder: 'Riordina esercizi',
      delete: 'Elimina giorno',
    },
    endReorder: 'Fine riordino',
    reorderHelp: 'Trascina gli esercizi dalla maniglia, o usa le frecce.',
    removeVariantsTitle: 'Togliere le varianti della seconda seduta?',
    removeVariants: (day: string, pairs: string[]): string =>
      `Con una sola seduta a settimana «${day}» non ha più una seconda seduta: ${
        pairs.length === 1 ? 'verrà tolta la variante' : 'verranno tolte le varianti'
      } ${pairs.join('; ')}.`,
    variantPair: (main: string, second: string): string => `«${second}» al posto di «${main}»`,
    removeVariantsAction: 'Cambia e togli le varianti',
    deleteDayTitle: 'Eliminare il giorno?',
    deleteDayConfirm: (name: string, slots: number): string =>
      `«${name}» verrà eliminato con ${plural(slots, 'esercizio', 'esercizi')}. L’eliminazione non si può annullare.`,
    deleteDayAction: 'Elimina giorno',
    emptyDay: 'Nessun esercizio in questo giorno.',
    addSlot: 'Aggiungi esercizio',
    addSlotTitle: 'Aggiungi un esercizio',
    family: 'Famiglia',
    familyPlaceholder: 'Scegli la famiglia',
    exercise: 'Esercizio',
    bestCandidate: 'Il migliore della famiglia (scelta automatica)',
    changeFamilyTitle: 'Cambia famiglia',
    changeFamilyHelp:
      'Serie e ripetizioni restano; l’esercizio diventa il migliore della nuova famiglia.',
    change: 'Cambia',
    noteTitle: 'Nota',
    notePlaceholder: 'es. presa stretta, schiena appoggiata',
    slotActions: (name: string): string => `Azioni per ${name}`,
    slotMenu: {
      changeFamily: 'Cambia famiglia',
      optionalOn: 'Segna come facoltativo',
      optionalOff: 'Non più facoltativo',
      alternateOn: 'A settimane alterne',
      alternateOff: 'Ogni settimana',
      note: 'Nota',
      delete: 'Elimina',
    },
    optional: 'facoltativo',
    alternate: 'settimane alterne',
    secondSession: (name: string): string => `2ª seduta: ${name}`,
    emptySlot: 'nessun esercizio disponibile',
    emptySlotExcluded: (tags: string[]): string => `tutti esclusi da ${quoted(tags)}`,
    lock: (name: string): string => `Blocca ${name}`,
    unlock: (name: string): string => `Sblocca ${name}`,
    lockedHelp: 'Bloccato: la rigenerazione non lo cambia.',
    sets: 'Serie',
    repMin: 'Ripetizioni minime',
    repMax: 'Ripetizioni massime',
    setsOf: (name: string): string => `Serie di ${name}`,
    repMinOf: (name: string): string => `Ripetizioni minime di ${name}`,
    repMaxOf: (name: string): string => `Ripetizioni massime di ${name}`,
    deleteSlotTitle: 'Eliminare l’esercizio?',
    deleteSlotConfirm: (name: string): string => `«${name}» verrà tolto da questo giorno.`,
    deleteSlotAction: 'Elimina esercizio',
    stretching: 'Stretching',
    moveUp: (name: string): string => `Sposta ${name} più in alto`,
    moveDown: (name: string): string => `Sposta ${name} più in basso`,
    drag: (name: string): string => `Trascina ${name}`,
    leaveTitle: 'Uscire con modifiche non salvate?',
    leaveText:
      'La connessione si è interrotta: alcune modifiche non sono state inviate e andranno perse.',
    leave: 'Esci comunque',
    stay: 'Resta',
    close: 'Chiudi',
  },

  volume: {
    title: 'Volume settimanale',
    filter: 'Muscoli da mostrare',
    filters: { priority: 'Prioritari', target: 'Con obiettivo', all: 'Tutti' },
    below: 'sotto',
    above: 'sopra',
    customized: 'personalizzato nella scheda',
    noTarget: (n: number): string => `Senza obiettivo (${String(n)})`,
    band: (min: number, max: number): string => `${formatNumber(min)}–${formatNumber(max)}`,
    row: (name: string, volume: number, min: number | null, max: number | null): string =>
      min === null || max === null
        ? `${name}: ${formatNumber(volume)} serie`
        : `${name}: ${formatNumber(volume)} serie, fascia ${formatNumber(min)}–${formatNumber(max)}`,
    warnings: (n: number): string => `Avvisi (${String(n)})`,
    noWarnings: 'Nessun avviso.',
    summary: (below: number, above: number): string =>
      `↓${String(below)} sotto · ↑${String(above)} sopra`,
    summaryWarnings: (n: number): string => (n === 0 ? '' : ` · ${plural(n, 'avviso', 'avvisi')}`),
    open: 'Apri il pannello del volume',
    close: 'Chiudi',
    warning: {
      below: (muscle: string, volume: number, min: number, max: number): string =>
        `${muscle} sotto fascia (${formatNumber(volume)} / ${formatNumber(min)}–${formatNumber(max)})`,
      above: (muscle: string, volume: number, min: number, max: number): string =>
        `${muscle} sopra fascia (${formatNumber(volume)} / ${formatNumber(min)}–${formatNumber(max)})`,
      cap: (day: string, muscle: string, volume: number): string =>
        `${day}: ${muscle} a ${formatNumber(volume)} serie, oltre il tetto per seduta`,
      long: (day: string, minutes: number, max: number | null): string =>
        max === null
          ? `${day}: seduta di ~${String(Math.round(minutes))} min`
          : `${day}: seduta di ~${String(Math.round(minutes))} min, oltre i ${String(max)} previsti`,
      empty: (day: string, position: number, family: string): string =>
        `${day}, esercizio ${String(position)}: nessun esercizio per «${family}»`,
      secondSession: (day: string): string => `${day} (2ª seduta)`,
    },
  },

  saveState: {
    idle: '',
    pending: 'Modifiche in attesa…',
    saving: 'Salvataggio…',
    saved: 'Salvato',
    error: 'Non salvato',
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
    tabs: {
      exercises: 'Esercizi',
      families: 'Famiglie',
      tags: 'Etichette',
      muscles: 'Muscoli',
      label: 'Sezioni del catalogo',
    },
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
    select: 'Seleziona',
    endSelect: 'Fine selezione',
    selected: (n: number): string => (n === 1 ? '1 selezionato' : `${String(n)} selezionati`),
    assignTag: 'Assegna etichetta…',
    unassignTag: 'Togli etichetta…',
    selectExercise: (name: string): string => `Seleziona ${name}`,
  },

  bulkTags: {
    assignTitle: (n: number): string =>
      `Assegna un’etichetta a ${n === 1 ? '1 esercizio' : `${String(n)} esercizi`}`,
    unassignTitle: (n: number): string =>
      `Togli un’etichetta da ${n === 1 ? '1 esercizio' : `${String(n)} esercizi`}`,
    tag: 'Etichetta',
    tagPlaceholder: 'Scegli l’etichetta',
    note: 'Nota (facoltativa)',
    noteHelp: 'Vale per tutti. Chi ha già l’etichetta mantiene la sua nota se la lasci vuota.',
    assign: 'Assegna',
    unassign: 'Togli',
    cancel: 'Annulla',
    assigned: (tag: string, n: number): string =>
      `«${tag}» assegnata: ora ce l’hanno ${n === 1 ? '1 esercizio' : `${String(n)} esercizi`}.`,
    unassigned: (tag: string): string => `«${tag}» tolta dagli esercizi selezionati.`,
  },

  editing: {
    edit: 'Modifica',
    save: 'Salva',
    cancel: 'Annulla',
    delete: 'Elimina',
    saved: 'Modifiche salvate.',
    created: 'Creato.',
    deleted: 'Eliminato.',
    actions: (name: string): string => `Azioni per ${name}`,
  },

  families: {
    title: 'Famiglie di movimento',
    intro:
      'Esercizi intercambiabili ai fini della scheda: ogni slot chiede una famiglia e propone i suoi esercizi.',
    add: 'Nuova famiglia',
    name: 'Nome',
    group: 'Gruppo',
    description: 'Descrizione',
    exercises: 'Esercizi',
    exerciseCount: (primary: number, secondary: number): string =>
      secondary > 0
        ? `${String(primary)} (+${String(secondary)} come secondaria)`
        : String(primary),
    namePlaceholder: 'es. Spinta convergente',
    groupPlaceholder: 'Scegli il gruppo',
    deleteTitle: 'Eliminare la famiglia?',
    deleteConfirm: (name: string, secondary: number): string =>
      secondary > 0
        ? `«${name}» non è usata come famiglia principale. ${String(secondary)} ${
            secondary === 1 ? 'esercizio la perderà' : 'esercizi la perderanno'
          } come famiglia secondaria.`
        : `«${name}» non è usata da nessun esercizio, split o scheda.`,
    deleteAction: 'Elimina famiglia',
    inUseTitle: 'Famiglia in uso',
    inUse: (name: string, exercises: number, splitSlots: number, plans: string[]): string => {
      const parts = []
      if (exercises > 0)
        parts.push(
          `${exercises === 1 ? '1 esercizio la ha' : `${String(exercises)} esercizi la hanno`} come famiglia principale`,
        )
      if (splitSlots > 0)
        parts.push(
          splitSlots === 1
            ? '1 slot degli split predefiniti la chiede'
            : `${String(splitSlots)} slot degli split predefiniti la chiedono`,
        )
      if (plans.length > 0) parts.push(`è usata nelle schede «${plans.join('», «')}»`)
      return `«${name}» non si può eliminare: ${parts.join('; ')}.`
    },
    close: 'Chiudi',
  },

  tags: {
    title: 'Etichette',
    intro:
      'Segni sugli esercizi con un effetto sulla scelta automatica: nessuno, bonus, penalità o esclusione.',
    add: 'Nuova etichetta',
    symbol: 'Simbolo',
    name: 'Nome',
    color: 'Colore',
    effect: 'Effetto',
    points: 'Punti',
    visible: 'Simbolo visibile',
    exercises: 'Esercizi',
    description: 'Descrizione',
    yes: 'sì',
    no: 'no',
    namePlaceholder: 'es. Non c’è nella mia palestra',
    effects: { none: 'Nessun effetto', bonus: 'Bonus', penalty: 'Penalità', exclude: 'Esclusione' },
    colors: {
      neutral: 'Neutro',
      info: 'Informazione',
      success: 'Positivo',
      warning: 'Attenzione',
      danger: 'Pericolo',
    },
    pointsHelp: 'Solo per bonus e penalità.',
    descriptionPlaceholder: 'Quando assegnarla',
    deleteTitle: 'Eliminare l’etichetta?',
    deleteConfirm: (name: string, exercises: number, plans: number): string => {
      const parts = []
      if (exercises > 0)
        parts.push(
          `assegnata a ${exercises === 1 ? '1 esercizio' : `${String(exercises)} esercizi`}`,
        )
      if (plans > 0)
        parts.push(`personalizzata in ${plans === 1 ? '1 scheda' : `${String(plans)} schede`}`)
      return parts.length === 0
        ? `«${name}» non è usata da nessun esercizio.`
        : `«${name}» è ${parts.join(' e ')}. Eliminarla toglie anche queste assegnazioni.`
    },
    deleteAction: 'Elimina etichetta',
  },

  muscles: {
    title: 'Muscoli',
    intro:
      'Priorità e fascia obiettivo del volume settimanale (serie frazionarie). Valgono per tutte le schede che non le personalizzano.',
    name: 'Nome',
    shortName: 'Nome breve',
    priority: 'Priorità',
    min: 'Min',
    max: 'Max',
    notes: 'Note',
    notesPlaceholder: 'es. lavora già negli esercizi piani',
    band: (min: number | null, max: number | null): string =>
      min === null || max === null ? '—' : `${String(min)}–${String(max)}`,
    invalidBand: (plans: string[]): string =>
      `Fascia non valida per ${plans.length === 1 ? 'la scheda' : 'le schede'} «${plans.join('», «')}», che ${
        plans.length === 1 ? 'personalizza' : 'personalizzano'
      } questo muscolo. Correggi prima le preferenze della scheda.`,
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
