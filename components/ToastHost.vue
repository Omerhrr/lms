<template>
  <div class="fixed bottom-5 right-5 z-[100] space-y-2 w-80">
    <TransitionGroup name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="rounded-lg px-4 py-3 text-sm font-medium shadow-lg flex items-center gap-2 text-white"
        :class="t.type === 'success' ? 'bg-emerald-600' : t.type === 'error' ? 'bg-rose-600' : 'bg-slate-800'"
      >
        <span class="flex-1">{{ t.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
const { toasts } = useToast()
</script>
