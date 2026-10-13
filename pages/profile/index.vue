<script setup lang="ts">
import { Save, KeyRound } from 'lucide-vue-next'

useSeoMeta({ title: 'Profile - Infohive' })
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const auth = useAuth()
const { show } = useToast()

const form = ref({ full_name: '', headline: '', bio: '', avatar_url: '' })
const pw = ref({ current_password: '', new_password: '', confirm: '' })
const saving = ref(false)
const savingPw = ref(false)

onMounted(() => {
  const u = auth.user.value
  if (u) form.value = { full_name: u.full_name, headline: u.headline || '', bio: u.bio || '', avatar_url: u.avatar_url || '' }
})

const save = async () => {
  saving.value = true
  try {
    const updated = await api.put<any>('/auth/me', form.value)
    auth.user.value = updated
    show('Profile updated!')
  } catch { /* the api client already showed the error */ } finally { saving.value = false }
}

const changePw = async () => {
  if (pw.value.new_password !== pw.value.confirm) return show('Passwords do not match', 'error')
  if (pw.value.new_password.length < 8) return show('New password must be 8+ characters', 'error')
  savingPw.value = true
  try {
    await api.post('/auth/change-password', { current_password: pw.value.current_password, new_password: pw.value.new_password })
    show('Password changed - please sign in again.', 'info')
    auth.logout()
    navigateTo('/login')
  } catch { /* the api client already showed the error */ } finally { savingPw.value = false }
}

const onUpload = async (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  try {
    const res = await api.upload(file)
    form.value.avatar_url = res.url
    show('Avatar uploaded - remember to save!', 'info')
  } catch { /* the api client already showed the error */ }
}
</script>

<template>
  <div class="max-w-3xl space-y-8">
    <h1 class="text-2xl font-extrabold text-slate-900">Profile settings</h1>

    <div class="card p-6">
      <h2 class="font-bold text-slate-800 mb-5">Public profile</h2>
      <div class="flex items-center gap-5 mb-6">
        <div class="w-20 h-20 rounded-full bg-brand-600 text-white text-3xl font-bold flex items-center justify-center overflow-hidden uppercase shrink-0">
          <img v-if="form.avatar_url" :src="form.avatar_url" class="w-full h-full object-cover" alt="avatar" />
          <template v-else>{{ (form.full_name || '?').slice(0, 1) }}</template>
        </div>
        <label class="btn-secondary cursor-pointer text-sm">
          Upload avatar
          <input type="file" class="hidden" aria-label="Upload a profile photo" accept="image/*" @change="onUpload" />
        </label>
      </div>

      <div class="grid sm:grid-cols-2 gap-4">
        <div>
          <label class="label" for="profile-index-form-full_name">Full name</label>
          <input id="profile-index-form-full_name" v-model="form.full_name" class="input" />
        </div>
        <div>
          <label class="label" for="profile-index-form-headline">Headline</label>
          <input id="profile-index-form-headline" v-model="form.headline" class="input" placeholder="e.g. Senior Software Engineer" />
        </div>
      </div>
      <div class="mt-4">
        <label class="label" for="profile-index-form-bio">Bio</label>
        <textarea id="profile-index-form-bio" v-model="form.bio" class="input min-h-[90px]" placeholder="Tell students about yourself…" />
      </div>
      <button class="btn-primary mt-5" :disabled="saving" @click="save">
        <Save class="w-4 h-4" /> {{ saving ? 'Saving…' : 'Save profile' }}
      </button>
    </div>

    <div class="card p-6">
      <h2 class="font-bold text-slate-800 mb-5 flex items-center gap-2"><KeyRound class="w-4.5 h-4.5 text-slate-500" /> Change password</h2>
      <div class="grid sm:grid-cols-3 gap-4">
        <div>
          <label class="label" for="profile-index-pw-current_password">Current</label>
          <input id="profile-index-pw-current_password" v-model="pw.current_password" type="password" class="input" />
        </div>
        <div>
          <label class="label" for="profile-index-pw-new_password">New</label>
          <input id="profile-index-pw-new_password" v-model="pw.new_password" type="password" class="input" />
        </div>
        <div>
          <label class="label" for="profile-index-pw-confirm">Confirm new</label>
          <input id="profile-index-pw-confirm" v-model="pw.confirm" type="password" class="input" />
        </div>
      </div>
      <button class="btn-secondary mt-5" :disabled="savingPw" @click="changePw">{{ savingPw ? 'Updating…' : 'Update password' }}</button>
    </div>
  </div>
</template>
