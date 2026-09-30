<script setup lang="ts">
import { KeyRound } from 'lucide-vue-next'

useSeoMeta({ title: 'Reset password — LearnHub' })

const api = useApi()
const { show } = useToast()
const router = useRouter()

const email = ref('')
const resetToken = ref('')
const newPassword = ref('')
const stage = ref<'request' | 'reset' | 'done'>('request')
const loading = ref(false)

const request = async () => {
  if (!email.value) return show('Enter your account email', 'error')
  loading.value = true
  try {
    const res = await api.post<{ message: string; reset_token?: string }>('/auth/forgot-password', { email: email.value })
    if (res.reset_token) {
      resetToken.value = res.reset_token
      stage.value = 'reset'
      show('Reset token generated (demo mode — normally emailed)', 'info')
    } else {
      show(res.message, 'info')
    }
  } catch (e: any) {
    show(e?.data?.detail || 'Request failed', 'error')
  } finally { loading.value = false }
}

const reset = async () => {
  if (newPassword.value.length < 6) return show('Password must be at least 6 characters', 'error')
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
          {{ stage === 'request' ? "We'll generate a secure reset token for your account" : 'Enter the new password for your account' }}
        </p>
      </div>

      <div v-if="stage === 'request'" class="card p-6 space-y-4">
        <div>
          <label class="label">Account email</label>
          <input v-model="email" type="email" class="input" placeholder="you@example.com" @keyup.enter="request" />
        </div>
        <button class="btn-primary w-full" :disabled="loading" @click="request">{{ loading ? 'Working…' : 'Generate reset token' }}</button>
        <p class="text-xs text-slate-400 text-center">Demo mode returns the token directly — production would email it.</p>
      </div>

      <div v-else-if="stage === 'reset'" class="card p-6 space-y-4">
        <div>
          <label class="label">Reset token</label>
          <input v-model="resetToken" class="input font-mono text-xs" />
        </div>
        <div>
          <label class="label">New password</label>
          <input v-model="newPassword" type="password" class="input" placeholder="6+ characters" />
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
