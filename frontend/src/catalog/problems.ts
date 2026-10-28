import type { Problem } from '@/api/client'

/**
 * Messaggi di un errore dell'API divisi per campo (API, § 3.1): `violations` di un
 * `rule-violation` e `errors` di un `validation-error`. Quello che non ha un campo, e
 * gli altri errori, finiscono in `general`.
 */
export function problemMessages(
  problem: Problem,
  invalidValue: string,
): { fields: Record<string, string>; general: string[] } {
  const fields: Record<string, string> = {}
  const general: string[] = []
  for (const violation of problem.violations ?? []) {
    if (violation.field === null) general.push(violation.message)
    else fields[violation.field] ??= violation.message
  }
  for (const error of problem.errors ?? []) {
    const field = error.loc[1]
    if (typeof field === 'string') fields[field] ??= invalidValue
    else general.push(error.msg)
  }
  if (Object.keys(fields).length === 0 && general.length === 0) {
    general.push(problem.detail ?? problem.title)
  }
  return { fields, general }
}
