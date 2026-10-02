<script setup lang="ts">
import {
  GraduationCap, LayoutDashboard, BookOpen, Bell, LogOut, Settings,
  ChevronDown, Menu, X, Shield, Briefcase, Compass
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

const isActive = (to: string) => route.path === to || route.path.startsWith(to + '/')

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

// Instructors and admins manage courses from their studio, so "Teach" is only
// shown to visitors and students (same rule as before the redesign).
const publicLinks = computed(() => {
  const u = auth.user.value
  const links = [{ label: 'Courses', to: '/courses' }]
  if (!u || u.role === 'student') links.push({ label: 'Teach', to: '/teach' })
  links.push({ label: 'Verify', to: '/verify' })
  return links
})

const doLogout = () => {
  auth.logout()
  show('Signed out. See you soon!', 'info')
  router.push('/')
}

// close the avatar dropdown when clicking anywhere outside it
const menuRoot = ref<HTMLElement | null>(null)
const onDocClick = (e: MouseEvent) => {
  if (menuOpen.value && menuRoot.value && !menuRoot.value.contains(e.target as Node)) menuOpen.value = false
}
onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <header class="sticky top-0 z-40 bg-white/95 dark:bg-slate-900/90 backdrop-blur border-b border-slate-200 dark:border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
      <NuxtLink to="/" class="flex items-center gap-2.5 shrink-0 group">
        <img src="/logo.svg" alt="LearnHub logo" class="w-9 h-9 rounded-xl transition-transform group-hover:scale-105" />
        <span class="text-xl font-extrabold tracking-tight text-slate-900 dark:text-white">Learn<span class="text-brand-600 dark:text-brand-400">Hub</span></span>
      </NuxtLink>

      <nav class="hidden md:flex items-center gap-1 text-sm font-medium">
        <NuxtLink v-for="link in publicLinks" :key="link.to" :to="link.to"
          class="px-3 py-2 rounded-lg transition"
          :class="isActive(link.to)
            ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300'
            : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'">
          {{ link.label }}
        </NuxtLink>
      </nav>

      <div class="flex items-center gap-1.5">
        <ThemeToggle />

        <template v-if="auth.isLoggedIn.value && auth.user.value">
          <NuxtLink to="/notifications" class="relative p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition" aria-label="Notifications">
            <Bell class="w-5 h-5" />
            <span v-if="unread > 0" class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center">
              {{ unread > 99 ? '99+' : unread }}
            </span>
          </NuxtLink>

          <div class="relative" ref="menuRoot">
            <button @click="menuOpen = !menuOpen" class="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition" aria-label="Account menu">
              <div class="w-8 h-8 rounded-full bg-brand-600 text-white text-sm font-bold flex items-center justify-center uppercase">
                {{ auth.user.value.full_name?.slice(0, 1) || '?' }}
              </div>
              <ChevronDown class="w-4 h-4 text-slate-400 transition-transform" :class="menuOpen ? 'rotate-180' : ''" />
            </button>
            <Transition name="toast">
              <div v-if="menuOpen" class="absolute right-0 mt-2 w-60 bg-white dark:bg-slate-900 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 py-2 z-50">
                <div class="px-4 py-2 border-b border-slate-100 dark:border-slate-800">
                  <div class="font-semibold text-sm text-slate-800 dark:text-slate-100">{{ auth.user.value.full_name }}</div>
                  <div class="text-xs text-slate-500 dark:text-slate-400 truncate">{{ auth.user.value.email }}</div>
                  <span class="badge bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300 mt-1.5 capitalize">{{ auth.user.value.role }}</span>
                </div>
                <NuxtLink v-for="item in menuItems" :key="item.to" :to="item.to"
                  class="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white transition">
                  <component :is="item.icon" class="w-4 h-4" />
                  {{ item.label }}
                </NuxtLink>
                <button @click="doLogout" class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition border-t border-slate-100 dark:border-slate-800 mt-1">
                  <LogOut class="w-4 h-4" /> Sign out
                </button>
              </div>
            </Transition>
          </div>
        </template>

        <template v-else>
          <NuxtLink to="/login" class="btn-ghost hidden sm:inline-flex">Sign in</NuxtLink>
          <NuxtLink to="/register" class="btn-primary hidden sm:inline-flex">Get started</NuxtLink>
        </template>

        <button class="md:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300" @click="mobileOpen = !mobileOpen" aria-label="Menu">
          <component :is="mobileOpen ? X : Menu" class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- mobile panel -->
    <Transition name="toast">
      <div v-if="mobileOpen" class="md:hidden border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-3 space-y-1">
        <template v-if="auth.isLoggedIn.value && auth.user.value">
          <div class="flex items-center gap-3 px-3 py-2 mb-1 rounded-lg bg-slate-50 dark:bg-slate-800/60">
            <div class="w-9 h-9 rounded-full bg-brand-600 text-white text-sm font-bold flex items-center justify-center uppercase">
              {{ auth.user.value.full_name?.slice(0, 1) || '?' }}
            </div>
            <div class="min-w-0">
              <div class="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">{{ auth.user.value.full_name }}</div>
              <div class="text-xs text-slate-500 dark:text-slate-400 capitalize">{{ auth.user.value.role }}</div>
            </div>
          </div>
          <NuxtLink v-for="item in menuItems" :key="item.to" :to="item.to"
            class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition"
            :class="isActive(item.to) ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300' : 'text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800'">
            <component :is="item.icon" class="w-4.5 h-4.5" />
            {{ item.label }}
          </NuxtLink>
          <button @click="doLogout" class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40">
            <LogOut class="w-4.5 h-4.5" /> Sign out
          </button>
        </template>

        <template v-else>
          <NuxtLink v-for="link in publicLinks" :key="link.to" :to="link.to"
            class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800">
            <Compass class="w-4.5 h-4.5 text-slate-400" />
            {{ link.label }}
          </NuxtLink>
          <div class="flex gap-2 pt-2">
            <NuxtLink to="/login" class="btn-secondary flex-1">Sign in</NuxtLink>
            <NuxtLink to="/register" class="btn-primary flex-1">Get started</NuxtLink>
          </div>
        </template>
      </div>
    </Transition>
  </header>
</template>
