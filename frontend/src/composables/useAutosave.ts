import { onBeforeUnmount, readonly, ref, type Ref } from 'vue'

/** Attesa dopo l'ultima modifica prima di salvare: abbastanza per finire di scrivere. */
export const AUTOSAVE_DELAY = 600

/**
 * - `idle`: niente da salvare;
 * - `pending`: modifiche in attesa;
 * - `saving`: salvataggio in corso;
 * - `saved`: salvato;
 * - `error`: l'ultimo salvataggio non è riuscito.
 */
export type SaveState = 'idle' | 'pending' | 'saving' | 'saved' | 'error'

export interface Autosave {
  state: Readonly<Ref<SaveState>>
  /** Segnala una modifica: il salvataggio parte dopo `delay` senza altre modifiche. */
  schedule: () => void
  /** Salva subito ciò che è in attesa e aspetta la fine (prima di uscire dalla pagina). */
  flush: () => Promise<void>
}

/**
 * Salvataggio automatico in coda (wireframe, principio 4): un solo salvataggio alla
 * volta; le modifiche fatte mentre si salva partono subito dopo, con lo stato più
 * recente. `save` restituisce `false` se il server ha rifiutato.
 */
export function useAutosave(save: () => Promise<boolean>, delay = AUTOSAVE_DELAY): Autosave {
  const state = ref<SaveState>('idle')
  let timer: ReturnType<typeof setTimeout> | null = null
  let running: Promise<void> | null = null
  let again = false
  // Letta con una funzione: `again` cambia durante l'attesa del salvataggio.
  const changedMeanwhile = (): boolean => again

  function schedule(): void {
    state.value = 'pending'
    if (timer !== null) clearTimeout(timer)
    timer = setTimeout(() => {
      timer = null
      void run()
    }, delay)
  }

  async function run(): Promise<void> {
    if (running !== null) {
      again = true
      return running
    }
    running = (async () => {
      do {
        again = false
        state.value = 'saving'
        let ok = false
        try {
          ok = await save()
        } catch {
          ok = false
        }
        state.value = changedMeanwhile() ? 'pending' : ok ? 'saved' : 'error'
      } while (changedMeanwhile())
    })()
    try {
      await running
    } finally {
      running = null
    }
  }

  async function flush(): Promise<void> {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
      await run()
    } else if (running !== null) {
      await running
    }
  }

  onBeforeUnmount(() => {
    void flush()
  })

  return { state: readonly(state), schedule, flush }
}
