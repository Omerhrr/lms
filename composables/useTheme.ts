// Theme manager: persists the choice in localStorage and falls back to the
// system preference on first visit. The class on <html> is applied by an
// inline script in nuxt.config.ts before first paint (no flash of wrong mode).
type Theme = 'light' | 'dark'

export const useTheme = () => {
  const theme = useState<Theme>('lh-theme', () => 'light')

  const apply = (t: Theme) => {
    theme.value = t
    if (import.meta.client) {
      document.documentElement.classList.toggle('dark', t === 'dark')
      try { localStorage.setItem('lh-theme', t) } catch { /* private mode */ }
    }
  }

  const init = () => {
    if (!import.meta.client) return
    let stored: string | null = null
    try { stored = localStorage.getItem('lh-theme') } catch { /* private mode */ }
    const system: Theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    theme.value = stored === 'dark' || stored === 'light' ? stored : system
    document.documentElement.classList.toggle('dark', theme.value === 'dark')
  }

  const toggle = () => apply(theme.value === 'dark' ? 'light' : 'dark')

  return { theme, init, toggle, apply }
}
