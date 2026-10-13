<script setup lang="ts">
import { Save, RotateCcw, ExternalLink, Plus, Trash2, ChevronUp, ChevronDown } from 'lucide-vue-next'

useSeoMeta({ title: 'Website - Admin - Infohive' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const api = useApi()
const { show } = useToast()
const site = useSiteContent()
const platform = usePlatform()

type Section = 'home' | 'services' | 'reasons' | 'about' | 'contact' | 'social' | 'banner' | 'legal'
const tabs: { key: string; label: string; sections: Section[]; page: string }[] = [
  { key: 'home', label: 'Home page', sections: ['home', 'reasons'], page: '/' },
  { key: 'services', label: 'Services', sections: ['services'], page: '/services' },
  { key: 'about', label: 'About', sections: ['about'], page: '/about' },
  { key: 'contact', label: 'Contact & social', sections: ['contact', 'social'], page: '/contact' },
  { key: 'banner', label: 'Announcement', sections: ['banner'], page: '/' },
  { key: 'legal', label: 'Legal pages', sections: ['legal'], page: '/privacy' },
]
const tab = ref('home')
const current = computed(() => tabs.find(t => t.key === tab.value)!)

const saved = ref<Record<string, any>>({})
const form = ref<Record<string, any>>({})
const meta = ref<Record<string, any>>({})
const icons = ref<string[]>([])
const topics = ref<string[]>([])
const loading = ref(true)
const saving = ref(false)

const clone = (v: any) => JSON.parse(JSON.stringify(v))
const load = async () => {
  loading.value = true
  try {
    const r = await api.get<any>('/admin/site/content')
    saved.value = r.content; form.value = clone(r.content); meta.value = r.meta; icons.value = r.icons; topics.value = r.topics
  } finally { loading.value = false }
}
onMounted(load)

const dirty = (sections: Section[]) => sections.some(s => JSON.stringify(form.value[s]) !== JSON.stringify(saved.value[s]))
const tabDirty = computed(() => dirty(current.value.sections))
const anyDirty = computed(() => tabs.some(t => dirty(t.sections)))

const save = async () => {
  saving.value = true
  try {
    for (const s of current.value.sections) {
      if (JSON.stringify(form.value[s]) === JSON.stringify(saved.value[s])) continue
      const r = await api.put<any>(`/admin/site/content/${s}`, form.value[s])
      saved.value[s] = clone(r.value); form.value[s] = clone(r.value)
    }
    show('Published. The website shows your changes now.')
    await Promise.all([site.load(true), reloadPlatform()])
    const m = await api.get<any>('/admin/site/content'); meta.value = m.meta
  } catch { /* the API message is shown */ } finally { saving.value = false }
}
const reloadPlatform = async () => {
  try { platform.config.value = await $fetch<any>('/api/config/public') } catch { /* ignore */ }
}
const discard = () => { for (const s of current.value.sections) form.value[s] = clone(saved.value[s]) }
const resetting = ref(false)
const reset = async () => {
  resetting.value = true
  try {
    for (const s of current.value.sections) {
      const r = await api.del<any>(`/admin/site/content/${s}`)
      saved.value[s] = clone(r.value); form.value[s] = clone(r.value)
    }
    show('Restored the original text', 'info')
    await Promise.all([site.load(true), reloadPlatform()])
    const m = await api.get<any>('/admin/site/content'); meta.value = m.meta
  } finally { resetting.value = false; confirmReset.value = false }
}
const confirmReset = ref(false)
const customized = computed(() => current.value.sections.some(s => meta.value[s]?.customized))
const lastEdit = computed(() => {
  const m = current.value.sections.map(s => meta.value[s]).filter(x => x?.updated_at).sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0]
  return m ? `Last published ${new Date(m.updated_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}${m.updated_by ? ` by ${m.updated_by}` : ''}` : 'Showing the original text'
})

// list helpers (services, reasons, values)
const move = (list: any[], i: number, d: number) => { const j = i + d; if (j < 0 || j >= list.length) return; [list[i], list[j]] = [list[j], list[i]] }
const addService = () => form.value.services.items.push({ icon: 'sparkles', title: 'New service', summary: '', text: '', topic: 'General Enquiry', on_home: true })
const addCard = (list: any[]) => list.push({ icon: 'sparkles', title: 'New item', text: '' })

const switchTab = (k: string) => {
  if (tabDirty.value) return show('Publish or discard your changes on this tab first', 'error')
  tab.value = k
}
onBeforeRouteLeave(() => {
  if (anyDirty.value && !window.confirm('You have unpublished changes. Leave without publishing?')) return false
})
const emptyToNull = (html: string) => (!html || /^(<p>(\s|&nbsp;|<br\s*\/?>)*<\/p>)*$/.test(html.trim()) ? null : html)
const iconLabel = (n: string) => n.replace(/-/g, ' ')
const homeCount = computed(() => (form.value.services?.items || []).filter((i: any) => i.on_home).length)
</script>

<template>
  <div class="max-w-5xl pb-24">
    <div class="mb-6">
      <h1 class="text-2xl font-extrabold text-slate-900">Website</h1>
      <p class="text-slate-600 mt-1">Edit the text on the public website. Changes go live when you publish.</p>
    </div>

    <div v-if="loading" class="card h-64 animate-pulse" />

    <template v-else>
      <div role="tablist" aria-label="Website sections" class="flex gap-1 overflow-x-auto border-b border-slate-200 mb-6 -mx-1 px-1">
        <button v-for="t in tabs" :key="t.key" role="tab" type="button" :aria-selected="tab === t.key"
          class="relative whitespace-nowrap px-3.5 py-2.5 text-sm font-semibold border-b-2 -mb-px transition"
          :class="tab === t.key ? 'border-brand-600 text-brand-700' : 'border-transparent text-slate-600 hover:text-slate-900'" @click="switchTab(t.key)">
          {{ t.label }}<span v-if="dirty(t.sections)" class="ml-1.5 inline-block w-1.5 h-1.5 rounded-full bg-amber-500 align-middle" aria-label="unpublished changes" />
        </button>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-2 mb-5 text-sm">
        <span class="text-slate-600">{{ lastEdit }}</span>
        <div class="flex items-center gap-3">
          <button v-if="customized" type="button" class="font-semibold text-slate-600 hover:text-slate-900 inline-flex items-center gap-1" @click="confirmReset = true"><RotateCcw class="w-3.5 h-3.5" /> Restore original</button>
          <NuxtLink :to="current.page" target="_blank" class="font-semibold text-brand-700 hover:underline inline-flex items-center gap-1">View page <ExternalLink class="w-3.5 h-3.5" /></NuxtLink>
        </div>
      </div>

      <!-- HOME -->
      <div v-if="tab === 'home'" class="space-y-5">
        <section class="card p-5 sm:p-6 space-y-4">
          <h2 class="font-bold text-slate-900">Top of the page</h2>
          <div><label class="label" for="h-badge">Tagline above the headline</label><input id="h-badge" v-model="form.home.badge" maxlength="80" class="input" /></div>
          <div class="grid sm:grid-cols-2 gap-4">
            <div><label class="label" for="h-headline">Headline</label><input id="h-headline" v-model="form.home.headline" maxlength="120" class="input" /></div>
            <div><label class="label" for="h-highlight">Highlighted ending <span class="font-normal text-slate-500">(shown in green)</span></label><input id="h-highlight" v-model="form.home.highlight" maxlength="80" class="input" /></div>
          </div>
          <div><label class="label" for="h-lead">Intro sentence</label><textarea id="h-lead" v-model="form.home.lead" rows="2" maxlength="400" class="input" /></div>
          <div class="rounded-xl bg-slate-900 text-white p-5">
            <p class="text-xs uppercase tracking-wider text-slate-400 mb-2">Preview</p>
            <p class="text-xs text-brand-200">{{ form.home.badge }}</p>
            <p class="mt-1 text-2xl font-extrabold leading-tight">{{ form.home.headline }} <span class="text-brand-400">{{ form.home.highlight }}</span></p>
            <p class="mt-2 text-sm text-slate-300">{{ form.home.lead }}</p>
          </div>
        </section>
        <section class="card p-5 sm:p-6 space-y-4">
          <h2 class="font-bold text-slate-900">Learning section</h2>
          <div><label class="label" for="h-lt">Heading</label><input id="h-lt" v-model="form.home.learn_title" maxlength="120" class="input" /></div>
          <div><label class="label" for="h-lx">Text</label><textarea id="h-lx" v-model="form.home.learn_text" rows="3" maxlength="600" class="input" /></div>
        </section>
        <section class="card p-5 sm:p-6 space-y-4">
          <h2 class="font-bold text-slate-900">Services section</h2>
          <div><label class="label" for="h-st">Heading</label><input id="h-st" v-model="form.home.services_title" maxlength="120" class="input" /></div>
          <div><label class="label" for="h-sl">Text</label><textarea id="h-sl" v-model="form.home.services_lead" rows="2" maxlength="400" class="input" /></div>
          <p class="text-sm text-slate-600">The cards come from the <button type="button" class="font-semibold text-brand-700 hover:underline" @click="switchTab('services')">Services tab</button> (items marked "Show on home page").</p>
        </section>
        <section class="card p-5 sm:p-6 space-y-4">
          <h2 class="font-bold text-slate-900">"Why choose us" section</h2>
          <div><label class="label" for="h-wt">Heading</label><input id="h-wt" v-model="form.home.why_title" maxlength="120" class="input" /></div>
          <div><label class="label" for="h-wx">Text</label><textarea id="h-wx" v-model="form.home.why_text" rows="2" maxlength="400" class="input" /></div>
          <div class="space-y-3">
            <div v-for="(r, i) in form.reasons.items" :key="i" class="rounded-xl border border-slate-200 p-4 grid sm:grid-cols-[10rem_1fr_auto] gap-3">
              <div><label class="label" :for="`r-icon-${i}`">Icon</label>
                <div class="flex items-center gap-2"><SiteIcon :name="r.icon" class="w-5 h-5 text-brand-600 shrink-0" />
                  <select :id="`r-icon-${i}`" v-model="r.icon" class="input capitalize"><option v-for="ic in icons" :key="ic" :value="ic">{{ iconLabel(ic) }}</option></select></div>
              </div>
              <div class="space-y-2">
                <div><label class="label" :for="`r-title-${i}`">Title</label><input :id="`r-title-${i}`" v-model="r.title" maxlength="60" class="input" /></div>
                <div><label class="label" :for="`r-text-${i}`">Text</label><textarea :id="`r-text-${i}`" v-model="r.text" rows="2" maxlength="300" class="input" /></div>
              </div>
              <div class="flex sm:flex-col gap-1 sm:pt-6">
                <button type="button" class="btn-ghost !px-2" :disabled="i === 0" :aria-label="`Move ${r.title} up`" @click="move(form.reasons.items, i, -1)"><ChevronUp class="w-4 h-4" /></button>
                <button type="button" class="btn-ghost !px-2" :disabled="i === form.reasons.items.length - 1" :aria-label="`Move ${r.title} down`" @click="move(form.reasons.items, i, 1)"><ChevronDown class="w-4 h-4" /></button>
                <button type="button" class="btn-ghost !px-2 text-rose-600" :aria-label="`Remove ${r.title}`" @click="form.reasons.items.splice(i, 1)"><Trash2 class="w-4 h-4" /></button>
              </div>
            </div>
            <button v-if="form.reasons.items.length < 8" type="button" class="btn-secondary" @click="addCard(form.reasons.items)"><Plus class="w-4 h-4" /> Add item</button>
          </div>
        </section>
        <section class="card p-5 sm:p-6 space-y-4">
          <h2 class="font-bold text-slate-900">Closing banner</h2>
          <div><label class="label" for="h-ct">Heading</label><input id="h-ct" v-model="form.home.cta_title" maxlength="120" class="input" /></div>
          <div><label class="label" for="h-cx">Text</label><textarea id="h-cx" v-model="form.home.cta_text" rows="2" maxlength="400" class="input" /></div>
        </section>
      </div>

      <!-- SERVICES -->
      <div v-else-if="tab === 'services'" class="space-y-5">
        <section class="card p-5 sm:p-6 space-y-4">
          <h2 class="font-bold text-slate-900">Page intro</h2>
          <div><label class="label" for="s-ht">Heading</label><input id="s-ht" v-model="form.services.hero_title" maxlength="120" class="input" /></div>
          <div><label class="label" for="s-hl">Intro</label><textarea id="s-hl" v-model="form.services.hero_lead" rows="3" maxlength="500" class="input" /></div>
        </section>
        <section class="card p-5 sm:p-6 space-y-3">
          <div class="flex items-center justify-between"><h2 class="font-bold text-slate-900">Services</h2><span class="text-sm text-slate-600">{{ homeCount }} on the home page (up to 6 show)</span></div>
          <div v-for="(sv, i) in form.services.items" :key="i" class="rounded-xl border border-slate-200 p-4 space-y-3">
            <div class="grid sm:grid-cols-[10rem_1fr_auto] gap-3">
              <div><label class="label" :for="`sv-icon-${i}`">Icon</label>
                <div class="flex items-center gap-2"><SiteIcon :name="sv.icon" class="w-5 h-5 text-brand-600 shrink-0" />
                  <select :id="`sv-icon-${i}`" v-model="sv.icon" class="input capitalize"><option v-for="ic in icons" :key="ic" :value="ic">{{ iconLabel(ic) }}</option></select></div>
              </div>
              <div><label class="label" :for="`sv-title-${i}`">Name</label><input :id="`sv-title-${i}`" v-model="sv.title" maxlength="80" class="input" /></div>
              <div class="flex gap-1 sm:pt-6">
                <button type="button" class="btn-ghost !px-2" :disabled="i === 0" :aria-label="`Move ${sv.title} up`" @click="move(form.services.items, i, -1)"><ChevronUp class="w-4 h-4" /></button>
                <button type="button" class="btn-ghost !px-2" :disabled="i === form.services.items.length - 1" :aria-label="`Move ${sv.title} down`" @click="move(form.services.items, i, 1)"><ChevronDown class="w-4 h-4" /></button>
                <button type="button" class="btn-ghost !px-2 text-rose-600" :aria-label="`Remove ${sv.title}`" @click="form.services.items.splice(i, 1)"><Trash2 class="w-4 h-4" /></button>
              </div>
            </div>
            <div><label class="label" :for="`sv-sum-${i}`">Short line <span class="font-normal text-slate-500">(home page card)</span></label><input :id="`sv-sum-${i}`" v-model="sv.summary" maxlength="200" class="input" /></div>
            <div><label class="label" :for="`sv-text-${i}`">Description <span class="font-normal text-slate-500">(Services page)</span></label><textarea :id="`sv-text-${i}`" v-model="sv.text" rows="3" maxlength="600" class="input" /></div>
            <div class="grid sm:grid-cols-2 gap-3 items-end">
              <div><label class="label" :for="`sv-topic-${i}`">"Enquire" opens the contact form with</label>
                <select :id="`sv-topic-${i}`" v-model="sv.topic" class="input"><option v-for="tp in topics" :key="tp" :value="tp">{{ tp }}</option></select></div>
              <label class="flex items-center gap-2 text-sm text-slate-700 pb-2"><input v-model="sv.on_home" type="checkbox" class="rounded border-slate-300 text-brand-600" /> Show on home page</label>
            </div>
          </div>
          <button v-if="form.services.items.length < 12" type="button" class="btn-secondary" @click="addService"><Plus class="w-4 h-4" /> Add service</button>
        </section>
        <section class="card p-5 sm:p-6 space-y-4">
          <h2 class="font-bold text-slate-900">Closing banner</h2>
          <div><label class="label" for="s-ct">Heading</label><input id="s-ct" v-model="form.services.cta_title" maxlength="120" class="input" /></div>
          <div><label class="label" for="s-cx">Text</label><textarea id="s-cx" v-model="form.services.cta_text" rows="2" maxlength="400" class="input" /></div>
        </section>
      </div>

      <!-- ABOUT -->
      <div v-else-if="tab === 'about'" class="space-y-5">
        <section class="card p-5 sm:p-6 space-y-4">
          <div><label class="label" for="a-ht">Heading</label><input id="a-ht" v-model="form.about.hero_title" maxlength="120" class="input" /></div>
          <div><label class="label" for="a-hl">Intro</label><textarea id="a-hl" v-model="form.about.hero_lead" rows="3" maxlength="600" class="input" /></div>
          <div><label class="label" for="a-in">Opening statement</label><textarea id="a-in" v-model="form.about.intro" rows="3" maxlength="600" class="input" /></div>
          <div class="grid sm:grid-cols-2 gap-4">
            <div><label class="label" for="a-vi">Vision</label><textarea id="a-vi" v-model="form.about.vision" rows="4" maxlength="600" class="input" /></div>
            <div><label class="label" for="a-mi">Mission</label><textarea id="a-mi" v-model="form.about.mission" rows="4" maxlength="600" class="input" /></div>
          </div>
          <div class="grid sm:grid-cols-2 gap-4">
            <div><label class="label" for="a-wd">What we do</label><textarea id="a-wd" v-model="form.about.what_we_do" rows="4" maxlength="800" class="input" /></div>
            <div><label class="label" for="a-co">Our commitment</label><textarea id="a-co" v-model="form.about.commitment" rows="4" maxlength="800" class="input" /></div>
          </div>
        </section>
        <section class="card p-5 sm:p-6 space-y-3">
          <h2 class="font-bold text-slate-900">Core values</h2>
          <div v-for="(v, i) in form.about.values" :key="i" class="rounded-xl border border-slate-200 p-4 grid sm:grid-cols-[10rem_1fr_auto] gap-3">
            <div><label class="label" :for="`v-icon-${i}`">Icon</label>
              <div class="flex items-center gap-2"><SiteIcon :name="v.icon" class="w-5 h-5 text-brand-600 shrink-0" />
                <select :id="`v-icon-${i}`" v-model="v.icon" class="input capitalize"><option v-for="ic in icons" :key="ic" :value="ic">{{ iconLabel(ic) }}</option></select></div>
            </div>
            <div class="space-y-2">
              <div><label class="label" :for="`v-title-${i}`">Value</label><input :id="`v-title-${i}`" v-model="v.title" maxlength="60" class="input" /></div>
              <div><label class="label" :for="`v-text-${i}`">Text</label><textarea :id="`v-text-${i}`" v-model="v.text" rows="2" maxlength="300" class="input" /></div>
            </div>
            <div class="flex sm:flex-col gap-1 sm:pt-6">
              <button type="button" class="btn-ghost !px-2" :disabled="i === 0" :aria-label="`Move ${v.title} up`" @click="move(form.about.values, i, -1)"><ChevronUp class="w-4 h-4" /></button>
              <button type="button" class="btn-ghost !px-2" :disabled="i === form.about.values.length - 1" :aria-label="`Move ${v.title} down`" @click="move(form.about.values, i, 1)"><ChevronDown class="w-4 h-4" /></button>
              <button type="button" class="btn-ghost !px-2 text-rose-600" :aria-label="`Remove ${v.title}`" @click="form.about.values.splice(i, 1)"><Trash2 class="w-4 h-4" /></button>
            </div>
          </div>
          <button v-if="form.about.values.length < 8" type="button" class="btn-secondary" @click="addCard(form.about.values)"><Plus class="w-4 h-4" /> Add value</button>
        </section>
      </div>

      <!-- CONTACT + SOCIAL -->
      <div v-else-if="tab === 'contact'" class="space-y-5">
        <section class="card p-5 sm:p-6 space-y-4">
          <h2 class="font-bold text-slate-900">Contact details</h2>
          <p class="text-sm text-slate-600 -mt-2">Shown on the Contact page and in the footer. Leave a field empty to hide it.</p>
          <div class="grid sm:grid-cols-2 gap-4">
            <div><label class="label" for="c-email">Email</label><input id="c-email" v-model="form.contact.email" type="email" maxlength="255" class="input" placeholder="hello@infohive.com" /></div>
            <div><label class="label" for="c-phone">Phone</label><input id="c-phone" v-model="form.contact.phone" type="tel" maxlength="50" class="input" placeholder="+234 …" /></div>
          </div>
          <div><label class="label" for="c-addr">Address</label><textarea id="c-addr" v-model="form.contact.address" rows="2" maxlength="300" class="input" /></div>
          <div><label class="label" for="c-hours">Opening hours</label><input id="c-hours" v-model="form.contact.hours" maxlength="120" class="input" placeholder="Mon–Fri, 9am–5pm WAT" /></div>
          <p class="text-xs text-slate-500">Contact-form messages are emailed to the address set on the server (ENQUIRY_NOTIFY_EMAIL), and always appear under Enquiries.</p>
        </section>
        <section class="card p-5 sm:p-6 space-y-4">
          <h2 class="font-bold text-slate-900">Contact page intro</h2>
          <div><label class="label" for="c-ht">Heading</label><input id="c-ht" v-model="form.contact.hero_title" maxlength="120" class="input" /></div>
          <div><label class="label" for="c-hl">Intro</label><textarea id="c-hl" v-model="form.contact.hero_lead" rows="2" maxlength="400" class="input" /></div>
        </section>
        <section class="card p-5 sm:p-6 space-y-4">
          <h2 class="font-bold text-slate-900">Social media</h2>
          <div class="grid sm:grid-cols-2 gap-4">
            <div v-for="k in ['facebook', 'linkedin', 'instagram', 'x', 'youtube']" :key="k">
              <label class="label capitalize" :for="`so-${k}`">{{ k === 'x' ? 'X (Twitter)' : k === 'linkedin' ? 'LinkedIn' : k === 'youtube' ? 'YouTube' : k }}</label>
              <input :id="`so-${k}`" v-model="form.social[k]" type="url" maxlength="300" class="input" :placeholder="`https://${k === 'x' ? 'x' : k}.com/…`" />
            </div>
          </div>
        </section>
      </div>

      <!-- BANNER -->
      <div v-else-if="tab === 'banner'" class="space-y-5">
        <section class="card p-5 sm:p-6 space-y-4">
          <h2 class="font-bold text-slate-900">Announcement bar</h2>
          <p class="text-sm text-slate-600 -mt-2">A thin bar across the top of every public page, for news like a new cohort or a holiday closure. Visitors can dismiss it.</p>
          <label class="flex items-center gap-2 text-sm font-semibold text-slate-800"><input v-model="form.banner.enabled" type="checkbox" class="rounded border-slate-300 text-brand-600" /> Show the announcement</label>
          <div><label class="label" for="b-text">Message</label><input id="b-text" v-model="form.banner.text" maxlength="200" class="input" placeholder="Our next cohort starts 3 November - places are limited." /></div>
          <div class="grid sm:grid-cols-2 gap-4">
            <div><label class="label" for="b-label">Link text <span class="font-normal text-slate-500">(optional)</span></label><input id="b-label" v-model="form.banner.link_label" maxlength="40" class="input" placeholder="See courses" /></div>
            <div><label class="label" for="b-url">Link to</label><input id="b-url" v-model="form.banner.link_url" maxlength="300" class="input" placeholder="/courses or https://…" /></div>
          </div>
          <fieldset><legend class="label">Colour</legend>
            <div class="flex gap-2">
              <label v-for="tn in [{ k: 'brand', l: 'Green', c: 'bg-brand-700' }, { k: 'amber', l: 'Amber', c: 'bg-amber-400' }, { k: 'slate', l: 'Dark', c: 'bg-slate-900' }]" :key="tn.k"
                class="flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer text-sm" :class="form.banner.tone === tn.k ? 'border-brand-500 bg-brand-50' : 'border-slate-200'">
                <input v-model="form.banner.tone" type="radio" :value="tn.k" class="sr-only" /><span class="w-4 h-4 rounded-full" :class="tn.c" /> {{ tn.l }}
              </label>
            </div>
          </fieldset>
          <div>
            <p class="text-xs uppercase tracking-wider text-slate-500 mb-1.5">Preview</p>
            <div class="rounded-lg text-sm px-4 py-2 text-center" :class="{ brand: 'bg-brand-700 text-white', amber: 'bg-amber-400 text-amber-950', slate: 'bg-slate-900 text-white' }[form.banner.tone as string]">
              {{ form.banner.text || 'Your message' }} <b v-if="form.banner.link_label" class="underline ml-1">{{ form.banner.link_label }} →</b>
            </div>
          </div>
        </section>
      </div>

      <!-- LEGAL -->
      <div v-else-if="tab === 'legal'" class="space-y-5">
        <div class="rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-sm p-4">
          Until you publish your own text, the Privacy Policy and Terms pages show a built-in draft marked "Draft". Have the final wording reviewed by your legal adviser.
        </div>
        <section class="card p-5 sm:p-6 space-y-4">
          <div><label class="label" for="l-up">"Last updated" date</label><input id="l-up" v-model="form.legal.updated" maxlength="40" class="input sm:w-64" placeholder="1 November 2026" /></div>
          <div>
            <div class="flex items-center justify-between mb-1"><span class="label !mb-0">Privacy Policy</span><NuxtLink to="/privacy" target="_blank" class="text-sm font-semibold text-brand-700 hover:underline">View</NuxtLink></div>
            <ClientOnly><RichEditor :model-value="form.legal.privacy_html || ''" placeholder="Paste or write your privacy policy…" @update:model-value="form.legal.privacy_html = emptyToNull($event)" /></ClientOnly>
          </div>
          <div>
            <div class="flex items-center justify-between mb-1"><span class="label !mb-0">Terms & Conditions</span><NuxtLink to="/terms" target="_blank" class="text-sm font-semibold text-brand-700 hover:underline">View</NuxtLink></div>
            <ClientOnly><RichEditor :model-value="form.legal.terms_html || ''" placeholder="Paste or write your terms…" @update:model-value="form.legal.terms_html = emptyToNull($event)" /></ClientOnly>
          </div>
        </section>
      </div>

      <!-- publish bar -->
      <div v-if="tabDirty" class="fixed bottom-0 inset-x-0 lg:left-64 z-30 bg-white border-t border-slate-200 shadow-[0_-4px_16px_rgba(0,0,0,.06)]">
        <div class="max-w-5xl px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-3">
          <span class="text-sm text-slate-700">You have unpublished changes.</span>
          <div class="flex gap-2">
            <button class="btn-secondary" :disabled="saving" @click="discard">Discard</button>
            <button class="btn-primary" :disabled="saving" @click="save"><Save class="w-4 h-4" /> {{ saving ? 'Publishing…' : 'Publish changes' }}</button>
          </div>
        </div>
      </div>
    </template>

    <Modal :open="confirmReset" title="Restore the original text?" @close="confirmReset = false">
      <p class="text-slate-700">Your edits on the <b>{{ current.label }}</b> tab are replaced with the original launch text. This can't be undone.</p>
      <template #footer>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn-secondary" @click="confirmReset = false">Cancel</button>
          <button class="btn-danger" :disabled="resetting" @click="reset">Restore original</button>
        </div>
      </template>
    </Modal>
  </div>
</template>
