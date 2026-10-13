<script setup lang="ts">
import { Sparkles } from 'lucide-vue-next'

defineProps<{ name: string }>()
</script>

<template>
  <component :is="SITE_ICONS[name] || Sparkles" aria-hidden="true" />
</template>
