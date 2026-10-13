<script setup lang="ts">
/**
 * Watch-only lesson player.
 *
 * - YouTube / Vimeo play inside the page. A transparent shield sits over the embed so the
 *   provider's logo, title, "Watch on YouTube" and end-screen links can't be clicked, and
 *   playback is driven by our own controls through the provider's player API.
 * - Direct video files use <video> with download, picture-in-picture and the context menu disabled.
 *
 * This stops casual downloading and leaving the course. It is not DRM: someone using developer
 * tools can still find the source link. Use a DRM-capable video host when that matters.
 */
import { Play, Pause, Volume2, VolumeX, Maximize, Minimize, RotateCcw, AlertTriangle } from 'lucide-vue-next'

const props = defineProps<{ url?: string | null }>()
const emit = defineEmits<{ (e: 'ended'): void }>()

const source = computed(() => parseVideoUrl(props.url))
const wrapper = ref<HTMLElement | null>(null)
const mount = ref<HTMLElement | null>(null)
const videoEl = ref<HTMLVideoElement | null>(null)

const ready = ref(false)
const playing = ref(false)
const started = ref(false)
const ended = ref(false)
const current = ref(0)
const duration = ref(0)
const muted = ref(false)
const rate = ref(1)
const fullscreen = ref(false)
const pseudoFull = ref(false)
const showControls = ref(true)
const failed = ref(false)

let yt: any = null
let vimeo: any = null
let poll: ReturnType<typeof setInterval> | undefined
let hideTimer: ReturnType<typeof setTimeout> | undefined

const loadScript = (src: string, globalName: string) =>
  new Promise<void>((resolve, reject) => {
    if ((window as any)[globalName]) return resolve()
    let tag = document.querySelector(`script[src="${src}"]`) as HTMLScriptElement | null
    if (!tag) {
      tag = document.createElement('script')
      tag.src = src
      tag.async = true
      document.head.appendChild(tag)
    }
    tag.addEventListener('load', () => resolve())
    tag.addEventListener('error', () => reject(new Error('script failed')))
  })

const loadYouTubeApi = () =>
  new Promise<void>((resolve, reject) => {
    const w = window as any
    if (w.YT?.Player) return resolve()
    const prev = w.onYouTubeIframeAPIReady
    w.onYouTubeIframeAPIReady = () => { prev?.(); resolve() }
    loadScript('https://www.youtube.com/iframe_api', '__never__').catch(reject)
    setTimeout(() => (w.YT?.Player ? resolve() : null), 4000)
  })

const destroy = () => {
  if (poll) clearInterval(poll)
  try { yt?.destroy() } catch { /* ignore */ }
  try { vimeo?.destroy() } catch { /* ignore */ }
  yt = vimeo = null
  ready.value = playing.value = started.value = ended.value = failed.value = false
  current.value = duration.value = 0
  if (mount.value) mount.value.innerHTML = ''
}

const setup = async () => {
  destroy()
  const src = source.value
  if (!src || src.kind === 'file') return
  await nextTick()
  const host = document.createElement('div')
  host.className = 'w-full h-full'
  mount.value?.appendChild(host)
  try {
    if (src.kind === 'youtube') {
      await loadYouTubeApi()
      const YT = (window as any).YT
      yt = new YT.Player(host, {
        host: 'https://www.youtube-nocookie.com',
        videoId: src.id,
        width: '100%', height: '100%',
        playerVars: {
          controls: 0, disablekb: 1, fs: 0, rel: 0, modestbranding: 1, iv_load_policy: 3,
          playsinline: 1, cc_load_policy: 0, origin: window.location.origin,
        },
        events: {
          onReady: () => { ready.value = true; duration.value = yt.getDuration() || 0 },
          onStateChange: (e: any) => {
            playing.value = e.data === YT.PlayerState.PLAYING
            if (playing.value) { started.value = true; ended.value = false }
            if (e.data === YT.PlayerState.ENDED) { ended.value = true; emit('ended') }
            duration.value = yt.getDuration() || duration.value
          },
          onError: () => { failed.value = true },
        },
      })
      poll = setInterval(() => { if (yt?.getCurrentTime) current.value = yt.getCurrentTime() }, 250)
    } else {
      await loadScript('https://player.vimeo.com/api/player.js', 'Vimeo')
      const Vimeo = (window as any).Vimeo
      vimeo = new Vimeo.Player(host, {
        id: Number(src.id), ...(src.hash ? { h: src.hash } : {}),
        controls: false, title: false, byline: false, portrait: false, pip: false,
        dnt: true, playsinline: true, responsive: true, keyboard: false,
      })
      vimeo.on('loaded', async () => { ready.value = true; duration.value = await vimeo.getDuration() })
      vimeo.on('play', () => { playing.value = true; started.value = true; ended.value = false })
      vimeo.on('pause', () => { playing.value = false })
      vimeo.on('ended', () => { playing.value = false; ended.value = true; emit('ended') })
      vimeo.on('timeupdate', (d: any) => { current.value = d.seconds; duration.value = d.duration })
      vimeo.on('error', () => { failed.value = true })
    }
  } catch {
    failed.value = true
  }
}

