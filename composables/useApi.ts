import { FetchError } from 'ofetch'

/**
 * API client for the FastAPI backend (same-origin /api proxy).
 *
 * The session lives in HttpOnly cookies set by the API, so this code never sees a token.
 * Every request sends `X-Requested-With`, which the API requires for cookie-authenticated
 * writes (CSRF protection). On a 401 it rotates the session once via /auth/refresh and retries.
 */
let refreshing: Promise<boolean> | null = null

export const useApi = () => {
  const { show } = useToast()

  const baseHeaders = (): Record<string, string> => {
    const h: Record<string, string> = { 'X-Requested-With': 'XMLHttpRequest' }
    // during server-side rendering, pass the visitor's cookies through to the API
    if (import.meta.server) {
      const cookie = useRequestHeaders(['cookie']).cookie
      if (cookie) h.cookie = cookie
    }
    return h
  }

  /** One shared refresh at a time, even if several requests 401 together. */
  const tryRefresh = (): Promise<boolean> => {
    if (import.meta.server) return Promise.resolve(false)
    if (!refreshing) {
      refreshing = $fetch('/api/auth/refresh', { method: 'POST', headers: baseHeaders() })
        .then(() => true, () => false)
        .finally(() => { setTimeout(() => { refreshing = null }, 0) })
    }
    return refreshing
  }

  const redirectToLogin = () => {
    if (import.meta.server) return
    let redirect: string | undefined
    try { redirect = useRoute().fullPath } catch { /* outside a route context */ }
    useState('auth:user').value = null
    show('Your session has expired. Please sign in again.', 'error')
    navigateTo(redirect && redirect !== '/login' ? { path: '/login', query: { redirect } } : '/login')
  }

  const handleErr = async (e: unknown, silent: boolean, retry?: () => Promise<any>) => {
    if (e instanceof FetchError) {
      const status = e.statusCode || 0
      const requestUrl = String(e.request || '')
      const detail = (e.data as { detail?: string } | undefined)?.detail
      const isAuthCall = requestUrl.includes('/auth/')

      if (status === 401 && retry && !isAuthCall && (await tryRefresh())) {
        return await retry()
      }
      if (status === 401 && !isAuthCall && useState('auth:user').value) redirectToLogin()
      if (!silent && !(status === 401 && !isAuthCall)) show(detail || e.message || 'Something went wrong', 'error')
      throw e
    }
    throw e
  }

  const request = async <T>(path: string, opts: Record<string, any>, silent: boolean): Promise<T> => {
    const call = () => $fetch<T>(`/api${path}`, { ...opts, headers: { ...baseHeaders(), ...(opts.headers || {}) } })
    try {
      return await call()
    } catch (e) {
      return handleErr(e, silent, call) as never
    }
  }

  const get = <T = any>(path: string, params?: Record<string, any>, silent = false) => request<T>(path, { params }, silent)
  const post = <T = any>(path: string, body?: any, silent = false) => request<T>(path, { method: 'POST', body }, silent)
  const put = <T = any>(path: string, body?: any, silent = false) => request<T>(path, { method: 'PUT', body }, silent)
  const del = <T = any>(path: string, silent = false) => request<T>(path, { method: 'DELETE' }, silent)

  const upload = (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<{ url: string; filename: string }>('/media/upload', { method: 'POST', body: form }, false)
  }

  return { get, post, put, del, upload, tryRefresh }
}
