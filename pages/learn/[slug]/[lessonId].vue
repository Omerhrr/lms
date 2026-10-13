<script setup lang="ts">
import {
  ChevronLeft, ChevronRight, CheckCircle2, Circle, PlayCircle, FileText,
  FileDown, BarChart3, ArrowLeft, Award, X, Menu, Lock, Bookmark, NotebookPen, ChevronDown, Trophy
} from 'lucide-vue-next'

// full-screen player: no site header/footer around it
definePageMeta({ middleware: 'auth', layout: false })

const route = useRoute()
const api = useApi()
const { show } = useToast()

const course = ref<any>(null)
const enrollment = ref<any>(null)
const currentLesson = ref<any>(null)
const fullLesson = ref<any>(null)
const lessonError = ref<string | null>(null)
const flatLessons = computed<any[]>(() => {
  const out: any[] = []
  for (const s of course.value?.sections || []) for (const l of s.lessons) out.push({ ...l, sectionTitle: s.title })
  return out
})
const completedIds = ref<Set<number>>(new Set())
const sidebarOpen = ref(false)
const justPassedQuiz = ref(false)
const loading = ref(true)

const loadCourse = async () => {
  loading.value = true
  try {
    course.value = await api.get<any>(`/courses/${route.params.slug}`)
    if (!course.value.can_manage) {
      const enr = await api.get<any>(`/enrollments/my/${course.value.id}`)
      enrollment.value = enr
      completedIds.value = new Set(enr.completed_lesson_ids)
    } else {
      enrollment.value = { progress: 0 }
    }
    const want = Number(route.params.lessonId)
    currentLesson.value =
      flatLessons.value.find(l => l.id === want) ||
      flatLessons.value.find(l => !completedIds.value.has(l.id) && !l.unlocks_at) ||
      flatLessons.value[0]
  } catch (e: any) {
    show(e?.data?.detail || 'Could not load course', 'error')
    navigateTo('/dashboard')
  } finally { loading.value = false }
}

const loadFullLesson = async (lessonId: number) => {
  fullLesson.value = null
  lessonError.value = null
  try {
    fullLesson.value = await api.get<any>(`/lessons/${lessonId}`, undefined, true)
  } catch (e: any) {
    lessonError.value = e?.data?.detail || null
  }
}

