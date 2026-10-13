<script setup lang="ts">
import { KeyRound } from 'lucide-vue-next'

useSeoMeta({ title: 'Reset password - Infohive' })

const api = useApi()
const { show } = useToast()
const router = useRouter()
const route = useRoute()

// The reset link (sent by email) carries the token: /forgot-password?token=...
const email = ref('')
const resetToken = ref((route.query.token as string) || '')
const newPassword = ref('')
const stage = ref<'request' | 'sent' | 'reset' | 'done'>(resetToken.value ? 'reset' : 'request')
const loading = ref(false)

const request = async () => {
  if (!email.value) return show('Enter your account email', 'error')
  loading.value = true
  try {
    await api.post('/auth/forgot-password', { email: email.value }, true)
    stage.value = 'sent'
  } catch (e: any) {
    show(e?.data?.detail || 'Request failed', 'error')
  } finally { loading.value = false }
}

const reset = async () => {
  if (newPassword.value.length < 8) return show('Password must be at least 8 characters', 'error')
  loading.value = true
  try {
    await api.post('/auth/reset-password', { token: resetToken.value, new_password: newPassword.value })
    stage.value = 'done'
    show('Password reset! Sign in with your new password.')
    setTimeout(() => router.push('/login'), 1500)
  } catch (e: any) {
    show(e?.data?.detail || 'Reset failed', 'error')
  } finally { loading.value = false }
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="w-14 h-14 rounded-2xl bg-brand-50 flex items-center justify-center mx-auto mb-4">
          <KeyRound class="w-7 h-7 text-brand-600" />
        </div>
        <h1 class="text-2xl font-extrabold text-slate-900">Reset your password</h1>
        <p class="text-slate-500 text-sm mt-1">
          {{ stage === 'reset' ? 'Enter the new password for your account' : "We'll send a reset link to your email" }}
        </p>
      </div>

      <div v-if="stage === 'request'" class="card p-6 space-y-4">
        <div>
          <label class="label" for="forgot-password-email">Account email</label>
          <input id="forgot-password-email" v-model="email" type="email" class="input" placeholder="you@example.com" @keyup.enter="request" />
        </div>
        <button class="btn-primary w-full" :disabled="loading" @click="request">{{ loading ? 'Working…' : 'Send reset link' }}</button>
      </div>

      <div v-else-if="stage === 'sent'" class="card p-8 text-center">
        <div class="text-4xl mb-2">📬</div>
        <p class="font-semibold text-slate-800">Check your email</p>
        <p class="text-sm text-slate-500 mt-1">If an account exists for {{ email }}, a reset link is on its way. It expires in 30 minutes.</p>
      </div>

      <div v-else-if="stage === 'reset'" class="card p-6 space-y-4">
        <div>
          <label class="label" for="forgot-password-newPassword">New password</label>
          <input id="forgot-password-newPassword" v-model="newPassword" type="password" class="input" placeholder="8+ characters" />
        </div>
        <button class="btn-primary w-full" :disabled="loading" @click="reset">{{ loading ? 'Resetting…' : 'Set new password' }}</button>
      </div>

      <div v-else class="card p-8 text-center">
        <div class="text-4xl mb-2">✅</div>
        <p class="font-semibold text-slate-800">Password updated!</p>
        <NuxtLink to="/login" class="btn-primary mt-4 inline-flex">Go to sign in</NuxtLink>
      </div>
    </div>
  </div>
</template>
