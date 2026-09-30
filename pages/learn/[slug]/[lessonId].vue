<script setup lang="ts">
import {
  ChevronLeft, ChevronRight, CheckCircle2, Circle, PlayCircle, FileText,
  FileDown, BarChart3, ArrowLeft, Award, X, Menu
} from 'lucide-vue-next'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const api = useApi()
const { show } = useToast()

const course = ref<any>(null)
const enrollment = ref<any>(null)
const currentLesson = ref<any>(null)
const fullLesson = ref<any>(null)
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
    const enr = await api.get<any>(`/enrollments/my/${course.value.id}`)
    enrollment.value = enr
    completedIds.value = new Set(enr.completed_lesson_ids)
    const want = Number(route.params.lessonId)
    currentLesson.value =
      flatLessons.value.find(l => l.id === want) ||
      flatLessons.value.find(l => !completedIds.value.has(l.id)) ||
      flatLessons.value[0]
  } catch (e: any) {
    show(e?.data?.detail || 'Could not load course', 'error')
    navigateTo('/dashboard')
  } finally { loading.value = false }
}

const loadFullLesson = async (lessonId: number) => {
  fullLesson.value = null
  try {
    fullLesson.value = await api.get<any>(`/lessons/${lessonId}`)
  } catch { fullLesson.value = null }
}

watch(currentLesson, (l) => {
  if (!l || !course.value) return
  loadFullLesson(l.id)
  if (l.id !== Number(route.params.lessonId)) {
    navigateTo(`/learn/${course.value.slug}/${l.id}`, { replace: true })
  }
})

const idx = computed(() => flatLessons.value.findIndex(l => l.id === currentLesson.value?.id))
const prevLesson = computed(() => (idx.value > 0 ? flatLessons.value[idx.value - 1] : null))
const nextLesson = computed(() => (idx.value < flatLessons.value.length - 1 ? flatLessons.value[idx.value + 1] : null))

const isDone = (id: number) => completedIds.value.has(id)

const toggleComplete = async () => {
  if (!currentLesson.value) return
  const done = isDone(currentLesson.value.id)
  try {
    const res = done
      ? await api.post(`/enrollments/${course.value.id}/lessons/${currentLesson.value.id}/uncomplete`)
      : await api.post(`/enrollments/${course.value.id}/lessons/${currentLesson.value.id}/complete`)
    if (done) completedIds.value.delete(currentLesson.value.id)
    else completedIds.value.add(currentLesson.value.id)
    enrollment.value.progress = res.progress
    if (!done) show(`Progress: ${res.progress}%${res.status === 'completed' ? ' — course completed! 🎓' : ''}`)
  } catch (e: any) { show(e?.data?.detail || 'Failed to update', 'error') }
}

const onQuizPassed = async () => {
  justPassedQuiz.value = true
  if (currentLesson.value && !isDone(currentLesson.value.id)) {
    try {
      const res = await api.post(`/enrollments/${course.value.id}/lessons/${currentLesson.value.id}/complete`)
      completedIds.value.add(currentLesson.value.id)
      enrollment.value.progress = res.progress
    } catch { /* ignore */ }
  }
}

const sectionProgress = (s: any) => {
  const done = s.lessons.filter((l: any) => completedIds.value.has(l.id)).length
  return `${done}/${s.lessons.length}`
}

