<script setup lang="ts">
defineProps<{ title: string; updated: string }>()
</script>

<template>
  <div>
    <PageHero eyebrow="Infohive Technology Ltd." :title="title" :lead="`Last updated: ${updated}`" />
    <article class="max-w-3xl mx-auto px-4 sm:px-6 py-12 rich-text text-slate-700">
      <p class="!mt-0 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-sm p-4">
        Draft: please have this reviewed by your legal adviser and complete the bracketed details before launch.
      </p>
      <slot />
    </article>
  </div>
</template>
