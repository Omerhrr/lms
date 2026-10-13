<script setup lang="ts">
import { Plus, Video, ExternalLink, Users, Pencil, Ban, Trash2, PlayCircle, Radio } from 'lucide-vue-next'

useSeoMeta({ title: 'Live classes - Infohive' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const route = useRoute()
const api = useApi()
const { show } = useToast()
const courseId = Number(route.params.id)

const data = ref<{ enrolled: number; sessions: any[] }>({ enrolled: 0, sessions: [] })
const loading = ref(true)
const load = async () => {
  loading.value = true
  try { data.value = await api.get<any>(`/teach/courses/${courseId}/live`) } finally { loading.value = false }
}
onMounted(load)

// ---------- schedule / edit ----------
const pad = (n: number) => String(n).padStart(2, '0')
const toLocalInput = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
const nextHour = () => { const d = new Date(); d.setHours(d.getHours() + 1, 0, 0, 0); return d }

const modal = ref<{ open: boolean; editing?: any }>({ open: false })
const form = ref<any>({})
const saving = ref(false)
const openForm = (s?: any) => {
  modal.value = { open: true, editing: s }
  form.value = s
    ? { title: s.title, description: s.description || '', starts_local: toLocalInput(new Date(s.starts_at)), duration_minutes: s.duration_minutes,
        provider: s.provider, external_url: s.external_url || '', recording_url: s.recording_url || '' }
    : { title: '', description: '', starts_local: toLocalInput(nextHour()), duration_minutes: 60, provider: 'jitsi', external_url: '', recording_url: '' }
}
const tz = Intl.DateTimeFormat().resolvedOptions().timeZone

const save = async () => {
  const f = form.value
  if (f.title.trim().length < 2) return show('Give the class a title', 'error')
  const starts = new Date(f.starts_local)
  if (isNaN(starts.getTime())) return show('Pick a date and time', 'error')
  if (f.provider === 'external' && !/^https:\/\//i.test(f.external_url)) return show('Paste the https:// meeting link', 'error')
  const body: any = {
    title: f.title.trim(), description: f.description || null, starts_at: starts.toISOString(),
    duration_minutes: Number(f.duration_minutes) || 60, provider: f.provider,
    external_url: f.provider === 'external' ? f.external_url.trim() : null,
  }
  saving.value = true
  try {
    if (modal.value.editing) {
      body.recording_url = f.recording_url.trim() || null
      await api.put(`/teach/live/${modal.value.editing.id}`, body)
      show('Live class updated')
    } else {
      await api.post(`/teach/courses/${courseId}/live`, body)
      show('Live class scheduled - enrolled students have been notified')
    }
    modal.value = { open: false }
    await load()
  } catch { /* toast shown */ } finally { saving.value = false }
}

const cancelSession = async (s: any) => {
  if (!confirm(`Cancel "${s.title}"? Enrolled students will be notified.`)) return
  await api.post(`/teach/live/${s.id}/cancel`)
  show('Live class cancelled', 'info')
  await load()
}
const removeSession = async (s: any) => {
  if (!confirm(`Delete "${s.title}" and its attendance record?`)) return
  await api.del(`/teach/live/${s.id}`)
  show('Deleted', 'info')
  await load()
}

// ---------- attendance ----------
const att = ref<any>(null)
const openAttendance = async (s: any) => { att.value = await api.get<any>(`/teach/live/${s.id}/attendance`) }

const when = (iso: string) => new Date(iso).toLocaleString(undefined, { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
const stateBadge: Record<string, [string, string]> = {
  live: ['Live now', 'bg-rose-50 text-rose-700'], starting_soon: ['Starting soon', 'bg-amber-50 text-amber-700'],
  upcoming: ['Scheduled', 'bg-sky-50 text-sky-700'], ended: ['Ended', 'bg-slate-100 text-slate-500'],
  cancelled: ['Cancelled', 'bg-slate-100 text-slate-400'],
}
</script>

<template>
  <div class="max-w-4xl">
    <div class="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Live classes</h1>
        <p class="text-slate-500 text-sm mt-0.5">Schedule live sessions. Enrolled students are notified by email and in the app, and can join 15 minutes early.</p>
      </div>
      <button class="btn-primary" @click="openForm()"><Plus class="w-4 h-4" /> Schedule a class</button>
    </div>

    <div v-if="loading" class="space-y-3"><div v-for="i in 2" :key="i" class="card h-20 animate-pulse" /></div>
    <div v-else-if="!data.sessions.length" class="card p-10 text-center text-slate-500">
      <Video class="w-10 h-10 mx-auto mb-2 text-slate-300" />
      <p class="font-semibold text-slate-700">No live classes yet</p>
      <p class="text-sm mt-1">Run a kick-off, weekly Q&amp;A or office hours with your students.</p>
    </div>
    <div v-else class="space-y-3">
      <div v-for="s in data.sessions" :key="s.id" class="card p-4 sm:p-5">
        <div class="flex flex-wrap items-start gap-3">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            :class="s.state === 'live' ? 'bg-rose-500 text-white' : 'bg-brand-50 text-brand-600'">
            <component :is="s.state === 'live' ? Radio : s.provider === 'external' ? ExternalLink : Video" class="w-5 h-5" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <h3 class="font-bold text-slate-800" :class="s.status === 'cancelled' && 'line-through text-slate-400'">{{ s.title }}</h3>
              <span class="badge" :class="stateBadge[s.state]?.[1]">{{ stateBadge[s.state]?.[0] }}</span>
            </div>
            <p class="text-xs text-slate-500 mt-0.5">{{ when(s.starts_at) }} · {{ s.duration_minutes }} min ·
              {{ s.provider === 'external' ? 'External link' : 'Built-in video room' }} ·
              <span class="font-semibold text-slate-600">{{ s.attendance_count }}/{{ data.enrolled }}</span> attended</p>
            <p v-if="s.recording_url" class="text-xs text-brand-700 mt-1 flex items-center gap-1"><PlayCircle class="w-3.5 h-3.5" /> Recording linked</p>
          </div>
        </div>
        <div class="mt-3 flex flex-wrap gap-1.5">
          <NuxtLink v-if="s.status !== 'cancelled' && s.state !== 'ended'" :to="`/live/${s.id}`" class="btn-primary text-xs !px-3 !py-1.5">
            <Video class="w-3.5 h-3.5" /> {{ s.state === 'live' || s.state === 'starting_soon' ? 'Start / join' : 'Open room' }}
          </NuxtLink>
          <button class="btn-secondary text-xs !px-3 !py-1.5" @click="openAttendance(s)"><Users class="w-3.5 h-3.5" /> Attendance</button>
          <button v-if="s.status !== 'cancelled'" class="btn-secondary text-xs !px-3 !py-1.5" @click="openForm(s)">
            <Pencil class="w-3.5 h-3.5" /> {{ s.state === 'ended' ? 'Add recording' : 'Edit' }}
          </button>
          <button v-if="s.status !== 'cancelled' && s.state !== 'ended'" class="btn-ghost text-xs !px-3 !py-1.5 text-amber-700" @click="cancelSession(s)"><Ban class="w-3.5 h-3.5" /> Cancel</button>
          <button class="btn-ghost text-xs !px-3 !py-1.5 text-rose-600" @click="removeSession(s)"><Trash2 class="w-3.5 h-3.5" /> Delete</button>
        </div>
      </div>
    </div>

    <!-- schedule / edit -->
    <Modal :open="modal.open" :title="modal.editing ? 'Edit live class' : 'Schedule a live class'" @close="modal = { open: false }">
      <div class="space-y-4">
        <div><label class="label">Title</label><input v-model="form.title" class="input" placeholder="e.g. Week 1 kick-off & Q&A" /></div>
        <div class="grid sm:grid-cols-[1fr_8rem] gap-3">
          <div><label class="label">Starts</label><input v-model="form.starts_local" type="datetime-local" class="input" /></div>
          <div><label class="label">Length (min)</label><input v-model.number="form.duration_minutes" type="number" min="10" max="600" step="5" class="input" /></div>
        </div>
        <p class="text-xs text-slate-400 -mt-2">Times are in your timezone ({{ tz }}); students see them in theirs.</p>
        <div>
          <label class="label">Where</label>
          <div class="grid sm:grid-cols-2 gap-2">
            <label class="flex gap-2 p-3 rounded-xl border cursor-pointer" :class="form.provider === 'jitsi' ? 'border-brand-500 bg-brand-50/50' : 'border-slate-200'">
              <input v-model="form.provider" type="radio" value="jitsi" class="mt-1 accent-brand-600" />
              <span><b class="text-sm text-slate-800">Built-in video room</b><span class="block text-xs text-slate-500">Video, screen sharing and chat inside Infohive</span></span>
            </label>
            <label class="flex gap-2 p-3 rounded-xl border cursor-pointer" :class="form.provider === 'external' ? 'border-brand-500 bg-brand-50/50' : 'border-slate-200'">
              <input v-model="form.provider" type="radio" value="external" class="mt-1 accent-brand-600" />
              <span><b class="text-sm text-slate-800">External link</b><span class="block text-xs text-slate-500">Zoom, Google Meet, Teams…</span></span>
            </label>
          </div>
        </div>
        <div v-if="form.provider === 'external'">
          <label class="label">Meeting link</label>
          <input v-model="form.external_url" class="input" placeholder="https://zoom.us/j/…" />
          <p class="text-xs text-slate-400 mt-1">Only enrolled students get this link, and only when the class opens.</p>
        </div>
        <div><label class="label">Description <span class="text-slate-400 font-normal">(optional)</span></label><textarea v-model="form.description" rows="3" class="input" placeholder="Agenda, what to prepare…" /></div>
        <div v-if="modal.editing">
          <label class="label">Recording link <span class="text-slate-400 font-normal">(after the class)</span></label>
          <input v-model="form.recording_url" class="input" placeholder="YouTube, Vimeo or .mp4 link" />
          <p class="text-xs text-slate-400 mt-1">Students watch it inside Infohive, with the same watch-only player as lessons.</p>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn-secondary" @click="modal = { open: false }">Cancel</button>
          <button class="btn-primary" :disabled="saving" @click="save">{{ saving ? 'Saving…' : modal.editing ? 'Save changes' : 'Schedule & notify' }}</button>
        </div>
      </template>
    </Modal>

    <!-- attendance -->
    <Modal :open="!!att" :title="att ? `Attendance - ${att.session.title}` : ''" @close="att = null">
      <template v-if="att">
        <p class="text-sm text-slate-500 mb-3"><b class="text-slate-800">{{ att.present }}</b> of {{ att.total }} enrolled students joined.</p>
        <ul class="divide-y divide-slate-100 border border-slate-100 rounded-xl">
          <li v-for="r in att.rows" :key="r.user.id" class="flex items-center gap-3 px-3 py-2.5 text-sm">
            <span class="w-2 h-2 rounded-full shrink-0" :class="r.present ? 'bg-brand-500' : 'bg-slate-300'" />
            <span class="flex-1 min-w-0"><span class="font-medium text-slate-800">{{ r.user.full_name }}</span><span class="block text-xs text-slate-400 truncate">{{ r.user.email }}</span></span>
            <span class="text-xs" :class="r.present ? 'text-brand-700' : 'text-slate-400'">{{ r.present ? `Joined ${new Date(r.first_joined_at).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}` : 'Absent' }}</span>
          </li>
          <li v-if="!att.rows.length" class="px-3 py-6 text-center text-sm text-slate-400">No students enrolled yet.</li>
        </ul>
      </template>
    </Modal>
  </div>
</template>
