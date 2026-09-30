<script setup lang="ts">
import { Users, Trophy, DollarSign, TrendingUp, BarChart3, ClipboardList } from 'lucide-vue-next'

useSeoMeta({ title: 'Course analytics — LearnHub' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const route = useRoute()
const api = useApi()
const courseId = Number(route.params.id)

const data = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  try { data.value = await api.get<any>(`/teach/analytics/courses/${courseId}`) } finally { loading.value = false }
})

const trendSeries = computed(() => {
  if (!data.value?.trend_30d) return []
  const entries = Object.entries(data.value.trend_30d).sort(([a], [b]) => a.localeCompare(b))
  const max = Math.max(...entries.map(([, n]) => Number(n)), 1)
  return entries.map(([d, n]) => ({ date: d.slice(5), count: Number(n), pct: (Number(n) / max) * 100 }))
})

const fmtDate = (s: string) => {
  const [y, m, d] = s.split('-')
  return new Date(Number(y), Number(m) - 1, Number(d)).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-extrabold text-slate-900">Course analytics</h1>
      <p class="text-slate-500 mt-1">{{ data?.course?.title }}</p>
    </div>

    <div v-if="loading" class="space-y-4"><div class="card h-28 animate-pulse" /><div class="card h-64 animate-pulse" /></div>

    <template v-else-if="data">
      <!-- stat cards -->
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-sky-50 flex items-center justify-center"><Users class="w-5.5 h-5.5 text-sky-600" /></div>
          <div><div class="text-2xl font-extrabold">{{ data.enrollments }}</div><div class="text-xs text-slate-400">Enrollments</div></div>
        </div>
        <div class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-emerald-50 flex items-center justify-center"><Trophy class="w-5.5 h-5.5 text-emerald-600" /></div>
          <div><div class="text-2xl font-extrabold">{{ data.completion_rate }}%</div><div class="text-xs text-slate-400">Completion rate</div></div>
        </div>
        <div class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-amber-50 flex items-center justify-center"><DollarSign class="w-5.5 h-5.5 text-amber-600" /></div>
          <div><div class="text-2xl font-extrabold">${{ data.revenue?.toLocaleString() }}</div><div class="text-xs text-slate-400">Revenue</div></div>
        </div>
        <div class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-violet-50 flex items-center justify-center"><BarChart3 class="w-5.5 h-5.5 text-violet-600" /></div>
          <div><div class="text-2xl font-extrabold">{{ data.quiz_stats.reduce((s: number, q: any) => s + q.attempts, 0) }}</div><div class="text-xs text-slate-400">Quiz attempts</div></div>
        </div>
      </div>

      <!-- enrollment trend -->
      <div class="card p-5 mb-8" v-if="trendSeries.length">
        <h2 class="font-bold text-slate-800 mb-4 flex items-center gap-2"><TrendingUp class="w-4.5 h-4.5 text-brand-600" /> Enrollments — last 30 days</h2>
        <div class="flex items-end gap-1 h-36">
          <div v-for="t in trendSeries" :key="t.date" class="flex-1 group relative">
            <div class="w-full bg-gradient-to-t from-brand-600 to-brand-400 rounded-t transition-all group-hover:from-brand-700"
              :style="`height:${Math.max(t.pct, 4)}%`" />
            <div class="absolute -top-8 left-1/2 -translate-x-1/2 hidden group-hover:block bg-slate-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
              {{ fmtDate(t.date) }}: {{ t.count }}
            </div>
          </div>
        </div>
      </div>

      <div class="grid lg:grid-cols-2 gap-6">
        <!-- lesson funnel -->
        <div class="card p-5">
          <h2 class="font-bold text-slate-800 mb-4">Lesson completion</h2>
          <div class="space-y-3">
            <div v-for="l in data.lesson_stats" :key="l.lesson_id">
              <div class="flex justify-between text-sm mb-1">
                <span class="text-slate-600 truncate pr-3">{{ l.title }}</span>
                <span class="text-slate-400 text-xs shrink-0">{{ l.completed_by }} students</span>
              </div>
              <div class="h-2 rounded-full bg-slate-100 overflow-hidden">
                <div class="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-400" :style="`width:${l.pct}%`" />
              </div>
            </div>
            <p v-if="!data.lesson_stats.length" class="text-sm text-slate-400 text-center py-4">No lessons yet.</p>
          </div>
        </div>

        <!-- quizzes & assignments -->
        <div class="space-y-6">
          <div class="card p-5">
            <h2 class="font-bold text-slate-800 mb-4 flex items-center gap-2"><BarChart3 class="w-4.5 h-4.5 text-violet-500" /> Quiz performance</h2>
            <div v-if="data.quiz_stats.length" class="space-y-3">
              <div v-for="q in data.quiz_stats" :key="q.quiz_id" class="flex items-center justify-between text-sm">
                <span class="text-slate-600 truncate pr-3">{{ q.title }}</span>
                <span class="text-slate-400 text-xs shrink-0">{{ q.attempts }} attempts · avg <b class="text-slate-700">{{ q.avg_score }}%</b></span>
              </div>
            </div>
            <p v-else class="text-sm text-slate-400 text-center py-4">No quizzes yet.</p>
          </div>
          <div class="card p-5">
            <h2 class="font-bold text-slate-800 mb-4 flex items-center gap-2"><ClipboardList class="w-4.5 h-4.5 text-amber-500" /> Assignment submissions</h2>
            <div v-if="data.assignment_stats.length" class="space-y-3">
              <div v-for="a in data.assignment_stats" :key="a.assignment_id" class="flex items-center justify-between text-sm">
                <span class="text-slate-600 truncate pr-3">{{ a.title }}</span>
                <span class="badge bg-slate-100 text-slate-600 shrink-0">{{ a.submissions }} submissions</span>
              </div>
            </div>
            <p v-else class="text-sm text-slate-400 text-center py-4">No assignments yet.</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
