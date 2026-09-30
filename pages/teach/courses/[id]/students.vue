<script setup lang="ts">
import { Users, Trophy, TrendingUp } from 'lucide-vue-next'

useSeoMeta({ title: 'Students - LearnHub' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const route = useRoute()
const api = useApi()
const courseId = Number(route.params.id)

const students = ref<any[]>([])
const loading = ref(true)
const search = ref('')

onMounted(async () => {
  try { students.value = await api.get<any[]>(`/enrollments/course/${courseId}/students`) } finally { loading.value = false }
})

const filtered = computed(() => students.value.filter(s =>
  s.user.full_name.toLowerCase().includes(search.value.toLowerCase()) ||
  s.user.email.toLowerCase().includes(search.value.toLowerCase())))

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
</script>

<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Enrolled students</h1>
        <p class="text-slate-500 mt-1">{{ students.length }} student{{ students.length === 1 ? '' : 's' }} enrolled</p>
      </div>
      <input v-model="search" placeholder="Search students…" class="input w-56" />
    </div>

    <div v-if="loading" class="card h-64 animate-pulse" />

    <EmptyState v-else-if="students.length === 0" empty>No one has enrolled yet. Publish and promote your course!</EmptyState>

    <div v-else class="card overflow-hidden overflow-x-auto">
      <table class="table-base">
        <thead><tr><th>Student</th><th>Progress</th><th>Status</th><th>Enrolled</th></tr></thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="s in filtered" :key="s.user.id" class="hover:bg-slate-50">
            <td>
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-brand-600 text-white text-sm font-bold flex items-center justify-center uppercase shrink-0">
                  {{ s.user.full_name.slice(0, 1) }}
                </div>
                <div>
                  <div class="font-semibold text-slate-800">{{ s.user.full_name }}</div>
                  <div class="text-xs text-slate-400">{{ s.user.email }}</div>
                </div>
              </div>
            </td>
            <td class="w-48">
              <div class="flex items-center gap-2">
                <div class="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div class="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-400" :style="`width:${s.progress}%`" />
                </div>
                <span class="text-xs font-bold text-slate-600 w-10">{{ Math.round(s.progress) }}%</span>
              </div>
            </td>
            <td>
              <span class="badge" :class="s.status === 'completed' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'">
                {{ s.status === 'completed' ? '🏆 completed' : 'in progress' }}
              </span>
            </td>
            <td class="text-sm text-slate-500">{{ fmtDate(s.enrolled_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
