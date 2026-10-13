<script setup lang="ts">
import { ArrowLeft, Video, Clock, ExternalLink, LogOut, AlertTriangle, CalendarX2, PlayCircle, Users } from 'lucide-vue-next'

definePageMeta({ middleware: 'auth', layout: false })

const route = useRoute()
const api = useApi()
const { show } = useToast()
const id = Number(route.params.id)

const session = ref<any>(null)
const error = ref<string | null>(null)
const joining = ref(false)
const inRoom = ref(false)
const limited = ref(false)
const roomEl = ref<HTMLElement | null>(null)
const now = ref(Date.now())
let jitsi: any = null
let tick: ReturnType<typeof setInterval> | undefined

useSeoMeta({ title: () => session.value ? `${session.value.title} - Live class - Infohive` : 'Live class - Infohive' })

const load = async () => {
  try { session.value = await api.get<any>(`/live/${id}`, undefined, true) }
  catch (e: any) { error.value = e?.data?.detail || 'This live class is not available.' }
}

const startsAt = computed(() => session.value ? new Date(session.value.starts_at).getTime() : 0)
const doorsOpen = computed(() => startsAt.value - 15 * 60_000)
const countdown = computed(() => {
  const ms = Math.max(0, doorsOpen.value - now.value)
  const d = Math.floor(ms / 86_400_000), h = Math.floor(ms / 3_600_000) % 24, m = Math.floor(ms / 60_000) % 60, s = Math.floor(ms / 1000) % 60
  return d ? `${d}d ${h}h ${m}m` : h ? `${h}h ${m}m ${s}s` : `${m}m ${s}s`
})
// re-check with the server when the doors open
watch(() => now.value >= doorsOpen.value, (open) => { if (open && session.value?.state === 'upcoming') load() })

const whenLong = (iso: string) => new Date(iso).toLocaleString(undefined, { weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })

const loadScript = (src: string) => new Promise<void>((resolve, reject) => {
  if ((window as any).JitsiMeetExternalAPI) return resolve()
  const tag = document.createElement('script')
  tag.src = src
  tag.async = true
  tag.onload = () => resolve()
  tag.onerror = () => reject(new Error('load failed'))
  document.head.appendChild(tag)
})

const join = async () => {
  joining.value = true
  try {
    const info = await api.post<any>(`/live/${id}/join`)
    if (info.provider === 'external') {
      window.open(info.url, '_blank', 'noopener')
      show('The class opened in a new tab. Your attendance has been recorded.', 'info')
      return
    }
    limited.value = !!info.limited
    const tenant = info.room.includes('/') ? info.room.split('/')[0] + '/' : ''
    await loadScript(`https://${info.domain}/${tenant}external_api.js`)
    inRoom.value = true
    await nextTick()
    const Api = (window as any).JitsiMeetExternalAPI
    jitsi = new Api(info.domain, {
      roomName: info.room,
      jwt: info.jwt || undefined,
      parentNode: roomEl.value,
      width: '100%', height: '100%',
      userInfo: { displayName: info.display_name, email: info.email },
      configOverwrite: {
        subject: info.subject, prejoinPageEnabled: true, disableDeepLinking: true,
        startWithAudioMuted: !info.moderator, enableWelcomePage: false, enableClosePage: false,
      },
      interfaceConfigOverwrite: { MOBILE_APP_PROMO: false, SHOW_JITSI_WATERMARK: false, SHOW_PROMOTIONAL_CLOSE_PAGE: false },
    })
    jitsi.addListener('readyToClose', leave)
  } catch (e: any) {
    if (e?.data?.detail) show(e.data.detail, 'error')
    else show("Couldn't open the video room. Check your connection and try again.", 'error')
  } finally {
    joining.value = false
  }
}

const leave = () => {
  try { jitsi?.dispose() } catch { /* ignore */ }
  jitsi = null
  inRoom.value = false
  load()
}

onMounted(() => { load(); tick = setInterval(() => { now.value = Date.now() }, 1000) })
onBeforeUnmount(() => { clearInterval(tick); try { jitsi?.dispose() } catch { /* ignore */ } })
</script>

