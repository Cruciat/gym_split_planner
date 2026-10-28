import { onScopeDispose, readonly, ref, type Ref } from 'vue'

/** Sotto questa larghezza l'interfaccia è quella del telefono (wireframe, § 2). */
export const MOBILE_QUERY = '(max-width: 767px)'

/** `true` sotto i 768 px; segue i cambi di larghezza della finestra. */
export function useIsMobile(): Readonly<Ref<boolean>> {
  const isMobile = ref(false)
  if (typeof window.matchMedia !== 'function') return readonly(isMobile)

  const media = window.matchMedia(MOBILE_QUERY)
  isMobile.value = media.matches
  const update = (event: MediaQueryListEvent) => {
    isMobile.value = event.matches
  }
  media.addEventListener('change', update)
  onScopeDispose(() => {
    media.removeEventListener('change', update)
  })
  return readonly(isMobile)
}
