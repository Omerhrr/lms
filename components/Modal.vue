<script setup lang="ts">
import { X } from 'lucide-vue-next'

defineProps<{ open: boolean; title: string; wide?: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" @click="emit('close')" />
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-h-[90vh] flex flex-col"
        :class="wide ? 'max-w-3xl' : 'max-w-lg'">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="font-bold text-slate-900">{{ title }}</h3>
          <button @click="emit('close')" class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400" aria-label="Close">
            <X class="w-5 h-5" />
          </button>
        </div>
        <div class="p-6 overflow-y-auto nice-scroll">
          <slot />
        </div>
        <div v-if="$slots.footer" class="px-6 py-4 border-t border-slate-100">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>
