<script setup lang="ts">
import { Inbox, Mail, Phone, CheckCircle2, RotateCcw } from 'lucide-vue-next'

useSeoMeta({ title: 'Enquiries - Admin - Infohive' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const api = useApi()
const { show } = useToast()
const rows = ref<any[]>([])
const loading = ref(true)
const filter = ref<'new' | 'handled' | ''>('new')
const open = ref<number | null>(null)

const load = async () => {
  loading.value = true
  try { rows.value = await api.get<any[]>('/admin/enquiries', filter.value ? { status: filter.value } : undefined) }
  finally { loading.value = false }
}
watch(filter, load)
onMounted(load)

const setStatus = async (e: any, status: 'new' | 'handled') => {
  await api.put(`/admin/enquiries/${e.id}`, { status })
  show(status === 'handled' ? 'Marked as handled' : 'Moved back to new', 'info')
  await load()
}
const when = (iso: string) => new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
</script>

<template>
  <div class="max-w-5xl">
    <div class="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Enquiries</h1>
        <p class="text-slate-500 text-sm mt-0.5">Messages from the website's contact form.</p>
      </div>
      <div class="inline-flex rounded-xl bg-slate-100 p-1">
        <button v-for="f in ([['new', 'New'], ['handled', 'Handled'], ['', 'All']] as const)" :key="f[0]" @click="filter = f[0]"
          class="px-3.5 py-1.5 rounded-lg text-sm font-semibold transition" :class="filter === f[0] ? 'bg-white shadow text-slate-900' : 'text-slate-500'">{{ f[1] }}</button>
      </div>
    </div>
    <div v-if="loading" class="card h-40 animate-pulse" />
    <div v-else-if="!rows.length" class="card p-10 text-center text-slate-500">
      <Inbox class="w-10 h-10 mx-auto mb-2 text-slate-300" />No {{ filter || '' }} enquiries.
    </div>
    <div v-else class="space-y-3">
      <div v-for="e in rows" :key="e.id" class="card p-4 sm:p-5">
        <button class="w-full text-left flex flex-wrap items-start gap-x-3 gap-y-1" @click="open = open === e.id ? null : e.id" :aria-expanded="open === e.id">
          <span class="badge bg-brand-50 text-brand-700">{{ e.topic }}</span>
          <span class="font-semibold text-slate-800 flex-1 min-w-0 truncate">{{ e.subject || e.message.slice(0, 70) }}</span>
          <span class="text-xs text-slate-500 whitespace-nowrap">{{ when(e.created_at) }}</span>
          <span class="w-full text-sm text-slate-500">{{ e.name }} · {{ e.email }}</span>
        </button>
        <div v-if="open === e.id" class="mt-4 border-t border-slate-100 pt-4">
          <p class="text-sm text-slate-700 whitespace-pre-wrap break-words leading-relaxed">{{ e.message }}</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <a :href="`mailto:${e.email}?subject=${encodeURIComponent('Re: ' + (e.subject || e.topic))}`" class="btn-primary text-sm"><Mail class="w-4 h-4" /> Reply by email</a>
            <a v-if="e.phone" :href="`tel:${e.phone}`" class="btn-secondary text-sm"><Phone class="w-4 h-4" /> {{ e.phone }}</a>
            <button v-if="e.status === 'new'" class="btn-secondary text-sm" @click="setStatus(e, 'handled')"><CheckCircle2 class="w-4 h-4" /> Mark handled</button>
            <button v-else class="btn-ghost text-sm" @click="setStatus(e, 'new')"><RotateCcw class="w-4 h-4" /> Mark as new</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
