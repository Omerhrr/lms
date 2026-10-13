<script setup lang="ts">
import { Clock, Wrench, BarChart3, ClipboardCheck, Award, Video, User, Building2, Handshake, ArrowRight, Search } from 'lucide-vue-next'

useSeoMeta({ title: 'LMS / Courses - Infohive', description: 'Welcome to the Infohive Learning Management System - flexible, accessible and practical online learning.' })

const api = useApi()
const auth = useAuth()
const router = useRouter()
const featured = ref<any[]>([])
const categories = ref<any[]>([])
const q = ref('')
onMounted(async () => {
  try {
    const [f, c] = await Promise.all([api.get<any[]>('/courses/featured', undefined, true), api.get<any[]>('/categories', undefined, true)])
    featured.value = f
    categories.value = c
  } catch { /* still useful without live data */ }
})
const search = () => router.push({ path: '/courses', query: q.value.trim() ? { search: q.value.trim() } : {} })

const why = [
  { icon: Clock, title: 'Learn at Your Own Pace', text: 'Access your courses and learning materials when it is convenient for you.' },
  { icon: Wrench, title: 'Practical Learning', text: 'Focus on knowledge and skills that can be applied in real-world situations.' },
  { icon: BarChart3, title: 'Track Your Progress', text: 'Monitor your learning journey and completed activities.' },
  { icon: ClipboardCheck, title: 'Assess Your Knowledge', text: 'Complete quizzes, assessments, assignments, or examinations where applicable.' },
  { icon: Video, title: 'Join Live Classes', text: 'Learn together with your instructor in scheduled live sessions, right inside the LMS.' },
  { icon: Award, title: 'Earn Certificates', text: 'Complete eligible courses and receive certificates that recognize your achievement.' },
]
</script>

<template>
  <div>
    <PageHero eyebrow="Infohive LMS" title="Learn. Develop. Grow."
      lead="Welcome to the Infohive Learning Management System - your gateway to flexible, accessible, and practical online learning.">
      <NuxtLink to="/courses" class="btn btn-light px-6 py-3 font-bold">Explore Courses <ArrowRight class="w-4 h-4" /></NuxtLink>
      <NuxtLink v-if="!auth.isLoggedIn.value" to="/login" class="btn border border-white/30 text-white hover:bg-white/10 px-6 py-3 font-bold">Login to LMS</NuxtLink>
      <NuxtLink v-else :to="auth.homeFor(auth.user.value)" class="btn border border-white/30 text-white hover:bg-white/10 px-6 py-3 font-bold">My Learning</NuxtLink>
    </PageHero>

    <section class="max-w-4xl mx-auto px-4 sm:px-6 py-12 text-center">
      <p class="text-lg text-slate-600 leading-relaxed">Our LMS provides access to courses and learning resources designed to help individuals develop new skills, strengthen professional capabilities, and prepare for opportunities in an increasingly digital world.</p>
      <form class="mt-7 flex gap-2 max-w-xl mx-auto" @submit.prevent="search">
        <div class="relative flex-1">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input v-model="q" class="input pl-9" placeholder="Search courses…" aria-label="Search courses" />
        </div>
        <button class="btn-primary">Search</button>
      </form>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6">
      <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Why Learn With Infohive?</h2>
      <div class="mt-7 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="w in why" :key="w.title" class="card p-5 flex gap-4">
          <div class="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center shrink-0"><component :is="w.icon" class="w-5 h-5" /></div>
          <div><h3 class="font-bold text-slate-900">{{ w.title }}</h3><p class="mt-1 text-sm text-slate-600 leading-relaxed">{{ w.text }}</p></div>
        </div>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-14">
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Explore Our Courses</h2>
          <p class="mt-1 text-slate-600">Review course information, then register or start learning.</p>
        </div>
        <NuxtLink to="/courses" class="btn-secondary">View all courses <ArrowRight class="w-4 h-4" /></NuxtLink>
      </div>
      <div v-if="categories.length" class="mt-6 flex flex-wrap gap-2">
        <NuxtLink v-for="c in categories" :key="c.id" :to="{ path: '/courses', query: { category_id: c.id } }"
          class="px-3.5 py-1.5 rounded-full border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:border-brand-400 hover:text-brand-700 transition">{{ c.name }}</NuxtLink>
      </div>
      <div v-if="featured.length" class="mt-7 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <CourseCard v-for="c in featured" :key="c.id" :course="c" />
      </div>
    </section>

    <ReviewsStrip />

    <section class="bg-slate-50 border-y border-slate-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-14 grid md:grid-cols-3 gap-5">
        <div class="card p-6 flex flex-col">
          <User class="w-7 h-7 text-brand-600" />
          <h3 class="mt-3 text-lg font-bold text-slate-900">For Individuals</h3>
          <p class="mt-2 text-sm text-slate-600 leading-relaxed flex-1">Develop skills, improve your professional capabilities, explore new areas of knowledge, and continue learning through courses available on the Infohive LMS.</p>
          <NuxtLink to="/courses" class="btn-primary mt-5 self-start">Start Learning</NuxtLink>
        </div>
        <div class="card p-6 flex flex-col">
          <Building2 class="w-7 h-7 text-brand-600" />
          <h3 class="mt-3 text-lg font-bold text-slate-900">For Organizations</h3>
          <p class="mt-2 text-sm text-slate-600 leading-relaxed flex-1">Use the Infohive learning platform to support employee development, onboarding, internal training, and professional growth.</p>
          <NuxtLink :to="{ path: '/contact', query: { topic: 'Corporate Training' } }" class="btn-secondary mt-5 self-start">Discuss Corporate Training</NuxtLink>
        </div>
        <div class="card p-6 flex flex-col">
          <Handshake class="w-7 h-7 text-brand-600" />
          <h3 class="mt-3 text-lg font-bold text-slate-900">For Training Providers &amp; Instructors</h3>
          <p class="mt-2 text-sm text-slate-600 leading-relaxed flex-1">Deliver structured learning experiences, manage learning materials, run live classes, assess learners, and monitor progress on the platform.</p>
          <NuxtLink :to="{ path: '/contact', query: { topic: 'Partnership' } }" class="btn-secondary mt-5 self-start">Become a Partner</NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>
