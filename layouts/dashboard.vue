<script setup lang="ts">
import {
  LayoutDashboard, BookOpen, GraduationCap, Bell, Settings, Shield,
  Menu, X, LogOut, FolderTree, Users, ClipboardList, Megaphone,
  BarChart3, Home
} from 'lucide-vue-next'

const auth = useAuth()
const route = useRoute()
const router = useRouter()
const { show } = useToast()

const sidebarOpen = ref(false)
watch(() => route.fullPath, () => { sidebarOpen.value = false })

const navMain = computed(() => {
  const u = auth.user.value
  if (!u) return []
  if (u.role === 'admin') {
    return [
      { label: 'Overview', to: '/admin', icon: Shield },
      { label: 'Users', to: '/admin/users', icon: Users },
      { label: 'Categories', to: '/admin/categories', icon: FolderTree },
      { label: 'Browse Courses', to: '/courses', icon: BookOpen },
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
  ]
})

const navShared = [
  { label: 'Certificates', to: '/certificates', icon: GraduationCap },
  { label: 'Notifications', to: '/notifications', icon: Bell },
  { label: 'Profile', to: '/profile', icon: Settings },
]

const teachTabs = computed(() => {
  const m = route.path.match(/^\/teach\/courses\/(\d+)(\/.*)?/)
  if (!m) return null
  const id = m[1]
  return [
    { label: 'Course Settings', to: `/teach/courses/${id}/edit`, icon: Settings, exact: false },
    { label: 'Curriculum Builder', to: `/teach/courses/${id}/builder`, icon: FolderTree },
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
  <div class="min-h-screen flex flex-col bg-slate-50">
    <!-- top bar -->
    <header class="sticky top-0 z-40 bg-white border-b border-slate-200 h-14 flex items-center justify-between px-4 sm:px-6">
      <div class="flex items-center gap-3">
        <button class="lg:hidden p-2 rounded-lg hover:bg-slate-100" @click="sidebarOpen = !sidebarOpen" aria-label="Toggle sidebar">
          <component :is="sidebarOpen ? X : Menu" class="w-5 h-5 text-slate-600" />
        </button>
        <NuxtLink to="/" class="flex items-center gap-2">
          <img src="/logo.svg" alt="LearnHub" class="w-8 h-8" />
          <span class="text-lg font-extrabold tracking-tight text-slate-900 hidden sm:block">Learn<span class="text-brand-600">Hub</span></span>
        </NuxtLink>
      </div>
      <div class="flex items-center gap-3">
        <NuxtLink to="/" class="btn-ghost hidden sm:inline-flex text-sm"><Home class="w-4 h-4" /> Site</NuxtLink>
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-brand-600 text-white text-sm font-bold flex items-center justify-center uppercase">
            {{ auth.user.value?.full_name.slice(0, 1) }}
          </div>
          <div class="hidden sm:block leading-tight">
            <div class="text-sm font-semibold text-slate-800">{{ auth.user.value?.full_name }}</div>
            <div class="text-[11px] text-slate-400 capitalize">{{ auth.user.value?.role }}</div>
          </div>
        </div>
        <button @click="doLogout" class="p-2 rounded-lg hover:bg-slate-100 text-slate-400" aria-label="Sign out">
          <LogOut class="w-4.5 h-4.5" />
        </button>
      </div>
    </header>

    <div class="flex flex-1">
      <!-- sidebar -->
      <aside
        class="fixed lg:sticky top-14 z-30 h-[calc(100vh-3.5rem)] w-64 bg-white border-r border-slate-200 py-4 px-3 overflow-y-auto nice-scroll transition-transform"
        :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'">
        <nav class="space-y-0.5">
          <NuxtLink v-for="item in navMain" :key="item.to" :to="item.to"
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition"
            :class="route.path === item.to ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-50'">
            <component :is="item.icon" class="w-4.5 h-4.5" />
            {{ item.label }}
          </NuxtLink>

          <div class="pt-3 pb-1 px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400">Account</div>
          <NuxtLink v-for="item in navShared" :key="item.to" :to="item.to"
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition"
            :class="route.path.startsWith(item.to) ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-50'">
            <component :is="item.icon" class="w-4.5 h-4.5" />
            {{ item.label }}
          </NuxtLink>
        </nav>

        <!-- course manage subnav -->
        <template v-if="teachTabs">
          <div class="pt-4 pb-1 px-3 border-t border-slate-100 mt-3 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Manage course
          </div>
          <nav class="space-y-0.5">
            <NuxtLink v-for="t in teachTabs" :key="t.to" :to="t.to"
              class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition"
              :class="route.path === t.to ? 'bg-brand-50 text-brand-700 font-semibold' : 'text-slate-600 hover:bg-slate-50'">
              <component :is="t.icon" class="w-4 h-4" />
              {{ t.label }}
            </NuxtLink>
          </nav>
        </template>
      </aside>

      <!-- overlay for mobile -->
      <div v-if="sidebarOpen" class="fixed inset-0 top-14 bg-slate-900/30 z-20 lg:hidden" @click="sidebarOpen = false" />

      <main class="flex-1 min-w-0 p-4 sm:p-6 lg:p-8 w-full">
        <slot />
      </main>
    </div>
  </div>
</template>
