<script setup lang="ts">
import { ChevronLeft, ChevronRight, ClipboardList, Unlock, CalendarDays, Video } from 'lucide-vue-next'

useSeoMeta({ title: 'Calendar - Infohive' })
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const today = new Date()
const cursor = ref(new Date(today.getFullYear(), today.getMonth(), 1))
const events = ref<any[]>([])
const loading = ref(true)
const selected = ref<string | null>(null)

const pad = (n: number) => String(n).padStart(2, '0')
const dayKey = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
// API times are UTC; show them in the viewer's local time
const toLocal = (iso: string) => new Date(iso.endsWith('Z') ? iso : iso + 'Z')

const gridDays = computed(() => {
  const first = new Date(cursor.value)
  const start = new Date(first)
  start.setDate(1 - ((first.getDay() + 6) % 7)) // weeks start on Monday
  return Array.from({ length: 42 }, (_, i) => {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    return d
  })
})

const load = async () => {
  loading.value = true
  const days = gridDays.value
  try {
    events.value = await api.get<any[]>('/me/calendar', {
      start: dayKey(days[0]), end: dayKey(days[days.length - 1]),
    })
  } catch { events.value = [] } finally { loading.value = false }
}
watch(cursor, load)
onMounted(load)

const byDay = computed(() => {
  const map: Record<string, any[]> = {}
  for (const e of events.value) (map[dayKey(toLocal(e.date))] ||= []).push(e)
  return map
})
const monthLabel = computed(() => cursor.value.toLocaleDateString(undefined, { month: 'long', year: 'numeric' }))
const shift = (n: number) => {
  selected.value = null
  cursor.value = new Date(cursor.value.getFullYear(), cursor.value.getMonth() + n, 1)
}
const goToday = () => { selected.value = dayKey(today); cursor.value = new Date(today.getFullYear(), today.getMonth(), 1) }

const inMonth = (d: Date) => d.getMonth() === cursor.value.getMonth()
const isToday = (d: Date) => dayKey(d) === dayKey(today)

// agenda: the selected day, or everything in this month from today on
const agenda = computed(() => {
  if (selected.value) return byDay.value[selected.value] || []
  return events.value.filter(e => {
    const d = toLocal(e.date)
    return d.getMonth() === cursor.value.getMonth() && d.getFullYear() === cursor.value.getFullYear()
  })
})
const time = (iso: string) => toLocal(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
const dateLong = (iso: string) => toLocal(iso).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })

const statusBadge = (e: any) => ({
  todo: ['To do', 'bg-sky-50 text-sky-700'],
  overdue: ['Overdue', 'bg-rose-50 text-rose-700'],
  submitted: ['Submitted', 'bg-brand-50 text-brand-700'],
  graded: ['Graded', 'bg-brand-50 text-brand-700'],
  upcoming: ['Unlocks', 'bg-amber-50 text-amber-700'],
  unlocked: ['Unlocked', 'bg-slate-100 text-slate-600'],
  live: ['Live class', 'bg-rose-50 text-rose-700'],
}[e.status as string] || (e.role === 'teacher' ? ['Due (your course)', 'bg-violet-50 text-violet-700'] : null))

const dot = (e: any) => e.type === 'live' ? 'bg-rose-500 ring-2 ring-rose-200' : e.type === 'unlock' ? 'bg-amber-500' : e.status === 'overdue' ? 'bg-rose-500' : e.role === 'teacher' ? 'bg-violet-500' : 'bg-sky-500'
const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
</script>

