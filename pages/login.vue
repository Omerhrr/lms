<script setup lang="ts">
import { LogIn, ShieldCheck } from 'lucide-vue-next'

useSeoMeta({ title: 'Sign in — LearnHub' })
definePageMeta({ middleware: 'guest' })

const auth = useAuth()
const route = useRoute()
const router = useRouter()
const { show } = useToast()

const email = ref('')
const password = ref('')
const loading = ref(false)

const demoAccounts = [
  { label: 'Admin', email: 'admin@learnhub.io', password: 'Admin123!' },
  { label: 'Instructor', email: 'sarah@learnhub.io', password: 'Teach123!' },
  { label: 'Student', email: 'emma@example.com', password: 'Study123!' },
]

const fill = (d: { email: string; password: string }) => {
  email.value = d.email
  password.value = d.password
}

const submit = async () => {
  if (!email.value || !password.value) return show('Enter your email and password', 'error')
  loading.value = true
  try {
    const user = await auth.login(email.value, password.value)
    show(`Welcome back, ${user.full_name.split(' ')[0]}!`)
    const redirect = (route.query.redirect as string) || auth.homeFor(user)
    router.push(redirect)
  } catch (e: any) {
    show(e?.data?.detail || 'Login failed', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] grid lg:grid-cols-2">
    <!-- form side -->
    <div class="flex items-center justify-center px-4 py-12">
      <div class="w-full max-w-md">
        <div class="text-center mb-8">
          <div class="w-14 h-14 rounded-2xl bg-brand-50 flex items-center justify-center mx-auto mb-4">
            <LogIn class="w-7 h-7 text-brand-600" />
          </div>
          <h1 class="text-2xl font-extrabold text-slate-900">Welcome back</h1>
          <p class="text-slate-500 text-sm mt-1">Sign in to continue your learning journey</p>
        </div>

        <form @submit.prevent="submit" class="space-y-4">
          <div>
            <label class="label">Email</label>
            <input v-model="email" type="email" class="input" placeholder="you@example.com" autocomplete="email" />
          </div>
          <div>
            <label class="label">Password</label>
            <input v-model="password" type="password" class="input" placeholder="••••••••" autocomplete="current-password" />
          </div>
          <div class="flex items-center justify-between text-sm">
            <NuxtLink to="/forgot-password" class="text-brand-700 hover:underline">Forgot password?</NuxtLink>
            <NuxtLink to="/register" class="text-slate-500 hover:underline">Create account</NuxtLink>
          </div>
          <button type="submit" class="btn-primary w-full py-3" :disabled="loading">
            {{ loading ? 'Signing in…' : 'Sign in' }}
          </button>
        </form>

        <div class="mt-8">
          <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 text-center">Quick demo access</div>
          <div class="grid grid-cols-3 gap-2">
            <button v-for="d in demoAccounts" :key="d.email" @click="fill(d)"
              class="rounded-lg border border-slate-200 px-2 py-2.5 text-xs font-semibold text-slate-600 hover:border-brand-400 hover:text-brand-700 transition">
              {{ d.label }}
            </button>
          </div>
          <p class="text-[11px] text-center text-slate-400 mt-2">Click a role to fill credentials, then sign in</p>
        </div>
      </div>
    </div>

    <!-- brand side -->
    <div class="hidden lg:flex bg-slate-900 items-center justify-center p-12 relative overflow-hidden">
      <div class="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-brand-500/20 blur-3xl" />
      <div class="relative text-white max-w-md">
        <ShieldCheck class="w-12 h-12 text-brand-400 mb-6" />
        <h2 class="text-3xl font-extrabold leading-tight">Your learning, <span class="text-brand-400">tracked and certified.</span></h2>
        <ul class="mt-6 space-y-3 text-slate-300 text-sm">
          <li>• Progress synced across every lesson</li>
          <li>• Quizzes graded instantly with explanations</li>
          <li>• Verifiable certificates for completed courses</li>
          <li>• Instructors see exactly where students struggle</li>
        </ul>
      </div>
    </div>
  </div>
</template>
