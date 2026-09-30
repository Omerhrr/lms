<script setup lang="ts">
import { UserPlus, GraduationCap, Briefcase } from 'lucide-vue-next'

useSeoMeta({ title: 'Create account - LearnHub' })
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
  if (f.password.length < 6) return show('Password must be at least 6 characters', 'error')
  if (f.password !== f.confirm) return show('Passwords do not match', 'error')
  loading.value = true
  try {
    const user = await auth.register({
      email: f.email,
      password: f.password,
      full_name: f.full_name,
      role: role.value,
    })
    show(`Welcome to LearnHub, ${user.full_name.split(' ')[0]}!`)
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
        <p class="text-slate-500 text-sm mt-1">Join thousands of learners and instructors</p>
      </div>

      <div class="card p-2 grid grid-cols-2 gap-2 mb-5">
        <button @click="role = 'student'" class="flex items-center justify-center gap-2 rounded-lg py-3 text-sm font-semibold transition"
          :class="role === 'student' ? 'bg-brand-600 text-white shadow' : 'text-slate-500 hover:bg-slate-50'">
          <GraduationCap class="w-4.5 h-4.5" /> I'm a student
        </button>
        <button @click="role = 'instructor'" class="flex items-center justify-center gap-2 rounded-lg py-3 text-sm font-semibold transition"
          :class="role === 'instructor' ? 'bg-brand-600 text-white shadow' : 'text-slate-500 hover:bg-slate-50'">
          <Briefcase class="w-4.5 h-4.5" /> I'm an instructor
        </button>
      </div>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="label">Full name</label>
          <input v-model="form.full_name" type="text" class="input" placeholder="Ada Lovelace" />
        </div>
        <div>
          <label class="label">Email</label>
          <input v-model="form.email" type="email" class="input" placeholder="you@example.com" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">Password</label>
            <input v-model="form.password" type="password" class="input" placeholder="6+ characters" />
          </div>
          <div>
            <label class="label">Confirm</label>
            <input v-model="form.confirm" type="password" class="input" placeholder="Repeat password" />
          </div>
        </div>
        <button type="submit" class="btn-primary w-full py-3" :disabled="loading">
          {{ loading ? 'Creating account…' : `Sign up as ${role}` }}
        </button>
        <p class="text-center text-sm text-slate-500">
          Already have an account? <NuxtLink to="/login" class="text-brand-700 font-semibold hover:underline">Sign in</NuxtLink>
        </p>
      </form>
    </div>
  </div>
</template>