onMounted(loadCourse)
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
    <header class="h-14 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-4 shrink-0 sticky top-0 z-40">
      <div class="flex items-center gap-3 min-w-0">
        <button class="lg:hidden p-2 -ml-2 rounded-lg hover:bg-slate-800" @click="sidebarOpen = !sidebarOpen" aria-label="Menu">
          <Menu class="w-5 h-5" />
        </button>
        <NuxtLink :to="`/courses/${route.params.slug}`" class="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition shrink-0">
          <ArrowLeft class="w-4 h-4" /> <span class="hidden sm:inline">Back to course</span>
        </NuxtLink>
        <span class="text-slate-600 hidden sm:block">/</span>
        <span class="font-semibold truncate hidden sm:block">{{ course?.title }}</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-28 h-2 rounded-full bg-slate-800 overflow-hidden">
          <div class="h-full bg-brand-500 rounded-full transition-all" :style="`width:${enrollment?.progress || 0}%`" />
        </div>
        <span class="text-slate-400 text-xs font-semibold w-9">{{ Math.round(enrollment?.progress || 0) }}%</span>
      </div>
    </header>

    <div class="flex flex-1 min-h-0">
      <aside class="fixed lg:sticky top-14 z-40 h-[calc(100vh-3.5rem)] w-80 bg-slate-900 border-r border-slate-800 overflow-y-auto nice-scroll transition-transform"
        :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'">
        <button class="lg:hidden absolute right-3 top-3 p-1.5 rounded-lg hover:bg-slate-800" @click="sidebarOpen = false">
          <X class="w-4 h-4" />
        </button>
        <div class="p-4">
          <div v-for="s in course?.sections || []" :key="s.id" class="mb-5">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-[11px] font-bold uppercase tracking-wider text-slate-400 leading-tight pr-2">{{ s.title }}</h3>
              <span class="text-[10px] text-slate-500 shrink-0">{{ sectionProgress(s) }}</span>
            </div>
            <button v-for="l in s.lessons" :key="l.id" @click="currentLesson = l; sidebarOpen = false"
              class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-left text-sm transition"
              :class="l.id === currentLesson?.id ? 'bg-brand-600/20 text-brand-300 border border-brand-500/30' : 'text-slate-300 hover:bg-slate-800 border border-transparent'">
              <component :is="isDone(l.id) ? CheckCircle2 : (l.type === 'video' ? PlayCircle : l.type === 'quiz' ? BarChart3 : l.type === 'file' ? FileDown : FileText)"
                class="w-4.5 h-4.5 shrink-0"
                :class="isDone(l.id) ? 'text-brand-400' : l.id === currentLesson?.id ? 'text-brand-300' : 'text-slate-500'" />
              <span class="flex-1 leading-snug">{{ l.title }}</span>
              <span class="text-[10px] text-slate-500 shrink-0">{{ l.duration_minutes }}m</span>
            </button>
          </div>
        </div>
      </aside>
      <div v-if="sidebarOpen" class="fixed inset-0 top-14 bg-black/50 z-30 lg:hidden" @click="sidebarOpen = false" />

      <main class="flex-1 min-w-0 flex flex-col">
        <div v-if="loading" class="flex-1 flex items-center justify-center text-slate-500">Loading lesson…</div>

        <template v-else-if="currentLesson">
          <div class="flex-1 p-4 sm:p-8 overflow-y-auto">
            <div class="max-w-4xl mx-auto">
              <div class="flex items-center gap-2 text-xs text-slate-500 mb-2">
                <span class="badge bg-slate-800 text-slate-300 border border-slate-700 capitalize">{{ currentLesson.type }}</span>
                <span>{{ currentLesson.duration_minutes }} min</span>
              </div>
              <h1 class="text-2xl font-bold mb-6">{{ currentLesson.title }}</h1>

              <div v-if="currentLesson.type === 'video'" class="aspect-video bg-black rounded-xl overflow-hidden border border-slate-800 mb-4">
                <iframe v-if="fullLesson?.video_url || currentLesson.video_url" :src="fullLesson?.video_url || currentLesson.video_url"
                  class="w-full h-full" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; picture-in-picture" allowfullscreen />
                <div v-else class="w-full h-full flex flex-col items-center justify-center text-slate-600 gap-2">
                  <PlayCircle class="w-12 h-12" /><span class="text-sm">No video attached to this lesson</span>
                </div>
              </div>

              <div v-else-if="currentLesson.type === 'text'" class="card !bg-slate-900 !border-slate-800 p-6 sm:p-8 text-slate-200">
                <RichText :content="(fullLesson?.content ?? currentLesson.content) || 'No content yet.'" />
              </div>

              <div v-else-if="currentLesson.type === 'file'" class="card !bg-slate-900 !border-slate-800 p-8 text-center">
                <FileDown class="w-12 h-12 mx-auto text-brand-400 mb-3" />
                <p class="text-slate-300 font-semibold mb-1">Lesson resource</p>
                <p class="text-slate-500 text-sm mb-5">Download the attached file to complete this lesson.</p>
                <a v-if="fullLesson?.file_url || currentLesson.file_url" :href="fullLesson?.file_url || currentLesson.file_url" target="_blank"
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
            </div>
          </div>

          <div class="shrink-0 border-t border-slate-800 bg-slate-900 px-4 sm:px-8 py-3 flex items-center justify-between gap-3">
            <button :disabled="!prevLesson" @click="currentLesson = prevLesson" class="btn-ghost !text-slate-300 disabled:opacity-30">
              <ChevronLeft class="w-4 h-4" /> Previous
            </button>
            <button @click="toggleComplete"
              class="btn font-semibold"
              :class="isDone(currentLesson.id) ? 'bg-slate-800 text-slate-300 hover:bg-slate-700' : 'bg-brand-500 text-white hover:bg-brand-400'">
              <component :is="isDone(currentLesson.id) ? CheckCircle2 : Circle" class="w-4 h-4" />
              {{ isDone(currentLesson.id) ? 'Completed' : 'Mark complete' }}
            </button>
            <button :disabled="!nextLesson" @click="currentLesson = nextLesson" class="btn-ghost !text-slate-300 disabled:opacity-30">
              Next <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>
