<script setup lang="ts">
/** Built-in draft text (slot) until an admin publishes the real policy in Admin → Website → Legal. */
const props = defineProps<{ title: string; updated: string; html?: string | null; customUpdated?: string }>()
const label = computed(() => (props.html ? props.customUpdated || '' : props.updated))
</script>

<template>
  <div>
    <PageHero eyebrow="Infohive Technology Ltd." :title="title" :lead="label ? `Last updated: ${label}` : undefined" />
    <!-- eslint-disable-next-line vue/no-v-html -- sanitized by the API on save -->
    <article v-if="html" class="max-w-3xl mx-auto px-4 sm:px-6 py-12 rich-text text-slate-700" v-html="html" />
    <article v-else class="max-w-3xl mx-auto px-4 sm:px-6 py-12 rich-text text-slate-700">
      <p class="!mt-0 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-sm p-4">
        Draft: please have this reviewed by your legal adviser and complete the bracketed details before launch.
      </p>
      <slot />
    </article>
  </div>
</template>
