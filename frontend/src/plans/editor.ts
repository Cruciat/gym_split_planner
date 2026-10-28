/**
 * Stato dell'editor della scheda e coda delle modifiche (API, § 4; wireframe, § 3.3).
 *
 * Ogni modifica è una richiesta che restituisce la scheda completa. Le richieste vanno
 * in coda e partono una alla volta, ciascuna con la revisione restituita dalla
 * precedente: così le modifiche rapide dallo stesso dispositivo non si scontrano.
 *
 * - `412`: la scheda è cambiata altrove. Si ricarica, si avvisa e si scarta il resto
 *   della coda, che era pensato sui dati vecchi; l'ultima azione si ripete a mano.
 * - Errore di rete: la richiesta resta in testa alla coda, lo stato diventa `error` e
 *   "Riprova" fa ripartire la coda dal punto in cui si era fermata.
 * - Altri errori (es. `422 rule-violation`): messaggio del server, la richiesta si
 *   scarta e la coda prosegue. La scheda resta quella del server.
 */

import { inject, type InjectionKey, provide, readonly, ref, type Ref, shallowRef } from 'vue'

import { api, asProblem, ifMatch, type Plan, type Problem } from '@/api/client'
import type { components } from '@/api/schema'
import type { SaveState } from '@/composables/useAutosave'
import { texts } from '@/texts'

type Schemas = components['schemas']
export type Day = Plan['days'][number]
export type Slot = Day['slots'][number]
export type DayInput = Schemas['DayIn']
export type DayPatch = Schemas['DayPatch']
export type SlotInput = Schemas['SlotIn']
export type SlotPatch = Schemas['SlotPatch']
export type Candidates = Schemas['CandidatesOut']
export type Candidate = Schemas['CandidateOut']
export type RegenerationPreview = Schemas['RegenerationPreviewOut']

interface Result {
  data?: Plan
  error?: unknown
  response: Response
}

interface Pending {
  send: (revision: number) => Promise<Result>
  resolve: (ok: boolean) => void
}

export interface Notifier {
  warning: (text: string) => void
  error: (text: string) => void
}

/** Testo di un errore del server: le regole violate, o titolo e dettaglio. */
export function problemText(problem: Problem): string {
  const messages = (problem.violations ?? []).map((v) => v.message)
  if (messages.length > 0) return messages.join(' ')
  return problem.detail === undefined ? problem.title : `${problem.title}: ${problem.detail}`
}

