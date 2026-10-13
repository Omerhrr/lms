<script setup lang="ts">
import { Search, Trash2, ShieldCheck, Ban, CheckCircle2, UserCog, ArrowUpDown } from 'lucide-vue-next'

useSeoMeta({ title: 'User management - Infohive' })
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
const sort = ref<'newest' | 'oldest' | 'name' | 'name_desc'>('newest')
const loading = ref(true)

let debounce: ReturnType<typeof setTimeout> | undefined

const load = async () => {
  loading.value = true
  try {
    const res = await api.get<any>('/users', {
      search: search.value || undefined,
      role: roleFilter.value && roleFilter.value !== 'requested' ? roleFilter.value : undefined,
      instructor_requested: roleFilter.value === 'requested' ? true : undefined,
      sort: sort.value,
      page: page.value, size: 15,
    })
    items.value = res.items
    total.value = res.total
    pages.value = res.pages
  } finally { loading.value = false }
}

watch([search, roleFilter, sort], () => {
  page.value = 1
  clearTimeout(debounce)
  debounce = setTimeout(load, 300)
})
watch(page, load)
onMounted(load)

// role changes go through a confirm step, never straight from a dropdown
const roleDialog = ref<{ open: boolean; user?: any; role: string }>({ open: false, role: 'student' })
const roleCopy: Record<string, string> = {
  student: 'Can enroll in and take courses.',
  instructor: 'Can create and manage their own courses, grade learners and run live classes.',
  admin: 'Full access: every user, course, payment and setting.',
}
const openRole = (u: any) => { roleDialog.value = { open: true, user: u, role: u.role } }
const confirmRole = async () => {
  const { user, role } = roleDialog.value
  if (user && role !== user.role) await setRole(user, role)
  roleDialog.value = { open: false, role: 'student' }
}
const sortBy = (col: 'name' | 'joined') => {
  sort.value = col === 'name' ? (sort.value === 'name' ? 'name_desc' : 'name') : (sort.value === 'newest' ? 'oldest' : 'newest')
}
const ariaSort = (col: 'name' | 'joined') => col === 'name'
  ? (sort.value === 'name' ? 'ascending' : sort.value === 'name_desc' ? 'descending' : 'none')
  : (sort.value === 'newest' ? 'descending' : sort.value === 'oldest' ? 'ascending' : 'none')

const setRole = async (u: any, role: string) => {
  try {
    await api.put(`/users/${u.id}?role=${role}`)
    u.role = role
    u.instructor_requested = false
    show(`${u.full_name} is now a ${role}`)
  } catch { /* the api client already showed the error */ }
}

const declineRequest = async (u: any) => {
  try {
    await api.put(`/users/${u.id}?role=student`)
    u.instructor_requested = false
    show('Instructor request declined', 'info')
  } catch { /* the api client already showed the error */ }
}

const toggleActive = async (u: any) => {
  try {
    await api.put(`/users/${u.id}?is_active=${!u.is_active}`)
    u.is_active = !u.is_active
    show(u.is_active ? 'Account activated' : 'Account deactivated', 'info')
  } catch { /* the api client already showed the error */ }
}

const remove = async (u: any) => {
  if (!confirm(`Delete ${u.full_name}? Their enrollments, submissions and posts will be removed. (Instructors who still own courses can't be deleted - deactivate them instead.)`)) return
  try {
    await api.del(`/users/${u.id}`)
    show('User deleted', 'info')
    await load()
  } catch { /* the api client already showed the error */ }
}

