<script setup lang="ts">
import { Search, Trash2, ShieldCheck, Ban, CheckCircle2 } from 'lucide-vue-next'

useSeoMeta({ title: 'User management - LearnHub' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const api = useApi()
const auth = useAuth()
const { show } = useToast()

const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pages = ref(1)
const search = ref('')
const roleFilter = ref('')
const loading = ref(true)

let debounce: ReturnType<typeof setTimeout> | undefined

const load = async () => {
  loading.value = true
  try {
    const res = await api.get<any>('/users', {
      search: search.value || undefined,
      role: roleFilter.value || undefined,
      page: page.value, size: 15,
    })
    items.value = res.items
    total.value = res.total
    pages.value = res.pages
  } finally { loading.value = false }
}

watch([search, roleFilter], () => {
  page.value = 1
  clearTimeout(debounce)
  debounce = setTimeout(load, 300)
})
watch(page, load)
onMounted(load)

const setRole = async (u: any, role: string) => {
  try {
    await api.put(`/users/${u.id}?role=${role}`)
    u.role = role
    show(`${u.full_name} is now a ${role}`)
  } catch (e: any) { show(e?.data?.detail || 'Failed', 'error') }
}

const toggleActive = async (u: any) => {
  try {
    await api.put(`/users/${u.id}?is_active=${!u.is_active}`)
    u.is_active = !u.is_active
    show(u.is_active ? 'Account activated' : 'Account deactivated', 'info')
  } catch (e: any) { show(e?.data?.detail || 'Failed', 'error') }
}

const remove = async (u: any) => {
  if (!confirm(`Delete ${u.full_name}? All their courses/enrollments will be removed.`)) return
  try {
    await api.del(`/users/${u.id}`)
    show('User deleted', 'info')
    await load()
  } catch (e: any) { show(e?.data?.detail || 'Delete failed', 'error') }
}

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString()
</script>

<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">User management</h1>
        <p class="text-slate-500 mt-1">{{ total }} registered users</p>
      </div>
      <div class="flex gap-2">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input v-model="search" placeholder="Search name or email…" class="input pl-9 w-56" />
        </div>
        <select v-model="roleFilter" class="input w-auto">
          <option value="">All roles</option>
          <option value="admin">Admins</option>
          <option value="instructor">Instructors</option>
          <option value="student">Students</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="card h-72 animate-pulse" />

    <div v-else class="card overflow-hidden overflow-x-auto">
      <table class="table-base">
        <thead><tr><th>User</th><th>Role</th><th>Status</th><th>Joined</th><th class="text-right">Actions</th></tr></thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="u in items" :key="u.id" class="hover:bg-slate-50">
            <td>
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-brand-600 text-white text-sm font-bold flex items-center justify-center uppercase shrink-0">
                  <img v-if="u.avatar_url" :src="u.avatar_url" class="w-full h-full rounded-full object-cover" alt="" />
                  <template v-else>{{ u.full_name.slice(0, 1) }}</template>
                </div>
                <div>
                  <div class="font-semibold text-slate-800">{{ u.full_name }}
                    <span v-if="u.id === auth.user.value?.id" class="text-xs text-brand-600 font-medium">(you)</span>
                  </div>
                  <div class="text-xs text-slate-400">{{ u.email }}</div>
                </div>
              </div>
            </td>
            <td>
              <select v-if="u.id !== auth.user.value?.id" :value="u.role" @change="setRole(u, ($event.target as HTMLSelectElement).value)"
                class="text-xs font-semibold rounded-lg border border-slate-200 px-2 py-1.5 capitalize bg-white">
                <option value="admin">admin</option>
                <option value="instructor">instructor</option>
                <option value="student">student</option>
              </select>
              <span v-else class="badge bg-slate-100 text-slate-600 capitalize">{{ u.role }}</span>
            </td>
            <td>
              <span class="badge" :class="u.is_active ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-600'">
                {{ u.is_active ? '● active' : '● deactivated' }}
              </span>
            </td>
            <td class="text-sm text-slate-500">{{ fmtDate(u.created_at) }}</td>
            <td>
              <div class="flex justify-end gap-1" v-if="u.id !== auth.user.value?.id">
                <button @click="toggleActive(u)" class="p-2 rounded-lg hover:bg-slate-100 text-slate-500" :title="u.is_active ? 'Deactivate' : 'Activate'">
                  <component :is="u.is_active ? Ban : CheckCircle2" class="w-4 h-4" />
                </button>
                <button @click="remove(u)" class="p-2 rounded-lg hover:bg-rose-50 text-rose-400" title="Delete">
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="pages > 1" class="flex justify-center gap-1.5 py-4 border-t border-slate-100">
        <button v-for="p in pages" :key="p" @click="page = p"
          class="w-9 h-9 rounded-lg text-sm font-semibold"
          :class="p === page ? 'bg-brand-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'">
          {{ p }}
        </button>
      </div>
    </div>
  </div>
</template>
