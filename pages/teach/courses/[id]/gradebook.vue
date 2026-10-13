<script setup lang="ts">
import { ClipboardList, Download } from 'lucide-vue-next'

useSeoMeta({ title: 'Gradebook - Infohive' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const route = useRoute()
const api = useApi()
const { show } = useToast()
const courseId = Number(route.params.id)

const data = ref<any>(null)
const loading = ref(true)

// grading modal
const gradeForm = ref({ grade: 0, feedback: '' })
const saving = ref(false)

// submission viewer
const viewing = ref<{ open: boolean; submission?: any }>({ open: false })

const load = async () => {
  loading.value = true
  try { data.value = await api.get<any>(`/teach/courses/${courseId}/gradebook`) } finally { loading.value = false }
}
onMounted(load)

const openGrading = async (row: any, col: any) => {
  if (!col.submission_id) return
  // fetch full submission detail
  try {
    const subs = await api.get<any[]>(`/teach/assignments/${col.assignment_id}/submissions`)
    const sub = subs.find(s => s.id === col.submission_id)
    viewing.value = { open: true, submission: sub }
    if (sub?.status === 'graded') {
      gradeForm.value = { grade: sub.grade, feedback: sub.feedback || '' }
    } else {
      gradeForm.value = { grade: col.max_points, feedback: '' }
    }
  } catch { /* the api client already showed the error */ }
}

// client-side CSV of everything on screen
const exportCsv = () => {
  const d = data.value
  if (!d) return
  const esc = (v: any) => {
    const t = v === null || v === undefined ? '' : String(v)
    const safe = /^[=+\-@]/.test(t) ? `'${t}` : t   // keep spreadsheets from running formulas
    return /[",\n]/.test(safe) ? `"${safe.replace(/"/g, '""')}"` : safe
  }
  const head = ['Student', 'Email', 'Progress %',
    ...d.quiz_columns.map((q: any) => `Quiz: ${q.lesson_title}`),
    ...d.assignment_columns.map((a: any) => `${a.title} (/${a.max_points})`)]
  const rows = d.students.map((r: any) => [r.user.full_name, r.user.email, Math.round(r.progress),
    ...r.quizzes.map((q: any) => q.best_score ?? ''),
    ...r.assignments.map((a: any) => a.status === 'graded' ? a.grade : a.submission_id ? 'ungraded' : '')])
  const csv = [head, ...rows].map(r => r.map(esc).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: `gradebook-course-${courseId}.csv` })
  a.click()
  URL.revokeObjectURL(url)
}

const grade = async () => {
  saving.value = true
  try {
    await api.put(`/teach/submissions/${viewing.value.submission.id}/grade`, gradeForm.value)
    show('Graded and student notified!')
    viewing.value = { open: false }
    await load()
  } catch { /* the api client already showed the error */ } finally { saving.value = false }
}
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Gradebook</h1>
        <p class="text-slate-600 mt-1">Quiz scores and assignment grades for every enrolled student</p>
      </div>
      <button v-if="data?.students.length" class="btn-secondary" @click="exportCsv"><Download class="w-4 h-4" /> Export CSV</button>
    </div>

    <div v-if="loading" class="card h-72 animate-pulse" />

    <EmptyState v-else-if="data && data.students.length === 0" empty>No enrolled students yet.</EmptyState>

    <div v-else-if="data" class="card overflow-hidden overflow-x-auto">
      <table class="table-base">
        <thead>
          <tr>
            <th class="sticky left-0 bg-slate-50 z-10 shadow-[1px_0_0_#e2e8f0]">Student</th>
            <th class="bg-slate-50">Progress</th>
            <th v-for="q in data.quiz_columns" :key="'q' + q.quiz_id" class="bg-slate-50 min-w-[130px]">
              <span class="text-violet-600">▦</span> {{ q.lesson_title }}
            </th>
            <th v-for="a in data.assignment_columns" :key="'a' + a.id" class="bg-slate-50 min-w-[140px]">
              <ClipboardList class="w-3.5 h-3.5 inline text-amber-600" /> {{ a.title }} <span class="text-slate-500 normal-case">({{ a.max_points }})</span>
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="row in data.students" :key="row.user.id" class="group hover:bg-slate-50">
            <td class="sticky left-0 bg-white group-hover:bg-slate-50 z-10 shadow-[1px_0_0_#e2e8f0] min-w-[180px]">
              <div class="font-semibold text-slate-800">{{ row.user.full_name }}</div>
              <div class="text-xs text-slate-500">{{ row.user.email }}</div>
            </td>
            <td><b class="text-brand-700">{{ Math.round(row.progress) }}%</b></td>
            <td v-for="q in row.quizzes" :key="'q' + q.quiz_id">
              <template v-if="q.best_score !== null">
                <span class="badge" :class="q.passed ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-600'">
                  {{ q.best_score }}% {{ q.passed ? '✓' : '✗' }}
                </span>
                <span class="text-xs text-slate-500 ml-1">({{ q.attempts }}×)</span>
              </template>
              <span v-else class="text-slate-300 text-xs">-</span>
            </td>
            <td v-for="a in row.assignments" :key="'a' + a.assignment_id">
              <button v-if="a.submission_id" @click="openGrading(row, a)"
                class="badge transition hover:scale-105"
                :class="a.status === 'graded' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">
                {{ a.status === 'graded' ? `${a.grade}/${Math.round(a.max_points)}` : 'Grade →' }}
              </button>
              <span v-else class="text-slate-300 text-xs">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- submission viewer + grading -->
    <Modal :open="viewing.open" title="Submission" wide @close="viewing = { open: false }">
      <div v-if="viewing.submission" class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="font-bold text-slate-800">{{ viewing.submission.user.full_name }}</p>
            <p class="text-xs text-slate-500">Submitted {{ new Date(viewing.submission.submitted_at).toLocaleString() }}</p>
          </div>
          <span class="badge" :class="viewing.submission.status === 'graded' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">
            {{ viewing.submission.status }}
          </span>
        </div>
        <div v-if="viewing.submission.text_response" class="rounded-lg bg-slate-50 border border-slate-200 p-4 text-sm text-slate-700 whitespace-pre-wrap font-mono">{{ viewing.submission.text_response }}</div>
        <a v-if="safeUrl(viewing.submission.file_url)" :href="safeUrl(viewing.submission.file_url)" rel="noopener noreferrer" target="_blank" class="btn-secondary text-sm inline-flex">Download attachment</a>

        <div class="border-t border-slate-100 pt-4 grid sm:grid-cols-3 gap-3">
          <div>
            <label class="label" for="teach-courses-id-gra-gradeForm-grade">Grade</label>
            <input id="teach-courses-id-gra-gradeForm-grade" v-model.number="gradeForm.grade" type="number" min="0" class="input" />
          </div>
          <div class="sm:col-span-2">
            <label class="label" for="teach-courses-id-gra-gradeForm-feedback">Feedback</label>
            <input id="teach-courses-id-gra-gradeForm-feedback" v-model="gradeForm.feedback" class="input" placeholder="Great work - watch the edge cases…" />
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn-secondary" @click="viewing = { open: false }">Close</button>
          <button class="btn-primary" :disabled="saving" @click="grade">{{ saving ? 'Saving…' : 'Save grade & notify' }}</button>
        </div>
      </template>
    </Modal>
  </div>
</template>
