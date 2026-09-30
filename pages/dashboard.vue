<script setup lang="ts">
import { BookOpen, Trophy, Flame, TrendingUp, PlayCircle, Clock } from 'lucide-vue-next'

useSeoMeta({ title: 'My Learning - LearnHub' })
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const auth = useAuth()

const enrollments = ref<any[]>([])
const certificates = ref<any[]>([])
const loading = ref(true)

const inProgress = computed(() => enrollments.value.filter(e => e.status === 'active'))
const completed = computed(() => enrollments.value.filter(e => e.status === 'completed'))
const avgProgress = computed(() => {
  if (!enrollments.value.length) return 0
  return Math.round(enrollments.value.reduce((s, e) => s + e.progress, 0) / enrollments.value.length)
})

onMounted(async () => {
  try {
    const [e, c] = await Promise.all([
      api.get<any[]>('/enrollments/my'),
      api.get<any[]>('/certificates/my', undefined, true),
    ])
    enrollments.value = e
    certificates.value = c
  } finally { loading.value = false }
})
</script>

<template>
  <div>
    <div class="mb-8">
      <h1 class="text-2xl font-extrabold text-slate-900">Hi {{ auth.user.value?.full_name.split(' ')[0] }} 👋</h1>
      <p class="text-slate-500 mt-1">Ready to pick up where you left off?</p>
    </div>

    <!-- stat cards -->
    <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <div class="card p-5 flex items-center gap-4">
        <div class="w-11 h-11 rounded-xl bg-brand-50 flex items-center justify-center"><BookOpen class="w-5.5 h-5.5 text-brand-600" /></div>
        <div><div class="text-2xl font-extrabold text-slate-900">{{ enrollments.length }}</div><div class="text-xs text-slate-400">Enrolled courses</div></div>
      </div>
      <div class="card p-5 flex items-center gap-4">
        <div class="w-11 h-11 rounded-xl bg-amber-50 flex items-center justify-center"><Flame class="w-5.5 h-5.5 text-amber-500" /></div>
        <div><div class="text-2xl font-extrabold text-slate-900">{{ inProgress.length }}</div><div class="text-xs text-slate-400">In progress</div></div>
      </div>
      <div class="card p-5 flex items-center gap-4">
        <div class="w-11 h-11 rounded-xl bg-emerald-50 flex items-center justify-center"><Trophy class="w-5.5 h-5.5 text-emerald-600" /></div>
        <div><div class="text-2xl font-extrabold text-slate-900">{{ certificates.length }}</div><div class="text-xs text-slate-400">Certificates</div></div>
      </div>
      <div class="card p-5 flex items-center gap-4">
        <div class="w-11 h-11 rounded-xl bg-slate-100 flex items-center justify-center"><TrendingUp class="w-5.5 h-5.5 text-slate-500" /></div>
        <div><div class="text-2xl font-extrabold text-slate-900">{{ avgProgress }}%</div><div class="text-xs text-slate-400">Avg. progress</div></div>
      </div>
    </div>

    <!-- continue learning -->
    <div v-if="inProgress.length" class="mb-10">
      <h2 class="text-lg font-bold text-slate-800 mb-4">Continue learning</h2>
      <div class="grid md:grid-cols-2 gap-4">
        <div v-for="e in inProgress" :key="e.id" class="card p-4 flex gap-4 items-center hover:border-brand-300 transition">
          <div class="w-16 h-16 rounded-xl bg-gradient-to-br from-brand-500 to-slate-700 flex items-center justify-center shrink-0">
            <PlayCircle class="w-7 h-7 text-white/80" />
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="font-bold text-slate-800 truncate">{{ e.course.title }}</h3>
            <div class="mt-2 h-2 rounded-full bg-slate-100 overflow-hidden">
              <div class="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-400" :style="`width:${e.progress}%`" />
            </div>
            <div class="mt-1.5 flex items-center justify-between text-xs">
              <span class="text-slate-400 flex items-center gap-1"><Clock class="w-3 h-3" /> {{ e.course.total_minutes }} min left total</span>
              <b class="text-brand-700">{{ Math.round(e.progress) }}%</b>
            </div>
          </div>
          <NuxtLink :to="`/learn/${e.course.slug}`" class="btn-primary shrink-0">Resume</NuxtLink>
        </div>
      </div>
    </div>

    <!-- completed -->
    <div v-if="completed.length" class="mb-10">
      <h2 class="text-lg font-bold text-slate-800 mb-4">Completed 🎓</h2>
      <div class="grid md:grid-cols-2 gap-4">
        <div v-for="e in completed" :key="e.id" class="card p-4 flex gap-4 items-center border-brand-200">
          <div class="w-16 h-16 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shrink-0">
            <Trophy class="w-7 h-7 text-white" />
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="font-bold text-slate-800 truncate">{{ e.course.title }}</h3>
            <p class="text-xs text-slate-400 mt-0.5">100% complete</p>
          </div>
          <NuxtLink :to="`/learn/${e.course.slug}`" class="btn-secondary shrink-0 text-sm">Review</NuxtLink>
        </div>
      </div>
    </div>

    <EmptyState v-if="!loading && enrollments.length === 0" empty>
      You haven't enrolled in any courses yet. <NuxtLink to="/courses" class="text-brand-700 font-semibold">Browse the catalog →</NuxtLink>
    </EmptyState>

    <div v-if="loading" class="space-y-4">
      <div v-for="i in 2" :key="i" class="card h-24 animate-pulse" />
    </div>
  </div>
</template>
