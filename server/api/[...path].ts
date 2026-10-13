/**
 * Same-origin gateway to the FastAPI backend.
 *
 * The browser only ever talks to this site, so the API's HttpOnly session cookies are
 * first-party cookies for this domain. We also pass the visitor's real IP (proven with a
 * shared secret) so the API's rate limits apply per visitor, not per proxy.
 */
import { getRequestIP, proxyRequest } from 'h3'

export default defineEventHandler((event) => {
  const { apiOrigin, proxySecret } = useRuntimeConfig(event)
  const target = apiOrigin.replace(/\/$/, '') + event.path   // event.path keeps /api/... and the query
  const headers: Record<string, string> = {}
  if (proxySecret) {
    headers['x-lh-proxy-secret'] = proxySecret
    headers['x-lh-client-ip'] = getRequestIP(event, { xForwardedFor: true }) || ''
  }
  return proxyRequest(event, target, { headers })
})
