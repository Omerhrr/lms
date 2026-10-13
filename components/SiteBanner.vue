<script setup lang="ts">
import { X, ArrowRight } from 'lucide-vue-next'

/** Site-wide announcement set in Admin → Website. Visitors can dismiss it (remembered per message). */
const { content } = useSiteContent()
const banner = computed(() => content.value?.banner)
const key = computed(() => `lh-banner:${banner.value?.text || ''}`)
const dismissed = ref(true)
onMounted(() => {
  try { dismissed.value = localStorage.getItem(key.value) === '1' } catch { dismissed.value = false }
})
const dismiss = () => {
  dismissed.value = true
  try { localStorage.setItem(key.value, '1') } catch { /* private mode */ }
}
const external = computed(() => (banner.value?.link_url || '').startsWith('http'))
const tone = computed(() => ({
  brand: 'bg-brand-700 text-white', amber: 'bg-amber-400 text-amber-950', slate: 'bg-slate-900 text-white',
}[banner.value?.tone || 'brand']))
</script>

<template>
  <div v-if="banner?.enabled && banner.text && !dismissed" class="banner-bar text-sm" :class="tone" role="region" aria-label="Announcement">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 py-2 flex items-center gap-3">
      <p class="flex-1 min-w-0 text-center">
        {{ banner.text }}
        <template v-if="banner.link_url && banner.link_label">
          <a v-if="external" :href="banner.link_url" target="_blank" rel="noopener noreferrer" class="ml-1 font-bold underline underline-offset-2 inline-flex items-center gap-1">{{ banner.link_label }} <ArrowRight class="w-3.5 h-3.5" /></a>
          <NuxtLink v-else :to="banner.link_url" class="ml-1 font-bold underline underline-offset-2 inline-flex items-center gap-1">{{ banner.link_label }} <ArrowRight class="w-3.5 h-3.5" /></NuxtLink>
        </template>
      </p>
      <button type="button" class="p-1 rounded opacity-80 hover:opacity-100 shrink-0" aria-label="Dismiss announcement" @click="dismiss"><X class="w-4 h-4" /></button>
    </div>
  </div>
</template>
