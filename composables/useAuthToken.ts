/**
 * Single source of truth for auth tokens.
 *
 * Why: Nuxt's useCookie ref writes are flushed to document.cookie
 * asynchronously, which races with client-side navigation - a fresh
 * page's cookie ref can read a stale (empty) value and lose the token.
 * We keep an in-memory useState as the runtime SSOT and mirror every
 * write to document.cookie synchronously.
 */
const MAX_AGE = 60 * 60 * 24 * 14          // access token: 14 days
const REFRESH_MAX_AGE = 60 * 60 * 24 * 30  // refresh token: 30 days

export const useAuthToken = () => {
  const state = useState<string | null>('auth:token-state', () => null)
  const refreshState = useState<string | null>('auth:refresh-state', () => null)
  const cookie = useCookie<string | null>('auth:token', { maxAge: MAX_AGE, sameSite: 'lax' })
  const refreshCookie = useCookie<string | null>('auth:refresh', { maxAge: REFRESH_MAX_AGE, sameSite: 'lax' })

  // bootstrap in-memory state from persisted cookie (page reloads)
  if (!state.value && cookie.value) state.value = cookie.value
  if (!refreshState.value && refreshCookie.value) refreshState.value = refreshCookie.value

  const write = (name: string, value: string | null, maxAge: number) => {
    if (import.meta.server) return
    document.cookie = value
      ? `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAge}; samesite=lax`
      : `${name}=; path=/; max-age=0; samesite=lax`
  }

  const setTokens = (access: string | null, refresh?: string | null) => {
    state.value = access
    cookie.value = access
    write('auth:token', access, MAX_AGE)
    if (refresh !== undefined) {
      refreshState.value = refresh
      refreshCookie.value = refresh
      write('auth:refresh', refresh, REFRESH_MAX_AGE)
    }
  }

  return { state, refreshState, setTokens }
}
