import Sortable from 'sortablejs'
import { onBeforeUnmount, type Ref, watch } from 'vue'

export interface SortableOptions {
  /** Selettore della maniglia; senza, si trascina l'intero elemento. */
  handle?: string
  /** Trascinamento attivo; si può cambiare (modalità "Riordina" sul telefono). */
  enabled: Ref<boolean>
  /** Spostamento concluso, tra gli indici degli elementi della lista. */
  onMove: (from: number, to: number) => void
}

/**
 * Riordino trascinando, con il mouse o tenendo premuto sul telefono (wireframe, § 3.3
 * e § 3.7). SortableJS sposta l'elemento nel DOM: lo si rimette dov'era e si lascia a
 * Vue ridisegnare la lista dal nuovo ordine, così DOM e dati non divergono.
 */
export function useSortable(element: Ref<HTMLElement | null>, options: SortableOptions): void {
  let sortable: Sortable | null = null

  function destroy(): void {
    sortable?.destroy()
    sortable = null
  }

  watch(
    [element, options.enabled],
    ([el, enabled]) => {
      destroy()
      if (el === null || !enabled) return
      sortable = Sortable.create(el, {
        ...(options.handle === undefined ? {} : { handle: options.handle }),
        animation: 150,
        // Sul telefono si trascina dopo una breve pressione, per non confondersi con lo scorrimento.
        delay: 200,
        delayOnTouchOnly: true,
        ghostClass: 'sortable-ghost',
        onEnd: (event) => {
          const { oldIndex, newIndex, item, from } = event
          if (oldIndex === undefined || newIndex === undefined || oldIndex === newIndex) return
          from.removeChild(item)
          from.insertBefore(item, from.children[oldIndex] ?? null)
          options.onMove(oldIndex, newIndex)
        },
      })
    },
    { immediate: true, flush: 'post' },
  )

  onBeforeUnmount(destroy)
}
