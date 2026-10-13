<script setup lang="ts">
import {
  ArrowRight, Code2, Server, Workflow, Presentation, MonitorPlay, LifeBuoy,
  Lightbulb, Sparkles, Award, Accessibility, TrendingUp, CheckCircle2, GraduationCap, Video
} from 'lucide-vue-next'

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
    featured.value = f.slice(0, 2)
    stats.value = s
  } catch { /* the page stays useful without live data */ }
})

const services = [
  { icon: Code2, title: 'Web & Software Development', text: 'Modern websites and tailored software for your business and operations.' },
  { icon: Server, title: 'IT Solutions & Consulting', text: 'Practical guidance and systems that improve productivity and day-to-day operations.' },
  { icon: Workflow, title: 'Digital Transformation', text: 'Adopt digital tools and processes that lift efficiency and customer experience.' },
  { icon: Presentation, title: 'Technology Training', text: 'Hands-on training that builds relevant digital capabilities for people and teams.' },
  { icon: MonitorPlay, title: 'LMS & Digital Learning Solutions', text: 'Deliver, manage and monitor online learning for your organization.' },
  { icon: LifeBuoy, title: 'Digital Support & Maintenance', text: 'Ongoing support that keeps your platforms reliable and effective.' },
]

const reasons = [
  { icon: CheckCircle2, title: 'Practical Solutions', text: 'We focus on solutions that address real needs and create measurable value.' },
  { icon: Lightbulb, title: 'Innovation', text: 'We embrace technology and new ideas to deliver better solutions.' },
  { icon: Award, title: 'Quality', text: 'We are committed to excellence in our services and learning experiences.' },
  { icon: Accessibility, title: 'Accessibility', text: 'We believe technology and knowledge should be accessible to more people.' },
  { icon: TrendingUp, title: 'Growth', text: 'We help individuals and organizations continuously learn, improve, and grow.' },
]
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
            <Sparkles class="w-3.5 h-3.5" /> Technology. Learning. Innovation. Growth.
          </span>
          <h1 class="mt-5 text-4xl sm:text-5xl lg:text-[3.6rem] font-extrabold leading-[1.08] tracking-tight">
            Empowering People and Organizations <span class="text-brand-400">Through Technology</span>
          </h1>
          <p class="mt-5 text-lg text-slate-300 max-w-2xl leading-relaxed">
            At Infohive Technology Ltd., we provide innovative technology solutions and digital learning opportunities that help
            businesses, institutions, professionals, and individuals thrive in a rapidly changing digital world.
          </p>
          <p class="mt-3 text-slate-400 max-w-2xl leading-relaxed">
            From technology services and digital solutions to online learning and professional development, we connect people
            with the tools, knowledge, and opportunities they need to succeed.
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <NuxtLink to="/services" class="btn bg-white text-slate-900 hover:bg-slate-100 px-6 py-3 text-base font-bold">
              Explore Our Services <ArrowRight class="w-4 h-4" />
            </NuxtLink>
            <NuxtLink to="/lms" class="btn bg-brand-500 hover:bg-brand-400 text-white px-6 py-3 text-base font-bold">
              Start Learning
            </NuxtLink>
          </div>
        </div>

        <!-- learning snapshot -->
        <div class="hidden lg:block">
          <div class="rounded-3xl bg-white/[0.06] border border-white/10 p-6 backdrop-blur">
            <p class="text-xs uppercase tracking-[0.18em] text-slate-400 font-semibold">Infohive LMS</p>
            <div class="mt-4 grid grid-cols-3 gap-3 text-center">
              <div class="rounded-2xl bg-white/5 p-4"><div class="text-3xl font-extrabold">{{ stats.courses }}</div><div class="text-xs text-slate-400 mt-1">Courses</div></div>
              <div class="rounded-2xl bg-white/5 p-4"><div class="text-3xl font-extrabold">{{ stats.users }}</div><div class="text-xs text-slate-400 mt-1">Learners</div></div>
              <div class="rounded-2xl bg-white/5 p-4"><div class="text-3xl font-extrabold">{{ stats.enrollments }}</div><div class="text-xs text-slate-400 mt-1">Enrolments</div></div>
            </div>
            <ul class="mt-5 space-y-2.5 text-sm text-slate-300">
              <li class="flex gap-2"><GraduationCap class="w-4.5 h-4.5 text-brand-400 shrink-0" /> Self-paced courses with assessments</li>
              <li class="flex gap-2"><Video class="w-4.5 h-4.5 text-brand-400 shrink-0" /> Live classes with your instructors</li>
              <li class="flex gap-2"><Award class="w-4.5 h-4.5 text-brand-400 shrink-0" /> Verifiable course certificates</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- about -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-20 grid lg:grid-cols-2 gap-10 items-center">
      <div>
        <p class="text-sm font-bold uppercase tracking-[0.16em] text-brand-600">About Infohive</p>
        <h2 class="mt-2 text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">Technology That Creates Possibilities</h2>
      </div>
      <div>
        <p class="text-slate-600 text-lg leading-relaxed">
          Infohive Technology Ltd. is a technology and digital solutions company committed to helping individuals and organizations
          harness the power of technology. We combine innovation, practical technology solutions, and digital learning to solve
          real-world challenges and create opportunities for sustainable growth.
        </p>
        <NuxtLink to="/about" class="mt-4 inline-flex items-center gap-1.5 font-semibold text-brand-700 hover:underline">More about us <ArrowRight class="w-4 h-4" /></NuxtLink>
      </div>
    </section>

    <!-- services -->
    <section class="bg-slate-50 border-y border-slate-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-20">
        <div class="max-w-2xl">
          <p class="text-sm font-bold uppercase tracking-[0.16em] text-brand-600">Our Services</p>
          <h2 class="mt-2 text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">Solutions that move your organization forward</h2>
          <p class="mt-3 text-slate-600 leading-relaxed">We provide technology solutions designed to help organizations improve productivity, efficiency, digital operations, and service delivery.</p>
        </div>
        <div class="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="s in services" :key="s.title" class="card p-6 hover:border-brand-300 hover:-translate-y-0.5 transition">
            <div class="w-11 h-11 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center"><component :is="s.icon" class="w-5.5 h-5.5" /></div>
            <h3 class="mt-4 font-bold text-slate-900">{{ s.title }}</h3>
            <p class="mt-1.5 text-sm text-slate-600 leading-relaxed">{{ s.text }}</p>
          </div>
        </div>
        <NuxtLink to="/services" class="btn-secondary mt-8 inline-flex">View All Services <ArrowRight class="w-4 h-4" /></NuxtLink>
      </div>
    </section>

    <!-- learn -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-20">
      <div class="grid lg:grid-cols-[1fr_1.4fr] gap-10 items-start">
        <div>
          <p class="text-sm font-bold uppercase tracking-[0.16em] text-brand-600">Learn With Infohive</p>
          <h2 class="mt-2 text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">Build Skills. Advance Your Career. Keep Learning.</h2>
          <p class="mt-4 text-slate-600 leading-relaxed">
            Our Learning Management System gives learners access to structured courses and digital learning resources designed to
            support professional development, digital skills, entrepreneurship, and lifelong learning.
          </p>
          <p class="mt-3 text-slate-600 leading-relaxed">
            Explore courses, learn at your own pace, complete assessments, and work toward recognized course certificates.
          </p>
          <NuxtLink to="/courses" class="btn-primary mt-6 inline-flex px-6 py-3">Explore Courses <ArrowRight class="w-4 h-4" /></NuxtLink>
        </div>
        <div v-if="featured.length" class="grid sm:grid-cols-2 gap-4">
          <CourseCard v-for="c in featured" :key="c.id" :course="c" />
        </div>
        <div v-else class="card p-10 text-center text-slate-500">
          <GraduationCap class="w-10 h-10 mx-auto text-slate-300 mb-2" />
          New courses are being added. <NuxtLink to="/courses" class="text-brand-700 font-semibold">Browse the catalogue →</NuxtLink>
        </div>
      </div>
    </section>

    <!-- why -->
    <section class="bg-slate-900 text-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-20">
        <p class="text-sm font-bold uppercase tracking-[0.16em] text-brand-400">Why Choose Infohive?</p>
        <h2 class="mt-2 text-3xl sm:text-4xl font-extrabold tracking-tight max-w-2xl">What you can count on from us</h2>
        <div class="mt-10 grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div v-for="r in reasons" :key="r.title" class="rounded-2xl bg-white/[0.05] border border-white/10 p-5">
            <component :is="r.icon" class="w-6 h-6 text-amber-400" />
            <h3 class="mt-3 font-bold">{{ r.title }}</h3>
            <p class="mt-1.5 text-sm text-slate-400 leading-relaxed">{{ r.text }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-20">
      <div class="rounded-3xl bg-gradient-to-br from-brand-600 to-brand-800 text-white p-8 sm:p-12 lg:p-14 relative overflow-hidden">
        <div class="absolute -right-10 -top-10 w-56 h-56 rounded-full bg-white/10" />
        <h2 class="relative text-3xl sm:text-4xl font-extrabold tracking-tight max-w-2xl">Ready to Learn, Build, or Transform?</h2>
        <p class="relative mt-3 text-brand-50 max-w-2xl leading-relaxed">
          Whether you need a technology solution, digital transformation support, training, or access to practical online courses,
          Infohive Technology Ltd. is ready to help.
        </p>
        <div class="relative mt-7 flex flex-wrap gap-3">
          <NuxtLink to="/register" class="btn bg-white text-brand-800 hover:bg-brand-50 px-6 py-3 font-bold">Get Started</NuxtLink>
          <NuxtLink to="/lms" class="btn border border-white/40 text-white hover:bg-white/10 px-6 py-3 font-bold">Start Learning</NuxtLink>
          <NuxtLink to="/contact" class="btn border border-white/40 text-white hover:bg-white/10 px-6 py-3 font-bold">Contact Us</NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>
