/**
 * Only let http(s) links and our own uploads into href/src attributes.
 * Vue does not block `javascript:` URLs, so user-supplied links must go through this.
 */
export const safeUrl = (value?: string | null): string | undefined => {
  if (!value) return undefined
  const v = String(value).trim()
  if (/^https?:\/\//i.test(v) || v.startsWith('/api/media/files/')) return v
  return undefined
}
