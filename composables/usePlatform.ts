/** Public, non-secret platform settings (payments on/off, currency), loaded once. */
interface PlatformConfig {
  payments_enabled: boolean
  currency: string
  contact?: { email?: string; phone?: string; address?: string; hours?: string }
  social?: Record<string, string>
  enquiry_topics?: string[]
}

let loading: Promise<void> | null = null

export const usePlatform = () => {
  const config = useState<PlatformConfig>('platform:config', () => ({ payments_enabled: false, currency: 'NGN', contact: {}, social: {}, enquiry_topics: [] }))
  const loaded = useState<boolean>('platform:loaded', () => false)

  const load = () => {
    if (loaded.value) return Promise.resolve()
    if (!loading) {
      loading = $fetch<PlatformConfig>('/api/config/public')
        .then((c) => { config.value = c; loaded.value = true })
        .catch(() => { /* keep defaults */ })
        .finally(() => { loading = null })
    }
    return loading
  }

  const money = (amount: number | null | undefined) => {
    if (!amount) return 'Free'
    try {
      return new Intl.NumberFormat(undefined, { style: 'currency', currencyDisplay: 'narrowSymbol', currency: config.value.currency, maximumFractionDigits: 2 }).format(amount)
    } catch {
      return `${config.value.currency} ${amount.toFixed(2)}`
    }
  }

  return { config, load, money }
}
