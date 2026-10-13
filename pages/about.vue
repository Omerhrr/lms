<script setup lang="ts">
import { Eye, Target, ArrowRight } from 'lucide-vue-next'

useSeoMeta({ title: 'About Us - Infohive Technology Ltd.', description: 'Technology with purpose. Learning with impact. Who we are, our vision, mission and values.' })

const { content } = useSiteContent()
const a = computed(() => content.value?.about)
</script>

<template>
  <div v-if="a">
    <PageHero eyebrow="Who We Are" :title="a.hero_title" :lead="a.hero_lead" />

    <section v-if="a.intro" class="max-w-4xl mx-auto px-4 sm:px-6 py-14">
      <p class="text-xl text-slate-700 leading-relaxed whitespace-pre-line">{{ a.intro }}</p>
    </section>

    <section v-if="a.vision || a.mission" class="max-w-7xl mx-auto px-4 sm:px-6 grid md:grid-cols-2 gap-5" :class="!a.intro && 'pt-14'">
      <div v-if="a.vision" class="card p-7 sm:p-8">
        <div class="w-11 h-11 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center"><Eye class="w-5.5 h-5.5" /></div>
        <h2 class="mt-4 text-xl font-extrabold text-slate-900">Our Vision</h2>
        <p class="mt-2 text-slate-600 leading-relaxed whitespace-pre-line">{{ a.vision }}</p>
      </div>
      <div v-if="a.mission" class="card p-7 sm:p-8">
        <div class="w-11 h-11 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center"><Target class="w-5.5 h-5.5" /></div>
        <h2 class="mt-4 text-xl font-extrabold text-slate-900">Our Mission</h2>
        <p class="mt-2 text-slate-600 leading-relaxed whitespace-pre-line">{{ a.mission }}</p>
      </div>
    </section>

    <section v-if="a.values.length" class="max-w-7xl mx-auto px-4 sm:px-6 py-16">
      <p class="text-sm font-bold uppercase tracking-[0.16em] text-brand-600">Our Core Values</p>
      <h2 class="mt-2 text-3xl font-extrabold text-slate-900 tracking-tight">What guides our work</h2>
      <div class="mt-8 swipe-row lg:grid-cols-5">
        <div v-for="v in a.values" :key="v.title" class="card p-5">
          <SiteIcon :name="v.icon" class="w-6 h-6 text-brand-600" />
          <h3 class="mt-3 font-bold text-slate-900">{{ v.title }}</h3>
          <p class="mt-1.5 text-sm text-slate-600 leading-relaxed">{{ v.text }}</p>
        </div>
      </div>
    </section>

    <section class="bg-slate-50 border-y border-slate-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-16 grid lg:grid-cols-2 gap-10">
        <div>
          <h2 class="text-2xl font-extrabold text-slate-900">What We Do</h2>
          <p class="mt-3 text-slate-600 leading-relaxed whitespace-pre-line">{{ a.what_we_do }}</p>
          <div class="mt-5 flex flex-wrap items-center gap-x-5 gap-y-3">
            <NuxtLink to="/services" class="btn-primary">Our Services <ArrowRight class="w-4 h-4" /></NuxtLink>
            <NuxtLink to="/lms" class="font-semibold text-brand-700 hover:underline">Learn With Infohive →</NuxtLink>
          </div>
        </div>
        <div v-if="a.commitment">
          <h2 class="text-2xl font-extrabold text-slate-900">Our Commitment</h2>
          <p class="mt-3 text-slate-600 leading-relaxed whitespace-pre-line">{{ a.commitment }}</p>
        </div>
      </div>
    </section>
  </div>
</template>
