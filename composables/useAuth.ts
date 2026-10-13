export interface AuthUser {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'instructor' | 'student'
  avatar_url: string | null
  headline: string | null
  bio: string | null
  is_active: boolean
  instructor_requested?: boolean
}

// Shared in-flight /auth/me promise (module scope = shared across all useAuth() callers)
let pendingMe: Promise<void> | null = null

/**
 * Session state. The tokens themselves are HttpOnly cookies owned by the API - nothing here
 * can read them. `lh_session` is a non-secret hint cookie meaning "a session may exist".
 */
export const useAuth = () => {
  const user = useState<AuthUser | null>('auth:user', () => null)
  const hint = useCookie<string | null>('lh_session', { readonly: true })
  const api = useApi()

  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isInstructor = computed(() => user.value?.role === 'instructor' || user.value?.role === 'admin')
  const isStudent = computed(() => user.value?.role === 'student')
  const hasSession = computed(() => !!hint.value || !!user.value)

  const login = async (email: string, password: string) => {
    const res = await api.post<{ user: AuthUser }>('/auth/login', { email, password }, true)
    user.value = res.user
    return res.user
  }

  const register = async (payload: { email: string; password: string; full_name: string; role: string }) => {
    const res = await api.post<{ user: AuthUser }>('/auth/register', payload, true)
    user.value = res.user
    return res.user
  }

  const fetchMe = async () => {
    if (user.value) return
    if (!hint.value && import.meta.client && !document.cookie.includes('lh_session=')) return
    if (pendingMe) return pendingMe
    pendingMe = (async () => {
      try {
        user.value = await api.get<AuthUser>('/auth/me', undefined, true)
      } catch {
        // access cookie expired: rotate once with the refresh cookie, then retry
        if (import.meta.client && (await api.tryRefresh())) {
          try { user.value = await api.get<AuthUser>('/auth/me', undefined, true) } catch { user.value = null }
        } else {
          user.value = null
        }
      } finally {
        pendingMe = null
      }
    })()
    return pendingMe
  }

  const logout = async () => {
    user.value = null
    try { await api.post('/auth/logout', undefined, true) } catch { /* cookies may already be gone */ }
  }

  const homeFor = (u: AuthUser | null) => {
    if (!u) return '/'
    if (u.role === 'admin') return '/admin'
    if (u.role === 'instructor') return '/teach'
    return '/dashboard'
  }

  return { user, isLoggedIn, hasSession, isAdmin, isInstructor, isStudent, login, register, fetchMe, logout, homeFor }
}
