<script setup lang="ts">
import { Search, ArrowRight, Sparkles, BookOpen, Users, GraduationCap, Trophy, CheckCircle2 } from 'lucide-vue-next'

useSeoMeta({ title: 'LearnHub - Learn anything, teach everything' })

const api = useApi()
const auth = useAuth()
const featured = ref<any[]>([])
const categories = ref<any[]>([])
const stats = ref({ courses: 0, enrollments: 0, users: 0 })
const loading = ref(true)

onMounted(async () => {
  try {
    const [f, c] = await Promise.all([
      api.get<any[]>('/courses/featured', undefined, true),
      api.get<any[]>('/categories', undefined, true),
    ])
    featured.value = f
    categories.value = c
    // lightweight platform stats from the catalog
    const list = await api.get<any>('/courses?size=48', undefined, true)
    stats.value = {
      courses: list.total,
      enrollments: list.items.reduce((s: number, c: any) => s + c.enrollment_count, 0),
      users: list.items.reduce((s: number, c: any) => s + c.enrollment_count, 0),
    }
  } catch { /* landing stays graceful */ } finally { loading.value = false }
})
</script>

<template>
  <div>
    <!-- hero -->
    <section class="relative overflow-hidden bg-slate-900 text-white">
      <div class="absolute inset-0 bg-gradient-to-br from-brand-900/60 via-slate-900 to-slate-900" />
      <div class="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-brand-500/20 blur-3xl" />
      <div class="absolute -bottom-32 -left-24 w-96 h-96 rounded-full bg-amber-400/10 blur-3xl" />
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 py-20 lg:py-28 grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <span class="badge bg-white/10 text-brand-300 border border-white/10 mb-5">
            <Sparkles class="w-3.5 h-3.5 mr-1" /> Industry-standard LMS, your own platform
          </span>
          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.1] tracking-tight">
            Learn anything.<br />
            <span class="text-brand-400">Teach everything.</span>
          </h1>
          <p class="mt-5 text-lg text-slate-300 max-w-xl leading-relaxed">
            LearnHub is a full-featured learning management system - video lessons, quizzes with auto-grading,
            assignments, discussions, certificates and analytics. All in one place.
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <NuxtLink to="/courses" class="btn bg-white text-slate-900 hover:bg-slate-100 px-6 py-3 text-base font-bold">
              Browse courses <ArrowRight class="w-4 h-4" />
            </NuxtLink>
            <NuxtLink v-if="!auth.isLoggedIn.value" to="/register?role=instructor" class="btn border border-white/25 text-white hover:bg-white/10 px-6 py-3 text-base font-bold">
              Start teaching
            </NuxtLink>
            <NuxtLink v-else :to="auth.isStudent.value ? '/dashboard' : '/teach'" class="btn border border-white/25 text-white hover:bg-white/10 px-6 py-3 text-base font-bold">
              Go to dashboard
            </NuxtLink>
          </div>
          <div class="mt-10 flex flex-wrap gap-8 text-sm">
            <div><div class="text-2xl font-extrabold text-white">{{ stats.courses }}+</div><div class="text-slate-400">Courses</div></div>
            <div><div class="text-2xl font-extrabold text-white">{{ stats.enrollments }}+</div><div class="text-slate-400">Enrollments</div></div>
            <div><div class="text-2xl font-extrabold text-white">6+</div><div class="text-slate-400">Demo users</div></div>
          </div>
        </div>

        <div class="hidden lg:block relative">
          <div class="bg-white rounded-2xl shadow-2xl p-6 text-slate-800 rotate-2 hover:rotate-0 transition-transform duration-300">
            <div class="flex items-center justify-between mb-4">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Course progress</span>
              <span class="badge bg-brand-50 text-brand-700">Python: Zero to Hero</span>
            </div>
            <div class="h-2.5 rounded-full bg-slate-100 overflow-hidden mb-5">
              <div class="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-400" style="width: 68%" />
            </div>
            <div class="space-y-2.5 text-sm">
              <div class="flex items-center gap-2.5 text-slate-600"><CheckCircle2 class="w-4.5 h-4.5 text-brand-500" /> Variables & data types</div>
              <div class="flex items-center gap-2.5 text-slate-600"><CheckCircle2 class="w-4.5 h-4.5 text-brand-500" /> Control flow quiz - <b class="text-brand-600">85%</b></div>
              <div class="flex items-center gap-2.5 text-slate-400"><div class="w-4.5 h-4.5 rounded-full border-2 border-slate-300" /> Functions & reusable code</div>
              <div class="flex items-center gap-2.5 text-slate-400"><Trophy class="w-4.5 h-4.5 text-amber-400" /> Certificate on completion</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- categories -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-14">
      <div class="flex flex-wrap justify-center gap-3">
        <NuxtLink v-for="c in categories" :key="c.id" :to="`/courses?category_id=${c.id}`"
          class="badge bg-white border border-slate-200 hover:border-brand-400 hover:text-brand-700 text-slate-600 px-4 py-2 text-sm shadow-sm transition">
          {{ c.name }}
        </NuxtLink>
      </div>
    </section>

    <!-- featured courses -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 pb-16">
      <div class="flex items-end justify-between mb-6">
        <div>
          <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900">Featured courses</h2>
          <p class="text-slate-500 mt-1">Hand-picked by our team to get you started</p>
        </div>
        <NuxtLink to="/courses" class="btn-ghost text-brand-700 hidden sm:inline-flex">
          View all <ArrowRight class="w-4 h-4" />
        </NuxtLink>
      </div>

      <div v-if="loading" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="i in 3" :key="i" class="card h-80 animate-pulse" />
      </div>
      <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <CourseCard v-for="c in featured" :key="c.id" :course="c" />
      </div>
    </section>

    <!-- features -->
    <section class="bg-white border-y border-slate-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-16">
        <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 text-center">Everything a modern LMS needs</h2>
        <p class="text-center text-slate-500 mt-2 max-w-2xl mx-auto">Built on a modular monolith - FastAPI + SQLAlchemy backend, Nuxt frontend - ready to grow into SaaS.</p>
        <div class="mt-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div class="card p-5"><BookOpen class="w-8 h-8 text-brand-600 mb-3" /><h3 class="font-bold">Course builder</h3><p class="text-sm text-slate-500 mt-1">Sections, video/text/file lessons, quizzes and resources with drag-free reordering.</p></div>
          <div class="card p-5"><Users class="w-8 h-8 text-brand-600 mb-3" /><h3 class="font-bold">Enrollment & progress</h3><p class="text-sm text-slate-500 mt-1">One-click enrollment, per-lesson completion tracking and live progress bars.</p></div>
          <div class="card p-5"><GraduationCap class="w-8 h-8 text-brand-600 mb-3" /><h3 class="font-bold">Certificates</h3><p class="text-sm text-slate-500 mt-1">Auto-issued on completion with publicly verifiable serial numbers.</p></div>
          <div class="card p-5"><Trophy class="w-8 h-8 text-brand-600 mb-3" /><h3 class="font-bold">Gradebook & analytics</h3><p class="text-sm text-slate-500 mt-1">Quiz attempts, assignment grading, completion rates and revenue insights.</p></div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-16">
      <div class="rounded-3xl bg-gradient-to-r from-brand-600 to-brand-800 text-white p-10 text-center">
        <h2 class="text-2xl sm:text-3xl font-extrabold">Ready to start learning?</h2>
        <p class="mt-2 text-brand-100">Join LearnHub today - demo accounts are available on the sign-in page.</p>
        <div class="mt-6 flex justify-center gap-3 flex-wrap">
          <NuxtLink to="/register" class="btn bg-white text-brand-800 hover:bg-brand-50 px-6">Create free account</NuxtLink>
          <NuxtLink to="/courses" class="btn border border-white/40 text-white hover:bg-white/10 px-6"><Search class="w-4 h-4" /> Explore courses</NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>
