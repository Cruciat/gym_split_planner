import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope } from 'vue'

import { useAutosave } from './useAutosave'

/** Un salvataggio che si conclude solo quando il test lo decide. */
function deferredSave() {
  const resolvers: ((ok: boolean) => void)[] = []
  const save = vi.fn(
    () =>
      new Promise<boolean>((resolve) => {
        resolvers.push(resolve)
      }),
  )
  return { save, finish: (ok = true) => resolvers.shift()?.(ok) }
}

describe('useAutosave', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const make = (save: () => Promise<boolean>) => {
    const scope = effectScope()
    const autosave = scope.run(() => useAutosave(save, 500))
    if (autosave === undefined) throw new Error('scope')
    return autosave
  }

  it('aspetta la fine delle modifiche e salva una volta', async () => {
    const save = vi.fn(() => Promise.resolve(true))
    const { state, schedule } = make(save)

    schedule()
    await vi.advanceTimersByTimeAsync(300)
    schedule()
    expect(state.value).toBe('pending')
    await vi.advanceTimersByTimeAsync(499)
    expect(save).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(1)

    expect(save).toHaveBeenCalledTimes(1)
    expect(state.value).toBe('saved')
  })

  it('una modifica durante il salvataggio parte subito dopo', async () => {
    const { save, finish } = deferredSave()
    const { state, schedule, flush } = make(save)

    schedule()
    await vi.advanceTimersByTimeAsync(500)
    expect(state.value).toBe('saving')
    schedule()
    const flushed = flush()
    finish()
    await vi.advanceTimersByTimeAsync(0)
    expect(save).toHaveBeenCalledTimes(2)
    finish()
    await flushed

    expect(state.value).toBe('saved')
  })

  it('segnala il salvataggio rifiutato', async () => {
    const { state, schedule, flush } = make(() => Promise.resolve(false))

    schedule()
    await flush()

    expect(state.value).toBe('error')
  })

  it('flush senza modifiche in attesa non salva', async () => {
    const save = vi.fn(() => Promise.resolve(true))
    const { state, flush } = make(save)

    await flush()

    expect(save).not.toHaveBeenCalled()
    expect(state.value).toBe('idle')
  })
})
