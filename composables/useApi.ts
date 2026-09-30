import { FetchError } from 'ofetch'

/**
 * Thin API client for the FastAPI backend (proxied via /api).
 * Reads the token from the shared auth-token state (SSOT).
 *
 * On a 401 from a protected endpoint it transparently rotates the
 * session once via POST /auth/refresh and retries the original call
 * before redirecting to the login page.
 */
export const useApi = () => {
  const { state: token, refreshState, setTokens } = useAuthToken()
  const { show } = useToast()

  const headers = (): Record<string, string> => {
    const h: Record<string, string> = {}
    if (token.value) h.Authorization = `Bearer ${token.value}`
    return h
  }

  const redirectToLogin = () => {
    let redirect: string | undefined
    try {
      redirect = useRoute().fullPath
    } catch { /* outside a route context (e.g. plugin) */ }
    setTokens(null, null)
    const user = useState('auth:user')
    user.value = null
    show('Your session has expired. Please sign in again.', 'error')
    navigateTo(redirect && redirect !== '/login' ? { path: '/login', query: { redirect } } : '/login')
  }

  const handleErr = async (e: unknown, silent: boolean, retry?: () => Promise<any>) => {
    if (e instanceof FetchError) {
      const status = e.statusCode || 0
      const requestUrl = String(e.request || '')
      const detail = (e.data as { detail?: string } | undefined)?.detail

      // expired access token on a protected endpoint: one silent refresh + retry
      if (status === 401 && retry && refreshState.value && !requestUrl.includes('/auth/')) {
        try {
          const res = await $fetch<{ access_token: string; refresh_token: string }>('/api/auth/refresh', {
            method: 'POST',
            body: { refresh_token: refreshState.value },
          })
          setTokens(res.access_token, res.refresh_token)
          return await retry()
        } catch { /* refresh failed - fall through to the logout flow */ }
      }

      if (status === 401 && !requestUrl.includes('/auth/')) {
        redirectToLogin()
      }
      if (!silent) show(detail || e.message || 'Something went wrong', 'error')
      throw e
    }
    throw e
  }

  const get = async <T = any>(path: string, params?: Record<string, any>, silent = false): Promise<T> => {
    const call = () => $fetch<T>(`/api${path}`, { headers: headers(), params })
    try {
      return await call()
    } catch (e) {
      return handleErr(e, silent, call) as never
    }
  }

  const post = async <T = any>(path: string, body?: any, silent = false): Promise<T> => {
    const call = () => $fetch<T>(`/api${path}`, { method: 'POST', body, headers: headers() })
    try {
      return await call()
    } catch (e) {
      return handleErr(e, silent, call) as never
    }
  }

  const put = async <T = any>(path: string, body?: any, silent = false): Promise<T> => {
    const call = () => $fetch<T>(`/api${path}`, { method: 'PUT', body, headers: headers() })
    try {
      return await call()
    } catch (e) {
      return handleErr(e, silent, call) as never
    }
  }

  const del = async <T = any>(path: string, silent = false): Promise<T> => {
    const call = () => $fetch<T>(`/api${path}`, { method: 'DELETE', headers: headers() })
    try {
      return await call()
    } catch (e) {
      return handleErr(e, silent, call) as never
    }
  }

  const upload = async (file: File): Promise<{ url: string; filename: string }> => {
    const form = new FormData()
    form.append('file', file)
    const call = () => $fetch<{ url: string; filename: string }>('/api/media/upload', { method: 'POST', body: form, headers: headers() })
    try {
      return await call()
    } catch (e) {
      return handleErr(e, false) as never
    }
  }

  return { get, post, put, del, upload }
}
