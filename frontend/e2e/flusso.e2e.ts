import { readFile } from 'node:fs/promises'
import { inflateSync } from 'node:zlib'

import { expect, type Page, test } from '@playwright/test'

/**
 * Flusso critico di M4 (issue #39; processo, § 7): crea una scheda da un preset,
 * cambia la variante di un esercizio, lo blocca, cambia le preferenze e rigenera.
 * L'esercizio bloccato deve restare quello scelto a mano (US-15 CA2, US-18 CA1); alla
 * fine la scheda si scarica in PDF (US-30).
 */

/** Pagine di un PDF: WeasyPrint le descrive dentro flussi compressi, qui si decomprimono. */
function countPages(pdf: Buffer): number {
  const text = pdf.toString('latin1')
  const pattern = /\/Type\s*\/Page(?!s)/g
  let pages = (text.match(pattern) ?? []).length
  for (let at = text.indexOf('stream'); at !== -1; at = text.indexOf('stream', at + 6)) {
    let start = at + 6
    if (text[start] === '\r') start += 1
    if (text[start] === '\n') start += 1
    const end = text.indexOf('endstream', start)
    if (end === -1) break
    try {
      pages += (inflateSync(pdf.subarray(start, end)).toString('latin1').match(pattern) ?? [])
        .length
    } catch {
      // Flusso non compresso con Flate (es. un font): non contiene pagine.
    }
    at = end
  }
  return pages
}

async function openPlanMenu(page: Page, item: string): Promise<void> {
  await page.getByTestId('plan-menu').click()
  await page.getByText(item, { exact: true }).click()
}

test('crea scheda da preset → cambia variante → blocca → rigenera → PDF', async ({
  page,
  request,
  isMobile,
}, testInfo) => {
  // 1. Creazione guidata da «Push/Pull/Legs, 6 giorni», con le preferenze già pronte.
  await page.goto('/schede/nuova')
  await page.getByTestId('split-choice').filter({ hasText: 'Push/Pull/Legs, 6 giorni' }).click()
  await expect(page.getByTestId('step')).toHaveText('Passo 2 di 3 — Preferenze')
  await page.getByTestId('next').click()
  const name = `E2E ${testInfo.project.name}`
  await page.getByTestId('plan-name').locator('input').fill(name)
  await page.getByTestId('create').click()
  await expect(page).toHaveURL(/\/schede\/\d+$/)
  const id = Number(/(\d+)$/.exec(page.url())?.[1])
  await expect(page.getByTestId('plan-name')).toHaveText(name)
  await expect(page.getByTestId('day-tab')).toHaveText(['Push ×2', 'Pull ×2', 'Legs ×2'])

  // 2. Variante del primo esercizio: un candidato diverso dall'attuale.
  const first = page.getByTestId('slot').first()
  if (isMobile) {
    await first.getByTestId('slot-main').click()
    await page.getByTestId('sheet-variants').click()
  } else {
    await first.getByTestId('open-variants').click()
  }
  const panel = page.getByTestId('variants-panel')
  const other = panel.locator('[data-testid="candidate"] button[aria-checked="false"]').first()
  const label = (await other.getAttribute('aria-label')) ?? ''
  const chosen = label.replace(/^Scegli /, '')
  await other.click()
  await expect(panel.getByTestId('variants-current')).toHaveText(`Attuale: ${chosen}`)
  await page.keyboard.press('Escape')
  await expect(first.getByTestId('slot-name')).toHaveText(chosen)

  // 3. Lucchetto.
  await first.getByTestId('slot-lock').click()
  await expect(first.getByTestId('slot-lock')).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByTestId('save-status')).toHaveText('Salvato')

  // 4. Preferenze: pesi liberi in cima, salvate da sole.
  if (isMobile) await openPlanMenu(page, 'Preferenze')
  else await page.getByTestId('open-preferences').click()
  const freeWeights = page.getByTestId('equipment').filter({ hasText: 'Pesi liberi' })
  await freeWeights.getByTestId('equipment-up').click()
  await freeWeights.getByTestId('equipment-up').click()
  await expect(page.getByTestId('equipment').first()).toContainText('Pesi liberi')
  await expect(page.getByTestId('save-status')).toHaveText('Salvato')
  await page.getByText('Torna alla scheda').click()
  await expect(page).toHaveURL(new RegExp(`/schede/${String(id)}`))

  // 5. Rigenera: l'esercizio bloccato non compare tra le differenze.
  if (isMobile) await openPlanMenu(page, 'Rigenera')
  else await page.getByTestId('regenerate').click()
  const dialog = page.getByTestId('regenerate-dialog')
  await expect(dialog.getByTestId('change').first()).toBeVisible()
  await expect(dialog.getByTestId('locked-note')).toContainText('(1)')
  await expect(dialog.getByTestId('change').filter({ hasText: /^Push · 1\b/ })).toHaveCount(0)
  await dialog.getByTestId('apply-regeneration').click()
  await expect(page.getByText(/^Rigenerat[oi] \d+ eserciz/)).toBeVisible()

  // 6. Sul server: lo slot bloccato è quello scelto a mano, e non resta nulla da rigenerare.
  const plan = (await (await request.get(`/api/plans/${String(id)}`)).json()) as {
    days: { slots: { locked: boolean; exercise: { name: string } | null }[] }[]
  }
  expect(plan.days[0]?.slots[0]).toMatchObject({ locked: true, exercise: { name: chosen } })
  const preview = (await (
    await request.post(`/api/plans/${String(id)}/regenerate/preview`)
  ).json()) as { changes: unknown[]; locked_slots: number }
  expect(preview).toMatchObject({ changes: [], locked_slots: 1 })

  // 7. PDF della scheda (US-30): nome dal server, una pagina per giorno e il riepilogo.
  const downloading = page.waitForEvent('download')
  if (isMobile) {
    await openPlanMenu(page, 'PDF')
    await page.getByTestId('pdf-download').click()
  } else {
    await page.getByTestId('pdf').click()
  }
  const download = await downloading
  expect(download.suggestedFilename()).toMatch(
    new RegExp(`^e2e-${testInfo.project.name}-\\d{4}-\\d{2}-\\d{2}\\.pdf$`),
  )
  const pdf = await readFile(await download.path())
  expect(pdf.subarray(0, 5).toString()).toBe('%PDF-')
  expect(countPages(pdf)).toBe(4)
})

test('l’app si apre sulla scheda attiva', async ({ page, request }) => {
  const created = (await (
    await request.post('/api/plans', { data: { split_id: null, name: 'Attiva E2E' } })
  ).json()) as { id: number }
  await request.post(`/api/plans/${String(created.id)}/activate`)

  await page.goto('/')

  await expect(page).toHaveURL(new RegExp(`/schede/${String(created.id)}$`))
  await expect(page.getByTestId('empty-plan')).toContainText('Questa scheda non ha ancora giorni.')
})
