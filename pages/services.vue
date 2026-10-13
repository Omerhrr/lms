<script setup lang="ts">
import { Globe, Code2, Server, Workflow, Compass, Presentation, Users, MonitorPlay, LifeBuoy, ArrowRight } from 'lucide-vue-next'

useSeoMeta({ title: 'Services - Infohive Technology Ltd.', description: 'Web and software development, IT solutions and consulting, digital transformation, technology and corporate training, LMS solutions and digital support.' })

const services = [
  { icon: Globe, title: 'Web Development', text: 'We design and develop modern, responsive websites that help businesses and organizations establish a strong digital presence and communicate effectively with their audiences.', topic: 'Web Development' },
  { icon: Code2, title: 'Software Development', text: 'We develop software and digital applications tailored to specific business, institutional, and operational needs.', topic: 'Technology / Software Project' },
  { icon: Server, title: 'IT Solutions', text: 'We provide practical technology solutions that help organizations improve their systems, processes, productivity, and day-to-day operations.', topic: 'Technology / Software Project' },
  { icon: Workflow, title: 'Digital Transformation', text: 'We help organizations adopt digital tools and processes that improve efficiency, customer experience, communication, and business performance.', topic: 'Digital Transformation' },
  { icon: Compass, title: 'IT Consulting', text: 'We provide technology guidance to help organizations understand their technology needs, identify opportunities, and choose appropriate solutions.', topic: 'IT Consulting' },
  { icon: Presentation, title: 'Technology Training', text: 'We provide practical technology training designed to help individuals, employees, and organizations develop relevant digital capabilities.', topic: 'Corporate Training' },
  { icon: Users, title: 'Corporate & Employee Training', text: 'Organizations can use our learning platform to deliver staff development, onboarding, compliance, skills development, and other training programs.', topic: 'Corporate Training' },
  { icon: MonitorPlay, title: 'LMS & Digital Learning Solutions', text: 'We provide learning technology solutions that enable organizations and training providers to deliver, manage, and monitor online learning.', topic: 'LMS / Learning Enquiry' },
  { icon: LifeBuoy, title: 'Digital Support & Maintenance', text: 'We provide ongoing technical support and maintenance to help keep digital platforms and technology solutions reliable and effective.', topic: 'General Enquiry' },
]
</script>

<template>
  <div>
    <PageHero eyebrow="Services" title="Technology Solutions Designed Around Your Needs"
      lead="At Infohive Technology Ltd., we help businesses, institutions, and individuals use technology more effectively. Our services are designed to improve digital presence, operational efficiency, productivity, and access to modern technology." />

    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-14 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="s in services" :key="s.title" class="card p-6 flex flex-col">
        <div class="w-11 h-11 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center"><component :is="s.icon" class="w-5.5 h-5.5" /></div>
        <h2 class="mt-4 text-lg font-bold text-slate-900">{{ s.title }}</h2>
        <p class="mt-2 text-sm text-slate-600 leading-relaxed flex-1">{{ s.text }}</p>
        <NuxtLink :to="{ path: '/contact', query: { topic: s.topic } }" class="mt-4 text-sm font-semibold text-brand-700 hover:underline inline-flex items-center gap-1">
          Enquire <ArrowRight class="w-3.5 h-3.5" />
        </NuxtLink>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 pb-16">
      <div class="rounded-3xl bg-slate-900 text-white p-8 sm:p-12 grid lg:grid-cols-[1.5fr_auto] gap-6 items-center">
        <div>
          <h2 class="text-3xl font-extrabold tracking-tight">Let's Build Something Better</h2>
          <p class="mt-3 text-slate-300 leading-relaxed max-w-2xl">Tell us what you want to build, improve, automate, or learn. Our team can help you identify the right technology or learning solution for your needs.</p>
        </div>
        <NuxtLink to="/contact" class="btn bg-brand-500 hover:bg-brand-400 text-white px-6 py-3 font-bold justify-self-start">Talk to Us <ArrowRight class="w-4 h-4" /></NuxtLink>
      </div>
    </section>
  </div>
</template>
