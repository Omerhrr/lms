<script setup lang="ts">
import { Users, BookOpen, GraduationCap, DollarSign, ShieldCheck, Briefcase, User as UserIcon } from 'lucide-vue-next'

useSeoMeta({ title: 'Admin — LearnHub' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const api = useApi()
const stats = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  try { stats.value = await api.get<any>('/admin/stats') } finally { loading.value = false }
})

const roleIcon = (r: string) => (r === 'admin' ? ShieldCheck : r === 'instructor' ? Briefcase : UserIcon)
</script>

<template>
  <div>
    <div class="mb-8">
      <h1 class="text-2xl font-extrabold text-slate-900">Platform overview</h1>
      <p class="text-slate-500 mt-1">Everything happening across LearnHub</p>
    </div>

    <div v-if="loading" class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <div v-for="i in 4" :key="i" class="card h-24 animate-pulse" />
    </div>

    <template v-else-if="stats">
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-brand-50 flex items-center justify-center"><Users class="w-5.5 h-5.5 text-brand-600" /></div>
          <div><div class="text-2xl font-extrabold">{{ stats.total_users }}</div><div class="text-xs text-slate-400">Total users</div></div>
        </div>
        <div class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-sky-50 flex items-center justify-center"><BookOpen class="w-5.5 h-5.5 text-sky-600" /></div>
          <div><div class="text-2xl font-extrabold">{{ stats.total_courses }}</div><div class="text-xs text-slate-400">Courses ({{ stats.published_courses }} live)</div></div>
        </div>
        <div class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-violet-50 flex items-center justify-center"><GraduationCap class="w-5.5 h-5.5 text-violet-600" /></div>
          <div><div class="text-2xl font-extrabold">{{ stats.total_enrollments }}</div><div class="text-xs text-slate-400">Enrollments</div></div>
        </div>
        <div class="card p-5 flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-amber-50 flex items-center justify-center"><DollarSign class="w-5.5 h-5.5 text-amber-600" /></div>
          <div><div class="text-2xl font-extrabold">${{ stats.revenue?.toLocaleString() }}</div><div class="text-xs text-slate-400">Total revenue</div></div>
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
                <div class="text-xs text-slate-400 truncate">{{ u.email }}</div>
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
