<script setup lang="ts">
import { Receipt } from 'lucide-vue-next'

useSeoMeta({ title: 'Payments - Admin - Infohive' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const api = useApi()
const { config } = usePlatform()
const rows = ref<any[]>([])
const loading = ref(true)
const status = ref('')
onMounted(async () => {
  try { rows.value = await api.get<any[]>('/admin/payments') } finally { loading.value = false }
})
const filtered = computed(() => rows.value.filter(r => !status.value || r.status === status.value))
const total = computed(() => rows.value.filter(r => r.status === 'success').reduce((s, r) => s + r.amount, 0))
const when = (iso: string) => new Date(iso.endsWith('Z') ? iso : iso + 'Z').toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
const fmt = (n: number) => new Intl.NumberFormat(undefined, { style: 'currency', currencyDisplay: 'narrowSymbol', currency: config.value.currency }).format(n)
const badge: Record<string, string> = {
  success: 'bg-brand-50 text-brand-700', pending: 'bg-amber-50 text-amber-700',
  failed: 'bg-rose-50 text-rose-700', abandoned: 'bg-slate-100 text-slate-500',
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Payments</h1>
        <p class="text-slate-500 text-sm mt-0.5">
          {{ config.payments_enabled ? 'Paystack checkout is on.' : 'Paystack checkout is off (set PAYSTACK_ENABLED=true on the API).' }}
          Collected: <b class="text-slate-800">{{ fmt(total) }}</b>
        </p>
      </div>
      <select v-model="status" class="input w-full sm:w-auto">
        <option value="">All statuses</option>
        <option value="success">Successful</option>
        <option value="pending">Pending</option>
        <option value="abandoned">Abandoned</option>
        <option value="failed">Failed</option>
      </select>
    </div>
    <div v-if="loading" class="card h-40 animate-pulse" />
    <div v-else-if="!filtered.length" class="card p-10 text-center text-slate-500">
      <Receipt class="w-10 h-10 mx-auto mb-2 text-slate-300" />No payments yet.
    </div>
    <div v-else class="card overflow-x-auto">
      <table class="table-base min-w-[640px]">
        <thead><tr><th>Student</th><th>Course</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="p in filtered" :key="p.reference">
            <td><div class="font-medium text-slate-800">{{ p.user?.full_name || 'Deleted user' }}</div><div class="text-xs text-slate-400">{{ p.user?.email }}</div></td>
            <td class="text-sm text-slate-700">{{ p.course_title }}<div class="text-[11px] text-slate-400 font-mono">{{ p.reference }}</div></td>
            <td class="font-semibold">{{ p.amount_display }}</td>
            <td><span class="badge capitalize" :class="badge[p.status] || badge.abandoned">{{ p.status }}</span></td>
            <td class="text-sm text-slate-500 whitespace-nowrap">{{ when(p.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