// ---------- unified controls ----------
const play = () => {
  if (source.value?.kind === 'file') return videoEl.value?.play()
  if (ended.value) seek(0)
  yt?.playVideo?.(); vimeo?.play?.()
}
const pause = () => {
  if (source.value?.kind === 'file') return videoEl.value?.pause()
  yt?.pauseVideo?.(); vimeo?.pause?.()
}
const toggle = () => (playing.value ? pause() : play())
const seek = (t: number) => {
  t = Math.max(0, Math.min(t, duration.value || t))
  current.value = t
  if (source.value?.kind === 'file' && videoEl.value) videoEl.value.currentTime = t
  yt?.seekTo?.(t, true); vimeo?.setCurrentTime?.(t)
}
const toggleMute = () => {
  muted.value = !muted.value
  if (videoEl.value) videoEl.value.muted = muted.value
  if (yt) muted.value ? yt.mute() : yt.unMute()
  vimeo?.setMuted?.(muted.value)
}
const cycleRate = () => {
  const rates = [1, 1.25, 1.5, 2, 0.75]
  rate.value = rates[(rates.indexOf(rate.value) + 1) % rates.length]
  if (videoEl.value) videoEl.value.playbackRate = rate.value
  yt?.setPlaybackRate?.(rate.value); vimeo?.setPlaybackRate?.(rate.value)
}
const toggleFullscreen = async () => {
  const el = wrapper.value as any
  if (!el) return
  if (document.fullscreenElement || (document as any).webkitFullscreenElement) {
    await (document.exitFullscreen?.() ?? (document as any).webkitExitFullscreen?.())
    return
  }
  const req = el.requestFullscreen || el.webkitRequestFullscreen
  if (req) {
    // the whole wrapper goes fullscreen, so the click shield stays on top
    await req.call(el)
  } else {
    pseudoFull.value = !pseudoFull.value   // iPhone Safari: no element fullscreen API
  }
}
const onFsChange = () => {
  fullscreen.value = !!(document.fullscreenElement || (document as any).webkitFullscreenElement)
}

const fmt = (s: number) => {
  if (!isFinite(s) || s < 0) s = 0
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = Math.floor(s % 60)
  return (h ? `${h}:${String(m).padStart(2, '0')}` : `${m}`) + `:${String(sec).padStart(2, '0')}`
}

const nudgeControls = () => {
  showControls.value = true
  if (hideTimer) clearTimeout(hideTimer)
  hideTimer = setTimeout(() => { if (playing.value) showControls.value = false }, 2500)
}
const onKey = (e: KeyboardEvent) => {
  if (e.code === 'Space' || e.key === 'k') { e.preventDefault(); toggle() }
  else if (e.key === 'ArrowRight') seek(current.value + 5)
  else if (e.key === 'ArrowLeft') seek(current.value - 5)
  else if (e.key === 'f') toggleFullscreen()
  else if (e.key === 'm') toggleMute()
  nudgeControls()
}

// native <video> state
const onVideoEvent = () => {
  const v = videoEl.value
  if (!v) return
  playing.value = !v.paused && !v.ended
  current.value = v.currentTime
  duration.value = v.duration || 0
  if (playing.value) started.value = true
}

watch(() => props.url, setup)
watch(playing, (p) => { if (!p) showControls.value = true; else nudgeControls() })
onMounted(() => {
  setup()
  document.addEventListener('fullscreenchange', onFsChange)
  document.addEventListener('webkitfullscreenchange', onFsChange)
})
onBeforeUnmount(() => {
  destroy()
  if (hideTimer) clearTimeout(hideTimer)
  document.removeEventListener('fullscreenchange', onFsChange)
  document.removeEventListener('webkitfullscreenchange', onFsChange)
})
</script>

