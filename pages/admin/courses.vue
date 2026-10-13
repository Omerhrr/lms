<script setup lang="ts">
import { Search, Settings, ListTree, Users, BarChart3, ExternalLink, UserCog, Rocket, Undo2, Archive, Plus } from 'lucide-vue-next'

useSeoMeta({ title: 'Courses - Admin - Infohive' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const api = useApi()
const { show } = useToast()
const { money, config } = usePlatform()

const items = ref<any[]>([])
const counts = ref<Record<string, number>>({})
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const loading = ref(true)
const search = ref('')
const status = ref(['draft', 'published', 'archived'].includes(String(useRoute().query.status)) ? String(useRoute().query.status) : '')

const load = async () => {
  loading.value = true
  try {
    const r = await api.get<any>('/admin/courses', { search: search.value || undefined, status: status.value || undefined, page: page.value, size: 20 })
    items.value = r.items; total.value = r.total; pages.value = r.pages; counts.value = r.counts || {}
  } finally { loading.value = false }
}
let t: ReturnType<typeof setTimeout> | undefined
watch([search, status], () => { page.value = 1; clearTimeout(t); t = setTimeout(load, 300) })
watch(page, load)
onMounted(load)

const tabs = computed(() => [
  { key: '', label: 'All', n: Object.values(counts.value).reduce((a, b) => a + b, 0) },
  { key: 'published', label: 'Published', n: counts.value.published || 0 },
  { key: 'draft', label: 'Drafts', n: counts.value.draft || 0 },
  { key: 'archived', label: 'Archived', n: counts.value.archived || 0 },
])
const statusClass: Record<string, string> = {
  published: 'bg-brand-50 text-brand-700', draft: 'bg-slate-100 text-slate-700', archived: 'bg-rose-50 text-rose-700',
}

const setStatus = async (c: any, action: 'publish' | 'unpublish' | 'archive') => {
  try {
    await api.post(`/teach/courses/${c.id}/${action}`)
    show(action === 'publish' ? `${c.title} is live` : action === 'unpublish' ? `${c.title} moved to drafts` : `${c.title} archived`)
    await load()
  } catch { /* toast shown */ }
}

// reassign instructor
const instructors = ref<any[]>([])
const reassign = ref<{ open: boolean; course?: any; to: number | null; saving: boolean }>({ open: false, to: null, saving: false })
const openReassign = async (c: any) => {
  reassign.value = { open: true, course: c, to: c.instructor?.id ?? null, saving: false }
  if (!instructors.value.length) instructors.value = await api.get<any[]>('/admin/instructors')
}
const saveReassign = async () => {
  const r = reassign.value
  if (!r.course || !r.to) return
  r.saving = true
  try {
    const res = await api.put<any>(`/admin/courses/${r.course.id}/instructor`, { instructor_id: r.to })
    show(res.message)
    reassign.value = { open: false, to: null, saving: false }
    await load()
  } catch { r.saving = false }
}
const showRevenue = computed(() => config.value.payments_enabled || items.value.some(i => i.revenue > 0))
</script>

<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Courses</h1>
        <p class="text-slate-600 mt-1">Every course on the platform, from every instructor.</p>
      </div>
      <NuxtLink to="/teach/courses/new" class="btn-primary"><Plus class="w-4 h-4" /> New course</NuxtLink>
    </div>

    <div class="flex flex-wrap items-center gap-3 mb-4">
      <div role="tablist" aria-label="Filter by status" class="flex flex-wrap gap-1 rounded-xl bg-slate-100 p-1">
        <button v-for="tb in tabs" :key="tb.key" role="tab" :aria-selected="status === tb.key" type="button"
          class="px-3 py-1.5 rounded-lg text-sm font-semibold transition"
          :class="status === tb.key ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'" @click="status = tb.key">
          {{ tb.label }} <span class="text-slate-500 font-normal">{{ tb.n }}</span>
        </button>
      </div>
      <div class="relative flex-1 min-w-[12rem] sm:max-w-xs sm:ml-auto">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input v-model="search" aria-label="Search courses" placeholder="Search courses…" class="input pl-9" />
      </div>
    </div>

    <div class="card overflow-x-auto">
      <table class="table-base">
        <thead><tr>
          <th>Course</th><th>Instructor</th><th>Status</th><th class="text-right">Learners</th><th class="text-right">Completion</th>
          <th v-if="showRevenue" class="text-right">Revenue</th><th><span class="sr-only">Actions</span></th>
        </tr></thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="loading"><td colspan="7"><div class="h-24 animate-pulse bg-slate-50 rounded-lg" /></td></tr>
          <tr v-else-if="!items.length"><td colspan="7" class="text-center text-slate-500 py-10">No courses match.</td></tr>
          <tr v-for="c in items" v-else :key="c.id" class="hover:bg-slate-50">
            <td class="min-w-[14rem]">
              <NuxtLink :to="`/teach/courses/${c.id}/edit`" class="font-semibold text-slate-900 hover:text-brand-700">{{ c.title }}</NuxtLink>
              <div class="text-xs text-slate-500">{{ c.category || 'Uncategorized' }} · {{ money(c.price) }}</div>
            </td>
            <td class="text-sm whitespace-nowrap">{{ c.instructor?.full_name || '-' }}</td>
            <td><span class="badge capitalize" :class="statusClass[c.status]">{{ c.status }}</span></td>
            <td class="text-right tabular-nums">{{ c.enrollments }}</td>
            <td class="text-right tabular-nums whitespace-nowrap">
              <span v-if="c.enrollments">{{ c.completion_rate }}% <span class="text-xs text-slate-500">({{ c.completions }})</span></span>
              <span v-else class="text-slate-400">-</span>
            </td>
            <td v-if="showRevenue" class="text-right tabular-nums font-semibold">{{ c.revenue ? money(c.revenue) : '-' }}</td>
            <td class="text-right">
              <RowMenu :label="`Actions for ${c.title}`" :items="[
                { label: 'Course settings', icon: Settings, action: () => navigateTo(`/teach/courses/${c.id}/edit`) },
                { label: 'Curriculum', icon: ListTree, action: () => navigateTo(`/teach/courses/${c.id}/builder`) },
                { label: 'Learners', icon: Users, action: () => navigateTo(`/admin/enrollments?course_id=${c.id}`) },
                { label: 'Analytics', icon: BarChart3, action: () => navigateTo(`/teach/courses/${c.id}/analytics`) },
                { label: 'View public page', icon: ExternalLink, disabled: c.status !== 'published', action: () => navigateTo(`/courses/${c.slug}`) },
                { label: 'Change instructor…', icon: UserCog, action: () => openReassign(c) },
                ...(c.status !== 'published' ? [{ label: 'Publish', icon: Rocket, action: () => setStatus(c, 'publish') }] : [{ label: 'Move to drafts', icon: Undo2, action: () => setStatus(c, 'unpublish') }]),
                ...(c.status !== 'archived' ? [{ label: 'Archive', icon: Archive, danger: true, action: () => setStatus(c, 'archive') }] : []),
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

    <Modal :open="reassign.open" :title="`Change instructor: ${reassign.course?.title || ''}`" @close="reassign.open = false">
      <label class="label" for="re-instructor">New instructor</label>
      <select id="re-instructor" v-model="reassign.to" class="input">
        <option v-for="i in instructors" :key="i.id" :value="i.id">{{ i.full_name }} · {{ i.email }}{{ i.role === 'admin' ? ' (admin)' : '' }}</option>
      </select>
      <p class="text-sm text-slate-600 mt-3">They take over the curriculum, grading, live classes and announcements. Learners, progress and certificates aren't affected. Both instructors are notified.</p>
      <template #footer>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn-secondary" @click="reassign.open = false">Cancel</button>
          <button class="btn-primary" :disabled="reassign.saving || reassign.to === reassign.course?.instructor?.id" @click="saveReassign">
            {{ reassign.saving ? 'Saving…' : 'Change instructor' }}
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
