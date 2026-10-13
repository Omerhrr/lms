<script setup lang="ts">
import { Star, StarHalf } from 'lucide-vue-next'

/** Read-only star rating. `size` is a Tailwind size class for each star (default w-4 h-4). */
const props = withDefaults(defineProps<{ rating: number; size?: string }>(), { size: 'w-4 h-4' })
const full = computed(() => Math.min(5, Math.floor(props.rating || 0)))
const hasHalf = computed(() => full.value < 5 && (props.rating || 0) - full.value >= 0.5)
const empty = computed(() => 5 - full.value - (hasHalf.value ? 1 : 0))
</script>

<template>
  <span class="inline-flex items-center gap-0.5 shrink-0" role="img" :aria-label="`Rated ${rating} out of 5`">
    <Star v-for="i in full" :key="'f' + i" :class="size" class="fill-amber-400 text-amber-400" aria-hidden="true" />
    <span v-if="hasHalf" class="relative inline-flex" :class="size" aria-hidden="true">
      <Star :class="size" class="text-slate-300 absolute inset-0" />
      <StarHalf :class="size" class="fill-amber-400 text-amber-400 relative" />
    </span>
    <Star v-for="i in empty" :key="'e' + i" :class="size" class="text-slate-300" aria-hidden="true" />
  </span>
</template>
