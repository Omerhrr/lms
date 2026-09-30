<script setup lang="ts">
import { Bell, CheckCheck, GraduationCap, Megaphone, BarChart3, MessageSquare, BookOpen, Star } from 'lucide-vue-next'

useSeoMeta({ title: 'Notifications - LearnHub' })
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const items = ref<any[]>([])
const loading = ref(true)
const page = ref(1)
const pages = ref(1)

const icons: Record<string, any> = {
  enrollment: BookOpen, certificate: GraduationCap, grade: BarChart3,
  discussion: MessageSquare, announcement: Megaphone, system: Star,
}

const load = async () => {
  loading.value = true
  try {
    const res = await api.get<any>('/notifications', { page: page.value, size: 15 })
    items.value = res.items
    pages.value = res.pages
  } finally { loading.value = false }
}

const markAll = async () => {
  try {
    await api.post('/notifications/read-all')
    items.value.forEach(n => n.is_read = true)
  } catch { /* the api client already showed the error */ }
}

const open = async (n: any) => {
  if (!n.is_read) {
    n.is_read = true
    api.post(`/notifications/${n.id}/read`).catch(() => {})
  }
  if (n.link && n.link !== '#') navigateTo(n.link)
}

onMounted(load)
watch(page, load)
</script>

<template>
  <div class="max-w-3xl">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-extrabold text-slate-900 flex items-center gap-2">
        <Bell class="w-6 h-6 text-brand-600" /> Notifications
      </h1>
      <button v-if="items.some(n => !n.is_read)" @click="markAll" class="btn-secondary text-sm">
        <CheckCheck class="w-4 h-4" /> Mark all read
      </button>
    </div>

    <div v-if="loading" class="space-y-3">
      <div v-for="i in 4" :key="i" class="card h-20 animate-pulse" />
    </div>

    <EmptyState v-else-if="items.length === 0" empty>You're all caught up!</EmptyState>

    <div v-else class="space-y-2.5">
      <button v-for="n in items" :key="n.id" @click="open(n)"
        class="w-full card p-4 flex items-start gap-3.5 text-left transition hover:border-brand-300"
        :class="n.is_read ? 'opacity-70' : 'border-l-4 border-l-brand-500'">
        <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          :class="n.is_read ? 'bg-slate-100 text-slate-400' : 'bg-brand-50 text-brand-600'">
          <component :is="icons[n.type] || Star" class="w-5 h-5" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-semibold text-sm" :class="n.is_read ? 'text-slate-600' : 'text-slate-900'">{{ n.title }}</p>
          <p v-if="n.body" class="text-sm text-slate-500 mt-0.5 line-clamp-2">{{ n.body }}</p>
          <p class="text-xs text-slate-400 mt-1">{{ new Date(n.created_at).toLocaleString() }}</p>
        </div>
        <span v-if="!n.is_read" class="w-2.5 h-2.5 rounded-full bg-brand-500 mt-1.5 shrink-0" />
      </button>
    </div>

    <div v-if="pages > 1" class="mt-6 flex justify-center gap-1.5">
      <button v-for="p in pages" :key="p" @click="page = p"
        class="w-9 h-9 rounded-lg text-sm font-semibold"
        :class="p === page ? 'bg-brand-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'">
        {{ p }}
      </button>
    </div>
  </div>
</template>
