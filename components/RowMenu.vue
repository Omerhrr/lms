<script setup lang="ts">
import { MoreHorizontal } from 'lucide-vue-next'

/** A "⋯" menu for row actions, so rare and destructive actions stay out of the way. */
export interface RowMenuItem { label: string; action: () => void; danger?: boolean; disabled?: boolean; icon?: any }
const props = defineProps<{ items: RowMenuItem[]; label?: string }>()
const open = ref(false)
const root = ref<HTMLElement | null>(null)
const btn = ref<HTMLButtonElement | null>(null)

const close = () => { open.value = false }
const onDoc = (e: MouseEvent) => { if (root.value && !root.value.contains(e.target as Node)) close() }
const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && open.value) { close(); btn.value?.focus() } }
onMounted(() => { document.addEventListener('click', onDoc); document.addEventListener('keydown', onKey) })
onBeforeUnmount(() => { document.removeEventListener('click', onDoc); document.removeEventListener('keydown', onKey) })

const run = (i: RowMenuItem) => { if (i.disabled) return; close(); i.action() }
const visible = computed(() => props.items.filter(Boolean))
</script>

<template>
  <div ref="root" class="relative">
    <button ref="btn" type="button" class="p-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition"
      :aria-label="label || 'More actions'" aria-haspopup="menu" :aria-expanded="open" @click.stop="open = !open">
      <MoreHorizontal class="w-4.5 h-4.5" />
    </button>
    <div v-if="open" role="menu" class="absolute right-0 top-full mt-1 z-30 min-w-[11rem] card py-1.5 shadow-lg">
      <template v-for="(i, n) in visible" :key="i.label">
        <div v-if="i.danger && n > 0" class="my-1 border-t border-slate-100" role="separator" />
        <button type="button" role="menuitem" :disabled="i.disabled"
          class="w-full flex items-center gap-2.5 px-3.5 py-2 text-sm text-left transition disabled:opacity-40 disabled:cursor-not-allowed"
          :class="i.danger ? 'text-rose-600 hover:bg-rose-50' : 'text-slate-700 hover:bg-slate-50'" @click="run(i)">
          <component :is="i.icon" v-if="i.icon" class="w-4 h-4" /> {{ i.label }}
        </button>
      </template>
    </div>
  </div>
</template>
