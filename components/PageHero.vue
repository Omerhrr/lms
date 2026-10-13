<script setup lang="ts">
defineProps<{ eyebrow: string; title: string; lead?: string }>()
</script>

<template>
  <section class="relative overflow-hidden bg-slate-900 text-white">
    <div class="absolute inset-0 bg-gradient-to-br from-brand-900/70 via-slate-900 to-slate-900" />
    <div class="absolute -top-20 -right-20 w-80 h-80 rounded-full bg-brand-500/20 blur-3xl" />
    <div class="relative max-w-7xl mx-auto px-4 sm:px-6 py-14 sm:py-20">
      <p class="text-sm font-bold uppercase tracking-[0.16em] text-brand-300">{{ eyebrow }}</p>
      <h1 class="mt-3 text-3xl sm:text-5xl font-extrabold tracking-tight max-w-3xl leading-[1.1]">{{ title }}</h1>
      <p v-if="lead" class="mt-4 text-lg text-slate-300 max-w-3xl leading-relaxed">{{ lead }}</p>
      <div v-if="$slots.default" class="mt-7 flex flex-wrap gap-3"><slot /></div>
    </div>
  </section>
</template>
