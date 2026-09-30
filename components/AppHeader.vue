<script setup lang="ts">
import {
  GraduationCap, LayoutDashboard, BookOpen, Bell, LogOut, Settings,
  ChevronDown, Menu, X, Shield, Briefcase
} from 'lucide-vue-next'

const auth = useAuth()
const api = useApi()
const route = useRoute()
const router = useRouter()
const { show } = useToast()

const mobileOpen = ref(false)
const menuOpen = ref(false)
const unread = ref(0)

const loadUnread = async () => {
  if (!auth.isLoggedIn.value) { unread.value = 0; return }
  try {
    const r = await api.get<{ count: number }>('/notifications/unread-count', undefined, true)
    unread.value = r.count
  } catch { /* ignore */ }
}

watch(() => auth.user.value?.id, () => loadUnread(), { immediate: true })
watch(() => route.fullPath, () => { mobileOpen.value = false; menuOpen.value = false; if (auth.isLoggedIn.value) loadUnread() })

const menuItems = computed(() => {
  const u = auth.user.value
  if (!u) return []
  const items = []
  if (u.role === 'student') {
    items.push({ label: 'My Learning', to: '/dashboard', icon: LayoutDashboard })
    items.push({ label: 'Browse Courses', to: '/courses', icon: BookOpen })
  } else {
    items.push({ label: u.role === 'admin' ? 'Admin Panel' : 'Instructor Studio', to: u.role === 'admin' ? '/admin' : '/teach', icon: u.role === 'admin' ? Shield : Briefcase })
    if (u.role === 'admin') items.push({ label: 'Browse Courses', to: '/courses', icon: BookOpen })
  }
  items.push({ label: 'My Certificates', to: '/certificates', icon: GraduationCap })
  items.push({ label: 'Profile', to: '/profile', icon: Settings })
  return items
})

const doLogout = () => {
  auth.logout()
  show('Signed out. See you soon!', 'info')
  router.push('/')
}
</script>

<template>
  <header class="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
      <NuxtLink to="/" class="flex items-center gap-2.5 shrink-0">
        <img src="/logo.svg" alt="LearnHub" class="w-9 h-9" />
        <span class="text-xl font-extrabold tracking-tight text-slate-900">Learn<span class="text-brand-600">Hub</span></span>
      </NuxtLink>

      <nav class="hidden md:flex items-center gap-1 text-sm font-medium">
        <NuxtLink to="/courses" class="px-3 py-2 rounded-lg hover:bg-slate-100 text-slate-600 hover:text-slate-900 transition">Courses</NuxtLink>
        <NuxtLink v-if="!auth.isLoggedIn.value || auth.isStudent.value" to="/teach" class="px-3 py-2 rounded-lg hover:bg-slate-100 text-slate-600 hover:text-slate-900 transition">Teach</NuxtLink>
      </nav>

      <div class="flex items-center gap-2">
        <template v-if="auth.isLoggedIn.value && auth.user.value">
          <NuxtLink to="/notifications" class="relative p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition" aria-label="Notifications">
            <Bell class="w-5 h-5" />
            <span v-if="unread > 0" class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center">
              {{ unread > 99 ? '99+' : unread }}
            </span>
          </NuxtLink>

          <div class="relative">
            <button @click="menuOpen = !menuOpen" class="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 hover:bg-slate-100 transition">
              <div class="w-8 h-8 rounded-full bg-brand-600 text-white text-sm font-bold flex items-center justify-center uppercase">
                {{ auth.user.value.full_name.slice(0, 1) }}
              </div>
              <ChevronDown class="w-4 h-4 text-slate-400" />
            </button>
            <div v-if="menuOpen" class="absolute right-0 mt-2 w-60 bg-white rounded-xl shadow-lg border border-slate-200 py-2 z-50">
              <div class="px-4 py-2 border-b border-slate-100">
                <div class="font-semibold text-sm text-slate-800">{{ auth.user.value.full_name }}</div>
                <div class="text-xs text-slate-500 truncate">{{ auth.user.value.email }}</div>
                <span class="badge bg-brand-50 text-brand-700 mt-1.5">{{ auth.user.value.role }}</span>
              </div>
              <NuxtLink v-for="item in menuItems" :key="item.to" :to="item.to"
                class="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-600 hover:bg-slate-50 transition">
                <component :is="item.icon" class="w-4 h-4" />
                {{ item.label }}
              </NuxtLink>
              <button @click="doLogout" class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-rose-600 hover:bg-rose-50 transition">
                <LogOut class="w-4 h-4" /> Sign out
              </button>
            </div>
          </div>
        </template>

        <template v-else>
          <NuxtLink to="/login" class="btn-ghost">Sign in</NuxtLink>
          <NuxtLink to="/register" class="btn-primary hidden sm:inline-flex">Get started</NuxtLink>
        </template>

        <button class="md:hidden p-2 rounded-lg hover:bg-slate-100" @click="mobileOpen = !mobileOpen" aria-label="Menu">
          <component :is="mobileOpen ? X : Menu" class="w-5 h-5 text-slate-600" />
        </button>
      </div>
    </div>

    <div v-if="mobileOpen" class="md:hidden border-t border-slate-200 bg-white px-4 py-3 space-y-1">
      <NuxtLink to="/courses" class="block px-3 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50">Courses</NuxtLink>
      <NuxtLink v-if="!auth.isLoggedIn.value" to="/register" class="block px-3 py-2.5 rounded-lg text-sm font-medium text-brand-700 hover:bg-brand-50">Get started</NuxtLink>
    </div>
  </header>
</template>
