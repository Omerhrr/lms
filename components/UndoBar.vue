<script setup lang="ts">
/** Bottom bar offering "Undo" for a few seconds after a delete; the delete only happens when it closes. */
defineProps<{ message: string | null }>()
defineEmits<{ undo: [] }>()
</script>

<template>
  <Transition enter-from-class="translate-y-4 opacity-0" leave-to-class="translate-y-4 opacity-0" enter-active-class="transition" leave-active-class="transition">
    <div v-if="message" role="status" class="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 rounded-xl bg-slate-900 text-white pl-4 pr-2 py-2 shadow-xl max-w-[calc(100vw-2rem)]">
      <span class="text-sm truncate">{{ message }}</span>
      <button type="button" class="btn-light btn !py-1.5 !px-3 text-sm font-bold shrink-0" @click="$emit('undo')">Undo</button>
    </div>
  </Transition>
</template>
