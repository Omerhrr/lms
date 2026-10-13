<script setup lang="ts">
import { Search, UserPlus, Trash2, ExternalLink } from 'lucide-vue-next'

useSeoMeta({ title: 'Enrollments - Admin - Infohive' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const route = useRoute()
const router = useRouter()
const api = useApi()
const { show } = useToast()

const courses = ref<any[]>([])
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const loading = ref(true)
const courseId = ref<number | null>(route.query.course_id ? Number(route.query.course_id) : null)
const search = ref('')
const status = ref('')

const load = async () => {
  loading.value = true
  try {
    const r = await api.get<any>('/admin/enrollments', {
      course_id: courseId.value || undefined, search: search.value || undefined, status: status.value || undefined, page: page.value, size: 25,
    })
    items.value = r.items; total.value = r.total; pages.value = r.pages
  } finally { loading.value = false }
}
let t: ReturnType<typeof setTimeout> | undefined
watch([courseId, search, status], () => {
  page.value = 1
  router.replace({ query: courseId.value ? { course_id: String(courseId.value) } : {} })
  clearTimeout(t); t = setTimeout(load, 300)
})
watch(page, load)
onMounted(async () => {
  load()
  try { courses.value = (await api.get<any>('/admin/courses', { size: 100 })).items } catch { /* ignore */ }
})

const ago = (iso: string | null) => {
  if (!iso) return 'Not started'
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000)
  return d <= 0 ? 'Today' : d === 1 ? 'Yesterday' : `${d} days ago`
}
const dateLong = (iso: string) => new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })

// remove, with confirmation (progress is deleted)
const removing = ref<any | null>(null)
const confirmRemove = async () => {
  const e = removing.value
  if (!e) return
  try {
    const r = await api.del<any>(`/admin/enrollments/${e.id}`)
    show(r.message, 'info')
    removing.value = null
    await load()
  } catch { /* toast shown */ }
}

