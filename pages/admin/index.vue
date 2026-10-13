<script setup lang="ts">
const { config: _platform } = usePlatform()
const showRevenue = computed(() => _platform.value.payments_enabled || (stats.value?.revenue || 0) > 0)
const revenue = (n?: number | null) => new Intl.NumberFormat(undefined, { style: 'currency', currencyDisplay: 'narrowSymbol', currency: _platform.value.currency, maximumFractionDigits: 0 }).format(n || 0)
import { Users, BookOpen, GraduationCap, DollarSign, ShieldCheck, Briefcase, User as UserIcon } from 'lucide-vue-next'

useSeoMeta({ title: 'Admin - Infohive' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const api = useApi()
const stats = ref<any>(null)
const loading = ref(true)

const attention = ref<{ apps: number; enquiries: number; drafts: number }>({ apps: 0, enquiries: 0, drafts: 0 })
onMounted(async () => {
  try {
    const [st, apps, enq, courses] = await Promise.all([
      api.get<any>('/admin/stats'),
      api.get<any[]>('/admin/instructor-requests', undefined, true).catch(() => []),
      api.get<any[]>('/admin/enquiries', { status: 'new' }, true).catch(() => []),
      api.get<any>('/admin/courses', { status: 'draft', size: 1 }, true).catch(() => ({ total: 0 })),
    ])
    stats.value = st
    attention.value = { apps: apps.length, enquiries: enq.length, drafts: courses.total }
  } finally { loading.value = false }
})
const todo = computed(() => [
  { n: attention.value.apps, label: 'instructor application', plural: 'instructor applications', to: '/admin/applications' },
  { n: attention.value.enquiries, label: 'new enquiry', plural: 'new enquiries', to: '/admin/enquiries' },
  { n: attention.value.drafts, label: 'draft course', plural: 'draft courses', to: '/admin/courses?status=draft' },
].filter(t => t.n))

const roleIcon = (r: string) => (r === 'admin' ? ShieldCheck : r === 'instructor' ? Briefcase : UserIcon)
</script>

<template>
  <div>
    <div class="mb-8">
      <h1 class="text-2xl font-extrabold text-slate-900">Platform overview</h1>
      <p class="text-slate-600 mt-1">Everything happening across Infohive</p>
    </div>

    <div v-if="!loading && todo.length" class="card p-4 mb-6 flex flex-wrap items-center gap-x-6 gap-y-2">
      <span class="text-sm font-bold text-slate-900">Needs attention</span>
      <NuxtLink v-for="t in todo" :key="t.to" :to="t.to" class="text-sm font-semibold text-brand-700 hover:underline">
        {{ t.n }} {{ t.n === 1 ? t.label : t.plural }} →
      </NuxtLink>
    </div>

    <div v-if="loading" class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <div v-for="i in 4" :key="i" class="card h-24 animate-pulse" />
    </div>

    <template v-else-if="stats">
      <div class="grid sm:grid-cols-2 gap-4 mb-8" :class="showRevenue ? 'lg:grid-cols-4' : 'lg:grid-cols-3'">
        <div class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-brand-50 flex items-center justify-center"><Users class="w-5.5 h-5.5 text-brand-600" /></div>
          <div><div class="text-2xl font-extrabold">{{ stats.total_users }}</div><div class="text-xs text-slate-500">Total users</div></div>
        </div>
        <div class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-sky-50 flex items-center justify-center"><BookOpen class="w-5.5 h-5.5 text-sky-600" /></div>
          <div><div class="text-2xl font-extrabold">{{ stats.total_courses }}</div><div class="text-xs text-slate-500">Courses ({{ stats.published_courses }} live)</div></div>
        </div>
        <div class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-violet-50 flex items-center justify-center"><GraduationCap class="w-5.5 h-5.5 text-violet-600" /></div>
          <div><div class="text-2xl font-extrabold">{{ stats.total_enrollments }}</div><div class="text-xs text-slate-500">Enrollments</div></div>
        </div>
        <div v-if="showRevenue" class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-amber-50 flex items-center justify-center"><DollarSign class="w-5.5 h-5.5 text-amber-600" /></div>
          <div><div class="text-2xl font-extrabold">{{ revenue(stats.revenue) }}</div><div class="text-xs text-slate-500">Total revenue</div></div>
        </div>
      </div>

      <div class="grid lg:grid-cols-2 gap-6">
        <!-- users by role -->
        <div class="card p-5">
          <h2 class="font-bold text-slate-800 mb-4">Users by role</h2>
          <div class="space-y-3">
            <div v-for="(count, role) in stats.users_by_role" :key="role" class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                <component :is="roleIcon(String(role))" class="w-4.5 h-4.5 text-slate-500" />
              </div>
              <div class="flex-1">
                <div class="flex justify-between text-sm mb-1">
                  <span class="font-medium text-slate-600 capitalize">{{ role }}s</span>
                  <b class="text-slate-800">{{ count }}</b>
                </div>
                <div class="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                  <div class="h-full bg-brand-500 rounded-full" :style="`width:${(Number(count) / stats.total_users) * 100}%`" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- recent signups -->
        <div class="card p-5">
          <h2 class="font-bold text-slate-800 mb-4">Recent signups</h2>
          <div class="space-y-3">
            <div v-for="u in stats.recent_users" :key="u.id" class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-full bg-brand-600 text-white text-sm font-bold flex items-center justify-center uppercase shrink-0">
                {{ u.full_name.slice(0, 1) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="font-semibold text-sm text-slate-800 truncate">{{ u.full_name }}</div>
                <div class="text-xs text-slate-500 truncate">{{ u.email }}</div>
              </div>
              <span class="badge bg-slate-100 text-slate-500 capitalize shrink-0">{{ u.role }}</span>
            </div>
          </div>
          <NuxtLink to="/admin/users" class="btn-secondary w-full mt-5 text-sm">Manage users</NuxtLink>
        </div>
      </div>
    </template>
  </div>
</template>
