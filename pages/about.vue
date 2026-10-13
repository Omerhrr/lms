<script setup lang="ts">
import { Lightbulb, ShieldCheck, Award, Accessibility, TrendingUp, Eye, Target, ArrowRight } from 'lucide-vue-next'

useSeoMeta({ title: 'About Us - Infohive Technology Ltd.', description: 'Technology with purpose. Learning with impact. Who we are, our vision, mission and values.' })

const values = [
  { icon: Lightbulb, title: 'Innovation', text: 'We seek better, smarter, and more effective ways to solve problems.' },
  { icon: ShieldCheck, title: 'Integrity', text: 'We build relationships based on trust, transparency, and accountability.' },
  { icon: Award, title: 'Excellence', text: 'We strive to deliver quality in every service and learning experience.' },
  { icon: Accessibility, title: 'Accessibility', text: 'We work toward making technology and knowledge easier to access.' },
  { icon: TrendingUp, title: 'Growth', text: 'We believe continuous learning and improvement are essential to success.' },
]
</script>

<template>
  <div>
    <PageHero eyebrow="Who We Are" title="Technology With Purpose. Learning With Impact."
      lead="Infohive Technology Ltd. is a technology and digital learning company focused on delivering practical technology solutions and creating opportunities for individuals and organizations to develop the knowledge and skills needed in today's digital economy." />

    <section class="max-w-4xl mx-auto px-4 sm:px-6 py-14">
      <p class="text-xl text-slate-700 leading-relaxed">
        We believe technology should do more than automate processes. It should create opportunities, improve access to information,
        strengthen organizations, and empower people to achieve more.
      </p>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 grid md:grid-cols-2 gap-5">
      <div class="card p-7 sm:p-8">
        <div class="w-11 h-11 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center"><Eye class="w-5.5 h-5.5" /></div>
        <h2 class="mt-4 text-xl font-extrabold text-slate-900">Our Vision</h2>
        <p class="mt-2 text-slate-600 leading-relaxed">To become a leading technology and digital learning company that empowers individuals and organizations across Africa and beyond to achieve more through technology, innovation, and knowledge.</p>
      </div>
      <div class="card p-7 sm:p-8">
        <div class="w-11 h-11 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center"><Target class="w-5.5 h-5.5" /></div>
        <h2 class="mt-4 text-xl font-extrabold text-slate-900">Our Mission</h2>
        <p class="mt-2 text-slate-600 leading-relaxed">To deliver innovative technology solutions and accessible learning opportunities that enable people and organizations to improve their capabilities, solve problems, and achieve sustainable growth.</p>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-16">
      <p class="text-sm font-bold uppercase tracking-[0.16em] text-brand-600">Our Core Values</p>
      <h2 class="mt-2 text-3xl font-extrabold text-slate-900 tracking-tight">What guides our work</h2>
      <div class="mt-8 grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div v-for="v in values" :key="v.title" class="card p-5">
          <component :is="v.icon" class="w-6 h-6 text-brand-600" />
          <h3 class="mt-3 font-bold text-slate-900">{{ v.title }}</h3>
          <p class="mt-1.5 text-sm text-slate-600 leading-relaxed">{{ v.text }}</p>
        </div>
      </div>
    </section>

    <section class="bg-slate-50 border-y border-slate-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-16 grid lg:grid-cols-2 gap-10">
        <div>
          <h2 class="text-2xl font-extrabold text-slate-900">What We Do</h2>
          <p class="mt-3 text-slate-600 leading-relaxed">Our work brings together technology services and digital learning. We support organizations with technology solutions while providing individuals and teams with opportunities to learn new skills through our LMS.</p>
          <div class="mt-5 flex flex-wrap gap-3">
            <NuxtLink to="/services" class="btn-primary">Our Services <ArrowRight class="w-4 h-4" /></NuxtLink>
            <NuxtLink to="/lms" class="btn-secondary">Learn With Infohive</NuxtLink>
          </div>
        </div>
        <div>
          <h2 class="text-2xl font-extrabold text-slate-900">Our Commitment</h2>
          <p class="mt-3 text-slate-600 leading-relaxed">We are committed to creating technology experiences that are useful, reliable, accessible, and focused on real-world results. As technology continues to evolve, we aim to remain a trusted partner for organizations and individuals navigating the digital future.</p>
        </div>
      </div>
    </section>
  </div>
</template>
