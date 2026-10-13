<script setup lang="ts">
import { ArrowRight, Sparkles, Award, GraduationCap, Video } from 'lucide-vue-next'

useSeoMeta({
  title: 'Infohive Technology Ltd. - Technology. Learning. Innovation. Growth.',
  description: 'Technology solutions and digital learning that help businesses, institutions, professionals and individuals thrive in a rapidly changing digital world.',
})

const api = useApi()
const featured = ref<any[]>([])
const stats = ref({ courses: 0, enrollments: 0, users: 0 })

onMounted(async () => {
  try {
    const [f, s] = await Promise.all([
      api.get<any[]>('/courses/featured', undefined, true),
      api.get<any>('/stats/public', undefined, true),
    ])
    featured.value = f.slice(0, 3)
    stats.value = s
  } catch { /* the page stays useful without live data */ }
})

const { content } = useSiteContent()
const h = computed(() => content.value?.home || {} as Record<string, string>)
const services = computed(() => (content.value?.services.items || []).filter(i => i.on_home).slice(0, 6))
const reasons = computed(() => content.value?.reasons.items || [])
</script>

<template>
  <div>
    <!-- hero -->
    <section class="relative overflow-hidden bg-slate-900 text-white">
      <div class="absolute inset-0 bg-gradient-to-br from-brand-900/70 via-slate-900 to-slate-900" />
      <div class="absolute inset-0 opacity-[0.07]" style="background-image:url(&quot;data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='56' height='98'%3E%3Cpath d='M28 66 0 50V18L28 2l28 16v32zm0 32L0 82V66l28 16 28-16v16z' fill='none' stroke='%23fff' stroke-width='1'/%3E%3C/svg%3E&quot;)" />
      <div class="absolute -bottom-32 -right-24 w-[28rem] h-[28rem] rounded-full bg-amber-400/10 blur-3xl" />
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 py-20 lg:py-28 grid lg:grid-cols-[1.25fr_1fr] gap-12 items-center">
        <div>
          <span class="inline-flex items-center gap-1.5 rounded-full bg-white/10 border border-white/10 px-3 py-1 text-xs font-semibold tracking-wide text-brand-200">
            <Sparkles class="w-3.5 h-3.5" /> {{ h.badge }}
          </span>
          <h1 class="mt-5 text-4xl sm:text-5xl lg:text-[3.6rem] font-extrabold leading-[1.08] tracking-tight">
            {{ h.headline }} <span class="text-brand-400">{{ h.highlight }}</span>
          </h1>
          <p class="mt-5 text-lg text-slate-300 max-w-xl leading-relaxed">{{ h.lead }}</p>
          <div class="mt-8 flex flex-wrap gap-3">
            <NuxtLink to="/lms" class="btn bg-brand-500 hover:bg-brand-400 text-white px-6 py-3 text-base font-bold">
              Start Learning <ArrowRight class="w-4 h-4" />
            </NuxtLink>
            <NuxtLink to="/services" class="btn btn-outline-light px-6 py-3 text-base font-bold">
              Explore Our Services <ArrowRight class="w-4 h-4" />
            </NuxtLink>
          </div>
        </div>

        <!-- a real course, not a list of claims -->
        <div class="hidden lg:block">
          <div v-if="featured[0]" class="max-w-sm ml-auto rotate-1 hover:rotate-0 transition">
            <p class="text-xs uppercase tracking-[0.18em] text-slate-300 font-semibold mb-3">Featured course</p>
            <CourseCard :course="featured[0]" />
          </div>
          <ul v-else class="rounded-3xl bg-white/[0.06] border border-white/10 p-6 space-y-2.5 text-sm text-slate-300">
            <li class="flex gap-2"><GraduationCap class="w-4.5 h-4.5 text-brand-400 shrink-0" /> Self-paced courses with assessments</li>
            <li class="flex gap-2"><Video class="w-4.5 h-4.5 text-brand-400 shrink-0" /> Live classes with your instructors</li>
            <li class="flex gap-2"><Award class="w-4.5 h-4.5 text-brand-400 shrink-0" /> Verifiable course certificates</li>
          </ul>
        </div>
      </div>
    </section>




    <!-- learn -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-20">
      <div class="grid lg:grid-cols-[1fr_1.4fr] gap-10 items-start">
        <div>
          <p class="text-sm font-bold uppercase tracking-[0.16em] text-brand-600">Learn With Infohive</p>
          <h2 class="mt-2 text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">{{ h.learn_title }}</h2>
          <p class="mt-4 text-slate-600 leading-relaxed">{{ h.learn_text }}</p>
          <NuxtLink to="/courses" class="btn-primary mt-6 inline-flex px-6 py-3">Explore Courses <ArrowRight class="w-4 h-4" /></NuxtLink>
        </div>
        <div v-if="featured.length" class="grid sm:grid-cols-2 gap-4">
          <!-- on large screens the first course is already in the hero -->
          <CourseCard v-for="(c, i) in featured" :key="c.id" :course="c" :class="i === 0 && featured.length > 2 ? 'lg:hidden' : ''" />
        </div>
        <div v-else class="card p-10 text-center text-slate-500">
          <GraduationCap class="w-10 h-10 mx-auto text-slate-300 mb-2" />
          New courses are being added. <NuxtLink to="/courses" class="text-brand-700 font-semibold">Browse the catalogue →</NuxtLink>
        </div>
      </div>
    </section>

    <ReviewsStrip />

    <!-- services -->
    <section class="bg-slate-50 border-y border-slate-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-20">
        <div class="max-w-2xl">
          <p class="text-sm font-bold uppercase tracking-[0.16em] text-brand-600">Our Services</p>
          <h2 class="mt-2 text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">{{ h.services_title }}</h2>
          <p class="mt-3 text-slate-600 leading-relaxed">{{ h.services_lead }}</p>
        </div>
        <div class="mt-8 swipe-row lg:grid-cols-3">
          <div v-for="s in services" :key="s.title" class="card p-6 hover:border-brand-300 hover:-translate-y-0.5 transition">
            <div class="w-11 h-11 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center"><SiteIcon :name="s.icon" class="w-5.5 h-5.5" /></div>
            <h3 class="mt-4 font-bold text-slate-900">{{ s.title }}</h3>
            <p class="mt-1.5 text-sm text-slate-600 leading-relaxed">{{ s.summary || s.text }}</p>
          </div>
        </div>
        <NuxtLink to="/services" class="btn-secondary mt-8 inline-flex">View All Services <ArrowRight class="w-4 h-4" /></NuxtLink>
      </div>
    </section>

    <!-- why -->

    <section class="bg-slate-900 text-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-20">
        <p class="text-sm font-bold uppercase tracking-[0.16em] text-brand-400">Why Choose Infohive?</p>
        <h2 class="mt-2 text-3xl sm:text-4xl font-extrabold tracking-tight max-w-2xl">{{ h.why_title }}</h2>
        <p class="mt-3 text-slate-300 max-w-2xl leading-relaxed">
          {{ h.why_text }}
          <NuxtLink to="/about" class="font-semibold text-brand-300 hover:underline whitespace-nowrap">More about us →</NuxtLink>
        </p>
        <div class="mt-8 swipe-row lg:grid-cols-5">
          <div v-for="r in reasons" :key="r.title" class="rounded-2xl bg-white/[0.05] border border-white/10 p-5">
            <SiteIcon :name="r.icon" class="w-6 h-6 text-amber-400" />
            <h3 class="mt-3 font-bold">{{ r.title }}</h3>
            <p class="mt-1.5 text-sm text-slate-300 leading-relaxed">{{ r.text }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-20">
      <div class="rounded-3xl bg-gradient-to-br from-brand-600 to-brand-800 text-white p-8 sm:p-12 lg:p-14 relative overflow-hidden">
                <h2 class="relative text-3xl sm:text-4xl font-extrabold tracking-tight max-w-2xl">{{ h.cta_title }}</h2>
        <p class="relative mt-3 text-brand-50 max-w-2xl leading-relaxed">{{ h.cta_text }}</p>
        <div class="relative mt-7 flex flex-wrap items-center gap-x-6 gap-y-3">
          <NuxtLink to="/register" class="btn btn-light px-6 py-3 font-bold">Create a free account</NuxtLink>
          <NuxtLink to="/contact" class="font-semibold text-white hover:underline">Or talk to our team →</NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>
