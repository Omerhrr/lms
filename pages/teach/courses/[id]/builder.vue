<script setup lang="ts">
import {
  Plus, Trash2, ChevronUp, ChevronDown, PlayCircle, FileText, FileDown,
  BarChart3, Save, X, Pencil, HelpCircle, ListPlus, GraduationCap
} from 'lucide-vue-next'

useSeoMeta({ title: 'Curriculum builder - LearnHub' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const route = useRoute()
const api = useApi()
const { show } = useToast()
const courseId = Number(route.params.id)

const course = ref<any>(null)
const loading = ref(true)

// modals state
const sectionModal = ref<{ open: boolean; id?: number; title: string }>({ open: false, title: '' })
const lessonModal = ref<{ open: boolean; sectionId?: number; editing?: any }>({ open: false })
const lessonForm = ref<any>({})
const quizModal = ref<{ open: boolean; lesson?: any }>({ open: false })
const quiz = ref<any>(null)
const questionModal = ref<{ open: boolean; editing?: any }>({ open: false })
const questionForm = ref<any>({})

const load = async () => {
  loading.value = true
  try { course.value = await api.get<any>(`/teach/courses/${courseId}`) }
  finally { loading.value = false }
}
onMounted(load)

// ---------- sections ----------
const saveSection = async () => {
  const title = sectionModal.value.title.trim()
  if (!title) return show('Section title is required', 'error')
  try {
    if (sectionModal.value.id) {
      await api.put(`/teach/sections/${sectionModal.value.id}`, { title })
      show('Section renamed')
    } else {
      await api.post(`/teach/courses/${courseId}/sections`, { title })
      show('Section added')
    }
    sectionModal.value = { open: false, title: '' }
    await load()
  } catch (e: any) { show(e?.data?.detail || 'Failed', 'error') }
}

const moveSection = async (id: number, direction: string) => {
  await api.post(`/teach/sections/${id}/move`, { direction })
  await load()
}

const deleteSection = async (id: number) => {
  if (!confirm('Delete this section and all its lessons?')) return
  await api.del(`/teach/sections/${id}`)
  show('Section deleted', 'info')
  await load()
}

// ---------- lessons ----------
const openLesson = (sectionId: number, editing?: any) => {
  lessonModal.value = { open: true, sectionId, editing }
  lessonForm.value = editing
    ? { title: editing.title, type: editing.type, duration_minutes: editing.duration_minutes, is_preview: editing.is_preview, video_url: editing.video_url || '', file_url: editing.file_url || '', content: editing.content || '' }
    : { title: '', type: 'video', duration_minutes: 10, is_preview: false, video_url: '', file_url: '', content: '' }
}

const saveLesson = async () => {
  const f = lessonForm.value
  if (!f.title.trim()) return show('Lesson title is required', 'error')
  try {
    if (lessonModal.value.editing) {
      await api.put(`/teach/lessons/${lessonModal.value.editing.id}`, f)
      show('Lesson updated')
    } else {
      await api.post(`/teach/sections/${lessonModal.value.sectionId}/lessons`, f)
      show('Lesson added')
    }
    lessonModal.value = { open: false }
    await load()
  } catch (e: any) { show(e?.data?.detail || 'Failed', 'error') }
}

const moveLesson = async (id: number, direction: string) => {
  await api.post(`/teach/lessons/${id}/move`, { direction })
  await load()
}

const deleteLesson = async (id: number) => {
  if (!confirm('Delete this lesson (and its quiz/attempts)?')) return
  await api.del(`/teach/lessons/${id}`)
  show('Lesson deleted', 'info')
  await load()
}

// ---------- quiz editor ----------
const openQuiz = async (lesson: any) => {
  quizModal.value = { open: true, lesson }
  quiz.value = null
  // find existing quiz for this lesson via teach quiz lookup: we don't have quiz id on lesson; use a lightweight trick - the gradebook API exposes quiz ids, but simpler: try fetching via course editor data endpoint? Instead: attempt GET /teach/quizzes/{id} is unknown; use attempt discovery via lesson-scoped endpoint below.
  try {
    const res = await api.get<any>(`/teach/lessons/${lesson.id}/quiz`)
    quiz.value = res
  } catch { quiz.value = null }
}

const saveQuizMeta = async () => {
  try {
    const res = await api.put<{ id: number }>(`/teach/lessons/${quizModal.value.lesson.id}/quiz`, {
      title: quiz.value?.title || 'Quiz',
      description: quiz.value?.description || null,
      time_limit_minutes: quiz.value?.time_limit_minutes || null,
      passing_score: quiz.value?.passing_score ?? 60,
      max_attempts: quiz.value?.max_attempts ?? 0,
    })
    quiz.value = { ...(quiz.value || {}), id: res.id }
    show('Quiz settings saved')
    await load()
  } catch (e: any) { show(e?.data?.detail || 'Failed', 'error') }
}

const openQuestion = (editing?: any) => {
  questionModal.value = { open: true, editing }
  questionForm.value = editing
    ? { type: editing.type, text: editing.text, options: [...editing.options], optionsText: editing.options.join('\n'), correct: editing.correct, points: editing.points, explanation: editing.explanation || '' }
    : { type: 'single_choice', text: '', options: [], optionsText: '', correct: [], points: 1, explanation: '' }
}

const qTypeChanged = () => {
  const f = questionForm.value
  if (f.type === 'true_false') { f.optionsText = 'True\nFalse'; f.correct = [] }
  if (f.type === 'short_answer') { f.optionsText = '' }
}

const correctIsIndex = computed(() => ['single_choice', 'true_false'].includes(questionForm.value.type))

const toggleCorrectIndex = (i: number) => {
  const f = questionForm.value
  if (f.type === 'single_choice' || f.type === 'true_false') f.correct = [i]
  else {
    const arr = [...(f.correct || [])]
    const at = arr.indexOf(i)
    at >= 0 ? arr.splice(at, 1) : arr.push(i)
    f.correct = arr.sort()
  }
}

const saveQuestion = async () => {
  const f = questionForm.value
  if (!f.text.trim()) return show('Question text is required', 'error')
  const options = f.type === 'short_answer' ? [] : f.optionsText.split('\n').map((o: string) => o.trim()).filter(Boolean)
  let correct: any
  if (f.type === 'short_answer') {
    correct = f.correctText ? f.correctText.split('\n').map((c: string) => c.trim()).filter(Boolean) : (Array.isArray(f.correct) ? f.correct : [])
  } else {
    correct = (f.correct || []).filter((c: any) => typeof c === 'number')
  }
  if (!correct.length) return show('Mark the correct answer(s) or accepted answers', 'error')
  const payload = { type: f.type, text: f.text, options, correct, points: Number(f.points) || 1, explanation: f.explanation || null }
  try {
    if (questionModal.value.editing) {
      await api.put(`/teach/questions/${questionModal.value.editing.id}`, payload)
      show('Question updated')
    } else {
      await api.post(`/teach/quizzes/${quiz.value.id}/questions`, payload)
      show('Question added')
    }
    questionModal.value = { open: false }
    await openQuiz(quizModal.value.lesson)
  } catch (e: any) { show(e?.data?.detail || 'Failed', 'error') }
}

const deleteQuestion = async (id: number) => {
  if (!confirm('Delete this question?')) return
  await api.del(`/teach/questions/${id}`)
  await openQuiz(quizModal.value.lesson)
}

const letter = (i: number) => String.fromCharCode(65 + i)
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-extrabold text-slate-900">Curriculum builder</h1>
      <p class="text-slate-500 mt-1">{{ course?.title }} - {{ course?.lesson_count }} lessons · {{ course?.sections.length }} sections</p>
    </div>

    <div v-if="loading" class="space-y-4"><div v-for="i in 3" :key="i" class="card h-16 animate-pulse" /></div>

    <div v-else class="space-y-4 max-w-4xl">
      <div v-for="(s, si) in course.sections" :key="s.id" class="card overflow-hidden">
        <div class="flex items-center gap-2 px-4 py-3.5 bg-slate-50 border-b border-slate-100">
          <GraduationCap class="w-4.5 h-4.5 text-brand-600 shrink-0" />
          <h3 class="font-bold text-slate-800 flex-1 min-w-0 truncate">{{ si + 1 }}. {{ s.title }}</h3>
          <div class="flex items-center gap-0.5 shrink-0">
            <button class="p-1.5 rounded hover:bg-slate-200 text-slate-500" title="Move up" :disabled="si === 0" @click="moveSection(s.id, 'up')"><ChevronUp class="w-4 h-4" /></button>
            <button class="p-1.5 rounded hover:bg-slate-200 text-slate-500" title="Move down" :disabled="si === course.sections.length - 1" @click="moveSection(s.id, 'down')"><ChevronDown class="w-4 h-4" /></button>
            <button class="p-1.5 rounded hover:bg-slate-200 text-slate-500" title="Rename" @click="sectionModal = { open: true, id: s.id, title: s.title }"><Pencil class="w-4 h-4" /></button>
            <button class="p-1.5 rounded hover:bg-rose-100 text-rose-500" title="Delete" @click="deleteSection(s.id)"><Trash2 class="w-4 h-4" /></button>
          </div>
        </div>

        <div class="divide-y divide-slate-50">
          <div v-for="(l, li) in s.lessons" :key="l.id" class="flex items-center gap-3 px-4 py-3 hover:bg-slate-50/60 group">
            <component :is="l.type === 'video' ? PlayCircle : l.type === 'quiz' ? BarChart3 : l.type === 'file' ? FileDown : FileText"
              class="w-4.5 h-4.5 shrink-0" :class="l.type === 'quiz' ? 'text-violet-500' : 'text-brand-600'" />
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-slate-700 truncate">{{ l.title }}
                <span v-if="l.is_preview" class="badge bg-brand-50 text-brand-700 ml-1.5">Preview</span>
              </div>
              <div class="text-xs text-slate-400 capitalize">{{ l.type }} · {{ l.duration_minutes }} min</div>
            </div>
            <button v-if="l.type === 'quiz'" @click="openQuiz(l)"
              class="btn-ghost text-xs !px-2.5 text-violet-700 hover:bg-violet-50 shrink-0">
              <HelpCircle class="w-3.5 h-3.5" /> Quiz
            </button>
            <div class="flex items-center gap-0.5 shrink-0 opacity-60 group-hover:opacity-100 transition">
              <button class="p-1.5 rounded hover:bg-slate-200 text-slate-500" :disabled="li === 0 && si === 0" title="Move up" @click="moveLesson(l.id, 'up')"><ChevronUp class="w-4 h-4" /></button>
              <button class="p-1.5 rounded hover:bg-slate-200 text-slate-500" title="Move down" @click="moveLesson(l.id, 'down')"><ChevronDown class="w-4 h-4" /></button>
              <button class="p-1.5 rounded hover:bg-slate-200 text-slate-500" title="Edit" @click="openLesson(s.id, l)"><Pencil class="w-4 h-4" /></button>
              <button class="p-1.5 rounded hover:bg-rose-100 text-rose-500" title="Delete" @click="deleteLesson(l.id)"><Trash2 class="w-4 h-4" /></button>
            </div>
          </div>
        </div>

        <div class="px-4 py-3">
          <button class="text-sm font-semibold text-brand-700 hover:bg-brand-50 rounded-lg px-3 py-2 transition flex items-center gap-1.5"
            @click="openLesson(s.id)">
            <Plus class="w-4 h-4" /> Add lesson
          </button>
        </div>
      </div>

      <button class="w-full border-2 border-dashed border-slate-300 rounded-xl py-4 text-sm font-semibold text-slate-500 hover:border-brand-400 hover:text-brand-700 transition flex items-center justify-center gap-2"
        @click="sectionModal = { open: true, title: '' }">
        <Plus class="w-4.5 h-4.5" /> Add section
      </button>

      <div v-if="course.status !== 'published'" class="pt-2">
        <NuxtLink :to="`/teach/courses/${courseId}/edit`" class="btn-primary">
          <Save class="w-4 h-4" /> Review & publish course
        </NuxtLink>
      </div>
    </div>

    <!-- section modal -->
    <Modal :open="sectionModal.open" :title="sectionModal.id ? 'Rename section' : 'Add section'" @close="sectionModal = { open: false, title: '' }">
      <input v-model="sectionModal.title" class="input" placeholder="Section title" @keyup.enter="saveSection" />
      <template #footer>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn-secondary" @click="sectionModal = { open: false, title: '' }">Cancel</button>
          <button class="btn-primary" @click="saveSection">Save</button>
        </div>
      </template>
    </Modal>

    <!-- lesson modal -->
    <Modal :open="lessonModal.open" :title="lessonModal.editing ? 'Edit lesson' : 'Add lesson'" @close="lessonModal = { open: false }">
      <div class="space-y-4">
        <div>
          <label class="label">Title</label>
          <input v-model="lessonForm.title" class="input" placeholder="Lesson title" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">Type</label>
            <select v-model="lessonForm.type" class="input">
              <option value="video">Video</option>
              <option value="text">Text</option>
              <option value="file">File download</option>
              <option value="quiz">Quiz</option>
            </select>
          </div>
          <div>
            <label class="label">Duration (min)</label>
            <input v-model.number="lessonForm.duration_minutes" type="number" min="1" class="input" />
          </div>
        </div>
        <div v-if="lessonForm.type === 'video'">
          <label class="label">Video embed URL</label>
          <input v-model="lessonForm.video_url" class="input" placeholder="https://www.youtube.com/embed/VIDEO_ID" />
          <p class="text-xs text-slate-400 mt-1">Use the embed form (youtube.com/embed/…) for in-player playback.</p>
        </div>
        <div v-if="lessonForm.type === 'file'">
          <label class="label">File URL (upload via Media, or paste link)</label>
          <input v-model="lessonForm.file_url" class="input" placeholder="/api/media/files/…" />
        </div>
        <div v-if="lessonForm.type === 'text'">
          <label class="label">Content</label>
          <textarea v-model="lessonForm.content" class="input min-h-[130px] font-mono text-xs"
            placeholder="## Heading&#10;- bullet point&#10;&#10;Paragraph text…" />
        </div>
        <label class="flex items-center gap-2 text-sm text-slate-600">
          <input v-model="lessonForm.is_preview" type="checkbox" class="rounded accent-brand-600" />
          Free preview (visible to non-enrolled visitors)
        </label>
      </div>
      <template #footer>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn-secondary" @click="lessonModal = { open: false }">Cancel</button>
          <button class="btn-primary" @click="saveLesson">Save lesson</button>
        </div>
      </template>
    </Modal>

    <!-- quiz editor modal -->
    <Modal :open="quizModal.open" :title="`Quiz · ${quizModal.lesson?.title || ''}`" wide @close="quizModal = { open: false }">
      <div v-if="quiz === null" class="text-sm text-slate-500 mb-4">
        No quiz configured for this lesson yet. Set the settings below and save to create it.
      </div>
      <div class="space-y-4">
        <div class="grid sm:grid-cols-2 gap-3">
          <div>
            <label class="label">Quiz title</label>
            <input v-model="quiz.title" class="input" placeholder="Quiz" />
          </div>
          <div>
            <label class="label">Description</label>
            <input v-model="quiz.description" class="input" placeholder="Optional instructions" />
          </div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="label">Pass score %</label>
            <input v-model.number="quiz.passing_score" type="number" min="1" max="100" class="input" />
          </div>
          <div>
            <label class="label">Max attempts</label>
            <input v-model.number="quiz.max_attempts" type="number" min="0" class="input" placeholder="0 = unlimited" />
          </div>
          <div>
            <label class="label">Time limit (min)</label>
            <input v-model.number="quiz.time_limit_minutes" type="number" min="0" class="input" placeholder="0 = none" />
          </div>
        </div>
        <button class="btn-secondary text-sm" @click="saveQuizMeta"><Save class="w-4 h-4" /> Save settings</button>

        <div v-if="quiz?.id" class="pt-3 border-t border-slate-100">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-bold text-slate-800 text-sm">Questions ({{ quiz.questions?.length || 0 }})</h4>
            <button class="btn-primary text-xs" @click="openQuestion()"><ListPlus class="w-3.5 h-3.5" /> Add question</button>
          </div>
          <div class="space-y-2.5">
            <div v-for="(q, qi) in quiz.questions || []" :key="q.id" class="border border-slate-200 rounded-lg p-3.5 flex gap-3">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-slate-700">{{ qi + 1 }}. {{ q.text }}</p>
                <p class="text-xs text-slate-400 mt-1 capitalize">{{ q.type.replace('_', ' ') }} · {{ q.points }} pt
                  · correct: {{ q.type === 'short_answer' ? q.correct.join(', ') : q.correct.map((c: number) => letter(c)).join(', ') }}</p>
              </div>
              <button class="p-1.5 rounded hover:bg-slate-100 text-slate-500 shrink-0" @click="openQuestion(q)"><Pencil class="w-4 h-4" /></button>
              <button class="p-1.5 rounded hover:bg-rose-100 text-rose-500 shrink-0" @click="deleteQuestion(q.id)"><Trash2 class="w-4 h-4" /></button>
            </div>
            <p v-if="!quiz.questions?.length" class="text-sm text-slate-400 text-center py-3">No questions yet.</p>
          </div>
        </div>
      </div>
      <template #footer><span /></template>
    </Modal>

    <!-- question modal -->
    <Modal :open="questionModal.open" :title="questionModal.editing ? 'Edit question' : 'Add question'" @close="questionModal = { open: false }">
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">Type</label>
            <select v-model="questionForm.type" class="input" @change="qTypeChanged">
              <option value="single_choice">Single choice</option>
              <option value="multi_choice">Multiple choice</option>
              <option value="true_false">True / False</option>
              <option value="short_answer">Short answer</option>
            </select>
          </div>
          <div>
            <label class="label">Points</label>
            <input v-model.number="questionForm.points" type="number" min="0.5" step="0.5" class="input" />
          </div>
        </div>
        <div>
          <label class="label">Question text</label>
          <textarea v-model="questionForm.text" class="input min-h-[70px]" />
        </div>
        <div v-if="questionForm.type !== 'short_answer'">
          <label class="label">Options (one per line)</label>
          <textarea v-model="questionForm.optionsText" class="input min-h-[90px] font-mono text-xs"
            :disabled="questionForm.type === 'true_false'" />
        </div>
        <div>
          <label class="label">{{ questionForm.type === 'short_answer' ? 'Accepted answers (one per line, case-insensitive)' : 'Click the correct answer(s)' }}</label>
          <div v-if="correctIsIndex || questionForm.type === 'multi_choice'" class="space-y-1.5">
            <button v-for="(opt, i) in (questionForm.optionsText || '').split('\n').filter((o: string) => o.trim())" :key="i"
              class="w-full flex items-center gap-2.5 rounded-lg border px-3 py-2 text-sm transition text-left"
              :class="(questionForm.correct || []).includes(i) ? 'border-brand-500 bg-brand-50 text-brand-800 font-semibold' : 'border-slate-200 hover:bg-slate-50'"
              @click="toggleCorrectIndex(i)">
              <span class="w-5 h-5 rounded-full border flex items-center justify-center text-xs shrink-0"
                :class="(questionForm.correct || []).includes(i) ? 'bg-brand-600 text-white border-brand-600' : 'text-slate-400'">{{ letter(i) }}</span>
              {{ opt }}
            </button>
          </div>
          <textarea v-else v-model="questionForm.correctText" class="input min-h-[70px] font-mono text-xs" placeholder="paris&#nThe capital of France" />
        </div>
        <div>
          <label class="label">Explanation (shown after grading)</label>
          <input v-model="questionForm.explanation" class="input" placeholder="Optional" />
        </div>
      </div>
      <template #footer>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn-secondary" @click="questionModal = { open: false }">Cancel</button>
          <button class="btn-primary" @click="saveQuestion">Save question</button>
        </div>
      </template>
    </Modal>
  </div>
</template>
