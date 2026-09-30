export interface AuthUser {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'instructor' | 'student'
  avatar_url: string | null
  headline: string | null
  bio: string | null
  is_active: boolean
}

export const useAuth = () => {
  const user = useState<AuthUser | null>('auth:user', () => null)
  const { state: token, setTokens } = useAuthToken()
  const api = useApi()

  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isInstructor = computed(() => user.value?.role === 'instructor' || user.value?.role === 'admin')
  const isStudent = computed(() => user.value?.role === 'student')

  const setSession = (data: { access_token: string; refresh_token: string; user: AuthUser }) => {
    setTokens(data.access_token, data.refresh_token)
    user.value = data.user
  }

  const login = async (email: string, password: string) => {
    const res = await api.post<{ access_token: string; refresh_token: string; user: AuthUser }>('/auth/login', { email, password }, true)
    setSession(res)
    return res.user
  }

  const register = async (payload: { email: string; password: string; full_name: string; role: string }) => {
    const res = await api.post<{ access_token: string; refresh_token: string; user: AuthUser }>('/auth/register', payload, true)
    setSession(res)
    return res.user
  }

  const fetchMe = async () => {
    if (!token.value) return
    try {
      user.value = await api.get<AuthUser>('/auth/me', undefined, true)
    } catch {
      setTokens(null, null)
      user.value = null
    }
  }

  const logout = () => {
    setTokens(null, null)
    user.value = null
  }

  const homeFor = (u: AuthUser | null) => {
    if (!u) return '/'
    if (u.role === 'admin') return '/admin'
    if (u.role === 'instructor') return '/teach'
    return '/dashboard'
  }

  return { user, token, isLoggedIn, isAdmin, isInstructor, isStudent, login, register, fetchMe, logout, homeFor }
}