<template>
  <div class="max-w-6xl">
    <div class="flex flex-wrap items-center justify-between gap-3 mb-5">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Calendar</h1>
        <p class="text-slate-500 text-sm mt-0.5">Live classes, assignment due dates and lessons that unlock over time.</p>
      </div>
      <div class="flex items-center gap-1">
        <button class="btn-secondary !px-2.5" aria-label="Previous month" @click="shift(-1)"><ChevronLeft class="w-4 h-4" /></button>
        <button class="btn-secondary text-sm" @click="goToday">Today</button>
        <button class="btn-secondary !px-2.5" aria-label="Next month" @click="shift(1)"><ChevronRight class="w-4 h-4" /></button>
      </div>
    </div>

    <div class="grid lg:grid-cols-[1fr_20rem] gap-5">
      <!-- month grid -->
      <div class="card p-3 sm:p-4">
        <h2 class="font-bold text-slate-800 mb-3 px-1">{{ monthLabel }}</h2>
        <div class="grid grid-cols-7 text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-1">
          <div v-for="w in weekdays" :key="w" class="px-1 py-1 text-center sm:text-left">{{ w.slice(0, 1) }}<span class="hidden sm:inline">{{ w.slice(1) }}</span></div>
        </div>
        <div class="grid grid-cols-7 gap-px bg-slate-100 rounded-xl overflow-hidden border border-slate-100">
          <button v-for="d in gridDays" :key="dayKey(d)" type="button" @click="selected = selected === dayKey(d) ? null : dayKey(d)"
            class="bg-white text-left p-1 sm:p-1.5 min-h-[3.25rem] sm:min-h-[5.5rem] transition hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 relative"
            :class="[!inMonth(d) && 'opacity-40', selected === dayKey(d) && '!bg-brand-50 ring-1 ring-inset ring-brand-300']">
            <span class="inline-flex w-6 h-6 items-center justify-center rounded-full text-xs font-semibold"
              :class="isToday(d) ? 'bg-brand-600 text-white' : 'text-slate-600'">{{ d.getDate() }}</span>
            <!-- phones: dots -->
            <div class="flex flex-wrap gap-0.5 mt-0.5 sm:hidden">
              <span v-for="(e, i) in (byDay[dayKey(d)] || []).slice(0, 4)" :key="i" class="w-1.5 h-1.5 rounded-full" :class="dot(e)" />
            </div>
            <!-- larger screens: labels -->
            <div class="hidden sm:block space-y-0.5 mt-0.5">
              <div v-for="(e, i) in (byDay[dayKey(d)] || []).slice(0, 2)" :key="i"
                class="text-[10.5px] leading-tight truncate rounded px-1 py-0.5 flex items-center gap-1 bg-slate-50 text-slate-700">
                <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="dot(e)" />{{ e.title }}
              </div>
              <div v-if="(byDay[dayKey(d)] || []).length > 2" class="text-[10px] text-slate-400 px-1">+{{ byDay[dayKey(d)].length - 2 }} more</div>
            </div>
          </button>
        </div>
        <div class="flex flex-wrap gap-x-4 gap-y-1 mt-3 px-1 text-xs text-slate-500">
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-sky-500" /> Assignment due</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-rose-500" /> Overdue</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-amber-500" /> Lesson unlocks</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-rose-500 ring-2 ring-rose-200" /> Live class</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-violet-500" /> Due in a course you teach</span>
        </div>
      </div>

      <!-- agenda -->
      <div class="card p-4">
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-bold text-slate-800">{{ selected ? dateLong(selected + 'T12:00:00') : 'This month' }}</h2>
          <button v-if="selected" class="text-xs text-brand-700 font-semibold hover:underline" @click="selected = null">Show month</button>
        </div>
        <div v-if="loading" class="space-y-2"><div v-for="i in 3" :key="i" class="h-14 rounded-lg bg-slate-100 animate-pulse" /></div>
        <div v-else-if="!agenda.length" class="text-center py-10 text-slate-400 text-sm">
          <CalendarDays class="w-9 h-9 mx-auto mb-2 opacity-60" />Nothing scheduled{{ selected ? ' this day' : '' }}.
        </div>
        <ul v-else class="space-y-2">
          <li v-for="(e, i) in agenda" :key="i">
            <NuxtLink :to="e.link" class="flex gap-3 p-2.5 rounded-xl hover:bg-slate-50 border border-slate-100 transition">
              <div class="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
                :class="e.type === 'live' ? 'bg-rose-50 text-rose-600' : e.type === 'unlock' ? 'bg-amber-50 text-amber-600' : 'bg-sky-50 text-sky-600'">
                <component :is="e.type === 'live' ? Video : e.type === 'unlock' ? Unlock : ClipboardList" class="w-4.5 h-4.5" />
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-semibold text-slate-800 truncate">{{ e.title }}</p>
                <p class="text-xs text-slate-500 truncate">{{ e.course_title }}</p>
                <div class="flex items-center gap-2 mt-1">
                  <span class="text-[11px] text-slate-400">{{ selected ? '' : dateLong(e.date) + ' · ' }}{{ time(e.date) }}</span>
                  <span v-if="statusBadge(e)" class="badge !text-[10px]" :class="statusBadge(e)![1]">{{ statusBadge(e)![0] }}</span>
                </div>
              </div>
            </NuxtLink>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