// ---------- drip locks ----------
const isLocked = (l: any) => !!l?.unlocks_at
const unlockLabel = (iso: string) =>
  new Date(iso.endsWith('Z') ? iso : iso + 'Z').toLocaleString(undefined, { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

// ---------- notes & bookmark ----------
const note = ref('')
const noteSavedAt = ref<string | null>(null)
const noteState = ref<'idle' | 'saving' | 'saved' | 'error'>('idle')
const notesOpen = ref(false)  // one line by default; opens when the lesson already has a note
const bookmarked = ref(false)
let noteTimer: ReturnType<typeof setTimeout> | undefined
let loadingNote = false

const loadNote = async (lessonId: number) => {
  loadingNote = true
  note.value = ''
  bookmarked.value = false
  noteState.value = 'idle'
  try {
    const res = await api.get<any>(`/lessons/${lessonId}/note`, undefined, true)
    note.value = res.body
    if (res.body) notesOpen.value = true
    noteSavedAt.value = res.updated_at
    bookmarked.value = res.bookmarked
  } catch { /* notes unavailable (e.g. preview without enrollment) */ }
  await nextTick()
  loadingNote = false
}

const saveNote = async (lessonId: number, body: string) => {
  noteState.value = 'saving'
  try {
    const res = await api.put<any>(`/lessons/${lessonId}/note`, { body }, true)
    noteSavedAt.value = res.updated_at
    noteState.value = 'saved'
  } catch { noteState.value = 'error' }
}

watch(note, (body) => {
  if (loadingNote || !currentLesson.value) return
  const id = currentLesson.value.id
  noteState.value = 'saving'
  if (noteTimer) clearTimeout(noteTimer)
  noteTimer = setTimeout(() => saveNote(id, body), 800)
})

const flushNote = () => {
  if (noteTimer && currentLesson.value && noteState.value === 'saving') {
    clearTimeout(noteTimer)
    saveNote(currentLesson.value.id, note.value)
  }
}

const toggleBookmark = async () => {
  if (!currentLesson.value) return
  const id = currentLesson.value.id
  try {
    if (bookmarked.value) await api.del(`/lessons/${id}/bookmark`)
    else await api.post(`/lessons/${id}/bookmark`)
    bookmarked.value = !bookmarked.value
    show(bookmarked.value ? 'Lesson bookmarked' : 'Bookmark removed', 'info')
  } catch { /* toast shown */ }
}

watch(currentLesson, (l, prev) => {
  if (prev && noteTimer) flushNote()
  if (!l || !course.value) return
  justPassedQuiz.value = false
  if (!isLocked(l)) loadFullLesson(l.id)
  loadNote(l.id)
  if (l.id !== Number(route.params.lessonId)) {
    navigateTo(`/learn/${course.value.slug}/${l.id}`, { replace: true })
  }
  if (import.meta.client) window.scrollTo({ top: 0 })
})

const idx = computed(() => flatLessons.value.findIndex(l => l.id === currentLesson.value?.id))
const prevLesson = computed(() => (idx.value > 0 ? flatLessons.value[idx.value - 1] : null))
const nextLesson = computed(() => (idx.value < flatLessons.value.length - 1 ? flatLessons.value[idx.value + 1] : null))

const isDone = (id: number) => completedIds.value.has(id)

// shown after a lesson is completed: next lesson, finished section, or finished course
const celebrate = ref<null | { kind: 'lesson' | 'section' | 'course'; section?: string }>(null)
const sectionOf = (id: number) => course.value?.sections.find((s: any) => s.lessons.some((l: any) => l.id === id))
const afterComplete = (lessonId: number, status?: string) => {
  if (status === 'completed') { celebrate.value = { kind: 'course' }; return }
  const sec = sectionOf(lessonId)
  if (sec && sec.lessons.every((l: any) => completedIds.value.has(l.id))) celebrate.value = { kind: 'section', section: sec.title }
  else celebrate.value = { kind: 'lesson' }
}
watch(currentLesson, () => { celebrate.value = null })

const toggleComplete = async () => {
  if (!currentLesson.value || course.value?.can_manage) return
  const done = isDone(currentLesson.value.id)
  try {
    const res = done
      ? await api.post(`/enrollments/${course.value.id}/lessons/${currentLesson.value.id}/uncomplete`)
      : await api.post(`/enrollments/${course.value.id}/lessons/${currentLesson.value.id}/complete`)
    if (done) completedIds.value.delete(currentLesson.value.id)
    else completedIds.value.add(currentLesson.value.id)
    completedIds.value = new Set(completedIds.value)
    enrollment.value.progress = res.progress
    if (!done) afterComplete(currentLesson.value.id, res.status)
    else celebrate.value = null
  } catch { /* toast shown */ }
}

const onVideoEnded = () => {
  if (currentLesson.value && !isDone(currentLesson.value.id)) toggleComplete()
}

const onQuizPassed = async () => {
  justPassedQuiz.value = true
  if (currentLesson.value && !isDone(currentLesson.value.id) && !course.value?.can_manage) {
    try {
      const res = await api.post(`/enrollments/${course.value.id}/lessons/${currentLesson.value.id}/complete`)
      completedIds.value = new Set([...completedIds.value, currentLesson.value.id])
      enrollment.value.progress = res.progress
      afterComplete(currentLesson.value.id, res.status)
    } catch { /* ignore */ }
  }
}

const sectionProgress = (s: any) => {
  const done = s.lessons.filter((l: any) => completedIds.value.has(l.id)).length
  return `${done}/${s.lessons.length}`
}

const lessonIcon = (l: any) =>
  isDone(l.id) ? CheckCircle2 : isLocked(l) ? Lock
    : l.type === 'video' ? PlayCircle : l.type === 'quiz' ? BarChart3 : l.type === 'file' ? FileDown : FileText

onMounted(() => {
  loadCourse()
})
onBeforeUnmount(flushNote)
</script>

<template>
  <div class="min-h-[100dvh] bg-slate-950 text-slate-100 flex flex-col">
    <header class="h-14 bg-slate-900 border-b border-slate-800 flex items-center justify-between gap-2 px-3 sm:px-4 shrink-0 sticky top-0 z-40">
      <div class="flex items-center gap-1.5 sm:gap-3 min-w-0">
        <button class="lg:hidden p-2 rounded-lg hover:bg-slate-800" @click="sidebarOpen = !sidebarOpen" aria-label="Course contents">
          <Menu class="w-5 h-5" />
        </button>
        <NuxtLink :to="`/courses/${route.params.slug}`" class="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition shrink-0 p-1" aria-label="Back to course">
          <ArrowLeft class="w-4 h-4" /> <span class="hidden md:inline">Back to course</span>
        </NuxtLink>
        <span class="text-slate-600 hidden md:block">/</span>
        <span class="font-semibold truncate text-sm sm:text-base hidden sm:block">{{ course?.title }}</span>
        <!-- phones: where you are, not a clipped course title -->
        <span class="font-semibold text-sm sm:hidden whitespace-nowrap">Lesson {{ idx + 1 }} of {{ flatLessons.length }}</span>
      </div>
      <div v-if="!course?.can_manage" class="flex items-center gap-2 shrink-0">
        <div class="w-16 sm:w-28 h-2 rounded-full bg-slate-800 overflow-hidden">
          <div class="h-full bg-brand-500 rounded-full transition-all" :style="`width:${enrollment?.progress || 0}%`" />
        </div>
        <span class="text-slate-400 text-xs font-semibold w-9">{{ Math.round(enrollment?.progress || 0) }}%</span>
      </div>
      <span v-else class="badge bg-slate-800 text-slate-300 shrink-0">Instructor preview</span>
    </header>

    <div class="flex flex-1 min-h-0">
      <aside class="fixed lg:sticky top-14 z-40 h-[calc(100dvh-3.5rem)] w-[85vw] max-w-xs lg:w-80 bg-slate-900 border-r border-slate-800 overflow-y-auto nice-scroll transition-transform shrink-0"
        :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'">
        <div class="flex items-center justify-between px-4 pt-4 lg:hidden">
          <span class="text-sm font-semibold text-slate-300">Course contents</span>
          <button class="p-2 rounded-lg hover:bg-slate-800" aria-label="Close" @click="sidebarOpen = false"><X class="w-4 h-4" /></button>
        </div>
        <div class="p-3 sm:p-4">
          <div v-for="s in course?.sections || []" :key="s.id" class="mb-5">
            <div class="flex items-center justify-between mb-2 px-1">
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 leading-tight pr-2">{{ s.title }}</h3>
              <span class="text-xs text-slate-500 shrink-0">{{ sectionProgress(s) }}</span>
            </div>
            <button v-for="l in s.lessons" :key="l.id" @click="currentLesson = l; sidebarOpen = false"
              class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-left text-sm transition"
              :class="l.id === currentLesson?.id ? 'bg-brand-600/20 text-brand-300 border border-brand-500/30' : 'text-slate-300 hover:bg-slate-800 border border-transparent'">
              <component :is="lessonIcon(l)" class="w-4.5 h-4.5 shrink-0"
                :class="isDone(l.id) ? 'text-brand-400' : isLocked(l) ? 'text-amber-400/80' : l.id === currentLesson?.id ? 'text-brand-300' : 'text-slate-500'" />
              <span class="flex-1 leading-snug" :class="isLocked(l) && 'text-slate-500'">{{ l.title }}</span>
              <span class="text-xs text-slate-500 shrink-0">{{ isLocked(l) ? 'soon' : fmtMinutes(l.duration_minutes) }}</span>
            </button>
          </div>
        </div>
      </aside>
      <div v-if="sidebarOpen" class="fixed inset-0 top-14 bg-black/60 z-30 lg:hidden" @click="sidebarOpen = false" />

      <main class="flex-1 min-w-0 flex flex-col">
        <div v-if="loading" class="flex-1 flex items-center justify-center text-slate-500">Loading lesson…</div>

        <template v-else-if="currentLesson">
          <div class="flex-1 px-3 py-4 sm:p-8">
            <div class="max-w-4xl mx-auto">
              <div class="flex items-center gap-2 text-xs text-slate-500 mb-2">
                <span class="badge bg-slate-800 text-slate-300 border border-slate-700 capitalize">{{ currentLesson.type }}</span>
                <span>{{ fmtMinutes(currentLesson.duration_minutes) }}</span>
                <span class="hidden sm:inline">· Lesson {{ idx + 1 }} of {{ flatLessons.length }}</span>
              </div>
              <div class="flex items-start justify-between gap-3 mb-5 sm:mb-6">
                <h1 class="text-xl sm:text-2xl font-bold leading-snug">{{ currentLesson.title }}</h1>
                <button v-if="!isLocked(currentLesson)" type="button" @click="toggleBookmark"
                  class="shrink-0 p-2 rounded-lg border transition"
                  :class="bookmarked ? 'border-amber-400/40 bg-amber-400/10 text-amber-300' : 'border-slate-700 text-slate-400 hover:text-white hover:bg-slate-800'"
                  :aria-label="bookmarked ? 'Remove bookmark' : 'Bookmark this lesson'" :title="bookmarked ? 'Bookmarked' : 'Bookmark'">
                  <Bookmark class="w-5 h-5" :class="bookmarked && 'fill-amber-300'" />
                </button>
              </div>

              <!-- drip-locked -->
              <div v-if="isLocked(currentLesson)" class="card !bg-slate-900 !border-amber-500/30 p-8 sm:p-10 text-center">
                <Lock class="w-12 h-12 mx-auto text-amber-400 mb-3" />
                <p class="font-semibold text-slate-200">This lesson isn't available yet</p>
                <p class="text-sm text-slate-400 mt-1">It unlocks on <b class="text-slate-200">{{ unlockLabel(currentLesson.unlocks_at) }}</b>. It's on your calendar.</p>
                <NuxtLink to="/calendar" class="btn-ghost !text-brand-300 mt-4 inline-flex">Open calendar</NuxtLink>
              </div>

              <div v-else-if="lessonError" class="card !bg-slate-900 !border-slate-800 p-8 text-center text-slate-400">
                <Lock class="w-10 h-10 mx-auto mb-2" />{{ lessonError }}
              </div>

              <template v-else>
                <div v-if="currentLesson.type === 'video'" class="mb-4">
                  <VideoPlayer v-if="fullLesson" :key="currentLesson.id" :url="fullLesson.video_url" @ended="onVideoEnded" />
                  <div v-else class="aspect-video rounded-xl bg-black animate-pulse" />
                </div>

                <div v-else-if="currentLesson.type === 'text'" class="lesson-dark card !bg-slate-900 !border-slate-800 p-5 sm:p-8 text-slate-200">
                  <RichText :content="fullLesson?.content || (fullLesson ? 'No content yet.' : 'Loading…')" />
                </div>

                <div v-else-if="currentLesson.type === 'file'" class="card !bg-slate-900 !border-slate-800 p-8 text-center">
                  <FileDown class="w-12 h-12 mx-auto text-brand-400 mb-3" />
                  <p class="text-slate-300 font-semibold mb-1">Lesson resource</p>
                  <p class="text-slate-500 text-sm mb-5">Download the attached file to complete this lesson.</p>
                  <a v-if="safeUrl(fullLesson?.file_url)" :href="safeUrl(fullLesson?.file_url)" rel="noopener noreferrer" target="_blank"
                    class="btn-primary inline-flex">Download file</a>
                  <p v-else class="text-sm text-slate-600">No file attached yet.</p>
                </div>

                <div v-else-if="currentLesson.type === 'quiz'" class="!text-slate-300">
                  <div v-if="justPassedQuiz" class="card !bg-slate-900 !border-brand-500/40 p-8 text-center mb-4">
                    <Award class="w-12 h-12 mx-auto text-brand-400 mb-2" />
                    <p class="font-bold">Quiz passed and lesson marked complete!</p>
                  </div>
                  <QuizRunner :key="currentLesson.id" :lesson-id="currentLesson.id" @passed="onQuizPassed" />
                </div>
              </template>

              <!-- next up / celebration -->
              <div v-if="celebrate" class="mt-6 rounded-xl border p-4 sm:p-5 flex flex-wrap items-center gap-4"
                :class="celebrate.kind === 'course' ? 'border-amber-400/40 bg-amber-400/10' : 'border-brand-500/30 bg-brand-500/10'" role="status">
                <component :is="celebrate.kind === 'course' ? Trophy : CheckCircle2" class="w-7 h-7 shrink-0" :class="celebrate.kind === 'course' ? 'text-amber-300' : 'text-brand-300'" />
                <div class="flex-1 min-w-0">
                  <p class="font-bold text-white">
                    {{ celebrate.kind === 'course' ? 'You finished the course! 🎓' : celebrate.kind === 'section' ? `Section complete: ${celebrate.section}` : 'Lesson complete' }}
                  </p>
                  <p class="text-sm text-slate-300 truncate">
                    <template v-if="celebrate.kind === 'course'">Your certificate is ready.</template>
                    <template v-else-if="nextLesson">Next up: {{ nextLesson.title }}</template>
                    <template v-else>{{ Math.round(enrollment?.progress || 0) }}% of the course complete</template>
                  </p>
                </div>
                <NuxtLink v-if="celebrate.kind === 'course'" to="/certificates" class="btn bg-amber-400 text-amber-950 hover:bg-amber-300 font-bold">View certificate</NuxtLink>
                <button v-else-if="nextLesson" class="btn bg-brand-500 text-white hover:bg-brand-400 font-semibold" @click="currentLesson = nextLesson">
                  Continue <ChevronRight class="w-4 h-4" />
                </button>
              </div>

              <!-- my notes -->
              <section v-if="!isLocked(currentLesson)" class="mt-6 rounded-xl border border-slate-800 bg-slate-900/70">
                <button type="button" class="w-full flex items-center justify-between gap-3 px-4 py-3 text-left" @click="notesOpen = !notesOpen" :aria-expanded="notesOpen">
                  <span class="flex items-center gap-2 font-semibold text-slate-200"><NotebookPen class="w-4.5 h-4.5 text-brand-400" /> My notes</span>
                  <span class="flex items-center gap-3">
                    <span class="text-xs text-slate-500">
                      {{ noteState === 'saving' ? 'Saving…' : noteState === 'error' ? 'Not saved - retrying on next edit' : noteState === 'saved' ? 'Saved' : note ? 'Private to you' : '' }}
                    </span>
                    <ChevronDown class="w-4 h-4 text-slate-500 transition" :class="notesOpen && 'rotate-180'" />
                  </span>
                </button>
                <div v-show="notesOpen" class="px-4 pb-4">
                  <textarea v-model="note" rows="5" maxlength="20000" @blur="flushNote"
                    class="w-full rounded-lg bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-0 text-sm text-slate-200 placeholder-slate-600 p-3 resize-y"
                    placeholder="Jot down key ideas, questions or timestamps. Notes save automatically and only you can see them." />
                  <NuxtLink to="/notes" class="text-xs text-slate-500 hover:text-brand-300">All my notes →</NuxtLink>
                </div>
              </section>
            </div>
          </div>

          <div class="shrink-0 sticky bottom-0 border-t border-slate-800 bg-slate-900/95 backdrop-blur px-3 sm:px-8 py-2.5 sm:py-3 flex items-center justify-between gap-2"
            style="padding-bottom: max(0.625rem, env(safe-area-inset-bottom))">
            <button :disabled="!prevLesson" @click="currentLesson = prevLesson" class="btn-ghost !text-slate-300 disabled:opacity-30 !px-2.5 sm:!px-4" aria-label="Previous lesson">
              <ChevronLeft class="w-4 h-4" /> <span class="hidden sm:inline">Previous</span>
            </button>
            <button v-if="!course?.can_manage" @click="toggleComplete" :disabled="isLocked(currentLesson)"
              class="btn font-semibold text-sm disabled:opacity-40"
              :class="isDone(currentLesson.id) ? 'bg-slate-800 text-slate-300 hover:bg-slate-700' : 'bg-brand-500 text-white hover:bg-brand-400'">
              <component :is="isDone(currentLesson.id) ? CheckCircle2 : Circle" class="w-4 h-4" />
              {{ isDone(currentLesson.id) ? 'Completed' : 'Mark complete' }}
            </button>
            <button :disabled="!nextLesson" @click="currentLesson = nextLesson" class="btn-ghost !text-slate-300 disabled:opacity-30 !px-2.5 sm:!px-4" aria-label="Next lesson">
              <span class="hidden sm:inline">Next</span> <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>
