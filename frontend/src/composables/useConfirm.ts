import { useDialog } from 'naive-ui'

export interface ConfirmOptions {
  title: string
  content: string
  /** Testo del pulsante che conferma: il verbo dell'azione, mai "OK" (wireframe, § 7). */
  action: string
  cancel: string
  type?: 'warning' | 'info' | 'error'
}

/** Finestra di conferma come promessa: `true` se si conferma, `false` altrimenti. */
export function useConfirm(): (options: ConfirmOptions) => Promise<boolean> {
  const dialog = useDialog()
  return (options) =>
    new Promise((resolve) => {
      dialog[options.type ?? 'warning']({
        title: options.title,
        content: options.content,
        positiveText: options.action,
        negativeText: options.cancel,
        onPositiveClick: () => {
          resolve(true)
        },
        onNegativeClick: () => {
          resolve(false)
        },
        onClose: () => {
          resolve(false)
        },
        onMaskClick: () => {
          resolve(false)
        },
      })
    })
}
