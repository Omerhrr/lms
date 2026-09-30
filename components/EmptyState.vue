<script setup lang="ts">
defineProps<{ empty?: boolean }>()
</script>

<template>
  <div v-if="empty" class="flex flex-col items-center justify-center py-16 text-center">
    <div class="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center text-slate-300 mb-4">
      <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
    </div>
    <h3 class="font-semibold text-slate-700">Nothing here yet</h3>
    <p class="text-sm text-slate-400 mt-1"><slot /></p>
  </div>
</template>
