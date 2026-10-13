<script setup lang="ts">
import { X } from 'lucide-vue-next'

/** Accessible dialog: labelled, Escape closes, focus moves in and returns to where it was. */
const props = defineProps<{ open: boolean; title: string; wide?: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const panel = ref<HTMLElement | null>(null)
const titleId = `modal-${Math.random().toString(36).slice(2, 9)}`
let returnFocus: HTMLElement | null = null

const focusables = () => [...(panel.value?.querySelectorAll<HTMLElement>(
  'a[href], button:not([disabled]), input:not([disabled]):not([type=hidden]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
) || [])].filter(el => el.offsetParent !== null)

const onKey = (e: KeyboardEvent) => {
  if (!props.open) return
  if (e.key === 'Escape') { e.stopPropagation(); emit('close'); return }
  if (e.key === 'Tab') {                       // keep Tab inside the dialog
    const els = focusables()
    if (!els.length) return
    const first = els[0], last = els[els.length - 1]
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
  }
}

watch(() => props.open, async (open) => {
  if (!import.meta.client) return
  if (open) {
    returnFocus = document.activeElement as HTMLElement | null
    document.addEventListener('keydown', onKey)
    await nextTick()
    // first form field if there is one, otherwise the dialog itself
    const field = panel.value?.querySelector<HTMLElement>('input:not([type=hidden]):not([type=radio]):not([type=checkbox]), textarea, select')
    ;(field || panel.value)?.focus()
  } else {
    document.removeEventListener('keydown', onKey)
    returnFocus?.focus?.()
  }
}, { immediate: true })
onBeforeUnmount(() => { if (import.meta.client) document.removeEventListener('keydown', onKey) })
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" aria-hidden="true" @click="emit('close')" />
      <div ref="panel" role="dialog" aria-modal="true" :aria-labelledby="titleId" tabindex="-1"
        class="relative bg-white rounded-2xl shadow-2xl w-full max-h-[90vh] flex flex-col focus:outline-none"
        :class="wide ? 'max-w-3xl' : 'max-w-lg'">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 :id="titleId" class="font-bold text-slate-900">{{ title }}</h2>
          <button @click="emit('close')" class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500" aria-label="Close">
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
