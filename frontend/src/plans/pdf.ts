/**
 * Scarico del PDF della scheda (US-30; API, § 6.10).
 *
 * Il PDF si chiede con `fetch` e si salva da un `Blob`, invece di aprire il link: così
 * un errore del server arriva come gli altri (titolo e dettaglio) e il file prende il
 * nome deciso dal server.
 */

import { asProblem, type Problem } from '@/api/client'

export const DEFAULT_WEEKS = 4
export const WEEK_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8] as const

/** Il nome del file da `Content-Disposition: attachment; filename="…"`. */
export function filenameFrom(header: string | null, fallback: string): string {
  const match = header === null ? null : /filename="?([^";]+)"?/i.exec(header)
  return match?.[1] ?? fallback
}

export async function downloadPlanPdf(
  planId: number,
  weeks: number,
): Promise<{ ok: true; filename: string } | { ok: false; problem: Problem }> {
  const url = new URL(`/api/plans/${String(planId)}/pdf`, window.location.origin)
  url.searchParams.set('weeks', String(weeks))
  const response = await globalThis.fetch(new Request(url))
  if (!response.ok) {
    let body: unknown = null
    try {
      body = await response.json()
    } catch {
      body = null
    }
    return { ok: false, problem: asProblem(body, response.status) }
  }
  const filename = filenameFrom(
    response.headers.get('Content-Disposition'),
    `scheda-${String(planId)}.pdf`,
  )
  const blob = await response.blob()
  const href = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = href
  link.download = filename
  document.body.append(link)
  link.click()
  link.remove()
  // Il browser ha già preso il file: l'indirizzo temporaneo si può liberare.
  setTimeout(() => {
    URL.revokeObjectURL(href)
  }, 1000)
  return { ok: true, filename }
}
