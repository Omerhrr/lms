<script setup lang="ts">
import { Trophy, Flame, PlayCircle, Clock, ArrowRight, Target } from 'lucide-vue-next'

useSeoMeta({ title: 'My Learning - Infohive' })
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const auth = useAuth()

const enrollments = ref<any[]>([])
const certificates = ref<any[]>([])
const summary = ref<any>(null)
const liveCount = ref(0)
const loading = ref(true)

const inProgress = computed(() => enrollments.value.filter(e => e.status === 'active'))
const completed = computed(() => enrollments.value.filter(e => e.status === 'completed'))
// the most recently touched active course leads the page
const hero = computed(() => inProgress.value[0] || null)
const others = computed(() => inProgress.value.slice(1))
const resumeLink = (e: any) => e.next_lesson ? `/learn/${e.course.slug}/${e.next_lesson.id}` : `/learn/${e.course.slug}`
const dayLabel = (iso: string) => new Date(iso + 'T00:00').toLocaleDateString(undefined, { weekday: 'narrow' })
const isToday = (iso: string) => iso === new Date().toISOString().slice(0, 10)

onMounted(async () => {
  try {
    const [e, c, s] = await Promise.all([
      api.get<any[]>('/enrollments/my'),
      api.get<any[]>('/certificates/my', undefined, true),
      api.get<any>('/me/learning-summary', undefined, true).catch(() => null),
    ])
    enrollments.value = e
    certificates.value = c
    summary.value = s
  } finally { loading.value = false }
})
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-extrabold text-slate-900">Hi {{ auth.user.value?.full_name.split(' ')[0] }} 👋</h1>
      <p class="text-slate-600 mt-1">{{ hero ? 'Ready to pick up where you left off?' : 'Let’s find something to learn.' }}</p>
    </div>

    <div v-if="loading" class="space-y-4">
      <div class="card h-40 animate-pulse" /><div class="card h-20 animate-pulse" />
    </div>

    <template v-else>
      <!-- continue: one clear next step -->
      <div v-if="hero" class="rounded-3xl bg-slate-900 text-white p-5 sm:p-7 mb-6 grid md:grid-cols-[1fr_auto] gap-5 items-center">
        <div class="min-w-0">
          <p class="text-xs uppercase tracking-[0.16em] text-brand-300 font-semibold">Continue learning</p>
          <h2 class="mt-2 text-xl sm:text-2xl font-extrabold leading-tight">{{ hero.course.title }}</h2>
          <p v-if="hero.next_lesson" class="mt-2 text-slate-300 text-sm flex items-center gap-2 min-w-0">
            <PlayCircle class="w-4 h-4 shrink-0 text-brand-300" />
            <span class="truncate">Next: {{ hero.next_lesson.title }}</span>
            <span v-if="hero.next_lesson.duration_minutes" class="shrink-0 text-slate-500">· {{ fmtMinutes(hero.next_lesson.duration_minutes) }}</span>
          </p>
          <div class="mt-4 h-2 rounded-full bg-white/10 overflow-hidden">
            <div class="h-full rounded-full bg-brand-400" :style="`width:${hero.progress}%`" />
          </div>
          <div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-300">
            <span><b class="text-white">{{ Math.round(hero.progress) }}%</b> complete</span>
            <span v-if="hero.remaining_lessons" class="flex items-center gap-1"><Clock class="w-3 h-3" /> {{ fmtMinutes(hero.remaining_minutes) }} left · {{ plural(hero.remaining_lessons, 'lesson') }}</span>
          </div>
        </div>
        <NuxtLink :to="resumeLink(hero)" class="btn bg-brand-500 hover:bg-brand-400 text-white px-6 py-3 font-bold w-full md:w-auto justify-center">
          Resume <ArrowRight class="w-4 h-4" />
        </NuxtLink>
      </div>

      <!-- this week -->
      <div v-if="summary && enrollments.length" class="card p-4 sm:p-5 mb-8 flex flex-wrap items-center gap-x-8 gap-y-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center"><Flame class="w-5 h-5" :class="summary.streak_days ? 'text-amber-500' : 'text-slate-300'" /></div>
          <div>
            <div class="font-extrabold text-slate-900">{{ plural(summary.streak_days, 'day') }}</div>
            <div class="text-xs text-slate-600">{{ summary.active_today ? 'Streak - nice work today' : summary.streak_days ? 'Streak - learn today to keep it' : 'Start a streak today' }}</div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center"><Target class="w-5 h-5 text-brand-600" /></div>
          <div>
            <div class="font-extrabold text-slate-900">{{ Math.min(summary.lessons_this_week, summary.weekly_goal) }} / {{ summary.weekly_goal }} lessons</div>
            <div class="text-xs text-slate-600">Weekly goal{{ summary.lessons_this_week >= summary.weekly_goal ? ' reached 🎉' : '' }}</div>
          </div>
        </div>
        <div class="flex gap-1.5 sm:ml-auto" aria-label="Days active this week">
          <div v-for="d in summary.week" :key="d.date" class="flex flex-col items-center gap-1">
            <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
              :class="d.active ? 'bg-brand-600 text-white' : isToday(d.date) ? 'ring-2 ring-brand-300 text-slate-500' : 'bg-slate-100 text-slate-400'">
              {{ dayLabel(d.date) }}
            </div>
          </div>
        </div>
      </div>

      <!-- live classes: only when there's something scheduled -->
      <div v-show="liveCount" class="mb-10">
        <h2 class="text-lg font-bold text-slate-800 mb-4">Upcoming live classes</h2>
        <LiveSessionList compact show-course @loaded="liveCount = $event" />
      </div>

      <!-- other courses -->
      <div v-if="others.length" class="mb-10">
        <h2 class="text-lg font-bold text-slate-800 mb-4">Also in progress</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="e in others" :key="e.id" class="card p-4 flex flex-wrap sm:flex-nowrap gap-4 items-center hover:border-brand-300 transition min-w-0">
            <div class="flex-1 min-w-0">
              <h3 class="font-bold text-slate-800 truncate">{{ e.course.title }}</h3>
              <p v-if="e.next_lesson" class="text-xs text-slate-600 truncate mt-0.5">Next: {{ e.next_lesson.title }}</p>
              <div class="mt-2 h-2 rounded-full bg-slate-100 overflow-hidden">
                <div class="h-full rounded-full bg-brand-500" :style="`width:${e.progress}%`" />
              </div>
              <div class="mt-1.5 flex items-center justify-between text-xs text-slate-600">
                <span v-if="e.remaining_lessons" class="flex items-center gap-1"><Clock class="w-3 h-3" /> {{ fmtMinutes(e.remaining_minutes) }} left</span>
                <b class="text-brand-700">{{ Math.round(e.progress) }}%</b>
              </div>
            </div>
            <NuxtLink :to="resumeLink(e)" class="btn-secondary shrink-0 w-full sm:w-auto">Resume</NuxtLink>
          </div>
        </div>
      </div>

      <!-- completed -->
      <div v-if="completed.length" class="mb-10">
        <h2 class="text-lg font-bold text-slate-800 mb-4">Completed</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="e in completed" :key="e.id" class="card p-4 flex gap-4 items-center min-w-0">
            <div class="w-11 h-11 rounded-xl bg-amber-100 flex items-center justify-center shrink-0"><Trophy class="w-5 h-5 text-amber-600" /></div>
            <h3 class="font-bold text-slate-800 truncate flex-1 min-w-0">{{ e.course.title }}</h3>
            <NuxtLink to="/certificates" class="text-sm font-semibold text-brand-700 shrink-0">Certificate</NuxtLink>
            <NuxtLink :to="`/learn/${e.course.slug}`" class="btn-secondary shrink-0 text-sm">Review</NuxtLink>
          </div>
        </div>
      </div>

      <EmptyState v-if="enrollments.length === 0" empty>
        You haven't enrolled in any courses yet. <NuxtLink to="/courses" class="text-brand-700 font-semibold">Browse the catalog →</NuxtLink>
      </EmptyState>
    </template>
  </div>
</template>
