<script setup lang="ts">
import { BookOpen, Users, Trophy, DollarSign, Plus, TrendingUp } from 'lucide-vue-next'

useSeoMeta({ title: 'Instructor Studio — LearnHub' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const api = useApi()
const auth = useAuth()

const overview = ref<any>(null)
const courses = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [o, c] = await Promise.all([api.get<any>('/teach/analytics/overview'), api.get<any[]>('/teach/courses')])
    overview.value = o
    courses.value = c
  } finally { loading.value = false }
})

const fmt = (n: number) => n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n)
</script>

<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Instructor studio</h1>
        <p class="text-slate-500 mt-1">Welcome back, {{ auth.user.value?.full_name.split(' ')[0] }}. Here's how your courses are doing.</p>
      </div>
      <NuxtLink to="/teach/courses/new" class="btn-primary"><Plus class="w-4 h-4" /> New course</NuxtLink>
    </div>

    <div v-if="loading" class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <div v-for="i in 4" :key="i" class="card h-24 animate-pulse" />
    </div>

    <div v-else class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
      <div class="card p-5 flex items-center gap-4">
        <div class="w-11 h-11 rounded-xl bg-brand-50 flex items-center justify-center"><BookOpen class="w-5.5 h-5.5 text-brand-600" /></div>
        <div><div class="text-2xl font-extrabold">{{ overview?.totals.courses }}</div><div class="text-xs text-slate-400">Courses</div></div>
      </div>
      <div class="card p-5 flex items-center gap-4">
        <div class="w-11 h-11 rounded-xl bg-sky-50 flex items-center justify-center"><Users class="w-5.5 h-5.5 text-sky-600" /></div>
        <div><div class="text-2xl font-extrabold">{{ overview?.totals.enrollments }}</div><div class="text-xs text-slate-400">Enrollments</div></div>
      </div>
      <div class="card p-5 flex items-center gap-4">
        <div class="w-11 h-11 rounded-xl bg-emerald-50 flex items-center justify-center"><Trophy class="w-5.5 h-5.5 text-emerald-600" /></div>
        <div><div class="text-2xl font-extrabold">{{ overview?.totals.completions }}</div><div class="text-xs text-slate-400">Completions</div></div>
      </div>
      <div class="card p-5 flex items-center gap-4">
        <div class="w-11 h-11 rounded-xl bg-amber-50 flex items-center justify-center"><DollarSign class="w-5.5 h-5.5 text-amber-600" /></div>
        <div><div class="text-2xl font-extrabold">${{ overview?.totals.revenue?.toLocaleString() }}</div><div class="text-xs text-slate-400">Revenue</div></div>
      </div>
    </div>

    <!-- per course -->
    <h2 class="text-lg font-bold text-slate-800 mb-4">Course performance</h2>
    <div v-if="!loading" class="card overflow-hidden mb-10 overflow-x-auto">
      <table class="table-base">
        <thead><tr><th>Course</th><th>Status</th><th>Enrollments</th><th>Completions</th><th>Rate</th><th>Revenue</th><th /></tr></thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="c in overview?.per_course || []" :key="c.id" class="hover:bg-slate-50">
            <td class="font-semibold text-slate-800">{{ c.title }}</td>
            <td><span class="badge" :class="c.status === 'published' ? 'bg-brand-50 text-brand-700' : 'bg-slate-100 text-slate-500'">{{ c.status }}</span></td>
            <td>{{ c.enrollments }}</td>
            <td>{{ c.completions }}</td>
            <td>{{ c.completion_rate }}%</td>
            <td class="font-semibold">${{ c.revenue?.toLocaleString() }}</td>
            <td><NuxtLink :to="`/teach/courses/${c.id}/analytics`" class="text-brand-700 hover:underline text-sm font-semibold flex items-center gap-1"><TrendingUp class="w-3.5 h-3.5" /> Details</NuxtLink></td>
          </tr>
          <tr v-if="overview && overview.per_course.length === 0"><td colspan="7" class="text-center text-slate-400 py-8">No courses yet — create your first one!</td></tr>
        </tbody>
      </table>
    </div>

    <!-- quick access -->
    <h2 class="text-lg font-bold text-slate-800 mb-4">Your courses</h2>
    <div v-if="!loading" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <CourseCard v-for="c in courses" :key="c.id" :course="c" show-status />
    </div>
  </div>
</template>
