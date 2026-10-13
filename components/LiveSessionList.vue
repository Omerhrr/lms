<script setup lang="ts">
import { Video, ExternalLink, PlayCircle, CalendarClock, Radio, CheckCircle2 } from 'lucide-vue-next'

/** Live classes for one course (courseId) or, without it, the signed-in user's upcoming classes. */
const props = defineProps<{ courseId?: number; compact?: boolean; showCourse?: boolean }>()
const emit = defineEmits<{ loaded: [upcoming: number] }>()
const api = useApi()
const sessions = ref<any[]>([])
const loading = ref(true)

const load = async () => {
  loading.value = true
  try {
    sessions.value = await api.get<any[]>(props.courseId ? `/courses/${props.courseId}/live` : '/me/live', undefined, true)
  } catch { sessions.value = [] } finally {
    loading.value = false
    emit('loaded', sessions.value.filter(s => ['upcoming', 'starting_soon', 'live'].includes(s.state)).length)
  }
}
onMounted(load)
// refresh states (upcoming -> starting soon -> live) every minute
let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => { timer = setInterval(load, 60_000) })
onBeforeUnmount(() => clearInterval(timer))

const upcoming = computed(() => sessions.value.filter(s => ['upcoming', 'starting_soon', 'live'].includes(s.state)))
const past = computed(() => sessions.value.filter(s => s.state === 'ended').reverse())
const when = (iso: string) => new Date(iso).toLocaleString(undefined, { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
const badge = (s: any) => ({
  live: ['Live now', 'bg-rose-50 text-rose-700'], starting_soon: ['Starting soon', 'bg-amber-50 text-amber-700'],
  upcoming: ['Scheduled', 'bg-slate-100 text-slate-600'], cancelled: ['Cancelled', 'bg-slate-100 text-slate-500 line-through'],
  ended: ['Ended', 'bg-slate-100 text-slate-500'],
}[s.state as string] || ['', ''])
defineExpose({ reload: load })
</script>

<template>
  <div>
    <div v-if="loading" class="space-y-2"><div v-for="i in 2" :key="i" class="h-16 rounded-xl bg-slate-100 animate-pulse" /></div>
    <template v-else>
      <div v-if="!upcoming.length && (compact || !past.length)" class="text-center py-8 text-sm text-slate-500">
        <CalendarClock class="w-9 h-9 mx-auto mb-2 text-slate-300" />No live classes scheduled{{ courseId ? ' for this course' : '' }} yet.
      </div>
      <ul v-if="upcoming.length" class="space-y-2.5">
        <li v-for="s in upcoming" :key="s.id" class="flex flex-wrap sm:flex-nowrap items-center gap-3 p-3 sm:p-4 rounded-xl border"
          :class="s.state === 'live' ? 'border-rose-200 bg-rose-50/40' : 'border-slate-200 bg-white'">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            :class="s.state === 'live' ? 'bg-rose-500 text-white' : 'bg-brand-50 text-brand-600'">
            <component :is="s.state === 'live' ? Radio : Video" class="w-5 h-5" :class="s.state === 'live' && 'animate-pulse'" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="font-semibold text-slate-800 truncate">{{ s.title }}</p>
            <p class="text-xs text-slate-500 truncate">
              <span v-if="showCourse && s.course">{{ s.course.title }} · </span>{{ when(s.starts_at) }} · {{ fmtMinutes(s.duration_minutes) }}
              <span v-if="s.provider === 'external'"> · external link</span>
            </p>
          </div>
          <span class="badge shrink-0" :class="badge(s)[1]">{{ badge(s)[0] }}</span>
          <NuxtLink :to="`/live/${s.id}`" class="shrink-0 w-full sm:w-auto"
            :class="s.can_join ? 'btn-primary text-sm' : 'btn-secondary text-sm'">
            {{ s.can_join ? 'Join' : 'Details' }}
          </NuxtLink>
        </li>
      </ul>
      <div v-if="!compact && past.length" class="mt-6">
        <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Past classes</h4>
        <ul class="divide-y divide-slate-100 border border-slate-100 rounded-xl bg-white">
          <li v-for="s in past" :key="s.id" class="flex items-center gap-3 px-4 py-3 text-sm">
            <CheckCircle2 v-if="s.attended" class="w-4 h-4 text-brand-500 shrink-0" />
            <Video v-else class="w-4 h-4 text-slate-300 shrink-0" />
            <span class="flex-1 min-w-0 truncate text-slate-700">{{ s.title }} <span class="text-slate-500">· {{ when(s.starts_at) }}</span></span>
            <NuxtLink v-if="s.recording_url" :to="`/live/${s.id}`" class="text-brand-700 font-semibold inline-flex items-center gap-1 shrink-0">
              <PlayCircle class="w-4 h-4" /> Recording
            </NuxtLink>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>
