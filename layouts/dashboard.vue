<script setup lang="ts">
import {
  LayoutDashboard, BookOpen, GraduationCap, Bell, Settings, Shield,
  Menu, X, LogOut, FolderTree, Users, ClipboardList, Megaphone,
  BarChart3, Home, CalendarDays, NotebookPen, Receipt, Inbox, Video, UserCheck, PanelsTopLeft
} from 'lucide-vue-next'

const auth = useAuth()
const route = useRoute()
const router = useRouter()
const { show } = useToast()

const { config: platform } = usePlatform()
const sidebarOpen = ref(false)
// pending instructor applications, shown as a count in the admin menu
const pendingApps = useState<number>('admin:pendingApps', () => 0)
const refreshApps = async () => {
  if (auth.user.value?.role !== 'admin') return
  try { pendingApps.value = (await useApi().get<any[]>('/admin/instructor-requests', undefined, true)).length } catch { /* ignore */ }
}
onMounted(refreshApps)
watch(() => route.fullPath, () => { sidebarOpen.value = false })

const navMain = computed(() => {
  const u = auth.user.value
  if (!u) return []
  if (u.role === 'admin') {
    return [
      { label: 'Overview', to: '/admin', icon: Shield },
      { heading: 'Learning' },
      { label: 'Courses', to: '/admin/courses', icon: BookOpen },
      { label: 'Enrollments', to: '/admin/enrollments', icon: ClipboardList },
      { label: 'Applications', to: '/admin/applications', icon: UserCheck, badge: pendingApps.value },
      { label: 'Reports', to: '/admin/reports', icon: BarChart3 },
      { label: 'Certificates', to: '/admin/certificates', icon: GraduationCap },
      { label: 'Categories', to: '/admin/categories', icon: FolderTree },
      { heading: 'Site & people' },
      { label: 'Website', to: '/admin/website', icon: PanelsTopLeft },
      { label: 'Users', to: '/admin/users', icon: Users },
      { label: 'Enquiries', to: '/admin/enquiries', icon: Inbox },
      ...(platform.value.payments_enabled ? [{ label: 'Payments', to: '/admin/payments', icon: Receipt }] : []),
    ]
  }
  if (u.role === 'instructor') {
    return [
      { label: 'Dashboard', to: '/teach', icon: BarChart3 },
      { label: 'My Courses', to: '/teach/courses', icon: BookOpen },
      { label: 'Browse Courses', to: '/courses', icon: BookOpen },
    ]
  }
  return [
    { label: 'My Learning', to: '/dashboard', icon: LayoutDashboard },
    { label: 'Browse Courses', to: '/courses', icon: BookOpen },
    ...(platform.value.payments_enabled ? [{ label: 'Payments', to: '/payments', icon: Receipt }] : []),
  ]
})

// admins don't take courses, so learner-only tools stay out of their menu
const navShared = computed(() => {
  const admin = auth.user.value?.role === 'admin'
  return [
    ...(admin ? [] : [{ label: 'Calendar', to: '/calendar', icon: CalendarDays }]),
    ...(admin ? [] : [{ label: 'Notes & Bookmarks', to: '/notes', icon: NotebookPen }]),
    ...(admin ? [] : [{ label: 'Certificates', to: '/certificates', icon: GraduationCap }]),
    { label: 'Notifications', to: '/notifications', icon: Bell },
    { label: 'Profile', to: '/profile', icon: Settings },
  ]
})

// a menu item is active on its own page and its sub-pages, unless another item owns that sub-path
const isActive = (to: string) => {
  const p = route.path
  if (p === to) return true
  if (!p.startsWith(to + '/')) return false
  return !navMain.value.some((i: any) => i.to && i.to !== to && i.to.startsWith(to + '/') && p.startsWith(i.to))
    && !(to === '/admin' || to === '/teach' || to === '/dashboard')
}

const teachTabs = computed(() => {
  const m = route.path.match(/^\/teach\/courses\/(\d+)(\/.*)?/)
  if (!m) return null
  const id = m[1]
  return [
    { label: 'Course Settings', to: `/teach/courses/${id}/edit`, icon: Settings, exact: false },
    { label: 'Curriculum Builder', to: `/teach/courses/${id}/builder`, icon: FolderTree },
    { label: 'Live Classes', to: `/teach/courses/${id}/live`, icon: Video },
    { label: 'Students', to: `/teach/courses/${id}/students`, icon: Users },
    { label: 'Gradebook', to: `/teach/courses/${id}/gradebook`, icon: ClipboardList },
    { label: 'Announcements', to: `/teach/courses/${id}/announcements`, icon: Megaphone },
    { label: 'Analytics', to: `/teach/courses/${id}/analytics`, icon: BarChart3 },
  ]
})

