<script setup lang="ts">
import { BookOpen, Users, Trophy, Banknote, Plus, TrendingUp, ClipboardCheck, UserX, FilePen, CheckCircle2, Mail } from 'lucide-vue-next'

useSeoMeta({ title: 'Instructor Studio - Infohive' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const { config: platform } = usePlatform()
const revenue = (n?: number | null) => new Intl.NumberFormat(undefined, { style: 'currency', currencyDisplay: 'narrowSymbol', currency: platform.value.currency, maximumFractionDigits: 0 }).format(n || 0)
const showRevenue = computed(() => platform.value.payments_enabled || (overview.value?.totals.revenue || 0) > 0)

const api = useApi()
const auth = useAuth()
const overview = ref<any>(null)
const actions = ref<any>(null)
const liveCount = ref(0)
const loading = ref(true)

onMounted(async () => {
  try {
    const [o, a] = await Promise.all([
      api.get<any>('/teach/analytics/overview'),
      api.get<any>('/teach/actions', undefined, true).catch(() => null),
    ])
    overview.value = o
    actions.value = a
  } finally { loading.value = false }
})

const ago = (iso: string) => {
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000)
  return d <= 0 ? 'today' : d === 1 ? 'yesterday' : `${d} days ago`
}
const gradeGroups = computed(() => {
  const m = new Map<number, { course_id: number; course_title: string; items: any[] }>()
  for (const s of actions.value?.to_grade || []) {
    if (!m.has(s.course_id)) m.set(s.course_id, { course_id: s.course_id, course_title: s.course_title, items: [] })
    m.get(s.course_id)!.items.push(s)
  }
  return [...m.values()]
})
const allClear = computed(() => actions.value && !actions.value.to_grade.length && !actions.value.stalled.length && !actions.value.drafts.length)
</script>

<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Instructor studio</h1>
        <p class="text-slate-600 mt-1">Welcome back, {{ auth.user.value?.full_name.split(' ')[0] }}. Here's what needs you today.</p>
      </div>
      <div class="flex gap-2">
        <NuxtLink to="/teach/courses" class="btn-secondary">My courses</NuxtLink>
        <NuxtLink to="/teach/courses/new" class="btn-primary"><Plus class="w-4 h-4" /> New course</NuxtLink>
      </div>
    </div>

    <div v-if="loading" class="space-y-4 mb-8"><div class="card h-40 animate-pulse" /><div class="card h-24 animate-pulse" /></div>

    <template v-else>
      <!-- action centre -->
      <div v-if="allClear" class="card p-5 mb-8 flex items-center gap-3 text-slate-700">
        <CheckCircle2 class="w-6 h-6 text-brand-600" /> You're all caught up - nothing to grade, nobody stalled, no drafts waiting.
      </div>
      <div v-else-if="actions" class="grid lg:grid-cols-3 gap-4 mb-8">
        <div class="card p-5">
          <h2 class="font-bold text-slate-900 flex items-center gap-2"><ClipboardCheck class="w-5 h-5 text-brand-600" /> To grade <span class="badge bg-brand-50 text-brand-700">{{ actions.to_grade.length }}</span></h2>
          <p v-if="!actions.to_grade.length" class="mt-3 text-sm text-slate-500">No submissions waiting.</p>
          <ul v-else class="mt-3 space-y-3">
            <li v-for="g in gradeGroups" :key="g.course_id">
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-semibold text-slate-800 truncate">{{ g.course_title }}</span>
                <NuxtLink :to="`/teach/courses/${g.course_id}/gradebook`" class="text-sm font-semibold text-brand-700 hover:underline shrink-0">Grade {{ g.items.length }} →</NuxtLink>
              </div>
              <p class="text-xs text-slate-500 truncate">{{ g.items.slice(0, 3).map(i => `${i.student} · ${i.assignment}`).join(', ') }}<span v-if="g.items.length > 3"> …</span></p>
            </li>
          </ul>
        </div>

        <div class="card p-5">
          <h2 class="font-bold text-slate-900 flex items-center gap-2"><UserX class="w-5 h-5 text-amber-600" /> Stalled learners <span class="badge bg-amber-50 text-amber-700">{{ actions.stalled_total }}</span></h2>
          <p class="text-xs text-slate-500 mt-1">No activity for 7+ days</p>
          <p v-if="!actions.stalled.length" class="mt-3 text-sm text-slate-500">Everyone's moving.</p>
          <ul v-else class="mt-3 space-y-2.5">
            <li v-for="s in actions.stalled.slice(0, 5)" :key="s.email + s.course_id" class="flex items-center gap-2 text-sm min-w-0">
              <div class="flex-1 min-w-0">
                <div class="font-semibold text-slate-800 truncate">{{ s.student }} <span class="font-normal text-slate-500">· {{ Math.round(s.progress) }}%</span></div>
                <div class="text-xs text-slate-500 truncate">{{ s.course_title }} · last active {{ ago(s.last_active) }}</div>
              </div>
              <a :href="`mailto:${s.email}?subject=${encodeURIComponent('Checking in: ' + s.course_title)}`" class="p-1.5 rounded-lg text-slate-500 hover:text-brand-700 hover:bg-brand-50" :aria-label="`Email ${s.student}`"><Mail class="w-4 h-4" /></a>
            </li>
          </ul>
        </div>

        <div class="card p-5">
          <h2 class="font-bold text-slate-900 flex items-center gap-2"><FilePen class="w-5 h-5 text-slate-600" /> Drafts <span class="badge bg-slate-100 text-slate-600">{{ actions.drafts.length }}</span></h2>
          <p v-if="!actions.drafts.length" class="mt-3 text-sm text-slate-500">No unpublished courses.</p>
          <ul v-else class="mt-3 space-y-3">
            <li v-for="d in actions.drafts" :key="d.course_id">
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-semibold text-slate-800 truncate">{{ d.title }}</span>
                <NuxtLink :to="`/teach/courses/${d.course_id}/edit`" class="text-sm font-semibold text-brand-700 hover:underline shrink-0">Finish →</NuxtLink>
              </div>
              <p class="text-xs text-slate-500">{{ d.todo.length ? `To do: ${d.todo.slice(0, 3).join(', ').toLowerCase()}` : 'Ready to publish' }}</p>
            </li>
          </ul>
        </div>
      </div>

      <!-- headline numbers -->
      <div class="grid grid-cols-2 gap-3 mb-8" :class="showRevenue ? 'lg:grid-cols-4' : 'lg:grid-cols-3'">
        <div class="card p-4 flex items-center gap-3">
          <BookOpen class="w-5 h-5 text-brand-600" />
          <div><div class="text-xl font-extrabold">{{ overview?.totals.courses }}</div><div class="text-xs text-slate-600">Courses</div></div>
        </div>
        <div class="card p-4 flex items-center gap-3">
          <Users class="w-5 h-5 text-sky-600" />
          <div><div class="text-xl font-extrabold">{{ overview?.totals.enrollments }}</div><div class="text-xs text-slate-600">Enrollments</div></div>
        </div>
        <div class="card p-4 flex items-center gap-3">
          <Trophy class="w-5 h-5 text-emerald-600" />
          <div><div class="text-xl font-extrabold">{{ overview?.totals.completions }}</div><div class="text-xs text-slate-600">Completions</div></div>
        </div>
        <div v-if="showRevenue" class="card p-4 flex items-center gap-3">
          <Banknote class="w-5 h-5 text-amber-600" />
          <div><div class="text-xl font-extrabold">{{ revenue(overview?.totals.revenue) }}</div><div class="text-xs text-slate-600">Revenue</div></div>
        </div>
      </div>

      <div v-show="liveCount" class="card p-5 mb-8">
        <h2 class="font-bold text-slate-800 mb-3">Upcoming live classes</h2>
        <LiveSessionList compact show-course @loaded="liveCount = $event" />
      </div>

      <h2 class="text-lg font-bold text-slate-800 mb-4">Course performance</h2>
      <div class="card overflow-hidden overflow-x-auto">
        <table class="table-base">
          <thead><tr><th>Course</th><th>Status</th><th>Enrollments</th><th>Completions</th><th>Rate</th><th v-if="showRevenue">Revenue</th><th /></tr></thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="c in overview?.per_course || []" :key="c.id" class="hover:bg-slate-50">
              <td class="font-semibold text-slate-800"><NuxtLink :to="`/teach/courses/${c.id}/builder`" class="hover:text-brand-700">{{ c.title }}</NuxtLink></td>
              <td><span class="badge" :class="c.status === 'published' ? 'bg-brand-50 text-brand-700' : 'bg-slate-100 text-slate-600'">{{ c.status }}</span></td>
              <td>{{ c.enrollments }}</td>
              <td>{{ c.completions }}</td>
              <td>{{ c.completion_rate }}%</td>
              <td v-if="showRevenue" class="font-semibold">{{ revenue(c.revenue) }}</td>
              <td><NuxtLink :to="`/teach/courses/${c.id}/analytics`" class="text-brand-700 hover:underline text-sm font-semibold flex items-center gap-1"><TrendingUp class="w-3.5 h-3.5" /> Details</NuxtLink></td>
            </tr>
            <tr v-if="overview && overview.per_course.length === 0"><td colspan="7" class="text-center text-slate-500 py-8">No courses yet - create your first one!</td></tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
