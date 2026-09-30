<script setup lang="ts">
import { Star, StarHalf } from 'lucide-vue-next'

const props = defineProps<{ rating: number; size?: string }>()
const full = computed(() => Math.floor(props.rating))
const hasHalf = computed(() => props.rating - full.value >= 0.5)
</script>

<template>
  <div class="flex items-center gap-0.5" :class="size || 'w-4 h-4'">
    <Star v-for="i in full" :key="'f' + i" class="w-4 h-4 fill-amber-400 text-amber-400" :class="size || ''" />
    <StarHalf v-if="hasHalf" class="w-4 h-4 fill-amber-400 text-amber-400" :class="size || ''" />
    <Star v-for="i in (5 - full - (hasHalf ? 1 : 0))" :key="'e' + i" class="w-4 h-4 text-slate-300" :class="size || ''" />
  </div>
</template>
