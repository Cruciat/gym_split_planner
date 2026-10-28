import { onScopeDispose, readonly, ref, type Ref } from 'vue'

/** Sotto questa larghezza l'interfaccia è quella del telefono (wireframe, § 2). */
export const MOBILE_QUERY = '(max-width: 767px)'

/** Sotto questa larghezza l'editor mette il pannello volume in un foglio (wireframe, § 2). */
export const NARROW_QUERY = '(max-width: 1023px)'

/** Segue una media query mentre la finestra cambia larghezza. */
export function useMediaQuery(query: string): Readonly<Ref<boolean>> {
  const matches = ref(false)
  if (typeof window.matchMedia !== 'function') return readonly(matches)

  const media = window.matchMedia(query)
  matches.value = media.matches
  const update = (event: MediaQueryListEvent) => {
    matches.value = event.matches
  }
  media.addEventListener('change', update)
  onScopeDispose(() => {
    media.removeEventListener('change', update)
  })
  return readonly(matches)
}

/** `true` sotto i 768 px; segue i cambi di larghezza della finestra. */
export function useIsMobile(): Readonly<Ref<boolean>> {
  return useMediaQuery(MOBILE_QUERY)
}
