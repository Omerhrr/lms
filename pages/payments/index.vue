<script setup lang="ts">
import { Receipt } from 'lucide-vue-next'

useSeoMeta({ title: 'Payments - Infohive' })
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const payments = ref<any[]>([])
const loading = ref(true)
onMounted(async () => {
  try { payments.value = await api.get<any[]>('/payments/my') } finally { loading.value = false }
})
const when = (iso: string) => new Date(iso.endsWith('Z') ? iso : iso + 'Z').toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
const badge: Record<string, string> = {
  success: 'bg-brand-50 text-brand-700', pending: 'bg-amber-50 text-amber-700',
  failed: 'bg-rose-50 text-rose-700', abandoned: 'bg-slate-100 text-slate-500',
}
</script>

<template>
  <div class="max-w-4xl">
    <h1 class="text-2xl font-extrabold text-slate-900">Payments</h1>
    <p class="text-slate-500 text-sm mt-0.5 mb-5">Your course purchases and receipts.</p>
    <div v-if="loading" class="card h-32 animate-pulse" />
    <div v-else-if="!payments.length" class="card p-10 text-center text-slate-500">
      <Receipt class="w-10 h-10 mx-auto mb-2 text-slate-300" />
      <p class="font-semibold text-slate-700">No payments yet</p>
      <p class="text-sm mt-1">Paid courses you buy will show up here.</p>
    </div>
    <div v-else class="card divide-y divide-slate-100">
      <div v-for="p in payments" :key="p.reference" class="p-4 flex flex-wrap sm:flex-nowrap items-center gap-x-4 gap-y-1">
        <div class="min-w-0 flex-1">
          <NuxtLink v-if="p.course_slug" :to="`/courses/${p.course_slug}`" class="font-semibold text-slate-800 hover:text-brand-700 truncate block">{{ p.course_title }}</NuxtLink>
          <p v-else class="font-semibold text-slate-800 truncate">{{ p.course_title }}</p>
          <p class="text-xs text-slate-400 truncate">{{ when(p.created_at) }} · <span class="font-mono">{{ p.reference }}</span></p>
        </div>
        <span class="font-bold text-slate-900">{{ p.amount_display }}</span>
        <span class="badge capitalize" :class="badge[p.status] || badge.abandoned">{{ p.status }}</span>
        <NuxtLink v-if="p.status !== 'success' && p.status !== 'failed'" :to="`/payments/callback?reference=${p.reference}`" class="text-xs font-semibold text-brand-700 hover:underline">Check status</NuxtLink>
      </div>
    </div>
  </div>
</template>