// add learners by email
const adding = ref({ open: false, course_id: null as number | null, emails: '', notify: true, saving: false })
const result = ref<any | null>(null)
const openAdd = () => { adding.value = { open: true, course_id: courseId.value, emails: '', notify: true, saving: false }; result.value = null }
const parsedEmails = computed(() => [...new Set(adding.value.emails.split(/[\s,;]+/).map(e => e.trim().toLowerCase()).filter(e => /^\S+@\S+\.\S+$/.test(e)))])
const submitAdd = async () => {
  const a = adding.value
  if (!a.course_id) return show('Choose a course', 'error')
  if (!parsedEmails.value.length) return show('Add at least one email address', 'error')
  a.saving = true
  try {
    result.value = await api.post<any>('/admin/enrollments', { course_id: a.course_id, emails: parsedEmails.value, notify: a.notify })
    if (result.value.enrolled.length) show(`${plural(result.value.enrolled.length, 'learner')} enrolled`)
    await load()
  } catch { /* toast shown */ } finally { a.saving = false }
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Enrollments</h1>
        <p class="text-slate-600 mt-1">{{ total }} enrollment{{ total === 1 ? '' : 's' }}{{ courseId ? ' in this course' : ' across all courses' }}</p>
      </div>
      <button class="btn-primary" @click="openAdd"><UserPlus class="w-4 h-4" /> Enroll learners</button>
    </div>

    <div class="card p-3 sm:p-4 mb-4 grid sm:grid-cols-[1fr_1fr_auto] gap-3">
      <select v-model="courseId" aria-label="Course" class="input">
        <option :value="null">All courses</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.title }}</option>
      </select>
      <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input v-model="search" aria-label="Search learners" placeholder="Search learner name or email…" class="input pl-9" />
      </div>
      <select v-model="status" aria-label="Status" class="input sm:w-40">
        <option value="">Any status</option>
        <option value="active">In progress</option>
        <option value="completed">Completed</option>
      </select>
    </div>

    <div class="card overflow-x-auto">
      <table class="table-base">
        <thead><tr><th>Learner</th><th v-if="!courseId">Course</th><th>Progress</th><th>Last active</th><th>Enrolled</th><th><span class="sr-only">Actions</span></th></tr></thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="loading"><td colspan="6"><div class="h-24 animate-pulse bg-slate-50 rounded-lg" /></td></tr>
          <tr v-else-if="!items.length"><td colspan="6" class="text-center text-slate-500 py-10">No enrollments match.</td></tr>
          <tr v-for="e in items" v-else :key="e.id" class="hover:bg-slate-50">
            <td><div class="font-semibold text-slate-900">{{ e.user.full_name }}</div><div class="text-xs text-slate-500">{{ e.user.email }}</div></td>
            <td v-if="!courseId" class="text-sm min-w-[10rem]">{{ e.course.title }}</td>
            <td class="min-w-[9rem]">
              <div class="flex items-center gap-2">
                <div class="h-2 w-20 rounded-full bg-slate-100 overflow-hidden"><div class="h-full rounded-full" :class="e.status === 'completed' ? 'bg-amber-500' : 'bg-brand-500'" :style="`width:${e.progress}%`" /></div>
                <span class="text-sm tabular-nums">{{ Math.round(e.progress) }}%</span>
              </div>
              <span v-if="e.status === 'completed'" class="text-xs font-semibold text-amber-700">Completed</span>
            </td>
            <td class="text-sm whitespace-nowrap"><time v-if="e.last_active" :datetime="e.last_active" :title="dateLong(e.last_active)">{{ ago(e.last_active) }}</time><span v-else class="text-slate-500">Not started</span></td>
            <td class="text-sm whitespace-nowrap"><time :datetime="e.enrolled_at" :title="dateLong(e.enrolled_at)">{{ ago(e.enrolled_at) }}</time></td>
            <td class="text-right">
              <RowMenu :label="`Actions for ${e.user.full_name}`" :items="[
                { label: 'Open course', icon: ExternalLink, action: () => navigateTo(`/teach/courses/${e.course.id}/students`) },
                { label: 'Remove enrollment…', icon: Trash2, danger: true, action: () => { removing = e } },
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

    <!-- remove -->
    <Modal :open="!!removing" title="Remove enrollment?" @close="removing = null">
      <p class="text-slate-700">
        <b>{{ removing?.user.full_name }}</b> will lose access to <b>{{ removing?.course.title }}</b>, and their lesson progress
        ({{ Math.round(removing?.progress || 0) }}%) will be deleted. A certificate they already earned stays valid.
      </p>
      <template #footer>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn-secondary" @click="removing = null">Cancel</button>
          <button class="btn-danger" @click="confirmRemove">Remove enrollment</button>
        </div>
      </template>
    </Modal>

    <!-- add -->
    <Modal :open="adding.open" title="Enroll learners" wide @close="adding.open = false">
      <div class="space-y-4">
        <div>
          <label class="label" for="add-course">Course</label>
          <select id="add-course" v-model="adding.course_id" class="input">
            <option :value="null" disabled>Choose a course…</option>
            <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.title }}{{ c.status !== 'published' ? ` (${c.status})` : '' }}</option>
          </select>
        </div>
        <div>
          <label class="label" for="add-emails">Learner emails</label>
          <textarea id="add-emails" v-model="adding.emails" rows="5" class="input font-mono text-sm" placeholder="one@example.com&#10;two@example.com" />
          <p class="text-xs text-slate-600 mt-1">Paste emails separated by new lines, commas or spaces. Learners need an account first. {{ parsedEmails.length ? `${plural(parsedEmails.length, 'valid address', 'valid addresses')}.` : '' }}</p>
        </div>
        <label class="flex items-center gap-2 text-sm text-slate-700">
          <input v-model="adding.notify" type="checkbox" class="rounded border-slate-300 text-brand-600" /> Email and notify each learner
        </label>
        <div v-if="result" class="rounded-xl border border-slate-200 p-4 text-sm space-y-1.5" role="status">
          <p v-if="result.enrolled.length" class="text-brand-700"><b>{{ result.enrolled.length }}</b> enrolled.</p>
          <p v-if="result.already.length" class="text-slate-700"><b>{{ result.already.length }}</b> already enrolled: {{ result.already.join(', ') }}</p>
          <p v-if="result.not_found.length" class="text-amber-700"><b>{{ result.not_found.length }}</b> have no account yet: {{ result.not_found.join(', ') }}</p>
          <p v-if="result.not_allowed.length" class="text-rose-700"><b>{{ result.not_allowed.length }}</b> can't be enrolled (staff or deactivated): {{ result.not_allowed.join(', ') }}</p>
        </div>
      </div>
      <template #footer>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn-secondary" @click="adding.open = false">{{ result ? 'Done' : 'Cancel' }}</button>
          <button class="btn-primary" :disabled="adding.saving" @click="submitAdd">{{ adding.saving ? 'Enrolling…' : 'Enroll' }}</button>
        </div>
      </template>
    </Modal>
  </div>
</template>