<template>
  <div class="min-h-[100dvh] bg-slate-950 text-slate-100 flex flex-col">
    <header class="h-14 bg-slate-900 border-b border-slate-800 flex items-center justify-between gap-3 px-3 sm:px-4 shrink-0">
      <div class="flex items-center gap-2 min-w-0">
        <NuxtLink :to="session?.course ? `/courses/${session.course.slug}?tab=live` : '/dashboard'" class="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800" aria-label="Back">
          <ArrowLeft class="w-4 h-4" />
        </NuxtLink>
        <span v-if="session?.state === 'live'" class="flex items-center gap-1.5 text-xs font-bold text-rose-400 shrink-0"><span class="w-2 h-2 rounded-full bg-rose-500 animate-pulse" /> LIVE</span>
        <span class="font-semibold truncate">{{ session?.title || 'Live class' }}</span>
        <span v-if="session?.course" class="text-slate-500 text-sm truncate hidden sm:inline">· {{ session.course.title }}</span>
      </div>
      <button v-if="inRoom" class="btn bg-rose-600 hover:bg-rose-500 text-white text-sm" @click="leave"><LogOut class="w-4 h-4" /> Leave</button>
    </header>

    <!-- in the room -->
    <div v-show="inRoom" class="flex-1 flex flex-col min-h-0">
      <p v-if="limited" class="bg-amber-500/15 text-amber-200 text-xs px-4 py-2 text-center">
        Test mode: rooms on the public meet.jit.si server end after a few minutes when embedded. Your admin can enable full-length rooms (JaaS) in the settings.
      </p>
      <div ref="roomEl" class="flex-1 min-h-[60vh] bg-black" />
    </div>

    <main v-if="!inRoom" class="flex-1 flex items-center justify-center p-4 sm:p-8">
      <div v-if="error" class="max-w-md text-center">
        <AlertTriangle class="w-12 h-12 mx-auto text-amber-400 mb-3" />
        <p class="text-slate-300">{{ error }}</p>
        <NuxtLink to="/dashboard" class="btn-ghost !text-brand-300 mt-4 inline-flex">Back to my learning</NuxtLink>
      </div>

      <div v-else-if="!session" class="text-slate-500">Loading…</div>

      <div v-else class="w-full max-w-2xl">
        <!-- recording -->
        <template v-if="session.state === 'ended'">
          <div v-if="session.recording_url">
            <p class="text-sm text-slate-400 mb-3 flex items-center gap-2"><PlayCircle class="w-4 h-4" /> Class recording</p>
            <VideoPlayer :url="session.recording_url" />
          </div>
          <div v-else class="text-center card !bg-slate-900 !border-slate-800 p-10">
            <Video class="w-12 h-12 mx-auto text-slate-600 mb-3" />
            <p class="font-semibold">This live class has ended</p>
            <p class="text-sm text-slate-400 mt-1">If the instructor shares a recording, it will appear here.</p>
          </div>
        </template>

        <div v-else-if="session.state === 'cancelled'" class="text-center card !bg-slate-900 !border-slate-800 p-10">
          <CalendarX2 class="w-12 h-12 mx-auto text-slate-500 mb-3" />
          <p class="font-semibold">This live class was cancelled</p>
        </div>

        <div v-else class="card !bg-slate-900 !border-slate-800 p-6 sm:p-10 text-center">
          <div class="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center"
            :class="session.state === 'live' ? 'bg-rose-500' : 'bg-brand-600'"><Video class="w-8 h-8 text-white" /></div>
          <h1 class="mt-4 text-xl sm:text-2xl font-bold">{{ session.title }}</h1>
          <p class="mt-1 text-slate-400 text-sm">{{ whenLong(session.starts_at) }} · {{ fmtMinutes(session.duration_minutes) }}
            <span v-if="session.host"> · with {{ session.host.full_name }}</span></p>
          <p v-if="session.description" class="mt-4 text-slate-300 text-sm leading-relaxed whitespace-pre-wrap text-left sm:text-center">{{ session.description }}</p>

          <div v-if="session.can_join" class="mt-7">
            <button class="btn bg-brand-500 hover:bg-brand-400 text-white px-8 py-3 text-base font-bold" :disabled="joining" @click="join">
              <component :is="session.provider === 'external' ? ExternalLink : Video" class="w-5 h-5" />
              {{ joining ? 'Opening…' : session.is_host ? (session.state === 'upcoming' ? 'Open the room early' : 'Start / join as host') : 'Join live class' }}
            </button>
            <p class="mt-3 text-xs text-slate-500">
              {{ session.provider === 'external' ? 'Opens the meeting link in a new tab.' : 'You can check your camera and microphone before entering.' }}
            </p>
          </div>
          <div v-else class="mt-7">
            <p class="text-sm text-slate-400 flex items-center justify-center gap-2"><Clock class="w-4 h-4" /> Doors open 15 minutes before the start</p>
            <p class="mt-2 text-3xl font-extrabold tabular-nums tracking-tight">{{ countdown }}</p>
          </div>
          <p v-if="session.is_host" class="mt-6 text-xs text-slate-500">
            <NuxtLink :to="`/teach/courses/${session.course_id}/live`" class="hover:text-brand-300 inline-flex items-center gap-1"><Users class="w-3.5 h-3.5" /> Manage classes & attendance</NuxtLink>
          </p>
        </div>
      </div>
    </main>
  </div>
</template>