<template>
  <div ref="wrapper" tabindex="0" @keydown="onKey" @mousemove="nudgeControls" @contextmenu.prevent
    class="video-shell relative w-full bg-black overflow-hidden select-none outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
    :class="pseudoFull ? 'fixed inset-0 z-[100] rounded-none' : 'aspect-video rounded-xl'">

    <div v-if="!source" class="absolute inset-0 flex flex-col items-center justify-center text-slate-500 gap-2 p-6 text-center">
      <AlertTriangle class="w-10 h-10" />
      <span class="text-sm">{{ url ? "This video link isn't supported. Ask your instructor to use a YouTube, Vimeo or .mp4 link." : 'No video attached to this lesson' }}</span>
    </div>

    <!-- direct file: native player with downloads disabled -->
    <video v-else-if="source.kind === 'file'" ref="videoEl" :src="source.url" class="w-full h-full" controls playsinline
      preload="metadata" controlslist="nodownload noremoteplayback" disablepictureinpicture disableremoteplayback
      @play="onVideoEvent" @pause="onVideoEvent" @timeupdate="onVideoEvent" @loadedmetadata="onVideoEvent"
      @ended="emit('ended')" />

    <!-- YouTube / Vimeo -->
    <template v-else>
      <div ref="mount" class="absolute inset-0 pointer-events-none [&_iframe]:w-full [&_iframe]:h-full" />

      <!-- click shield: blocks every link inside the provider's player -->
      <div class="absolute inset-0 z-10 cursor-pointer" @click="toggle(); nudgeControls()" @dblclick="toggleFullscreen"
        @touchstart.passive="nudgeControls" />

      <!-- cover before start and after the end (hides title cards and suggested videos) -->
      <div v-if="!started || ended || failed" class="absolute inset-0 z-20 flex items-center justify-center bg-gradient-to-br from-slate-900 to-black">
        <div v-if="failed" class="text-center text-slate-400 text-sm px-6">
          <AlertTriangle class="w-10 h-10 mx-auto mb-2" />This video couldn't load. Check your internet connection - or the video may be private or removed.
        </div>
        <button v-else type="button" @click.stop="play"
          class="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-brand-500 hover:bg-brand-400 text-white flex items-center justify-center shadow-xl transition disabled:opacity-50"
          :disabled="!ready" :aria-label="ended ? 'Replay' : 'Play'">
          <component :is="ended ? RotateCcw : Play" class="w-8 h-8 sm:w-9 sm:h-9" :class="ended ? '' : 'ml-1'" />
        </button>
        <span v-if="!ready && !failed" class="absolute bottom-4 text-xs text-slate-500">Loading video…</span>
      </div>

      <!-- our controls -->
      <div v-show="started && !ended && !failed && (showControls || !playing)"
        class="absolute inset-x-0 bottom-0 z-30 px-3 sm:px-4 pt-8 pb-2 sm:pb-3 bg-gradient-to-t from-black/85 to-transparent text-white"
        @click.stop>
        <input type="range" min="0" :max="duration || 0" step="0.1" :value="current" aria-label="Seek"
          class="w-full h-1.5 accent-brand-500 cursor-pointer" @input="seek(Number(($event.target as HTMLInputElement).value))" />
        <div class="mt-1.5 flex items-center gap-1 sm:gap-2 text-xs sm:text-sm">
          <button type="button" class="p-2 rounded-lg hover:bg-white/10" :aria-label="playing ? 'Pause' : 'Play'" @click="toggle">
            <component :is="playing ? Pause : Play" class="w-5 h-5" />
          </button>
          <button type="button" class="p-2 rounded-lg hover:bg-white/10" :aria-label="muted ? 'Unmute' : 'Mute'" @click="toggleMute">
            <component :is="muted ? VolumeX : Volume2" class="w-5 h-5" />
          </button>
          <span class="tabular-nums text-white/80">{{ fmt(current) }} / {{ fmt(duration) }}</span>
          <span class="flex-1" />
          <button type="button" class="px-2 py-1.5 rounded-lg hover:bg-white/10 font-semibold tabular-nums" aria-label="Playback speed" @click="cycleRate">{{ rate }}×</button>
          <button type="button" class="p-2 rounded-lg hover:bg-white/10" :aria-label="fullscreen || pseudoFull ? 'Exit full screen' : 'Full screen'" @click="toggleFullscreen">
            <component :is="fullscreen || pseudoFull ? Minimize : Maximize" class="w-5 h-5" />
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.video-shell:fullscreen { border-radius: 0; aspect-ratio: auto; width: 100vw; height: 100vh; }
</style>
