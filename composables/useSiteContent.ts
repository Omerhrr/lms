/** Admin-editable website copy (Admin → Website). Loaded once per visit; the API always fills in defaults. */
export interface SiteCard { icon: string; title: string; text: string }
export interface SiteService extends SiteCard { summary: string; topic: string; on_home: boolean }
export interface SiteContent {
  home: Record<string, string>
  services: { hero_title: string; hero_lead: string; items: SiteService[]; cta_title: string; cta_text: string }
  reasons: { items: SiteCard[] }
  about: { hero_title: string; hero_lead: string; intro: string; vision: string; mission: string; values: SiteCard[]; what_we_do: string; commitment: string }
  contact: { email: string; phone: string; address: string; hours: string; hero_title: string; hero_lead: string }
  social: Record<string, string>
  banner: { enabled: boolean; text?: string; link_label?: string; link_url?: string; tone?: 'brand' | 'amber' | 'slate' }
  legal: { privacy_html: string | null; terms_html: string | null; updated: string }
}

let loading: Promise<void> | null = null

export const useSiteContent = () => {
  const content = useState<SiteContent | null>('site:content', () => null)
  const load = (force = false) => {
    if (content.value && !force) return Promise.resolve()
    if (!loading) {
      loading = $fetch<SiteContent>('/api/site/content')
        .then((c) => { content.value = c })
        .catch(() => { /* pages keep their built-in fallbacks */ })
        .finally(() => { loading = null })
    }
    return loading
  }
  return { content, load }
}
