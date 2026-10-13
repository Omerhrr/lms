<script setup lang="ts">
import { CheckCircle2, UserCheck } from 'lucide-vue-next'

useSeoMeta({ title: 'Instructor applications - Admin - Infohive' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const api = useApi()
const { show } = useToast()
const pendingApps = useState<number>('admin:pendingApps', () => 0)

const items = ref<any[]>([])
const loading = ref(true)
const load = async () => {
  loading.value = true
  try { items.value = await api.get<any[]>('/admin/instructor-requests'); pendingApps.value = items.value.length } finally { loading.value = false }
}
onMounted(load)

const deciding = ref<{ user: any; approve: boolean; message: string; saving: boolean } | null>(null)
const decide = async () => {
  const d = deciding.value
  if (!d) return
  d.saving = true
  try {
    await api.post(`/admin/instructor-requests/${d.user.id}`, { approve: d.approve, message: d.message })
    show(d.approve ? `${d.user.full_name} can now teach` : 'Application declined', d.approve ? 'success' : 'info')
    deciding.value = null
    await load()
  } catch { d.saving = false }
}
const ago = (iso: string) => {
  const n = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000)
  return n <= 0 ? 'today' : n === 1 ? 'yesterday' : `${n} days ago`
}
</script>

<template>
  <div class="max-w-4xl">
    <div class="mb-6">
      <h1 class="text-2xl font-extrabold text-slate-900">Instructor applications</h1>
      <p class="text-slate-600 mt-1">People who signed up and asked to teach. Approving gives them the Instructor studio.</p>
    </div>

    <div v-if="loading" class="space-y-3"><div v-for="i in 2" :key="i" class="card h-28 animate-pulse" /></div>
    <div v-else-if="!items.length" class="card p-10 text-center text-slate-600">
      <CheckCircle2 class="w-10 h-10 mx-auto text-brand-500 mb-2" />
      No applications waiting.
    </div>
    <ul v-else class="space-y-3">
      <li v-for="u in items" :key="u.id" class="card p-5 flex flex-col sm:flex-row gap-4">
        <div class="w-11 h-11 rounded-full bg-brand-600 text-white font-bold flex items-center justify-center shrink-0 uppercase">{{ u.full_name.slice(0, 1) }}</div>
        <div class="flex-1 min-w-0">
          <p class="font-bold text-slate-900">{{ u.full_name }} <span v-if="!u.is_active" class="badge bg-rose-50 text-rose-700 ml-1">deactivated</span></p>
          <p class="text-sm text-slate-600">{{ u.email }} · applied {{ ago(u.created_at) }}</p>
          <p v-if="u.headline" class="mt-2 text-sm font-medium text-slate-800">{{ u.headline }}</p>
          <p v-if="u.bio" class="mt-1 text-sm text-slate-600 whitespace-pre-line">{{ u.bio }}</p>
          <p v-if="!u.headline && !u.bio" class="mt-2 text-sm text-slate-500">No profile details yet. You may want to email them before deciding.</p>
        </div>
        <div class="flex sm:flex-col gap-2 shrink-0">
          <button class="btn-primary" @click="deciding = { user: u, approve: true, message: '', saving: false }"><UserCheck class="w-4 h-4" /> Approve</button>
          <button class="btn-secondary" @click="deciding = { user: u, approve: false, message: '', saving: false }">Decline</button>
        </div>
      </li>
    </ul>

    <Modal :open="!!deciding" :title="deciding?.approve ? `Approve ${deciding?.user.full_name}?` : `Decline ${deciding?.user.full_name}?`" @close="deciding = null">
      <p class="text-slate-700">
        {{ deciding?.approve
          ? 'They will be able to create courses, grade learners and run live classes. They are signed out once so the new access takes effect.'
          : 'They keep their learner account. You can make them an instructor later from Users.' }}
      </p>
      <label class="label mt-4" for="decision-msg">Message to the applicant <span class="font-normal text-slate-500">(optional)</span></label>
      <textarea v-if="deciding" id="decision-msg" v-model="deciding.message" rows="3" maxlength="1000" class="input"
        :placeholder="deciding.approve ? 'Welcome aboard! Start with…' : 'Thanks for applying. Right now we…'" />
      <template #footer>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn-secondary" @click="deciding = null">Cancel</button>
          <button :class="deciding?.approve ? 'btn-primary' : 'btn-danger'" :disabled="deciding?.saving" @click="decide">
            {{ deciding?.approve ? 'Approve' : 'Decline' }}
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
