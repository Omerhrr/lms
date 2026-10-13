/** Human-friendly formatting shared across the app. */

/** 25 -> "25 min", 65 -> "1 h 5 min", 120 -> "2 h" */
export const fmtMinutes = (min?: number | null): string => {
  const m = Math.max(0, Math.round(min || 0))
  if (m < 60) return `${m} min`
  const h = Math.floor(m / 60), r = m % 60
  return r ? `${h} h ${r} min` : `${h} h`
}

/** 1 -> "1 lesson", 3 -> "3 lessons" */
export const plural = (n: number, one: string, many = one + 's') => `${n} ${n === 1 ? one : many}`