const fmtDate = (iso: string) => new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
const relDate = (iso: string) => {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000)
  if (days <= 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 30) return `${days} days ago`
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">User management</h1>
        <p class="text-slate-500 mt-1">{{ total }} registered users</p>
      </div>
      <div class="flex flex-wrap gap-2 w-full sm:w-auto">
        <div class="relative flex-1 sm:flex-none">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input v-model="search" aria-label="Search users" placeholder="Search name or email…" class="input pl-9 w-full sm:w-56" />
        </div>
        <select v-model="roleFilter" aria-label="Filter by role" class="input w-full sm:w-auto">
          <option value="">All roles</option>
          <option value="requested">Instructor requests</option>
          <option value="admin">Admins</option>
          <option value="instructor">Instructors</option>
          <option value="student">Students</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="card h-72 animate-pulse" />

    <div v-else class="card overflow-hidden overflow-x-auto">
      <table class="table-base">
        <thead><tr>
          <th :aria-sort="ariaSort('name')"><button type="button" class="inline-flex items-center gap-1 uppercase hover:text-slate-900" @click="sortBy('name')">User <ArrowUpDown class="w-3.5 h-3.5" /></button></th>
          <th>Role</th><th>Status</th>
          <th :aria-sort="ariaSort('joined')"><button type="button" class="inline-flex items-center gap-1 uppercase hover:text-slate-900" @click="sortBy('joined')">Joined <ArrowUpDown class="w-3.5 h-3.5" /></button></th>
          <th class="text-right"><span class="sr-only">Actions</span></th>
        </tr></thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="u in items" :key="u.id" class="hover:bg-slate-50">
            <td>
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-brand-600 text-white text-sm font-bold flex items-center justify-center uppercase shrink-0">
                  <img v-if="safeUrl(u.avatar_url)" :src="safeUrl(u.avatar_url)" class="w-full h-full rounded-full object-cover" alt="" />
                  <template v-else>{{ u.full_name.slice(0, 1) }}</template>
                </div>
                <div>
                  <div class="font-semibold text-slate-800">{{ u.full_name }}
                    <span v-if="u.id === auth.user.value?.id" class="text-xs text-brand-600 font-medium">(you)</span>
                  </div>
                  <div class="text-xs text-slate-500">{{ u.email }}</div>
                </div>
              </div>
            </td>
            <td>
              <span class="badge capitalize" :class="u.role === 'admin' ? 'bg-violet-50 text-violet-700' : u.role === 'instructor' ? 'bg-sky-50 text-sky-700' : 'bg-slate-100 text-slate-700'">{{ u.role }}</span>
              <div v-if="u.instructor_requested" class="mt-1.5 flex items-center gap-1">
                <span class="badge bg-amber-100 text-amber-800">wants to teach</span>
                <button class="text-xs font-semibold text-brand-700 hover:underline" @click="setRole(u, 'instructor')">Approve</button>
                <button class="text-xs text-slate-500 hover:underline" @click="declineRequest(u)">Decline</button>
              </div>
            </td>
            <td>
              <span class="badge" :class="u.is_active ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-600'">
                {{ u.is_active ? '● active' : '● deactivated' }}
              </span>
            </td>
            <td class="text-sm text-slate-600 whitespace-nowrap"><time :datetime="u.created_at" :title="fmtDate(u.created_at)">{{ relDate(u.created_at) }}</time></td>
            <td>
              <div class="flex justify-end" v-if="u.id !== auth.user.value?.id">
                <RowMenu :label="`Actions for ${u.full_name}`" :items="[
                  { label: 'Change role…', icon: UserCog, action: () => openRole(u) },
                  { label: u.is_active ? 'Deactivate account' : 'Activate account', icon: u.is_active ? Ban : CheckCircle2, action: () => toggleActive(u) },
                  { label: 'Delete user…', icon: Trash2, danger: true, action: () => remove(u) },
                ]" />
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="pages > 1" class="flex justify-center gap-1.5 py-4 border-t border-slate-100">
        <button v-for="p in pages" :key="p" @click="page = p"
          class="w-9 h-9 rounded-lg text-sm font-semibold"
          :aria-label="`Page ${p}`" :aria-current="p === page ? 'page' : undefined"
          :class="p === page ? 'bg-brand-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'">
          {{ p }}
        </button>
      </div>
    </div>

    <Modal :open="roleDialog.open" :title="`Change role: ${roleDialog.user?.full_name || ''}`" @close="roleDialog = { open: false, role: 'student' }">
      <fieldset class="space-y-2">
        <legend class="sr-only">Role</legend>
        <label v-for="r in ['student', 'instructor', 'admin']" :key="r"
          class="flex gap-3 rounded-xl border p-3.5 cursor-pointer transition"
          :class="roleDialog.role === r ? 'border-brand-500 bg-brand-50' : 'border-slate-200 hover:border-slate-300'">
          <input v-model="roleDialog.role" type="radio" name="role" :value="r" class="mt-1 text-brand-600" />
          <span>
            <span class="block font-semibold text-slate-900 capitalize">{{ r }}<span v-if="roleDialog.user?.role === r" class="text-xs font-normal text-slate-500"> · current</span></span>
            <span class="block text-sm text-slate-600">{{ roleCopy[r] }}</span>
          </span>
        </label>
      </fieldset>
      <p v-if="roleDialog.role === 'admin' && roleDialog.user?.role !== 'admin'" class="mt-3 text-sm text-amber-700 bg-amber-50 rounded-lg p-3">
        Admins can see and change everything, including other admins. Only grant this to people you fully trust.
      </p>
      <template #footer>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn-secondary" @click="roleDialog = { open: false, role: 'student' }">Cancel</button>
          <button class="btn-primary" :disabled="roleDialog.role === roleDialog.user?.role" @click="confirmRole">
            Make {{ roleDialog.role }}
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