const doLogout = () => {
  auth.logout()
  show('Signed out. See you soon!', 'info')
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950">
    <!-- top bar -->
    <header class="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 h-14 flex items-center justify-between px-4 sm:px-6">
      <div class="flex items-center gap-3">
        <button class="lg:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" @click="sidebarOpen = !sidebarOpen" aria-label="Toggle sidebar">
          <component :is="sidebarOpen ? X : Menu" class="w-5 h-5 text-slate-600 dark:text-slate-300" />
        </button>
        <NuxtLink to="/" class="flex items-center gap-2 group">
          <BrandLogo size="sm" />
        </NuxtLink>
      </div>
      <div class="flex items-center gap-2">
        <NuxtLink to="/" class="btn-ghost hidden sm:inline-flex text-sm"><Home class="w-4 h-4" /> Site</NuxtLink>
        <ThemeToggle />
        <NuxtLink to="/notifications" class="btn-ghost hidden sm:inline-flex text-sm !px-2" aria-label="Notifications"><Bell class="w-4.5 h-4.5" /></NuxtLink>
        <ClientOnly>
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-brand-600 text-white text-sm font-bold flex items-center justify-center uppercase">
            {{ auth.user.value?.full_name?.slice(0, 1) || '?' }}
          </div>
          <div class="hidden sm:block leading-tight">
            <div class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ auth.user.value?.full_name }}</div>
            <div class="text-xs text-slate-500 dark:text-slate-400 capitalize">{{ auth.user.value?.role }}</div>
          </div>
        </div>
          <template #fallback><div class="w-8 h-8 rounded-full bg-slate-200 animate-pulse" /></template>
        </ClientOnly>
        <button @click="doLogout" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 dark:text-slate-500 hover:text-rose-500 transition" aria-label="Sign out">
          <LogOut class="w-4.5 h-4.5" />
        </button>
      </div>
    </header>

    <div class="flex flex-1">
      <!-- sidebar -->
      <div class="hidden lg:block w-64 shrink-0 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800" aria-hidden="true" />
      <aside
        class="fixed top-14 left-0 z-30 h-[calc(100vh-3.5rem)] w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 py-4 px-3 overflow-y-auto nice-scroll transition-transform"
        :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'" aria-label="Dashboard navigation">
        <!-- signed-in state is only known in the browser (session cookies are scoped to /api) -->
        <ClientOnly>
        <nav class="space-y-0.5">
          <template v-for="item in navMain" :key="item.to || item.heading">
            <div v-if="item.heading" class="pt-3 pb-1 px-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">{{ item.heading }}</div>
            <NuxtLink v-else :to="item.to!"
              class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition"
              :class="isActive(item.to!) ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300' : 'text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800'">
              <component :is="item.icon" class="w-4.5 h-4.5" />
              <span class="flex-1">{{ item.label }}</span>
              <span v-if="item.badge" class="badge bg-amber-100 text-amber-800">{{ item.badge }}</span>
            </NuxtLink>
          </template>

          <div class="pt-3 pb-1 px-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Account</div>
          <NuxtLink v-for="item in navShared" :key="item.to" :to="item.to"
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition"
            :class="route.path.startsWith(item.to) ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300' : 'text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800'">
            <component :is="item.icon" class="w-4.5 h-4.5" />
            {{ item.label }}
          </NuxtLink>
        </nav>

        <!-- course manage subnav -->
        <template v-if="teachTabs">
          <div class="pt-4 pb-1 px-3 border-t border-slate-100 dark:border-slate-800 mt-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Manage course
          </div>
          <nav class="space-y-0.5">
            <NuxtLink v-for="t in teachTabs" :key="t.to" :to="t.to"
              class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition"
              :class="route.path === t.to ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300 font-semibold' : 'text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800'">
              <component :is="t.icon" class="w-4 h-4" />
              {{ t.label }}
            </NuxtLink>
          </nav>
        </template>
          <template #fallback>
            <div class="space-y-2 px-1" aria-hidden="true"><div v-for="i in 6" :key="i" class="h-9 rounded-lg bg-slate-100 animate-pulse" /></div>
          </template>
        </ClientOnly>
      </aside>

      <!-- overlay for mobile -->
      <div v-if="sidebarOpen" class="fixed inset-0 top-14 bg-slate-900/50 dark:bg-black/60 z-20 lg:hidden" @click="sidebarOpen = false" />

      <main class="flex-1 min-w-0 p-4 sm:p-6 lg:p-8 w-full">
        <ClientOnly>
          <slot />
          <template #fallback>
            <div class="space-y-4" aria-busy="true" aria-label="Loading"><div class="h-8 w-56 rounded-lg bg-slate-200 animate-pulse" /><div class="card h-40 animate-pulse" /></div>
          </template>
        </ClientOnly>
      </main>
    </div>
  </div>
</template>