export function createPlanEditor(planId: number, notify: Notifier) {
  const plan = shallowRef<Plan | null>(null)
  const loadState = ref<'loading' | 'ready' | 'not-found' | 'failed'>('loading')
  const saveState = ref<SaveState>('idle')
  const queue: Pending[] = []
  let pumping = false
  let waiting: (() => void)[] = []

  async function load(): Promise<void> {
    try {
      const { data, response } = await api.GET('/api/plans/{plan_id}', {
        params: { path: { plan_id: planId } },
      })
      if (response.status === 404) loadState.value = 'not-found'
      else if (data === undefined) loadState.value = 'failed'
      else {
        plan.value = data
        loadState.value = 'ready'
      }
    } catch {
      loadState.value = 'failed'
    }
  }

  /** Mette in coda una modifica; la promessa dice se è stata applicata. */
  function enqueue(send: Pending['send']): Promise<boolean> {
    return new Promise((resolve) => {
      queue.push({ send, resolve })
      void pump()
    })
  }

  async function pump(): Promise<void> {
    if (pumping) return
    pumping = true
    try {
      for (let item = queue[0]; item !== undefined; item = queue[0]) {
        const current = plan.value
        if (current === null) break
        saveState.value = 'saving'
        let result: Result
        try {
          result = await item.send(current.revision)
        } catch {
          // Rete: la modifica resta in coda e riparte con "Riprova".
          saveState.value = 'error'
          return
        }
        queue.shift()
        if (result.data !== undefined) {
          plan.value = result.data
          item.resolve(true)
        } else if (result.response.status === 412) {
          const dropped = [item, ...queue.splice(0)]
          notify.warning(texts.editor.reloaded)
          await load()
          for (const each of dropped) each.resolve(false)
        } else {
          item.resolve(false)
          notify.error(problemText(asProblem(result.error, result.response.status)))
        }
      }
      saveState.value = 'saved'
    } finally {
      pumping = false
      // Chi aspetta la fine della coda la riceve anche se la rete l'ha fermata.
      if (queue.length === 0 || saveState.value === 'error') {
        for (const resolve of waiting.splice(0)) resolve()
      }
    }
  }

  /** Riprende la coda dopo un errore di rete. */
  function retry(): void {
    void pump()
  }

  /** Aspetta che la coda sia vuota; `false` se resta qualcosa di non inviato. */
  async function settle(): Promise<boolean> {
    if (queue.length > 0 && saveState.value !== 'error') {
      await new Promise<void>((resolve) => {
        waiting.push(resolve)
      })
    }
    return queue.length === 0
  }

  function dispose(): void {
    waiting = []
  }

  // --- Modifiche -----------------------------------------------------------------

  const headers = (revision: number) => ifMatch(revision)

  const rename = (name: string) =>
    enqueue((revision) =>
      api.PATCH('/api/plans/{plan_id}', {
        params: { path: { plan_id: planId } },
        body: { name },
        headers: headers(revision),
      }),
    )

  const addDay = (body: DayInput) =>
    enqueue((revision) =>
      api.POST('/api/plans/{plan_id}/days', {
        params: { path: { plan_id: planId } },
        body,
        headers: headers(revision),
      }),
    )

  const updateDay = (dayId: number, body: DayPatch) =>
    enqueue((revision) =>
      api.PATCH('/api/plans/{plan_id}/days/{day_id}', {
        params: { path: { plan_id: planId, day_id: dayId } },
        body,
        headers: headers(revision),
      }),
    )

  const deleteDay = (dayId: number) =>
    enqueue((revision) =>
      api.DELETE('/api/plans/{plan_id}/days/{day_id}', {
        params: { path: { plan_id: planId, day_id: dayId } },
        headers: headers(revision),
      }),
    )

  /** Nuovo ordine dei giorni: subito sullo schermo, poi confermato dal server. */
  function reorderDays(dayIds: number[]): Promise<boolean> {
    const current = plan.value
    if (current !== null) {
      const byId = new Map(current.days.map((d) => [d.id, d]))
      const days = dayIds.flatMap((id) => byId.get(id) ?? [])
      plan.value = { ...current, days }
    }
    return enqueue((revision) =>
      api.PUT('/api/plans/{plan_id}/days/order', {
        params: { path: { plan_id: planId } },
        body: { day_ids: dayIds },
        headers: headers(revision),
      }),
    )
  }

  const addSlot = (dayId: number, body: SlotInput) =>
    enqueue((revision) =>
      api.POST('/api/plans/{plan_id}/days/{day_id}/slots', {
        params: { path: { plan_id: planId, day_id: dayId } },
        body,
        headers: headers(revision),
      }),
    )

  const updateSlot = (slotId: number, body: SlotPatch) =>
    enqueue((revision) =>
      api.PATCH('/api/plans/{plan_id}/slots/{slot_id}', {
        params: { path: { plan_id: planId, slot_id: slotId } },
        body,
        headers: headers(revision),
      }),
    )

  const deleteSlot = (slotId: number) =>
    enqueue((revision) =>
      api.DELETE('/api/plans/{plan_id}/slots/{slot_id}', {
        params: { path: { plan_id: planId, slot_id: slotId } },
        headers: headers(revision),
      }),
    )

  /** Nuovo ordine degli esercizi di un giorno, come per i giorni. */
  function reorderSlots(dayId: number, slotIds: number[]): Promise<boolean> {
    const current = plan.value
    if (current !== null) {
      plan.value = {
        ...current,
        days: current.days.map((day) => {
          if (day.id !== dayId) return day
          const byId = new Map(day.slots.map((s) => [s.id, s]))
          return { ...day, slots: slotIds.flatMap((id) => byId.get(id) ?? []) }
        }),
      }
    }
    return enqueue((revision) =>
      api.PUT('/api/plans/{plan_id}/days/{day_id}/slots/order', {
        params: { path: { plan_id: planId, day_id: dayId } },
        body: { slot_ids: slotIds },
        headers: headers(revision),
      }),
    )
  }

  /** Candidati di uno slot, per la prima (`1`) o la seconda seduta (`2`): sola lettura. */
  async function candidates(slotId: number, session: 1 | 2): Promise<Candidates | null> {
    try {
      const { data, error, response } = await api.GET(
        '/api/plans/{plan_id}/slots/{slot_id}/candidates',
        { params: { path: { plan_id: planId, slot_id: slotId }, query: { session } } },
      )
      if (data !== undefined) return data
      notify.error(problemText(asProblem(error, response.status)))
    } catch {
      notify.error(texts.common.loadFailed)
    }
    return null
  }

  /** Differenze della rigenerazione con le preferenze correnti (US-18 CA2). */
  async function previewRegeneration(): Promise<RegenerationPreview | null> {
    try {
      const { data, error, response } = await api.POST('/api/plans/{plan_id}/regenerate/preview', {
        params: { path: { plan_id: planId } },
      })
      if (data !== undefined) return data
      notify.error(problemText(asProblem(error, response.status)))
    } catch {
      notify.error(texts.common.loadFailed)
    }
    return null
  }

  /**
   * Applica le differenze scelte. La revisione è quella dell'anteprima, non quella
   * corrente: se nel frattempo la scheda è cambiata, il server risponde `412` e le
   * differenze mostrate non valgono più.
   */
  const regenerate = (slotIds: number[], previewRevision: number) =>
    enqueue(() =>
      api.POST('/api/plans/{plan_id}/regenerate', {
        params: { path: { plan_id: planId } },
        body: { slot_ids: slotIds },
        headers: headers(previewRevision),
      }),
    )

  return {
    plan: plan as Readonly<Ref<Plan | null>>,
    loadState: readonly(loadState),
    saveState: readonly(saveState),
    load,
    retry,
    settle,
    dispose,
    rename,
    addDay,
    updateDay,
    deleteDay,
    reorderDays,
    addSlot,
    updateSlot,
    deleteSlot,
    reorderSlots,
    candidates,
    previewRegeneration,
    regenerate,
  }
}

export type PlanEditor = ReturnType<typeof createPlanEditor>

const KEY: InjectionKey<PlanEditor> = Symbol('plan-editor')

export function providePlanEditor(editor: PlanEditor): void {
  provide(KEY, editor)
}

/** L'editor della pagina, per i componenti dentro l'editor. */
export function usePlanEditor(): PlanEditor {
  const editor = inject(KEY)
  if (editor === undefined) throw new Error('usePlanEditor fuori dall’editor della scheda')
  return editor
}
