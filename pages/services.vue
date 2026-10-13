<script setup lang="ts">
import { ArrowRight } from 'lucide-vue-next'

useSeoMeta({ title: 'Services - Infohive Technology Ltd.', description: 'Web and software development, IT solutions and consulting, digital transformation, technology and corporate training, LMS solutions and digital support.' })

const { content } = useSiteContent()
const sv = computed(() => content.value?.services)
</script>

<template>
  <div v-if="sv">
    <PageHero eyebrow="Services" :title="sv.hero_title" :lead="sv.hero_lead" />

    <section class="max-w-7xl mx-auto px-4 sm:px-6 py-14 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="s in sv.items" :key="s.title" class="card p-6 flex flex-col">
        <div class="w-11 h-11 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center"><SiteIcon :name="s.icon" class="w-5.5 h-5.5" /></div>
        <h2 class="mt-4 text-lg font-bold text-slate-900">{{ s.title }}</h2>
        <p class="mt-2 text-sm text-slate-600 leading-relaxed flex-1">{{ s.text || s.summary }}</p>
        <NuxtLink :to="{ path: '/contact', query: { topic: s.topic } }" class="mt-4 text-sm font-semibold text-brand-700 hover:underline inline-flex items-center gap-1">
          Enquire about {{ s.title }} <ArrowRight class="w-3.5 h-3.5" />
        </NuxtLink>
      </div>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 pb-16">
      <div class="rounded-3xl bg-slate-900 text-white p-8 sm:p-12 grid lg:grid-cols-[1.5fr_auto] gap-6 items-center">
        <div>
          <h2 class="text-3xl font-extrabold tracking-tight">{{ sv.cta_title }}</h2>
          <p class="mt-3 text-slate-300 leading-relaxed max-w-2xl">{{ sv.cta_text }}</p>
        </div>
        <NuxtLink to="/contact" class="btn bg-brand-500 hover:bg-brand-400 text-white px-6 py-3 font-bold justify-self-start">Talk to Us <ArrowRight class="w-4 h-4" /></NuxtLink>
      </div>
    </section>
  </div>
</template>
