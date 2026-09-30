import { FetchError } from 'ofetch'

/**
 * Thin API client for the FastAPI backend (proxied via /api).
 * Reads the token from the shared auth-token state (SSOT).
 */
export const useApi = () => {
  const { state: token, setTokens } = useAuthToken()
  const { show } = useToast()

  const headers = (): Record<string, string> => {
    const h: Record<string, string> = {}
    if (token.value) h.Authorization = `Bearer ${token.value}`
    return h
  }

  const handleErr = (e: unknown, silent = false) => {
    if (e instanceof FetchError) {
      const status = e.statusCode || 0
      const detail = (e.data as { detail?: string } | undefined)?.detail
      if (status === 401 && !String(e.request || '').includes('/auth/')) {
        setTokens(null, null)
        const user = useState('auth:user')
        user.value = null
        show('Your session has expired. Please sign in again.', 'error')
        navigateTo('/login')
      }
      if (!silent) show(detail || e.message || 'Something went wrong', 'error')
      throw e
    }
    throw e
  }

  const get = async <T = any>(path: string, params?: Record<string, any>, silent = false): Promise<T> => {
    try {
      return await $fetch<T>(`/api${path}`, { headers: headers(), params })
    } catch (e) {
      return handleErr(e, silent) as never
    }
  }

  const post = async <T = any>(path: string, body?: any, silent = false): Promise<T> => {
    try {
      return await $fetch<T>(`/api${path}`, { method: 'POST', body, headers: headers() })
    } catch (e) {
      return handleErr(e, silent) as never
    }
  }

  const put = async <T = any>(path: string, body?: any, silent = false): Promise<T> => {
    try {
      return await $fetch<T>(`/api${path}`, { method: 'PUT', body, headers: headers() })
    } catch (e) {
      return handleErr(e, silent) as never
    }
  }

  const del = async <T = any>(path: string, silent = false): Promise<T> => {
    try {
      return await $fetch<T>(`/api${path}`, { method: 'DELETE', headers: headers() })
    } catch (e) {
      return handleErr(e, silent) as never
    }
  }

  const upload = async (file: File): Promise<{ url: string; filename: string }> => {
    const form = new FormData()
    form.append('file', file)
    return $fetch('/api/media/upload', { method: 'POST', body: form, headers: headers() })
  }

  return { get, post, put, del, upload }
}
