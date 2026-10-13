<script setup lang="ts">
import { Search, ExternalLink, Download, Ban, RotateCcw } from 'lucide-vue-next'

useSeoMeta({ title: 'Certificates - Admin - Infohive' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const api = useApi()
const { show } = useToast()
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const loading = ref(true)
const search = ref('')
const status = ref('')

const load = async () => {
  loading.value = true
  try {
    const r = await api.get<any>('/admin/certificates', { search: search.value || undefined, status: status.value || undefined, page: page.value })
    items.value = r.items; total.value = r.total; pages.value = r.pages
  } finally { loading.value = false }
}
let t: ReturnType<typeof setTimeout> | undefined
watch([search, status], () => { page.value = 1; clearTimeout(t); t = setTimeout(load, 300) })
watch(page, load)
onMounted(load)

const openPdf = (serial: string) => { window.open(`/api/certificates/${serial}/pdf`, '_blank', 'noopener') }
const fmt = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
const revoking = ref<{ cert: any; reason: string; saving: boolean } | null>(null)
const revoke = async () => {
  const r = revoking.value
  if (!r || r.reason.trim().length < 3) return show('Give a short reason (it is shown on the verification page)', 'error')
  r.saving = true
  try {
    await api.post(`/admin/certificates/${r.cert.id}/revoke`, { reason: r.reason.trim() })
    show('Certificate revoked', 'info'); revoking.value = null; await load()
  } catch { r.saving = false }
}
const restore = async (c: any) => {
  try { await api.post(`/admin/certificates/${c.id}/restore`); show('Certificate restored'); await load() } catch { /* toast */ }
}
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-extrabold text-slate-900">Certificates</h1>
      <p class="text-slate-600 mt-1">{{ total }} certificate{{ total === 1 ? '' : 's' }}. Look one up by serial, learner or course.</p>
    </div>

    <div class="card p-3 sm:p-4 mb-4 grid sm:grid-cols-[1fr_auto] gap-3">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input v-model="search" aria-label="Search certificates" placeholder="Serial (LH-…), learner or course…" class="input pl-9" />
      </div>
      <select v-model="status" aria-label="Status" class="input sm:w-40">
        <option value="">All</option><option value="valid">Valid</option><option value="revoked">Revoked</option>
      </select>
    </div>

    <div class="card overflow-x-auto">
      <table class="table-base">
        <thead><tr><th>Serial</th><th>Learner</th><th>Course</th><th>Issued</th><th>Status</th><th><span class="sr-only">Actions</span></th></tr></thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="loading"><td colspan="6"><div class="h-20 animate-pulse bg-slate-50 rounded-lg" /></td></tr>
          <tr v-else-if="!items.length"><td colspan="6" class="text-center text-slate-500 py-10">No certificates match.</td></tr>
          <tr v-for="c in items" v-else :key="c.id" class="hover:bg-slate-50">
            <td class="font-mono text-sm whitespace-nowrap">{{ c.serial }}</td>
            <td class="font-semibold text-slate-900">{{ c.user_name }}</td>
            <td class="text-sm min-w-[10rem]">{{ c.course_title }}</td>
            <td class="text-sm whitespace-nowrap">{{ fmt(c.issued_at) }}</td>
            <td>
              <span v-if="c.revoked_at" class="badge bg-rose-50 text-rose-700" :title="c.revoke_reason">Revoked</span>
              <span v-else class="badge bg-brand-50 text-brand-700">Valid</span>
            </td>
            <td class="text-right">
              <RowMenu :label="`Actions for ${c.serial}`" :items="[
                { label: 'Open verification page', icon: ExternalLink, action: () => navigateTo(`/certificates/${c.serial}`) },
                { label: 'Download PDF', icon: Download, disabled: !!c.revoked_at, action: () => openPdf(c.serial) },
                c.revoked_at
                  ? { label: 'Restore certificate', icon: RotateCcw, action: () => restore(c) }
                  : { label: 'Revoke…', icon: Ban, danger: true, action: () => { revoking = { cert: c, reason: '', saving: false } } },
              ]" />
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="pages > 1" class="flex justify-center gap-1.5 py-4 border-t border-slate-100">
        <button v-for="p in pages" :key="p" class="w-9 h-9 rounded-lg text-sm font-semibold" :aria-label="`Page ${p}`" :aria-current="p === page ? 'page' : undefined"
          :class="p === page ? 'bg-brand-600 text-white' : 'border border-slate-200 text-slate-600 hover:bg-slate-50'" @click="page = p">{{ p }}</button>
      </div>
    </div>

    <Modal :open="!!revoking" :title="`Revoke ${revoking?.cert.serial}?`" @close="revoking = null">
      <p class="text-slate-700">Anyone checking <b>{{ revoking?.cert.user_name }}</b>'s certificate for <b>{{ revoking?.cert.course_title }}</b> will see that it was revoked, with your reason. The PDF can no longer be downloaded. You can restore it later.</p>
      <label class="label mt-4" for="revoke-reason">Reason</label>
      <input v-if="revoking" id="revoke-reason" v-model="revoking.reason" maxlength="500" class="input" placeholder="e.g. Issued in error" />
      <template #footer>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn-secondary" @click="revoking = null">Cancel</button>
          <button class="btn-danger" :disabled="revoking?.saving" @click="revoke">Revoke certificate</button>
        </div>
      </template>
    </Modal>
  </div>
</template>
