<script setup lang="ts">
import { UserPlus, Briefcase } from 'lucide-vue-next'

useSeoMeta({ title: 'Create account - Infohive' })
definePageMeta({ middleware: 'guest' })

const auth = useAuth()
const route = useRoute()
const router = useRouter()
const { show } = useToast()

const form = ref({ full_name: '', email: '', password: '', confirm: '' })
const role = ref((route.query.role as string) === 'instructor' ? 'instructor' : 'student')
const loading = ref(false)

const submit = async () => {
  const f = form.value
  if (!f.full_name || !f.email || !f.password) return show('Please fill in all fields', 'error')
  if (f.password.length < 8) return show('Password must be at least 8 characters', 'error')
  if (f.password !== f.confirm) return show('Passwords do not match', 'error')
  loading.value = true
  try {
    const user = await auth.register({
      email: f.email,
      password: f.password,
      full_name: f.full_name,
      role: role.value,
    })
    show(user.instructor_requested
      ? `Welcome, ${user.full_name.split(' ')[0]}! An admin will review your instructor request - you can start learning meanwhile.`
      : `Welcome to Infohive, ${user.full_name.split(' ')[0]}!`)
    router.push(auth.homeFor(user))
  } catch (e: any) {
    show(e?.data?.detail || 'Registration failed', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="w-14 h-14 rounded-2xl bg-brand-50 flex items-center justify-center mx-auto mb-4">
          <UserPlus class="w-7 h-7 text-brand-600" />
        </div>
        <h1 class="text-2xl font-extrabold text-slate-900">Create your account</h1>
        <p class="text-slate-500 text-sm mt-1">Start learning in minutes</p>
      </div>

      <div v-if="role === 'instructor'" class="rounded-xl bg-brand-50 border border-brand-100 px-4 py-3 mb-5 text-xs text-brand-800 flex gap-2">
        <Briefcase class="w-4 h-4 shrink-0 mt-0.5" />
        <span>You're applying to teach. You'll get a learner account right away and teaching access once an admin approves you.</span>
      </div>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="label" for="r-full_name">Full name</label>
          <input id="r-full_name" v-model="form.full_name" autocomplete="name" type="text" class="input" placeholder="Ada Lovelace" />
        </div>
        <div>
          <label class="label" for="r-email">Email</label>
          <input id="r-email" v-model="form.email" autocomplete="email" type="email" class="input" placeholder="you@example.com" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label" for="r-password">Password</label>
            <input id="r-password" v-model="form.password" autocomplete="new-password" type="password" class="input" placeholder="8+ characters" />
          </div>
          <div>
            <label class="label" for="r-confirm">Confirm password</label>
            <input id="r-confirm" v-model="form.confirm" autocomplete="new-password" type="password" class="input" placeholder="Repeat password" />
          </div>
        </div>
        <label class="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
          <input type="checkbox" class="rounded border-slate-300 text-brand-600" :checked="role === 'instructor'" @change="role = ($event.target as HTMLInputElement).checked ? 'instructor' : 'student'" />
          I also want to teach on Infohive
        </label>
        <button type="submit" class="btn-primary w-full py-3" :disabled="loading">
          {{ loading ? 'Creating account…' : (role === 'instructor' ? 'Sign up & request instructor access' : 'Create account') }}
        </button>
        <p class="text-center text-sm text-slate-500">
          Already have an account? <NuxtLink to="/login" class="text-brand-700 font-semibold hover:underline">Sign in</NuxtLink>
        </p>
      </form>
    </div>
  </div>
</template>
