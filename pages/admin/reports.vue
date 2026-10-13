<script setup lang="ts">
import { Mail, Table2, BarChart3 } from 'lucide-vue-next'

useSeoMeta({ title: 'Reports - Admin - Infohive' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const api = useApi()
const days = ref(30)
const data = ref<any>(null)
const loading = ref(true)
const asTable = ref(false)

const load = async () => {
  loading.value = true
  try { data.value = await api.get<any>('/admin/reports', { days: days.value }) } finally { loading.value = false }
}
watch(days, load)
onMounted(load)

const tiles = computed(() => {
  const t = data.value?.totals
  if (!t) return []
  return [
    { label: 'Active learners (7 days)', value: t.active_7d, hint: `of ${t.learners} learners` },
    { label: `New enrollments`, value: t.new_enrollments, hint: `last ${days.value} days` },
    { label: 'Courses completed', value: t.completions, hint: `last ${days.value} days` },
    { label: 'Lessons completed', value: t.lessons_completed, hint: `last ${days.value} days` },
  ]
})
const weekLabel = (iso: string) => new Date(iso + 'T00:00').toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
// three single-series charts, one per measure (never two scales on one chart)
const charts = computed(() => {
  const s = data.value?.series
  if (!s) return []
  return [
    { key: 'enrollments', title: 'New enrollments per week', values: s.enrollments },
    { key: 'completions', title: 'Course completions per week', values: s.completions },
    { key: 'lessons', title: 'Lessons completed per week', values: s.lessons },
  ].map(c => ({ ...c, max: Math.max(1, ...c.values), total: c.values.reduce((a: number, b: number) => a + b, 0) }))
})
const hover = ref<{ chart: string; i: number } | null>(null)
const ago = (iso: string) => {
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000)
  return d <= 0 ? 'today' : `${d} days ago`
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Learning reports</h1>
        <p class="text-slate-600 mt-1">How learners are doing across the whole platform.</p>
      </div>
      <div role="tablist" aria-label="Period" class="flex gap-1 rounded-xl bg-slate-100 p-1">
        <button v-for="d in [7, 30, 90]" :key="d" role="tab" :aria-selected="days === d" type="button"
          class="px-3 py-1.5 rounded-lg text-sm font-semibold transition"
          :class="days === d ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'" @click="days = d">{{ d }} days</button>
      </div>
    </div>

    <div v-if="loading && !data" class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6"><div v-for="i in 4" :key="i" class="card h-24 animate-pulse" /></div>

    <template v-if="data">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6" :class="loading && 'opacity-60'">
        <div v-for="t in tiles" :key="t.label" class="card p-4">
          <div class="text-xs font-semibold text-slate-600">{{ t.label }}</div>
          <div class="mt-1 text-3xl font-extrabold text-slate-900 tabular-nums">{{ t.value }}</div>
          <div class="text-xs text-slate-500">{{ t.hint }}</div>
        </div>
      </div>

      <!-- weekly activity -->
      <div class="card p-5 mb-6">
        <div class="flex items-center justify-between gap-3 mb-4">
          <h2 class="font-bold text-slate-900">Last 12 weeks</h2>
          <button type="button" class="btn-ghost text-sm" :aria-pressed="asTable" @click="asTable = !asTable">
            <component :is="asTable ? BarChart3 : Table2" class="w-4 h-4" /> {{ asTable ? 'Show charts' : 'Show as table' }}
          </button>
        </div>
        <div v-if="!asTable" class="grid lg:grid-cols-3 gap-6">
          <figure v-for="c in charts" :key="c.key" class="min-w-0">
            <figcaption class="flex items-baseline justify-between text-sm mb-2">
              <span class="font-semibold text-slate-800">{{ c.title }}</span>
              <span class="text-slate-600 tabular-nums">{{ c.total }} total</span>
            </figcaption>
            <div class="relative h-36 flex items-end gap-[2px] border-b border-slate-200" role="img" :aria-label="`${c.title}: ${c.values.join(', ')}`">
              <div v-for="(v, i) in c.values" :key="i" class="relative flex-1 h-full flex items-end cursor-default"
                @mouseenter="hover = { chart: c.key, i }" @mouseleave="hover = null">
                <div class="w-full rounded-t bg-brand-500 transition-opacity" :class="hover && hover.chart === c.key && hover.i !== i ? 'opacity-50' : ''"
                  :style="`height:${v ? Math.max(4, (v / c.max) * 100) : 0}%`" />
                <div v-if="hover?.chart === c.key && hover.i === i" class="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 z-10 whitespace-nowrap rounded-lg bg-slate-900 text-white text-xs px-2 py-1 shadow-lg pointer-events-none">
                  Week of {{ weekLabel(data.series.weeks[i]) }}: <b>{{ v }}</b>
                </div>
              </div>
            </div>
            <div class="flex justify-between text-xs text-slate-500 mt-1">
              <span>{{ weekLabel(data.series.weeks[0]) }}</span><span>This week</span>
            </div>
          </figure>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="table-base">
            <thead><tr><th>Week of</th><th class="text-right">Enrollments</th><th class="text-right">Completions</th><th class="text-right">Lessons</th></tr></thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="(w, i) in data.series.weeks" :key="w">
                <td>{{ weekLabel(w) }}</td>
                <td class="text-right tabular-nums">{{ data.series.enrollments[i] }}</td>
                <td class="text-right tabular-nums">{{ data.series.completions[i] }}</td>
                <td class="text-right tabular-nums">{{ data.series.lessons[i] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- per course -->
      <div class="card overflow-x-auto mb-6">
        <h2 class="font-bold text-slate-900 px-5 pt-5 pb-3">By course</h2>
        <table class="table-base">
          <thead><tr><th>Course</th><th class="text-right">Learners</th><th class="text-right">Active ({{ days }}d)</th><th>Average progress</th><th class="text-right">Completion rate</th></tr></thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="c in data.per_course" :key="c.id" class="hover:bg-slate-50">
              <td class="min-w-[12rem]">
                <NuxtLink :to="`/admin/enrollments?course_id=${c.id}`" class="font-semibold text-slate-900 hover:text-brand-700">{{ c.title }}</NuxtLink>
                <div class="text-xs text-slate-500">{{ c.instructor }}<span v-if="c.status !== 'published'"> · {{ c.status }}</span></div>
              </td>
              <td class="text-right tabular-nums">{{ c.enrollments }}</td>
              <td class="text-right tabular-nums">{{ c.active }}</td>
              <td class="min-w-[9rem]">
                <div class="flex items-center gap-2">
                  <div class="h-2 w-24 rounded-full bg-slate-100 overflow-hidden"><div class="h-full bg-brand-500 rounded-full" :style="`width:${c.avg_progress}%`" /></div>
                  <span class="text-sm tabular-nums">{{ Math.round(c.avg_progress) }}%</span>
                </div>
              </td>
              <td class="text-right tabular-nums">{{ c.enrollments ? `${c.completion_rate}%` : '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- stalled -->
      <div class="card p-5">
        <h2 class="font-bold text-slate-900">Learners who've gone quiet <span class="badge bg-amber-50 text-amber-700 ml-1">{{ data.stalled_total }}</span></h2>
        <p class="text-sm text-slate-600 mt-0.5">Started a course but no activity for 14+ days.</p>
        <p v-if="!data.stalled.length" class="mt-4 text-sm text-slate-600">Nobody right now.</p>
        <ul v-else class="mt-4 divide-y divide-slate-100">
          <li v-for="s in data.stalled" :key="s.enrollment_id" class="py-2.5 flex items-center gap-3">
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-slate-900 truncate">{{ s.student }} <span class="font-normal text-slate-600">· {{ Math.round(s.progress) }}%</span></p>
              <p class="text-xs text-slate-600 truncate">{{ s.course_title }} · last active {{ ago(s.last_active) }}</p>
            </div>
            <a :href="`mailto:${s.email}?subject=${encodeURIComponent('Checking in: ' + s.course_title)}`" class="btn-ghost text-sm shrink-0" :aria-label="`Email ${s.student}`"><Mail class="w-4 h-4" /> <span class="hidden sm:inline">Email</span></a>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>
