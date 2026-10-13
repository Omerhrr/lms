<script setup lang="ts">
import { Award, ExternalLink, Download } from 'lucide-vue-next'

useSeoMeta({ title: 'My Certificates - Infohive' })
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const certs = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try { certs.value = await api.get<any[]>('/certificates/my') } finally { loading.value = false }
})
</script>

<template>
  <div class="max-w-3xl">
    <h1 class="text-2xl font-extrabold text-slate-900 mb-6">My certificates</h1>

    <div v-if="loading" class="card h-32 animate-pulse" />
    <EmptyState v-else-if="certs.length === 0" empty>
      Complete a course to earn your first certificate. <NuxtLink to="/dashboard" class="text-brand-700 font-semibold">Keep learning →</NuxtLink>
    </EmptyState>

    <div v-else class="space-y-4">
      <div v-for="c in certs" :key="c.serial" class="card p-4 sm:p-5 flex flex-wrap sm:flex-nowrap items-center gap-4 sm:gap-5 border-amber-200 bg-gradient-to-r from-amber-50 to-white">
        <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shrink-0">
          <Award class="w-7 h-7 text-white" />
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-bold text-slate-900 truncate">{{ c.course_title }}</h3>
          <p class="text-xs text-slate-500 mt-0.5">
            Issued {{ new Date(c.issued_at).toLocaleDateString() }} · Serial <span class="font-mono">{{ c.serial }}</span>
          </p>
          <p v-if="c.revoked" class="text-xs font-semibold text-rose-700 mt-1">Revoked{{ c.revoke_reason ? `: ${c.revoke_reason}` : '' }}</p>
        </div>
        <div class="flex gap-2 shrink-0 w-full sm:w-auto">
          <a v-if="!c.revoked" :href="`/api/certificates/${c.serial}/pdf`" download class="btn-primary text-sm flex-1 sm:flex-none" aria-label="Download PDF">
            <Download class="w-3.5 h-3.5" /> PDF
          </a>
          <NuxtLink :to="`/certificates/${c.serial}`" class="btn-secondary text-sm flex-1 sm:flex-none">
            View <ExternalLink class="w-3.5 h-3.5" />
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>
