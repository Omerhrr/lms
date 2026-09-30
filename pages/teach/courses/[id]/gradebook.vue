<script setup lang="ts">
import { ClipboardList } from 'lucide-vue-next'

useSeoMeta({ title: 'Gradebook - LearnHub' })
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
    <div class="mb-6">
      <h1 class="text-2xl font-extrabold text-slate-900">Gradebook</h1>
      <p class="text-slate-500 mt-1">Quiz scores and assignment grades for every enrolled student</p>
    </div>

    <div v-if="loading" class="card h-72 animate-pulse" />

    <EmptyState v-else-if="data && data.students.length === 0" empty>No enrolled students yet.</EmptyState>

    <div v-else-if="data" class="card overflow-hidden overflow-x-auto">
      <table class="table-base">
        <thead>
          <tr>
            <th class="sticky left-0 bg-slate-50 z-10">Student</th>
            <th class="bg-slate-50">Progress</th>
            <th v-for="q in data.quiz_columns" :key="'q' + q.quiz_id" class="bg-slate-50 min-w-[130px]">
              <span class="text-violet-600">▦</span> {{ q.lesson_title }}
            </th>
            <th v-for="a in data.assignment_columns" :key="'a' + a.id" class="bg-slate-50 min-w-[140px]">
              <ClipboardList class="w-3.5 h-3.5 inline text-amber-600" /> {{ a.title }} <span class="text-slate-400 normal-case">({{ a.max_points }})</span>
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="row in data.students" :key="row.user.id" class="hover:bg-slate-50">
            <td class="sticky left-0 bg-white z-10">
              <div class="font-semibold text-slate-800">{{ row.user.full_name }}</div>
              <div class="text-xs text-slate-400">{{ row.user.email }}</div>
            </td>
            <td><b class="text-brand-700">{{ Math.round(row.progress) }}%</b></td>
            <td v-for="q in row.quizzes" :key="'q' + q.quiz_id">
              <template v-if="q.best_score !== null">
                <span class="badge" :class="q.passed ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-600'">
                  {{ q.best_score }}% {{ q.passed ? '✓' : '✗' }}
                </span>
                <span class="text-[10px] text-slate-400 ml-1">({{ q.attempts }}×)</span>
              </template>
              <span v-else class="text-slate-300 text-xs">-</span>
            </td>
            <td v-for="a in row.assignments" :key="'a' + a.assignment_id">
              <button v-if="a.submission_id" @click="openGrading(row, a)"
                class="badge transition hover:scale-105"
                :class="a.status === 'graded' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">
                {{ a.status === 'graded' ? `${a.grade}/${Math.round(a.max_points)}` : 'grade me →' }}
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
            <p class="text-xs text-slate-400">Submitted {{ new Date(viewing.submission.submitted_at).toLocaleString() }}</p>
          </div>
          <span class="badge" :class="viewing.submission.status === 'graded' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">
            {{ viewing.submission.status }}
          </span>
        </div>
        <div v-if="viewing.submission.text_response" class="rounded-lg bg-slate-50 border border-slate-200 p-4 text-sm text-slate-700 whitespace-pre-wrap font-mono">{{ viewing.submission.text_response }}</div>
        <a v-if="viewing.submission.file_url" :href="viewing.submission.file_url" target="_blank" class="btn-secondary text-sm inline-flex">Download attachment</a>

        <div class="border-t border-slate-100 pt-4 grid sm:grid-cols-3 gap-3">
          <div>
            <label class="label">Grade</label>
            <input v-model.number="gradeForm.grade" type="number" min="0" class="input" />
          </div>
          <div class="sm:col-span-2">
            <label class="label">Feedback</label>
            <input v-model="gradeForm.feedback" class="input" placeholder="Great work - watch the edge cases…" />
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
