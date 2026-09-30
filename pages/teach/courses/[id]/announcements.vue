<script setup lang="ts">
import { Megaphone, Trash2, Send } from 'lucide-vue-next'

useSeoMeta({ title: 'Announcements - LearnHub' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const route = useRoute()
const api = useApi()
const { show } = useToast()
const courseId = Number(route.params.id)

const items = ref<any[]>([])
const loading = ref(true)
const form = ref({ title: '', body: '' })
const posting = ref(false)

const load = async () => {
  loading.value = true
  try { items.value = await api.get<any[]>(`/courses/${courseId}/announcements`) } finally { loading.value = false }
}
onMounted(load)

const post = async () => {
  if (!form.value.title.trim()) return show('Give it a title', 'error')
  posting.value = true
  try {
    await api.post(`/teach/courses/${courseId}/announcements`, form.value)
    show('Announcement sent to all enrolled students!')
    form.value = { title: '', body: '' }
    await load()
  } catch { /* the api client already showed the error */ } finally { posting.value = false }
}

const remove = async (id: number) => {
  if (!confirm('Delete this announcement?')) return
  await api.del(`/teach/announcements/${id}`)
  show('Deleted', 'info')
  await load()
}

const fmt = (iso: string) => new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
</script>

<template>
  <div class="max-w-3xl">
    <div class="mb-6">
      <h1 class="text-2xl font-extrabold text-slate-900">Announcements</h1>
      <p class="text-slate-500 mt-1">Broadcast updates to every enrolled student (they get an in-app notification)</p>
    </div>

    <div class="card p-5 mb-8">
      <div class="flex items-center gap-2 mb-3">
        <Megaphone class="w-4.5 h-4.5 text-amber-500" />
        <h2 class="font-bold text-slate-800 text-sm">New announcement</h2>
      </div>
      <input v-model="form.title" class="input mb-2" placeholder="Title - e.g. Live Q&A this Friday" />
      <textarea v-model="form.body" class="input min-h-[90px]" placeholder="Details your students should know…" />
      <button class="btn-primary mt-3" :disabled="posting" @click="post">
        <Send class="w-4 h-4" /> {{ posting ? 'Publishing…' : 'Publish announcement' }}
      </button>
    </div>

    <div v-if="loading" class="space-y-3"><div v-for="i in 2" :key="i" class="card h-24 animate-pulse" /></div>
    <EmptyState v-else-if="items.length === 0" empty>No announcements yet.</EmptyState>

    <div v-else class="space-y-3">
      <div v-for="a in items" :key="a.id" class="card p-5 flex gap-4">
        <div class="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center shrink-0">
          <Megaphone class="w-5 h-5 text-amber-500" />
        </div>
        <div class="flex-1 min-w-0">
          <h4 class="font-bold text-slate-800">{{ a.title }}</h4>
          <p class="text-sm text-slate-600 mt-1 whitespace-pre-wrap">{{ a.body }}</p>
          <p class="text-xs text-slate-400 mt-2">{{ fmt(a.created_at) }}</p>
        </div>
        <button class="p-1.5 rounded-lg hover:bg-rose-50 text-rose-400 h-fit shrink-0" @click="remove(a.id)" aria-label="Delete">
          <Trash2 class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>
